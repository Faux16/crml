"""
Core Monte Carlo simulation engine for CRML.
"""
import time
import numpy as np
from typing import Union, Optional, Dict, List

from crml_lang.models.crml_model import load_crml_from_yaml_str, CRScenarioSchema
from ..models.result_model import SimulationResult, Metrics, Distribution, Metadata
from ..models.fx_model import FXConfig, convert_currency, get_currency_symbol, normalize_fx_config
from ..models.constants import DEFAULT_FX_RATES
from ..controls import apply_control_effectiveness

from .frequency import FrequencyEngine
from .severity import SeverityEngine


def _normalize_cardinality(cardinality: int | None) -> int:
    try:
        value = int(cardinality) if cardinality is not None else 1
    except Exception:
        value = 1
    return max(1, value)


def _coerce_multiplier(
    multiplier: Optional[object],
    *,
    n_runs: int,
    label: str,
    result: SimulationResult,
) -> Optional[object]:
    if multiplier is None:
        return None

    if isinstance(multiplier, (int, float, np.floating)):
        return float(multiplier)

    arr = np.asarray(multiplier, dtype=np.float64)
    if arr.shape != (n_runs,):
        result.errors.append(f"{label} must be a scalar or shape (n_runs,)")
        return None
    return arr


def _load_scenario_document(yaml_content: Union[str, dict], *, result: SimulationResult) -> Optional[CRScenarioSchema]:
    try:
        if isinstance(yaml_content, str):
            import os

            if os.path.isfile(yaml_content):
                with open(yaml_content, 'r', encoding='utf-8') as f:
                    yaml_str = f.read()
                return load_crml_from_yaml_str(yaml_str)
            return load_crml_from_yaml_str(yaml_content)

        if isinstance(yaml_content, dict):
            return CRScenarioSchema.model_validate(yaml_content)

        result.errors.append("Invalid input type")
        return None
    except Exception as e:
        result.errors.append(f"Parsing error: {str(e)}")
        return None


def _validate_supported_models(
    *,
    frequency_model: str,
    severity_model: str,
    result: SimulationResult,
) -> bool:
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
    seed: int | None,
    fx_config: FXConfig,
    cardinality: int,
    frequency_model: str,
    frequency_params: object,
    severity_model: str,
    severity_params: object,
    severity_components: Optional[object],
    frequency_rate_multiplier: Optional[object],
    severity_loss_multiplier: Optional[object],
) -> np.ndarray:
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
    )

    if len(severities) != total_events:
        severities = np.zeros(total_events)

    losses = _aggregate_severities_by_count(counts, severities)
    if severity_loss_multiplier is not None:
        losses = losses * severity_loss_multiplier
    return losses


def _apply_output_currency(losses_base: np.ndarray, *, fx_config: FXConfig) -> np.ndarray:
    losses_base = np.asarray(losses_base, dtype=np.float64)
    if fx_config.base_currency == fx_config.output_currency:
        return losses_base

    factor = convert_currency(1.0, fx_config.base_currency, fx_config.output_currency, fx_config)
    return losses_base * factor


def _compute_metrics_and_distribution(losses: np.ndarray, *, raw_data_limit: Optional[int]) -> tuple[Metrics, Distribution]:
    losses = np.asarray(losses, dtype=np.float64)

    metrics = Metrics(
        eal=float(np.mean(losses)),
        var_95=float(np.percentile(losses, 95)),
        var_99=float(np.percentile(losses, 99)),
        var_999=float(np.percentile(losses, 99.9)),
        min=float(np.min(losses)),
        max=float(np.max(losses)),
        median=float(np.median(losses)),
        std_dev=float(np.std(losses)),
    )

    hist, bin_edges = np.histogram(losses, bins=50)
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
    n_runs: int = 10000,
    seed: int = None,
    fx_config: Optional[FXConfig] = None,
    cardinality: int = 1,
    frequency_rate_multiplier: Optional[object] = None,
    severity_loss_multiplier: Optional[object] = None,
    raw_data_limit: Optional[int] = 1000,
) -> SimulationResult:
    """
    Orchestrates the Monte Carlo simulation.
    """
    start_time = time.time()

    fx_config = normalize_fx_config(fx_config)
    output_symbol = get_currency_symbol(fx_config.output_currency)
    if seed is not None:
        np.random.seed(seed)

    result = SimulationResult(
        success=False,
        metrics=Metrics(),
        distribution=Distribution(),
        metadata=Metadata(
            runs=n_runs,
            seed=seed,
            currency=output_symbol,
            currency_code=fx_config.output_currency,
        ),
        errors=[],
    )

    crml_obj = _load_scenario_document(yaml_content, result=result)
    if crml_obj is None:
        return result

    meta = crml_obj.meta
    result.metadata.model_name = meta.name
    result.metadata.model_version = meta.version or 'N/A'
    result.metadata.description = meta.description or ''

    scenario = crml_obj.scenario
    freq = scenario.frequency
    sev = scenario.severity

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
            severity_components=sev.components,
            frequency_rate_multiplier=freq_mult,
            severity_loss_multiplier=sev_mult,
        )

        losses_out = _apply_output_currency(losses_base, fx_config=fx_config)
        metrics, distribution = _compute_metrics_and_distribution(losses_out, raw_data_limit=raw_data_limit)
        result.metrics = metrics
        result.distribution = distribution
        result.metadata.runtime_ms = (time.time() - start_time) * 1000
        result.success = True
        return result
    except Exception as e:
        result.errors.append(f"Simulation execution error: {str(e)}")
        return result
