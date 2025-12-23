"""Runtime entry points for the reference CRML simulation engine.

This module provides user-facing convenience functions that:

- Run a single CRML scenario (YAML string, dict, or file path)
- Run a CRML portfolio (portfolio YAML with scenario references)
- Produce the engine-agnostic `CRSimulationResult`
- Provide CLI-friendly wrappers (printing / JSON output)

The numerical model implementation lives in `crml_engine.simulation.*`.
Portfolio planning/binding resolution lives in `crml_engine.pipeline`.
"""

import json
from typing import Union, Optional, Tuple, Any

import hashlib
import os
import yaml

from crml_engine.pipeline import plan_bundle
import numpy as np

from .models.result_model import (
    SimulationResult as EngineSimulationResult,
    Metrics,
    Distribution,
    Metadata,
    print_result,
)
# NOTE: We intentionally avoid static imports from `crml_lang.models.*` here.
# In some dev environments, VS Code/Pylance may resolve `crml_lang` to an
# installed package version instead of the in-repo workspace package, causing
# false-positive import errors. We instead import the envelope models lazily
# where needed.
from .models.fx_model import (
    FXConfig,
    convert_currency,
    load_fx_config,
    normalize_fx_config,
    get_currency_symbol
)

from .models.constants import DEFAULT_FX_RATES
from .simulation.engine import run_monte_carlo
from .simulation.severity import SeverityEngine
from .copula import gaussian_copula_uniforms


LOSS_VAR_ID = "loss.var"
VALUE_AT_RISK_LABEL = "Value at Risk"

LOSS_ANNUAL_ID = "loss.annual"
LOSS_ANNUAL_LABEL = "Annual Loss"


def _sha256_digest_bytes(data: bytes) -> str:
    """Return a sha256 digest string with a stable prefix."""
    h = hashlib.sha256()
    h.update(data)
    return "sha256:" + h.hexdigest()


def _input_reference_from_yaml_content(yaml_content: Union[str, dict]) -> Any:
    """Best-effort input reference for traceability.

    This is intentionally engine-agnostic: it records where the input came from
    and a digest to support audit/repro.
    """
    uri: Optional[str] = None
    digest: Optional[str] = None

    if isinstance(yaml_content, str):
        if os.path.isfile(yaml_content):
            uri = yaml_content
            try:
                with open(yaml_content, "rb") as f:
                    digest = _sha256_digest_bytes(f.read())
            except Exception:
                digest = None
        else:
            digest = _sha256_digest_bytes(yaml_content.encode("utf-8"))
    elif isinstance(yaml_content, dict):
        try:
            stable = json.dumps(yaml_content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            digest = _sha256_digest_bytes(stable.encode("utf-8"))
        except Exception:
            digest = None

    sr = _simulation_result_models()
    return sr.InputReference(type="scenario", uri=uri, digest=digest)


def _try_parse_scenario(yaml_content: Union[str, dict]) -> Optional[Any]:
    """Parse a scenario for traceability extraction.

    This is separate from the simulation engine's parsing so trace extraction
    does not depend on internal engine state.
    """
    try:
        lang = _crml_lang_module()
        if isinstance(yaml_content, str) and os.path.isfile(yaml_content):
            with open(yaml_content, "r", encoding="utf-8") as f:
                return lang.CRScenario.load_from_yaml_str(f.read())
        if isinstance(yaml_content, str):
            return lang.CRScenario.load_from_yaml_str(yaml_content)
        if isinstance(yaml_content, dict):
            return lang.CRScenario.model_validate(yaml_content)
    except Exception:
        return None
    return None


def _approx_quantile_from_histogram(bin_edges: list[float], counts: list[int], p: float) -> Optional[float]:
    """Approximate quantile from a histogram using linear interpolation within bins."""
    if not bin_edges or not counts:
        return None
    if len(bin_edges) != len(counts) + 1:
        return None
    total = float(sum(counts))
    if total <= 0:
        return float(bin_edges[0])

    target = p * total
    cumulative = 0.0
    for i, c in enumerate(counts):
        c = float(c)
        next_cum = cumulative + c
        if target <= next_cum:
            left = float(bin_edges[i])
            right = float(bin_edges[i + 1])
            if c <= 0:
                return left
            frac = (target - cumulative) / c
            return left + frac * (right - left)
        cumulative = next_cum

    return float(bin_edges[-1])


def _tail_segment_mass_and_sum(
    *,
    left: float,
    right: float,
    count: float,
    threshold: float,
) -> tuple[float, float]:
    """Return (mass, mass_weighted_sum) for the segment >= threshold within a bin.

    Assumes uniform density within the bin.
    """
    width = right - left
    if count <= 0 or width <= 0:
        return 0.0, 0.0
    if right <= threshold:
        return 0.0, 0.0

    if left >= threshold:
        seg_left = left
        frac = 1.0
    else:
        seg_left = threshold
        frac = (right - threshold) / width

    mass = count * frac
    if mass <= 0:
        return 0.0, 0.0

    seg_mean = 0.5 * (seg_left + right)
    return mass, mass * seg_mean


def _approx_right_tail_expectation_from_histogram(
    bin_edges: list[float],
    counts: list[int],
    *,
    level: float,
) -> Optional[float]:
    """Approximate right-tail expectation (CVaR/ES) from histogram bins.

    Assumes uniform density within each bin.
    """
    if not bin_edges or not counts:
        return None
    if len(bin_edges) != len(counts) + 1:
        return None
    total = float(sum(counts))
    if total <= 0:
        return 0.0

    threshold = _approx_quantile_from_histogram(bin_edges, counts, level)
    if threshold is None:
        return None

    mass_accum = 0.0
    sum_accum = 0.0

    for i, c_int in enumerate(counts):
        mass, seg_sum = _tail_segment_mass_and_sum(
            left=float(bin_edges[i]),
            right=float(bin_edges[i + 1]),
            count=float(c_int),
            threshold=float(threshold),
        )
        mass_accum += mass
        sum_accum += seg_sum

    if mass_accum <= 0:
        return float(threshold)
    return sum_accum / mass_accum


def _simulation_result_models() -> Any:
    """Load `crml_lang` simulation-result envelope models lazily.

    This avoids module-level imports that can be mis-resolved in some IDE
    configurations.
    """
    from importlib import import_module

    return import_module("crml_lang.models.simulation_result")


def _crml_lang_module() -> Any:
    """Load the `crml_lang` top-level module lazily (as `Any`)."""
    from importlib import import_module

    return import_module("crml_lang")


def _populate_envelope_summaries(
    *,
    envelope: Any,
    result: EngineSimulationResult,
    currency_unit: Optional[Any],
    runs: Optional[int],
) -> None:
    """Populate `envelope.result.summaries` from engine outputs (best-effort)."""
    if result.metrics is None:
        return

    sr = _simulation_result_models()

    stats = sr.SummaryStatistics(
        mean=result.metrics.eal,
        median=result.metrics.median,
        std_dev=result.metrics.std_dev,
        quantiles=[],
        tail_expectations=[],
    )

    stats.quantiles.extend(
        [
            sr.Quantile(p=0.50, value=result.metrics.median),
            sr.Quantile(p=0.95, value=result.metrics.var_95),
            sr.Quantile(p=0.99, value=result.metrics.var_99),
        ]
    )

    estimation = sr.SummaryEstimation(
        computed_from="unknown",
        sample_count_used=runs,
        truncated=None,
        method=None,
    )

    dist = result.distribution
    if dist is not None and dist.bins and dist.frequencies:
        stats.quantiles.extend(
            [
                sr.Quantile(p=0.05, value=_approx_quantile_from_histogram(dist.bins, dist.frequencies, 0.05)),
                sr.Quantile(p=0.90, value=_approx_quantile_from_histogram(dist.bins, dist.frequencies, 0.90)),
            ]
        )

        stats.tail_expectations.extend(
            [
                sr.TailExpectation(
                    kind="cvar",
                    level=0.95,
                    tail="right",
                    value=_approx_right_tail_expectation_from_histogram(dist.bins, dist.frequencies, level=0.95),
                ),
                sr.TailExpectation(
                    kind="cvar",
                    level=0.99,
                    tail="right",
                    value=_approx_right_tail_expectation_from_histogram(dist.bins, dist.frequencies, level=0.99),
                ),
            ]
        )

        estimation.computed_from = "histogram"
        estimation.histogram_bins_used = max(len(dist.bins) - 1, 0)
        estimation.method = "histogram_linear_interpolation"

    envelope.result.summaries.append(
        sr.SummaryBlock(
            id=LOSS_ANNUAL_ID,
            label=LOSS_ANNUAL_LABEL,
            unit=currency_unit,
            stats=stats,
            estimation=estimation,
        )
    )


def _build_traceability(
    *,
    yaml_content: Union[str, dict],
    parsed_scenario: Optional[Any],
    fx_config: Optional[FXConfig],
) -> Any:
    """Build a best-effort Traceability object for the result envelope."""
    input_ref = _input_reference_from_yaml_content(yaml_content)

    sr = _simulation_result_models()

    trace = sr.Traceability(
        scenario_ids=[],
        inputs=[input_ref],
        model_components=[],
        dependencies=[],
        extra={},
    )

    if parsed_scenario is not None:
        scenario_name = parsed_scenario.meta.name
        trace.scenario_ids.append(scenario_name)
        input_ref.id = scenario_name
        input_ref.version = parsed_scenario.meta.version
        input_ref.metadata.update(
            {
                "description": parsed_scenario.meta.description,
                "tags": list(parsed_scenario.meta.tags) if getattr(parsed_scenario.meta, "tags", None) else [],
                "crml_scenario": getattr(parsed_scenario, "crml_scenario", None),
            }
        )

        trace.model_components.extend(
            [
                sr.ModelComponent(
                    id="frequency",
                    role="frequency",
                    model=parsed_scenario.scenario.frequency.model,
                    parameters={"parameters": parsed_scenario.scenario.frequency.parameters},
                    source_input_id=scenario_name,
                ),
                sr.ModelComponent(
                    id="severity",
                    role="severity",
                    model=parsed_scenario.scenario.severity.model,
                    parameters={
                        "parameters": parsed_scenario.scenario.severity.parameters,
                        "components": parsed_scenario.scenario.severity.components,
                    },
                    source_input_id=scenario_name,
                ),
            ]
        )

    if fx_config is not None:
        trace.model_components.append(
            sr.ModelComponent(
                id="fx",
                role="fx",
                model="fixed_rates",
                parameters={
                    "base_currency": fx_config.base_currency,
                    "output_currency": fx_config.output_currency,
                    "rates": fx_config.rates,
                },
            )
        )

    # Placeholder for future single-scenario dependencies.
    trace.dependencies.extend([])
    return trace


def _load_yaml_root_for_routing(source: Union[str, dict]) -> Optional[dict]:
    """Best-effort YAML load for routing.

    Returns the parsed root mapping when possible, otherwise None.
    """
    if isinstance(source, dict):
        return source
    if not isinstance(source, str):
        return None

    try:
        if os.path.isfile(source):
            with open(source, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
        else:
            loaded = yaml.safe_load(source)
    except Exception:
        return None

    return loaded if isinstance(loaded, dict) else None


def _infer_source_kind(source: Union[str, dict]) -> str:
    """Infer runtime source_kind for portfolio/bundle runners."""
    if isinstance(source, dict):
        return "data"
    if isinstance(source, str) and os.path.isfile(source):
        return "path"
    return "yaml"


def _route_simulation_document(
    *,
    root: dict,
    source: Union[str, dict],
    n_runs: int,
    seed: Optional[int],
    fx_config: Optional[FXConfig],
) -> Optional[EngineSimulationResult]:
    """Route a parsed YAML root to the appropriate simulation function."""
    kind = _infer_source_kind(source)

    if "crml_portfolio_bundle" in root:
        return run_portfolio_bundle_simulation(
            source,
            source_kind=kind,
            n_runs=n_runs,
            seed=seed,
            fx_config=fx_config,
        )

    if "crml_portfolio" in root:
        return _portfolio_error_result(
            "Refusing to simulate a raw 'crml_portfolio' input. "
            "Portfolios are non-executable inputs; create a 'crml_portfolio_bundle' first. "
            "Use the language-layer bundler API: from crml_lang import bundle_portfolio."
        )

    if "crml_scenario" in root:
        return _portfolio_error_result(
            "Refusing to simulate a raw 'crml_scenario' input. "
            "Scenarios are not executable in a vacuum; execute a 'crml_portfolio_bundle' that provides context. "
            "Use the language-layer bundler API: from crml_lang import bundle_portfolio."
        )

    return None


def _portfolio_error_result(msg: str) -> EngineSimulationResult:
    """Create a standardized failure `SimulationResult` for portfolio execution.

    Args:
        msg: Human-readable error message.

    Returns:
        A `SimulationResult` with `success=False` and `errors=[msg]`.
    """
    return EngineSimulationResult(
        success=False,
        metrics=None,
        distribution=None,
        metadata=None,
        errors=[msg],
    )


def _collect_control_info(scenarios: list[Any]) -> dict[str, dict[str, Any]]:
    """Collect minimal control metadata needed for sampling control state.

    The portfolio runtime can optionally sample a per-run binary state for each
    control (working vs failed) based on its reliability.

    Args:
        scenarios: Planned scenarios from `plan_portfolio()`. Each scenario is
            expected to have a `.controls` iterable with `.id`,
            `.combined_reliability`, and `.affects` attributes.

    Returns:
        Mapping control_id -> {"reliability": float, "affects": str}.
    """
    control_info: dict[str, dict[str, Any]] = {}
    for sc in scenarios:
        for c in sc.controls:
            control_info.setdefault(
                c.id,
                {
                    "reliability": float(c.combined_reliability) if c.combined_reliability is not None else 1.0,
                    "affects": str(c.affects) if c.affects is not None else "frequency",
                },
            )
    return control_info


def _extract_copula_targets(dependency: object) -> Tuple[list[str], Optional[np.ndarray]]:
    """Extract control-state copula targets and correlation matrix.

    The v1 portfolio dependency format allows specifying a Gaussian copula over
    a list of references like `control:<id>:state`, together with a correlation
    matrix.

    Args:
        dependency: Arbitrary dependency payload from the execution plan.

    Returns:
        (target_controls, corr)

        - target_controls: list of control ids (strings).
        - corr: correlation matrix as a float64 numpy array, or None.
    """
    dep = dependency if isinstance(dependency, dict) else {}
    cop = (dep.get("copula") if isinstance(dep, dict) else None) or None

    target_controls: list[str] = []
    corr = None
    if isinstance(cop, dict):
        targets = cop.get("targets")
        matrix = cop.get("matrix")
        if isinstance(targets, list) and isinstance(matrix, list):
            for t in targets:
                if isinstance(t, str) and t.startswith("control:") and t.endswith(":state"):
                    target_controls.append(t[len("control:") : -len(":state")])
            corr = np.asarray(matrix, dtype=np.float64)
    return target_controls, corr


def _sample_control_state(
    *,
    control_info: dict[str, dict[str, Any]],
    target_controls: list[str],
    corr: Optional[np.ndarray],
    n_runs: int,
    seed: Optional[int],
) -> dict[str, np.ndarray]:
    """Sample per-run binary control states.

    If a copula correlation matrix is provided and targets are specified, the
    sampled states are correlated via a Gaussian copula.

    Otherwise, each control is sampled independently as Bernoulli(reliability).

    Args:
        control_info: Mapping returned by `_collect_control_info()`.
        target_controls: Control ids to correlate (order matters).
        corr: Correlation matrix for the Gaussian copula (dim x dim).
        n_runs: Number of Monte Carlo runs.
        seed: Optional seed for reproducibility.

    Returns:
        Mapping control_id -> array of shape (n_runs,) with values {0.0, 1.0}.
        A value of 1 means the control is "up" for that run.
    """
    rng = np.random.default_rng(seed)
    control_state: dict[str, np.ndarray] = {}

    if target_controls and corr is not None:
        u = gaussian_copula_uniforms(corr=corr, n=n_runs, seed=seed)
        for i, cid in enumerate(target_controls):
            rel = float((control_info.get(cid, {}) or {}).get("reliability", 1.0) or 1.0)
            control_state[cid] = (u[:, i] <= rel).astype(np.float64)
        return control_state

    for cid, info in control_info.items():
        rel = float((info or {}).get("reliability", 1.0) or 1.0)
        control_state[cid] = (rng.random(n_runs) <= rel).astype(np.float64)
    return control_state


def _load_text_file(path: str) -> str:
    """Read a UTF-8 text file into memory."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _control_multipliers_for_scenario(sc: Any, control_state: dict[str, np.ndarray], n_runs: int) -> tuple[np.ndarray, np.ndarray]:
    """Compute per-run frequency and severity multipliers for a planned scenario.

    Each control contributes a multiplicative reduction of the form:

    - reduction = effectiveness × coverage × state
    - multiplier = 1 - reduction

    where `state` is 1 when the control is functioning on that run, else 0.

    Args:
        sc: Planned scenario object with `.controls`.
        control_state: Mapping control_id -> {0,1} array from `_sample_control_state()`.
        n_runs: Number of Monte Carlo runs.

    Returns:
        (freq_mult, sev_mult) arrays of shape (n_runs,).
    """
    freq_mult = np.ones(n_runs, dtype=np.float64)
    sev_mult = np.ones(n_runs, dtype=np.float64)

    for ctrl in sc.controls:
        eff = float(ctrl.combined_implementation_effectiveness or 0.0)
        cov = float(ctrl.combined_coverage_value if ctrl.combined_coverage_value is not None else 1.0)
        state = control_state.get(ctrl.id)
        if state is None:
            state = np.ones(n_runs, dtype=np.float64)
        reduction = eff * cov * state
        affects = (ctrl.affects or "frequency").lower()
        if affects in ("frequency", "both"):
            freq_mult = freq_mult * (1.0 - reduction)
        if affects in ("severity", "both"):
            sev_mult = sev_mult * (1.0 - reduction)

    return freq_mult, sev_mult


def _aggregate_portfolio_losses(
    *,
    semantics: str,
    scenario_losses: list[np.ndarray],
    scenario_weights: list[float],
    n_runs: int,
    seed: Optional[int],
) -> np.ndarray:
    """Aggregate scenario loss samples into a portfolio loss sample.

    Args:
        semantics: Aggregation method from the execution plan.
            Supported: "sum", "max", "mixture", "choose_one".
        scenario_losses: List of arrays of shape (n_runs,), one per scenario.
        scenario_weights: Optional weights aligned with `scenario_losses`.
            Only used for mixture/choose_one. NaNs are treated as unspecified.
        n_runs: Number of Monte Carlo runs.
        seed: Optional seed for reproducible mixture selection.

    Returns:
        Array of shape (n_runs,) representing portfolio annual loss samples.

    Raises:
        ValueError: If `semantics` is not recognized.
    """
    stacked = np.vstack(scenario_losses)  # shape: (n_scen, n_runs)

    if semantics == "sum":
        return np.sum(stacked, axis=0)
    if semantics == "max":
        return np.max(stacked, axis=0)

    if semantics in ("mixture", "choose_one"):
        weights = np.asarray(scenario_weights, dtype=np.float64)
        if np.isnan(weights).any():
            weights = np.ones(len(scenario_losses), dtype=np.float64)
        wsum = float(np.sum(weights))
        if wsum <= 0:
            weights = np.ones(len(scenario_losses), dtype=np.float64)
            wsum = float(np.sum(weights))
        weights = weights / wsum

        rng = np.random.default_rng(seed)
        pick = rng.choice(len(scenario_losses), size=n_runs, replace=True, p=weights)
        return stacked[pick, np.arange(n_runs)]

    raise ValueError(f"Unsupported portfolio semantics '{semantics}'")


def _run_single_portfolio_scenario(
    *,
    sc: Any,
    idx: int,
    control_state: dict[str, np.ndarray],
    n_runs: int,
    seed: Optional[int],
    fx_config: FXConfig,
) -> Tuple[np.ndarray, float]:
    """Execute a single scenario referenced by a portfolio plan.

    This loads the scenario document, applies per-run control multipliers,
    and runs the core Monte Carlo engine.

    Args:
        sc: Planned scenario (resolved by `plan_portfolio()`).
        idx: Scenario index in the plan (used to perturb the base seed).
        control_state: Mapping control_id -> {0,1} array.
        n_runs: Number of Monte Carlo runs.
        seed: Optional base seed.
        fx_config: FX configuration used for output currency conversion.

    Returns:
        (losses, weight)

        - losses: array of shape (n_runs,) for this scenario.
        - weight: float weight; may be NaN when not specified.

    Raises:
        ValueError: For missing/invalid scenario path or malformed outputs.
        RuntimeError: If the scenario engine run fails.
    """
    # Prefer inlined scenario docs (bundle mode) to avoid filesystem dependency.
    scenario_doc = getattr(sc, "scenario", None)
    if scenario_doc is not None:
        # `run_monte_carlo` expects CRML-shaped keys (e.g. "lambda"), but Pydantic
        # models dump field names by default (e.g. "lambda_"). Use aliases here.
        scenario_input: Any = scenario_doc.model_dump(exclude_none=True, by_alias=True)
    else:
        scenario_path = sc.resolved_path or sc.path
        if not scenario_path:
            raise ValueError(f"Scenario '{sc.id}' has no path")
        try:
            scenario_input = _load_text_file(scenario_path)
        except Exception as e:
            raise ValueError(f"Failed to read scenario '{sc.id}': {e}") from e

    freq_mult, sev_mult = _control_multipliers_for_scenario(sc, control_state, n_runs)

    scenario_seed = None if seed is None else int(seed + idx * 1000)
    res = run_monte_carlo(
        scenario_input,
        n_runs=n_runs,
        seed=scenario_seed,
        fx_config=fx_config,
        cardinality=int(sc.cardinality or 1),
        frequency_rate_multiplier=freq_mult,
        severity_loss_multiplier=sev_mult,
        raw_data_limit=n_runs,
    )
    if not res.success or res.distribution is None:
        errors = list(res.errors or [f"Scenario '{sc.id}' failed"])
        raise RuntimeError("; ".join(errors))

    losses = np.asarray(res.distribution.raw_data, dtype=np.float64)
    if losses.shape != (n_runs,):
        raise ValueError(f"Scenario '{sc.id}' did not return {n_runs} samples")

    weight = float(sc.weight) if sc.weight is not None else float("nan")
    return losses, weight


def _run_portfolio_scenarios(
    *,
    scenarios: list[Any],
    control_state: dict[str, np.ndarray],
    n_runs: int,
    seed: Optional[int],
    fx_config: FXConfig,
) -> Tuple[list[np.ndarray], list[float]]:
    """Run all scenarios in a portfolio plan and collect losses/weights."""
    scenario_losses: list[np.ndarray] = []
    scenario_weights: list[float] = []

    for idx, sc in enumerate(scenarios):
        losses, weight = _run_single_portfolio_scenario(
            sc=sc,
            idx=idx,
            control_state=control_state,
            n_runs=n_runs,
            seed=seed,
            fx_config=fx_config,
        )
        scenario_losses.append(losses)
        scenario_weights.append(weight)

    return scenario_losses, scenario_weights


def _compute_metrics_and_distribution(total: np.ndarray, *, bin_count: int = 50) -> Tuple[Metrics, Distribution]:
    """Compute summary metrics and a histogram distribution for loss samples.

    Notes:
        This portfolio helper intentionally truncates raw samples to 1000
        elements for `Distribution.raw_data`.
    """
    total = np.asarray(total, dtype=np.float64)
    metrics = Metrics(
        eal=float(np.mean(total)),
        var_95=float(np.percentile(total, 95)),
        var_99=float(np.percentile(total, 99)),
        var_999=float(np.percentile(total, 99.9)),
        min=float(np.min(total)),
        max=float(np.max(total)),
        median=float(np.median(total)),
        std_dev=float(np.std(total)),
    )

    hist, bin_edges = np.histogram(total, bins=bin_count)
    distribution = Distribution(
        bins=bin_edges.tolist(),
        frequencies=hist.tolist(),
        raw_data=total.tolist()[:1000],
    )
    return metrics, distribution


def run_portfolio_simulation(
    portfolio_source: Union[str, dict],
    *,
    source_kind: str = "path",
    n_runs: int = 10000,
    seed: Optional[int] = None,
    fx_config: Optional[FXConfig] = None,
) -> EngineSimulationResult:
    """Run a CRML portfolio simulation.

    This function is a reference implementation demonstrating CRML portfolio
    semantics and the optional dependency mechanism.

    High-level flow:
        1. Plan/resolve the portfolio into executable scenarios via
           `crml_engine.pipeline.plan_portfolio`.
        2. Sample per-run control state (Bernoulli(reliability)), optionally
           correlated using a Gaussian copula when the portfolio dependency
           payload defines `portfolio.dependency.copula`.
        3. Run each scenario through `run_monte_carlo()` with frequency/severity
           multipliers derived from the sampled controls.
        4. Aggregate scenario annual losses according to the portfolio
           semantics method.

    Args:
        portfolio_source: Portfolio input. Interpretation depends on
            `source_kind`.
        source_kind: One of:
            - "path": `portfolio_source` is a filesystem path to YAML.
            - "yaml": `portfolio_source` is a YAML string.
            - "data": `portfolio_source` is an already-parsed dict.
        n_runs: Number of Monte Carlo iterations.
        seed: Optional base seed. Used both for copula/control sampling and to
            derive scenario-specific seeds.
        fx_config: Optional FXConfig. If omitted, defaults are used.

    Returns:
        A `SimulationResult` with metrics/distribution in the configured output
        currency.

    Raises:
        This function does not raise for most user errors; it returns
        `success=False` with an error message. Internal helpers may raise, but
        are caught and converted to failures.
    """

    # Keep signature stable, but make it explicit that portfolios are not executable.
    del portfolio_source, source_kind, n_runs, seed, fx_config
    return _portfolio_error_result(
        "Refusing to simulate a raw 'crml_portfolio' input. "
        "Portfolios are non-executable inputs; create a 'crml_portfolio_bundle' first via "
        "the language-layer API: from crml_lang import bundle_portfolio."
    )


def run_portfolio_bundle_simulation(
    bundle_source: Union[str, dict],
    *,
    source_kind: str = "path",
    n_runs: int = 10000,
    seed: Optional[int] = None,
    fx_config: Optional[FXConfig] = None,
) -> EngineSimulationResult:
    """Run a CRML portfolio bundle simulation.

    A portfolio bundle is a self-contained artifact produced by `crml_lang`
    that inlines the portfolio and referenced documents. This runtime executes
    the bundle without requiring filesystem access to scenario paths.

    Args:
        bundle_source: Bundle input. Interpretation depends on `source_kind`.
        source_kind: One of:
            - "path": `bundle_source` is a filesystem path to YAML.
            - "yaml": `bundle_source` is a YAML string.
            - "data": `bundle_source` is an already-parsed dict.
        n_runs: Number of Monte Carlo iterations.
        seed: Optional base seed.
        fx_config: Optional FXConfig.

    Returns:
        A `SimulationResult` for the bundled portfolio.
    """
    lang = _crml_lang_module()

    fx_config = normalize_fx_config(fx_config)
    output_symbol = get_currency_symbol(fx_config.output_currency)

    try:
        if source_kind == "path":
            assert isinstance(bundle_source, str)
            bundle = lang.CRPortfolioBundle.load_from_yaml(bundle_source)
        elif source_kind == "yaml":
            assert isinstance(bundle_source, str)
            bundle = lang.CRPortfolioBundle.load_from_yaml_str(bundle_source)
        else:
            assert isinstance(bundle_source, dict)
            bundle = lang.CRPortfolioBundle.model_validate(bundle_source)
    except Exception as e:
        return _portfolio_error_result(str(e))

    report = plan_bundle(bundle)
    if not report.ok or report.plan is None:
        errors = [e.message for e in (report.errors or [])]
        return EngineSimulationResult(success=False, metrics=None, distribution=None, metadata=None, errors=errors)

    plan = report.plan
    semantics = plan.semantics_method
    scenarios = list(plan.scenarios)
    if not scenarios:
        return _portfolio_error_result("Portfolio contains no scenarios")

    control_info = _collect_control_info(scenarios)
    target_controls, corr = _extract_copula_targets(plan.dependency)
    control_state = _sample_control_state(
        control_info=control_info,
        target_controls=target_controls,
        corr=corr,
        n_runs=n_runs,
        seed=seed,
    )

    try:
        scenario_losses, scenario_weights = _run_portfolio_scenarios(
            scenarios=scenarios,
            control_state=control_state,
            n_runs=n_runs,
            seed=seed,
            fx_config=fx_config,
        )
    except (ValueError, RuntimeError) as e:
        return _portfolio_error_result(str(e))

    try:
        total = _aggregate_portfolio_losses(
            semantics=semantics,
            scenario_losses=scenario_losses,
            scenario_weights=scenario_weights,
            n_runs=n_runs,
            seed=seed,
        )
    except ValueError as e:
        return _portfolio_error_result(str(e))

    metrics, distribution = _compute_metrics_and_distribution(total, bin_count=50)
    return EngineSimulationResult(
        success=True,
        metrics=metrics,
        distribution=distribution,
        metadata=Metadata(
            runs=n_runs,
            seed=seed,
            currency=output_symbol,
            currency_code=fx_config.output_currency,
            model_name=plan.portfolio_name,
            model_version="N/A",
            description="",
            runtime_ms=None,
            lambda_baseline=None,
            lambda_effective=None,
            controls_applied=True,
            control_reduction_pct=None,
            control_details=None,
            control_warnings=None,
            correlation_info=None,
        ),
        errors=[],
    )

def run_simulation(
    yaml_content: Union[str, dict], 
    n_runs: int = 10000, 
    seed: Optional[int] = None,    fx_config: Optional[FXConfig] = None
) -> EngineSimulationResult:
    """Run a Monte Carlo simulation for CRML inputs.

    This convenience wrapper accepts only one executable CRML artifact:
    - CRML portfolio bundle (runs `run_portfolio_bundle_simulation`)

    Args:
        yaml_content: Input as a YAML string, parsed dict, or a file path.
        n_runs: Number of Monte Carlo iterations.
        seed: Optional RNG seed.
        fx_config: Optional FX configuration (base/output currencies and rates).

    Returns:
        A `SimulationResult` containing summary metrics, distribution artifacts,
        and metadata.
    """

    root = _load_yaml_root_for_routing(yaml_content)
    if root is not None:
        routed = _route_simulation_document(
            root=root,
            source=yaml_content,
            n_runs=n_runs,
            seed=seed,
            fx_config=fx_config,
        )
        if routed is not None:
            return routed

        # Diagnostic: If not routed, use crml_lang to explain exactly what is wrong/unsupported.
        lang = _crml_lang_module()
        report = lang.validate_document(yaml_content)
        
        if report.ok:
            # Document is valid CRML, but not one we can simulate.
            supported = ["crml_scenario", "crml_portfolio", "crml_portfolio_bundle"]
            found = next((k for k in root if k.startswith("crml_")), "unknown")
            return _portfolio_error_result(
                f"Document type '{found}' is valid CRML but does not support simulation. "
                f"Simulation is supported for: {', '.join(supported)}"
            )
        else:
            # Document is invalid CRML. Provide specific errors.
            err_msg = "Document failed validation:\n" + report.render_text()
            return _portfolio_error_result(err_msg)

    return _portfolio_error_result(
        "Unsupported simulation input. Expected a 'crml_portfolio_bundle' document. "
        "To execute, bundle a portfolio using the language-layer API: from crml_lang import bundle_portfolio."
    )


def run_simulation_envelope(
    yaml_content: Union[str, dict],
    n_runs: int = 10000,
    seed: Optional[int] = None,
    fx_config: Optional[Union[FXConfig, dict]] = None,
) -> Any:
    """Run a simulation and return the engine-agnostic result envelope.

    The envelope type is defined by `crml_lang` to provide a stable interchange
    format across engines/implementations.

    Args:
        yaml_content: Portfolio bundle input (YAML string, dict, or file path).
        n_runs: Number of Monte Carlo iterations.
        seed: Optional RNG seed.
        fx_config: Optional FX configuration.

    Returns:
        A `CRSimulationResult` with engine info, run info, measures, and
        artifacts.
    """

    sr = _simulation_result_models()
    fx_config_norm = normalize_fx_config(fx_config)
    result = run_simulation(yaml_content, n_runs=n_runs, seed=seed, fx_config=fx_config_norm)

    # Best-effort extraction of portfolio-level risk tolerance from bundle inputs.
    # This is intentionally non-fatal; the simulation should still run even if parsing fails.
    risk_tolerance = None
    try:
        root = _load_yaml_root_for_routing(yaml_content)
        if isinstance(root, dict) and "crml_portfolio_bundle" in root:
            lang = _crml_lang_module()
            kind = _infer_source_kind(yaml_content)
            if kind == "path":
                assert isinstance(yaml_content, str)
                bundle = lang.CRPortfolioBundle.load_from_yaml(yaml_content)
            elif kind == "yaml":
                assert isinstance(yaml_content, str)
                bundle = lang.CRPortfolioBundle.load_from_yaml_str(yaml_content)
            else:
                bundle = lang.CRPortfolioBundle.model_validate(yaml_content)

            risk_tolerance = getattr(bundle.portfolio_bundle.portfolio.portfolio, "risk_tolerance", None)
    except Exception:
        risk_tolerance = None

    # Best-effort parsing for traceability extraction.
    parsed_scenario = _try_parse_scenario(yaml_content)

    try:
        from importlib import metadata as importlib_metadata

        engine_version = importlib_metadata.version("crml_engine")
    except Exception:
        engine_version = None

    currency_code = None
    currency_symbol = None
    model_name = None
    model_version = None
    description = None
    runtime_ms = None
    runs = None

    if result.metadata is not None:
        currency_code = result.metadata.currency_code
        currency_symbol = result.metadata.currency
        model_name = result.metadata.model_name
        model_version = result.metadata.model_version
        description = result.metadata.description
        runtime_ms = result.metadata.runtime_ms
        runs = result.metadata.runs

    currency_unit = None
    if currency_code is not None:
        currency_unit = sr.CurrencyUnit(code=currency_code, symbol=currency_symbol)

    envelope = sr.CRSimulationResult(
        result=sr.SimulationResult(
            success=result.success,
            errors=list(result.errors or []),
            warnings=list(getattr(result, "warnings", None) or []),
            engine=sr.EngineInfo(name="crml_engine", version=engine_version),
            run=sr.RunInfo(
                runs=runs,
                seed=seed,
                runtime_ms=runtime_ms,
                started_at=sr.now_utc(),
            ),
            inputs=sr.InputInfo(model_name=model_name, model_version=model_version, description=description),
            units=sr.Units(
                currency=sr.CurrencyUnit(code=currency_code or "USD", symbol=currency_symbol),
                horizon="annual",
            ),
            summaries=[],
            trace=None,
        )
    )

    # Persist portfolio risk tolerance into the envelope for downstream reporting.
    if risk_tolerance is not None:
        envelope.result.inputs.risk_tolerance = risk_tolerance

    _populate_envelope_summaries(envelope=envelope, result=result, currency_unit=currency_unit, runs=runs)
    envelope.result.trace = _build_traceability(
        yaml_content=yaml_content,
        parsed_scenario=parsed_scenario,
        fx_config=fx_config_norm,
    )

    metrics = result.metrics
    if metrics is not None:
        envelope.result.results.measures.extend(
            [
                sr.Measure(id="loss.eal", label="Expected Annual Loss", value=metrics.eal, unit=currency_unit),
                sr.Measure(id="loss.min", label="Minimum Loss", value=metrics.min, unit=currency_unit),
                sr.Measure(id="loss.max", label="Maximum Loss", value=metrics.max, unit=currency_unit),
                sr.Measure(id="loss.median", label="Median Loss", value=metrics.median, unit=currency_unit),
                sr.Measure(id="loss.std_dev", label="Standard Deviation", value=metrics.std_dev, unit=currency_unit),
            ]
        )

        envelope.result.results.measures.extend(
            [
                sr.Measure(
                    id=LOSS_VAR_ID,
                    label=VALUE_AT_RISK_LABEL,
                    value=metrics.var_95,
                    unit=currency_unit,
                    parameters={"level": 0.95},
                ),
                sr.Measure(
                    id=LOSS_VAR_ID,
                    label=VALUE_AT_RISK_LABEL,
                    value=metrics.var_99,
                    unit=currency_unit,
                    parameters={"level": 0.99},
                ),
                sr.Measure(
                    id=LOSS_VAR_ID,
                    label=VALUE_AT_RISK_LABEL,
                    value=metrics.var_999,
                    unit=currency_unit,
                    parameters={"level": 0.999},
                ),
            ]
        )

    distribution = result.distribution
    if distribution is not None:
        if distribution.bins and distribution.frequencies:
            envelope.result.results.artifacts.append(
                sr.HistogramArtifact(
                    id=LOSS_ANNUAL_ID,
                    unit=currency_unit,
                    bin_edges=list(distribution.bins),
                    counts=list(distribution.frequencies),
                    binning={"method": "fixed_bins", "bin_count": max(len(distribution.bins) - 1, 0)},
                )
            )
        if distribution.raw_data:
            envelope.result.results.artifacts.append(
                sr.SamplesArtifact(
                    id=LOSS_ANNUAL_ID,
                    unit=currency_unit,
                    values=list(distribution.raw_data),
                    sample_count_total=runs,
                    sample_count_returned=len(distribution.raw_data),
                    sampling={"method": "first_n"},
                )
            )

    return envelope


def _measure_value(envelope: Any, *, measure_id: str, level: Optional[float] = None) -> Optional[float]:
    measures = getattr(getattr(getattr(envelope, "result", None), "results", None), "measures", None)
    if not isinstance(measures, list):
        return None
    for m in measures:
        if getattr(m, "id", None) != measure_id:
            continue
        if level is None:
            return getattr(m, "value", None)
        params = getattr(m, "parameters", None) or {}
        if isinstance(params, dict) and params.get("level") == level:
            return getattr(m, "value", None)
    return None


def _print_simulation_envelope(envelope: Any) -> None:
    # Lightweight, stable text output sourced from the envelope.
    result = getattr(envelope, "result", None)
    if result is None:
        print("No result payload.")
        return

    if not getattr(result, "success", False):
        print("❌ Simulation failed:")
        for e in list(getattr(result, "errors", None) or []):
            print(f"  • {e}")
        return

    currency_symbol = None
    units = getattr(result, "units", None)
    if units is not None and getattr(units, "currency", None) is not None:
        currency_symbol = getattr(units.currency, "symbol", None) or ""

    rt = getattr(getattr(result, "inputs", None), "risk_tolerance", None)
    if rt is not None:
        metric = getattr(rt, "metric", None)
        threshold = getattr(rt, "threshold", None)

        # Prefer an explicitly provided tolerance currency code.
        rt_currency = getattr(rt, "currency", None)
        rt_prefix = currency_symbol
        if isinstance(rt_currency, str) and rt_currency.strip():
            rt_prefix = rt_currency.strip() + " "

        if threshold is not None:
            try:
                threshold_f = float(threshold)
                print(f"Risk tolerance: {metric} <= {rt_prefix}{threshold_f:,.2f}")
            except Exception:
                print(f"Risk tolerance: {metric} <= {rt_prefix}{threshold}")
        else:
            print(f"Risk tolerance: {metric}")

    eal = _measure_value(envelope, measure_id="loss.eal")
    var95 = _measure_value(envelope, measure_id="loss.var", level=0.95)
    var99 = _measure_value(envelope, measure_id="loss.var", level=0.99)
    var999 = _measure_value(envelope, measure_id="loss.var", level=0.999)

    if eal is not None:
        print(f"EAL (Expected Annual Loss):  {currency_symbol}{eal:,.2f}")
    if var95 is not None:
        print(f"VaR 95%:                      {currency_symbol}{var95:,.2f}")
    if var99 is not None:
        print(f"VaR 99%:                      {currency_symbol}{var99:,.2f}")
    if var999 is not None:
        print(f"VaR 99.9%:                    {currency_symbol}{var999:,.2f}")

def calibrate_lognormal_from_single_losses(
    single_losses: list,
    currency: Optional[str],
    base_currency: str,
    fx_config: FXConfig,
) -> tuple[float, float]:
    """Calibrate lognormal parameters from single-event losses.

    This is a convenience wrapper around
    `crml_engine.simulation.severity.SeverityEngine.calibrate_lognormal_from_single_losses`.

    Args:
        single_losses: Sequence of single-event losses. Values may be numeric
            or string-like (see severity implementation for parsing).
        currency: Currency code/symbol used by `single_losses` (optional).
        base_currency: Base currency code to calibrate in.
        fx_config: FX rates/config used for currency conversion.

    Returns:
        (mu, sigma) parameters for a lognormal distribution in log-space.
    """
    return SeverityEngine.calibrate_lognormal_from_single_losses(
        single_losses, currency, base_currency, fx_config
    )

def run_simulation_cli(file_path: str, n_runs: int = 10000, output_format: str = 'text', fx_config_path: Optional[str] = None):
    """CLI-friendly wrapper to run a portfolio bundle and print results.

        Behavior:
                - Accepts only `crml_portfolio_bundle` documents.
                - Refuses raw `crml_portfolio` inputs (portfolios are non-executable).
                - Refuses raw `crml_scenario` inputs (scenarios are not executable in a vacuum).
                - Prints results to stdout in either text or JSON form.

    Args:
        file_path: Path to a CRML portfolio bundle YAML file.
        n_runs: Number of Monte Carlo iterations.
        output_format: "text" (pretty console output) or "json".
        fx_config_path: Optional path to an FX config YAML document.

    Returns:
        True on success, False on failure.
    """
    # Load FX config
    fx_config = load_fx_config(fx_config_path)

    root = _load_yaml_root_for_routing(file_path)
    if not (isinstance(root, dict) and "crml_portfolio_bundle" in root):
        import sys

        print(
            "Unsupported input for simulation. Expected a 'crml_portfolio_bundle' document.",
            file=sys.stderr,
        )
        return False

    envelope = run_simulation_envelope(
        file_path,
        n_runs=n_runs,
        seed=None,
        fx_config=fx_config,
    )

    if output_format == 'json':
        # Use model_dump for pretty JSON output
        print(json.dumps(envelope.model_dump(), indent=2))
        return bool(getattr(envelope.result, "success", False))

    # Text output
    _print_simulation_envelope(envelope)
    return bool(getattr(envelope.result, "success", False))
