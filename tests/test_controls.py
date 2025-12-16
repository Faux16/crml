"""
Tests for control effectiveness modeling in CRML.

Tests cover:
- Single control effectiveness
- Multiple controls in series (defense in depth)
- Control dependencies/correlations
- Edge cases (0%, 100% effectiveness)
- Partial coverage scenarios
- Reliability factors
- Invalid parameters
- Integration with full models
"""

import pytest
import numpy as np
from crml.controls import (
    validate_control,
    calculate_effective_reduction,
    apply_control_effectiveness,
    adjust_for_dependencies,
    calculate_control_roi
)
from crml.runtime import run_simulation


class TestControlValidation:
    """Test control parameter validation."""
    
    def test_valid_control(self):
        """Test validation of a valid control."""
        control = {
            'id': 'test_control',
            'type': 'preventive',
            'effectiveness': 0.85,
            'coverage': 0.95,
            'reliability': 0.99
        }
        is_valid, error = validate_control(control)
        assert is_valid
        assert error is None
    
    def test_missing_required_field(self):
        """Test validation fails for missing required fields."""
        control = {
            'id': 'test_control',
            'type': 'preventive'
            # Missing effectiveness
        }
        is_valid, error = validate_control(control)
        assert not is_valid
        assert 'effectiveness' in error
    
    def test_invalid_effectiveness_range(self):
        """Test validation fails for effectiveness outside [0,1]."""
        control = {
            'id': 'test_control',
            'type': 'preventive',
            'effectiveness': 1.5  # Invalid
        }
        is_valid, error = validate_control(control)
        assert not is_valid
        assert 'effectiveness' in error
    
    def test_invalid_control_type(self):
        """Test validation fails for invalid control type."""
        control = {
            'id': 'test_control',
            'type': 'invalid_type',
            'effectiveness': 0.85
        }
        is_valid, error = validate_control(control)
        assert not is_valid
        assert 'type' in error


class TestEffectiveReduction:
    """Test calculation of effective reduction for individual controls."""
    
    def test_perfect_control(self):
        """Test control with perfect effectiveness, coverage, and reliability."""
        control = {
            'effectiveness': 1.0,
            'coverage': 1.0,
            'reliability': 1.0
        }
        reduction = calculate_effective_reduction(control)
        assert reduction == 1.0
    
    def test_zero_effectiveness(self):
        """Test control with zero effectiveness."""
        control = {
            'effectiveness': 0.0,
            'coverage': 1.0,
            'reliability': 1.0
        }
        reduction = calculate_effective_reduction(control)
        assert reduction == 0.0
    
    def test_partial_coverage(self):
        """Test control with partial coverage."""
        control = {
            'effectiveness': 0.90,
            'coverage': 0.80,
            'reliability': 1.0
        }
        reduction = calculate_effective_reduction(control)
        assert reduction == pytest.approx(0.72)  # 0.90 * 0.80 * 1.0
    
    def test_unreliable_control(self):
        """Test control with lower reliability."""
        control = {
            'effectiveness': 0.90,
            'coverage': 1.0,
            'reliability': 0.95
        }
        reduction = calculate_effective_reduction(control)
        assert reduction == pytest.approx(0.855)  # 0.90 * 1.0 * 0.95
    
    def test_defaults(self):
        """Test that coverage and reliability default to 1.0."""
        control = {
            'effectiveness': 0.85
            # coverage and reliability not specified
        }
        reduction = calculate_effective_reduction(control)
        assert reduction == pytest.approx(0.85)


class TestSingleControl:
    """Test applying a single control to frequency."""
    
    def test_single_control_reduces_lambda(self):
        """Test that a single control reduces lambda."""
        base_lambda = 0.10
        controls_config = {
            'layers': [{
                'name': 'test_layer',
                'controls': [{
                    'id': 'test_control',
                    'type': 'preventive',
                    'effectiveness': 0.80,
                    'coverage': 1.0,
                    'reliability': 1.0
                }]
            }]
        }
        
        result = apply_control_effectiveness(base_lambda, controls_config)
        
        # Lambda should be reduced by 80%
        expected_lambda = base_lambda * (1 - 0.80)
        assert result['effective_lambda'] == pytest.approx(expected_lambda)
        assert result['reduction_pct'] == pytest.approx(80.0)
    
    def test_no_controls(self):
        """Test that no controls means no reduction."""
        base_lambda = 0.10
        controls_config = {'layers': []}
        
        result = apply_control_effectiveness(base_lambda, controls_config)
        
        assert result['effective_lambda'] == base_lambda
        assert result['reduction_pct'] == 0.0


class TestMultipleControls:
    """Test defense-in-depth with multiple controls."""
    
    def test_two_controls_in_series(self):
        """Test that multiple controls multiply their effects."""
        base_lambda = 0.10
        controls_config = {
            'layers': [{
                'name': 'layer1',
                'controls': [
                    {
                        'id': 'control1',
                        'type': 'preventive',
                        'effectiveness': 0.80,
                        'coverage': 1.0,
                        'reliability': 1.0
                    },
                    {
                        'id': 'control2',
                        'type': 'detective',
                        'effectiveness': 0.70,
                        'coverage': 1.0,
                        'reliability': 1.0
                    }
                ]
            }]
        }
        
        result = apply_control_effectiveness(base_lambda, controls_config)
        
        # Combined: 0.10 * (1-0.80) * (1-0.70) = 0.10 * 0.20 * 0.30 = 0.006
        expected_lambda = base_lambda * (1 - 0.80) * (1 - 0.70)
        assert result['effective_lambda'] == pytest.approx(expected_lambda)
        
        # Reduction: (0.10 - 0.006) / 0.10 = 94%
        assert result['reduction_pct'] == pytest.approx(94.0)
    
    def test_multiple_layers(self):
        """Test controls across multiple layers."""
        base_lambda = 0.15
        controls_config = {
            'layers': [
                {
                    'name': 'email_security',
                    'controls': [{
                        'id': 'email_filter',
                        'type': 'preventive',
                        'effectiveness': 0.90,
                        'coverage': 1.0,
                        'reliability': 0.95
                    }]
                },
                {
                    'name': 'endpoint',
                    'controls': [{
                        'id': 'edr',
                        'type': 'detective',
                        'effectiveness': 0.80,
                        'coverage': 0.98,
                        'reliability': 0.92
                    }]
                }
            ]
        }
        
        result = apply_control_effectiveness(base_lambda, controls_config)
        
        # Email: 0.90 * 1.0 * 0.95 = 0.855
        # EDR: 0.80 * 0.98 * 0.92 = 0.72128
        # Combined: 0.15 * (1-0.855) * (1-0.72128) ≈ 0.00606
        
        assert result['effective_lambda'] < base_lambda
        assert result['reduction_pct'] > 90.0  # Should be very high


class TestControlDependencies:
    """Test control dependencies and correlations."""
    
    def test_dependencies_reduce_effectiveness(self):
        """Test that correlated controls are less effective together."""
        base_lambda = 0.10
        
        # Without dependencies
        controls_config_independent = {
            'layers': [{
                'name': 'test',
                'controls': [
                    {'id': 'ctrl1', 'type': 'preventive', 'effectiveness': 0.80},
                    {'id': 'ctrl2', 'type': 'preventive', 'effectiveness': 0.80}
                ]
            }]
        }
        
        # With dependencies
        controls_config_dependent = {
            'layers': [{
                'name': 'test',
                'controls': [
                    {'id': 'ctrl1', 'type': 'preventive', 'effectiveness': 0.80},
                    {'id': 'ctrl2', 'type': 'preventive', 'effectiveness': 0.80}
                ]
            }],
            'dependencies': [{
                'controls': ['ctrl1', 'ctrl2'],
                'correlation': 0.8  # Highly correlated
            }]
        }
        
        result_independent = apply_control_effectiveness(base_lambda, controls_config_independent)
        result_dependent = apply_control_effectiveness(base_lambda, controls_config_dependent)
        
        # Dependent controls should be less effective
        assert result_dependent['effective_lambda'] > result_independent['effective_lambda']


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_base_lambda(self):
        """Test with zero baseline frequency."""
        controls_config = {
            'layers': [{
                'name': 'test',
                'controls': [{'id': 'ctrl', 'type': 'preventive', 'effectiveness': 0.80}]
            }]
        }
        
        result = apply_control_effectiveness(0.0, controls_config)
        
        assert result['effective_lambda'] == 0.0
        assert result['reduction_pct'] == 0.0
    
    def test_unrealistic_reduction_warning(self):
        """Test that unrealistic reductions generate warnings."""
        base_lambda = 0.10
        controls_config = {
            'layers': [{
                'name': 'test',
                'controls': [
                    {'id': 'ctrl1', 'type': 'preventive', 'effectiveness': 0.999},
                    {'id': 'ctrl2', 'type': 'preventive', 'effectiveness': 0.999}
                ]
            }]
        }
        
        result = apply_control_effectiveness(base_lambda, controls_config)
        
        assert len(result['warnings']) > 0
        assert any('unrealistic' in w.lower() or 'very high' in w.lower() for w in result['warnings'])


class TestControlROI:
    """Test control ROI calculations."""
    
    def test_roi_calculation(self):
        """Test basic ROI calculation."""
        control_details = [
            {
                'id': 'test_control',
                'reduction': 0.80,
                'cost': 100000
            }
        ]
        
        eal_baseline = 500000
        eal_with_controls = 100000
        
        results = calculate_control_roi(
            control_details,
            eal_baseline,
            eal_with_controls,
            horizon_years=1
        )
        
        assert len(results) == 1
        assert 'roi' in results[0]
        assert results[0]['roi']['cost'] == 100000
        assert results[0]['roi']['estimated_risk_reduction'] > 0


class TestIntegration:
    """Integration tests with full CRML models."""
    
    def test_full_model_with_controls(self):
        """Test running a complete simulation with controls."""
        model_yaml = """
crml: "1.1"
meta:
  name: "test-with-controls"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.10
  controls:
    layers:
      - name: "test_layer"
        controls:
          - id: "test_control"
            type: "preventive"
            effectiveness: 0.80
            coverage: 1.0
            reliability: 1.0
  severity:
    model: lognormal
    parameters:
      median: "100000"
      sigma: 1.2
"""
        result = run_simulation(model_yaml, n_runs=1000, seed=42)

        assert result.success
        assert result.metadata.controls_applied
        assert result.metadata.lambda_baseline == 0.10
        assert result.metadata.lambda_effective < 0.10
        assert result.metadata.control_reduction_pct > 0
    
    def test_model_without_controls(self):
        """Test that models without controls still work."""
        model_yaml = """
crml: "1.1"
meta:
  name: "test-no-controls"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.10
  severity:
    model: lognormal
    parameters:
      median: "100000"
      sigma: 1.2
"""
        
        result = run_simulation(model_yaml, n_runs=1000, seed=42)
        
        assert result.success
        assert not result.metadata.controls_applied


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
