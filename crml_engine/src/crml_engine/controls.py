"""
Control Effectiveness Modeling for CRML

This module implements security control effectiveness calculations to model
how preventive, detective, and recovery controls reduce cyber risk.

Mathematical Model:
-------------------
For a control with:
- Effectiveness e ∈ [0,1]: How well it works when functioning
- Coverage c ∈ [0,1]: What percentage of assets/surface it covers  
- Reliability r ∈ [0,1]: How reliably it functions (uptime)

Effective risk reduction = e × c × r

For multiple controls in series (defense in depth):
P(breach) = P₀ × ∏ᵢ (1 - eᵢ × cᵢ × rᵢ)

Where P₀ is baseline probability without controls.

With dependencies (correlation between controls):
Adjusted using copula-based correlation to account for controls that
may fail together or provide overlapping protection.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple


def _collect_valid_controls(
    controls_config: Dict[str, Any],
    result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    all_controls: List[Dict[str, Any]] = []
    for layer in controls_config.get('layers', []):
        for control in layer.get('controls', []):
            is_valid, error_msg = validate_control(control)
            if not is_valid:
                result['warnings'].append(error_msg)
                continue
            all_controls.append(control)
    return all_controls


def _apply_controls_in_series(
    base_lambda: float,
    all_controls: List[Dict[str, Any]],
) -> Tuple[float, List[Dict[str, Any]]]:
    effective_lambda = base_lambda
    control_details: List[Dict[str, Any]] = []

    for control in all_controls:
        reduction = calculate_effective_reduction(control)

        # Apply reduction (multiplicative for defense in depth)
        lambda_before = effective_lambda
        effective_lambda *= (1 - reduction)
        lambda_after = effective_lambda

        control_details.append({
            'id': control['id'],
            'type': control['type'],
            'effectiveness': control.get('effectiveness'),
            'coverage': control.get('coverage', 1.0),
            'reliability': control.get('reliability', 1.0),
            'reduction': reduction,
            'lambda_before': lambda_before,
            'lambda_after': lambda_after,
            'cost': control.get('cost')
        })

    return effective_lambda, control_details


def validate_control(control: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a single control configuration.
    
    Args:
        control: Control configuration dictionary
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = ['id', 'type', 'effectiveness']
    for field in required_fields:
        if field not in control:
            return False, f"Control missing required field: {field}"
    
    # Validate effectiveness
    eff = control.get('effectiveness')
    if not isinstance(eff, (int, float)) or not (0 <= eff <= 1):
        return False, f"Control '{control['id']}': effectiveness must be in [0, 1], got {eff}"
    
    # Validate coverage if present
    if 'coverage' in control:
        cov = control['coverage']
        if not isinstance(cov, (int, float)) or not (0 <= cov <= 1):
            return False, f"Control '{control['id']}': coverage must be in [0, 1], got {cov}"
    
    # Validate reliability if present
    if 'reliability' in control:
        rel = control['reliability']
        if not isinstance(rel, (int, float)) or not (0 <= rel <= 1):
            return False, f"Control '{control['id']}': reliability must be in [0, 1], got {rel}"
    
    # Validate control type
    valid_types = ['preventive', 'detective', 'corrective', 'recovery', 'deterrent', 'compensating']
    if control['type'] not in valid_types:
        return False, f"Control '{control['id']}': invalid type '{control['type']}'. Must be one of {valid_types}"
    
    return True, None


def calculate_effective_reduction(control: Dict[str, Any]) -> float:
    """
    Calculate the effective risk reduction for a single control.
    
    Args:
        control: Control configuration with effectiveness, coverage, reliability
    
    Returns:
        Effective reduction factor (0 to 1)
    """
    effectiveness = control.get('effectiveness', 0)
    coverage = control.get('coverage', 1.0)
    reliability = control.get('reliability', 1.0)
    
    return effectiveness * coverage * reliability


def apply_control_effectiveness(
    base_lambda: float,
    controls_config: Dict[str, Any],
    warn_unrealistic: bool = True
) -> Dict[str, Any]:
    """
    Apply control effectiveness to reduce frequency parameter.
    
    This is the main entry point for control effectiveness calculations.
    
    Args:
        base_lambda: Baseline frequency without controls
        controls_config: Controls configuration from CRML model
        warn_unrealistic: Whether to warn about unrealistic combinations
    
    Returns:
        Dictionary with:
        - effective_lambda: Adjusted lambda after controls
        - reduction_pct: Percentage reduction
        - control_details: Per-control breakdown
        - warnings: List of warning messages
    """
    result = {
        'effective_lambda': base_lambda,
        'reduction_pct': 0.0,
        'control_details': [],
        'warnings': []
    }
    
    if not controls_config or 'layers' not in controls_config:
        return result
    
    # Collect all controls from all layers
    all_controls = _collect_valid_controls(controls_config, result)
    
    if not all_controls:
        return result
    
    # Calculate effective lambda with controls in series
    effective_lambda, control_details = _apply_controls_in_series(base_lambda, all_controls)
    
    # Apply dependencies/correlations if specified
    if 'dependencies' in controls_config:
        effective_lambda = adjust_for_dependencies(
            effective_lambda,
            base_lambda,
            all_controls,
            controls_config['dependencies']
        )
    
    # Calculate total reduction percentage
    reduction_pct = ((base_lambda - effective_lambda) / base_lambda * 100) if base_lambda > 0 else 0
    
    # Warnings for unrealistic configurations
    if warn_unrealistic:
        if reduction_pct > 99.9:
            result['warnings'].append(
                f"Warning: Total risk reduction is {reduction_pct:.1f}%. "
                "This is extremely high and may be unrealistic. Consider reviewing control effectiveness values."
            )
        
        if effective_lambda < 0.001 and base_lambda > 0.01:
            result['warnings'].append(
                f"Warning: Effective lambda ({effective_lambda:.6f}) is very low compared to baseline ({base_lambda:.6f}). "
                "Verify that control parameters are realistic."
            )
    
    result['effective_lambda'] = effective_lambda
    result['reduction_pct'] = reduction_pct
    result['control_details'] = control_details
    
    return result


def adjust_for_dependencies(
    effective_lambda: float,
    base_lambda: float,
    controls: List[Dict],
    dependencies: List[Dict]
) -> float:
    """
    Adjust effective lambda for control dependencies/correlations.
    
    When controls are correlated, their combined effectiveness is reduced
    because they may fail together or provide overlapping protection.
    
    Args:
        effective_lambda: Lambda after applying independent controls
        base_lambda: Original baseline lambda
        controls: List of all controls
        dependencies: List of dependency specifications
    
    Returns:
        Adjusted effective lambda
    """
    if not dependencies:
        return effective_lambda
    
    # For each dependency group, reduce effectiveness based on correlation
    for dep in dependencies:
        dep_control_ids = dep.get('controls', [])
        correlation = dep.get('correlation', 0)
        
        if len(dep_control_ids) < 2:
            continue
        
        # Find controls in this dependency group
        dep_controls = [c for c in controls if c['id'] in dep_control_ids]
        
        if len(dep_controls) < 2:
            continue
        
        # Calculate adjustment factor based on correlation
        # Higher correlation = less benefit from multiple controls
        # correlation = 0: fully independent (no adjustment)
        # correlation = 1: perfectly correlated (significant adjustment)
        
        # Simple model: reduce combined effectiveness by correlation factor
        # More sophisticated models could use copulas
        avg_reduction = np.mean([calculate_effective_reduction(c) for c in dep_controls])
        
        # Adjustment: when correlation is high, treat controls as more redundant
        redundancy_factor = correlation * avg_reduction * 0.5  # Conservative adjustment
        
        # Increase effective lambda slightly to account for redundancy
        effective_lambda += (base_lambda - effective_lambda) * redundancy_factor
    
    return effective_lambda


def calculate_control_roi(
    control_details: List[Dict],
    eal_baseline: float,
    eal_with_controls: float,
    horizon_years: int = 1
) -> List[Dict]:
    """
    Calculate return on investment for each control.
    
    ROI = (Risk Reduction - Control Cost) / Control Cost
    
    Args:
        control_details: List of control detail dictionaries
        eal_baseline: Expected Annual Loss without controls
        eal_with_controls: Expected Annual Loss with controls
        horizon_years: Time horizon for ROI calculation
    
    Returns:
        List of controls with ROI calculations added
    """
    total_risk_reduction = eal_baseline - eal_with_controls
    
    results = []
    for control in control_details:
        control_copy = control.copy()
        
        if 'cost' in control and control['cost'] is not None:
            cost = control['cost'] * horizon_years
            
            # Estimate this control's contribution to total reduction
            # Based on its reduction factor relative to total
            contribution_factor = control['reduction']
            estimated_reduction = total_risk_reduction * contribution_factor
            
            # Calculate ROI
            net_benefit = estimated_reduction - cost
            roi = (net_benefit / cost * 100) if cost > 0 else 0
            
            control_copy['roi'] = {
                'cost': cost,
                'estimated_risk_reduction': estimated_reduction,
                'net_benefit': net_benefit,
                'roi_percentage': roi,
                'payback_years': (cost / estimated_reduction) if estimated_reduction > 0 else float('inf')
            }
        
        results.append(control_copy)
    
    return results


def get_control_summary(controls_result: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of control effectiveness.
    
    Args:
        controls_result: Result from apply_control_effectiveness()
    
    Returns:
        Formatted summary string
    """
    lines = []
    lines.append("Control Effectiveness Summary")
    lines.append("=" * 50)
    lines.append(f"Risk Reduction: {controls_result['reduction_pct']:.1f}%")
    lines.append(f"Effective Lambda: {controls_result['effective_lambda']:.6f}")
    lines.append("")
    
    if controls_result['control_details']:
        lines.append("Individual Controls:")
        lines.append("-" * 50)
        for ctrl in controls_result['control_details']:
            lines.append(f"  {ctrl['id']} ({ctrl['type']})")
            lines.append(f"    Effectiveness: {ctrl['effectiveness']:.0%}")
            lines.append(f"    Coverage: {ctrl['coverage']:.0%}")
            lines.append(f"    Reliability: {ctrl['reliability']:.0%}")
            lines.append(f"    Combined Reduction: {ctrl['reduction']:.0%}")
            if ctrl.get('cost'):
                lines.append(f"    Annual Cost: ${ctrl['cost']:,.0f}")
            lines.append("")
    
    if controls_result['warnings']:
        lines.append("Warnings:")
        lines.append("-" * 50)
        for warning in controls_result['warnings']:
            lines.append(f"  ⚠️  {warning}")
    
    return "\n".join(lines)
