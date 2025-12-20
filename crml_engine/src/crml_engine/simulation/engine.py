"""Core Monte Carlo simulation engine for CRML.

This module contains the reference Monte Carlo implementation used by
`crml_engine.runtime`.

Inputs:
    - CRML scenario documents (YAML text, parsed dict, or file path)
    - Optional per-run multipliers for frequency/severity (used by portfolios
      and control modeling)

Outputs:
    - `SimulationResult` including summary metrics and distribution artifacts.
"""
import os
import time

import numpy as np

from crml_lang.models.scenario_model import load_crml_from_yaml_str, CRScenario
from ..models.result_model import SimulationResult, Metrics, Distribution, Metadata
from ..models.fx_model import FXConfig, convert_currency, get_currency_symbol, normalize_fx_config
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from .frequency import FrequencyEngine
from .severity import SeverityEngine
from .utils import format_pydantic_error


DEFAULT_N_RUNS = 10_000
DEFAULT_RAW_DATA_LIMIT = 1_000
MILLISECONDS_PER_SECOND = 1_000.0

PERCENTILE_VAR_95 = 95
PERCENTILE_VAR_99 = 99
PERCENTILE_VAR_999 = 99.9

HISTOGRAM_BINS_MIN = 50
HISTOGRAM_BINS_MAX = 200
HISTOGRAM_EMPTY_MAX_EDGE = 1.0


def _normalize_cardinality(cardinality: Optional[int]) -> int:
    """Normalize exposure cardinality to a positive integer.

    Args:
        cardinality: Optional input value.

    Returns:
        An integer >= 1. Invalid inputs are treated as 1.
    """
    try:
        value = int(cardinality) if cardinality is not None else 1
    except (TypeError, ValueError):
        value = 1
    return max(1, value)


def _coerce_multiplier(
    multiplier: Optional[object],
    *,
    n_runs: int,
    label: str,
    result: SimulationResult,
) -> Optional[object]:
    """Validate and normalize a multiplier argument.

    The engine accepts either:
        - a scalar (int/float) applied to all runs, or
        - a 1-D array-like of shape (n_runs,) for per-run multipliers.

    On shape/type errors, this appends a message to `result.errors` and returns
    None.

    Args:
        multiplier: Candidate multiplier value.
        n_runs: Expected number of runs.
        label: Label used in error messages.
        result: SimulationResult used to accumulate errors.

    Returns:
        None if input was None, a float scalar, or a numpy float64 array of
        shape (n_runs,).
    """
    if multiplier is None:
        return None

    if isinstance(multiplier, (int, float, np.floating)):
        return float(multiplier)

    arr = np.asarray(multiplier, dtype=np.float64)
    if arr.shape != (n_runs,):
        result.errors.append(f"{label} must be a scalar or shape (n_runs,)")
        return None
    return arr


def _load_scenario_document(yaml_content: Union[str, dict], *, result: SimulationResult) -> Optional[CRScenario]:
    """Parse and validate a CRML scenario from supported input types.

    Args:
        yaml_content: Either a YAML string, a file path to a YAML document, or
            a parsed dict.
        result: Result object used to collect parsing/validation errors.

    Returns:
        A validated `CRScenario` on success, otherwise None.

    Notes:
        Errors are recorded in `result.errors` rather than raised.
    """
    try:
        if isinstance(yaml_content, str):
            if os.path.isfile(yaml_content):
                with open(yaml_content, 'r', encoding='utf-8') as f:
                    yaml_str = f.read()
                return load_crml_from_yaml_str(yaml_str)
            return load_crml_from_yaml_str(yaml_content)

        if isinstance(yaml_content, dict):
            return CRScenario.model_validate(yaml_content)

        result.errors.append("Invalid input type")
        return None
    except Exception as e:
        from pydantic import ValidationError
        if isinstance(e, ValidationError):
            result.errors.extend(format_pydantic_error(e))
        else:
            result.errors.append(f"Parsing error: {e}")
        return None


def _validate_supported_models(
    *,
    frequency_model: str,
    severity_model: str,
    result: SimulationResult,
) -> bool:
    """Validate that the configured frequency/severity models are supported.

    Args:
        frequency_model: Frequency model name from the CRML scenario.
        severity_model: Severity model name from the CRML scenario.
        result: Result object used to accumulate errors.

    Returns:
        True if both models are supported, else False.
    """
    supported_frequency_models = {"poisson", "gamma", "hierarchical_gamma_poisson"}
    supported_severity_models = {"lognormal", "gamma", "mixture"}

    if not frequency_model or frequency_model not in supported_frequency_models:
        result.errors.append(f"Unsupported frequency model: {frequency_model}")
        return False

    if not severity_model or severity_model not in supported_severity_models:
        result.errors.append(f"Unsupported severity model: {severity_model}")
        return False

    return True


def _aggregate_severities_by_count(counts: np.ndarray, severities: np.ndarray) -> np.ndarray:
    """Sum per-event severities into per-run annual losses.

    Args:
        counts: Integer event counts per run (shape: (n_runs,)).
        severities: Per-event loss samples concatenated across runs
            (shape: (sum(counts),)).

    Returns:
        Per-run total loss array of shape (n_runs,).
    """
    current_idx = 0
    losses: list[float] = []
    for c in counts:
        if c > 0:
            loss = float(np.sum(severities[current_idx : current_idx + c]))
            losses.append(loss)
            current_idx += c
        else:
            losses.append(0.0)
    return np.asarray(losses, dtype=np.float64)


def _simulate_annual_losses(
    *,
    n_runs: int,
    seed: Optional[int],
    fx_config: FXConfig,
    cardinality: int,
    frequency_model: str,
    frequency_params: object,
    severity_model: str,
    severity_params: object,
    severity_components: Optional[List[Dict[str, Any]]],
    frequency_rate_multiplier: Optional[object],
    severity_loss_multiplier: Optional[object],
) -> np.ndarray:
    """Simulate annual loss samples in the base currency.

    This generates event counts using `FrequencyEngine`, generates per-event
    severities using `SeverityEngine`, then aggregates to annual loss per run.

    Args:
        n_runs: Number of Monte Carlo iterations.
        seed: Optional seed.
        fx_config: FX configuration used for currency normalization.
        cardinality: Exposure multiplier (e.g., number of assets in scope).
        frequency_model: Frequency model name.
        frequency_params: Parsed frequency parameters.
        severity_model: Severity model name.
        severity_params: Parsed severity parameters.
        severity_components: Optional mixture components.
        frequency_rate_multiplier: Optional scalar or per-run multiplier.
        severity_loss_multiplier: Optional scalar or per-run multiplier.

    Returns:
        Array of per-run annual losses in the FX base currency.
    """
    counts = FrequencyEngine.generate_frequency(
        freq_model=frequency_model,
        params=frequency_params,
        n_runs=n_runs,
        cardinality=cardinality,
        seed=seed,
        uniforms=None,
        rate_multiplier=frequency_rate_multiplier,
    )

    total_events = int(np.sum(counts))
    if total_events <= 0:
        return np.zeros(n_runs, dtype=np.float64)

    severities = SeverityEngine.generate_severity(
        sev_model=severity_model,
        params=severity_params,
        components=severity_components,
        total_events=total_events,
        fx_config=fx_config,
        seed=None if seed is None else int(seed) + 1,
    )

    if len(severities) != total_events:
        severities = np.zeros(total_events)

    losses = _aggregate_severities_by_count(counts, severities)
    if severity_loss_multiplier is not None:
        losses = losses * severity_loss_multiplier
    return losses


def _apply_output_currency(losses_base: np.ndarray, *, fx_config: FXConfig) -> np.ndarray:
    """Convert base-currency losses to the configured output currency."""
    losses_base = np.asarray(losses_base, dtype=np.float64)
    if fx_config.base_currency == fx_config.output_currency:
        return losses_base

    factor = convert_currency(1.0, fx_config.base_currency, fx_config.output_currency, fx_config)
    return losses_base * factor


def _compute_metrics_and_distribution(losses: np.ndarray, *, raw_data_limit: Optional[int]) -> Tuple[Metrics, Distribution]:
    """Compute summary statistics and histogram artifacts for loss samples.

    Args:
        losses: Per-run annual loss array.
        raw_data_limit: Optional cap for returned raw samples. If None, returns
            all samples.

    Returns:
        (metrics, distribution)
    """
    losses = np.asarray(losses, dtype=np.float64)

    metrics = Metrics(
        eal=float(np.mean(losses)),
        var_95=float(np.percentile(losses, PERCENTILE_VAR_95)),
        var_99=float(np.percentile(losses, PERCENTILE_VAR_99)),
        var_999=float(np.percentile(losses, PERCENTILE_VAR_999)),
        min=float(np.min(losses)),
        max=float(np.max(losses)),
        median=float(np.median(losses)),
        std_dev=float(np.std(losses)),
    )

    # Histogram binning:
    # - Smaller steps (more bins) improve readability near $0.
    # - But too many bins makes the chart noisy for a finite number of runs.
    # Use a simple, stable heuristic: bins ~ sqrt(n_runs), clamped.
    n_runs = int(losses.size)
    bin_count = int(np.clip(int(np.sqrt(max(n_runs, 1))), HISTOGRAM_BINS_MIN, HISTOGRAM_BINS_MAX))

    max_loss = float(np.max(losses)) if n_runs > 0 else 0.0
    if max_loss <= 0:
        # All-zero (or empty) distribution: keep a minimal, well-defined range.
        bin_edges = np.asarray([0.0, HISTOGRAM_EMPTY_MAX_EDGE], dtype=np.float64)
        hist = np.asarray([n_runs], dtype=np.int64)
    else:
        # Force the range to start at 0 so the histogram consistently represents
        # "nothing happens" mass (loss==0) and plots from $0 in the UI.
        hist, bin_edges = np.histogram(losses, bins=bin_count, range=(0.0, max_loss))
    if raw_data_limit is None:
        raw = losses.tolist()
    else:
        raw = losses.tolist()[: int(raw_data_limit)]

    distribution = Distribution(
        bins=bin_edges.tolist(),
        frequencies=hist.tolist(),
        raw_data=raw,
    )

    return metrics, distribution


def run_monte_carlo(
    yaml_content: Union[str, dict],
    n_runs: int = DEFAULT_N_RUNS,
    seed: Optional[int] = None,
    fx_config: FXConfig | Mapping[str, Any] | None = None,
    cardinality: int = 1,
    frequency_rate_multiplier: Optional[object] = None,
    severity_loss_multiplier: Optional[object] = None,
    raw_data_limit: Optional[int] = DEFAULT_RAW_DATA_LIMIT,
) -> SimulationResult:
    """Run the reference Monte Carlo simulation for a CRML scenario.

    Supported inputs:
        - YAML string of a CRML scenario document
        - Parsed dict matching the CRML schema
        - File path to a YAML scenario document

    Frequency/severity modifiers:
        `frequency_rate_multiplier` and `severity_loss_multiplier` can be used
        to apply control effects or other adjustments. They may be either a
        scalar (applied to all runs) or an array of shape (n_runs,).

    Args:
        yaml_content: Scenario input.
        n_runs: Number of Monte Carlo iterations.
        seed: Optional RNG seed.
        fx_config: Optional FX config; if omitted, defaults are used.
        cardinality: Exposure multiplier (>=1). For portfolios, this is often
            the number of assets the scenario applies to.
        frequency_rate_multiplier: Optional scalar/array multiplier for the
            scenario frequency rate.
        severity_loss_multiplier: Optional scalar/array multiplier applied to
            per-run annual loss.
        raw_data_limit: Maximum number of raw samples included in the returned
            `Distribution.raw_data`. Use None to include all.

    Returns:
        A `SimulationResult`. On failure, `success=False` and errors are
        populated.
    """
    start_time = time.time()

    fx_config = normalize_fx_config(fx_config)
    output_symbol = get_currency_symbol(fx_config.output_currency)
    if seed is not None:
        np.random.seed(seed)

    result = SimulationResult(
        success=False,
        metrics=Metrics.model_validate({}),
        distribution=Distribution.model_validate({}),
        metadata=Metadata(
            runs=n_runs,
            seed=seed,
            currency=output_symbol,
            currency_code=fx_config.output_currency,
            model_name=None,
            model_version=None,
            description=None,
            runtime_ms=None,
            lambda_baseline=None,
            lambda_effective=None,
            controls_applied=None,
            control_reduction_pct=None,
            control_details=None,
            control_warnings=None,
            correlation_info=None,
        ),
        errors=[],
    )

    crml_obj = _load_scenario_document(yaml_content, result=result)
    if crml_obj is None:
        return result

    meta = crml_obj.meta
    assert result.metadata is not None
    result.metadata.model_name = meta.name
    result.metadata.model_version = meta.version or 'N/A'
    result.metadata.description = meta.description or ''

    scenario = crml_obj.scenario
    freq = scenario.frequency
    sev = scenario.severity

    severity_components_any = getattr(sev, "components", None)
    severity_components: List[Dict[str, Any]] | None = None
    if isinstance(severity_components_any, list) and all(isinstance(x, dict) for x in severity_components_any):
        severity_components = severity_components_any

    cardinality = _normalize_cardinality(cardinality)

    freq_mult = _coerce_multiplier(
        frequency_rate_multiplier,
        n_runs=n_runs,
        label="frequency_rate_multiplier",
        result=result,
    )
    if result.errors:
        return result

    sev_mult = _coerce_multiplier(
        severity_loss_multiplier,
        n_runs=n_runs,
        label="severity_loss_multiplier",
        result=result,
    )
    if result.errors:
        return result

    if not _validate_supported_models(
        frequency_model=freq.model,
        severity_model=sev.model,
        result=result,
    ):
        return result

    try:
        losses_base = _simulate_annual_losses(
            n_runs=n_runs,
            seed=seed,
            fx_config=fx_config,
            cardinality=cardinality,
            frequency_model=freq.model,
            frequency_params=freq.parameters,
            severity_model=sev.model,
            severity_params=sev.parameters,
            severity_components=severity_components,
            frequency_rate_multiplier=freq_mult,
            severity_loss_multiplier=sev_mult,
        )

        losses_out = _apply_output_currency(losses_base, fx_config=fx_config)
        metrics, distribution = _compute_metrics_and_distribution(losses_out, raw_data_limit=raw_data_limit)
        result.metrics = metrics
        result.distribution = distribution
        result.metadata.runtime_ms = (time.time() - start_time) * MILLISECONDS_PER_SECOND
        result.success = True
        return result
    except (TypeError, ValueError, RuntimeError) as e:
        result.errors.append(f"Simulation execution error: {e}")
        return result
    except Exception as e:  # NOSONAR
        # Defensive catch-all: ensure the API returns a structured error rather than crashing.
        result.errors.append(f"Simulation execution error: {e}")
        return result
