from typing import Dict, List
import math

from crml_lang.models.attack_chain_model import AttackChain
from crml_lang.models.control_ref import ControlId

class AttackChainEngine:
    """Engine for simulating attack chain progression and calculating effective frequencies."""

    def calculate_effective_probability(
        self, 
        chain: AttackChain, 
        control_effectiveness_map: Dict[str, float]
    ) -> float:
        """
        Calculate the overall probability of the attack chain succeeding.

        Args:
            chain: The AttackChain model defining stages.
            control_effectiveness_map: A dictionary mapping ControlId (str) to 
                                       its current effectiveness (0.0 - 1.0) in the portfolio.
                                       If a control is missing, it is assumed to have 0.0 effectiveness.

        Returns:
            The cumulative probability (0.0 - 1.0) of the chain completing successfully.
        """
        cumulative_prob = 1.0

        for stage in chain.stages:
            # 1. Start with the stage's inherent probability
            stage_prob = stage.probability

            # 2. Calculate mitigation from controls
            # Logic: We treat controls as independent barriers.
            # Residual Probability = Initial * (1 - C1) * (1 - C2) ...
            
            mitigation_factor = 1.0
            if stage.controls:
                for control_id in stage.controls:
                    # Get effectiveness from portfolio state, default to 0.0 if not present/implemented
                    eff = control_effectiveness_map.get(control_id, 0.0)
                    
                    # Ensure validity
                    eff = max(0.0, min(1.0, eff))
                    
                    mitigation_factor *= (1.0 - eff)
            
            # Apply mitigation
            # If mitigation_factor is 1.0 (no controls), residual is 100% of stage_prob.
            # If mitigation_factor starts approaching 0.0 (perfect controls), residual -> 0.
            stage_residual_prob = stage_prob * mitigation_factor
            
            # 3. Chain logic: The chain succeeds if Stage 1 succeeds AND Stage 2 succeeds...
            cumulative_prob *= stage_residual_prob
            
            # Optimization: If probability drops to near zero, we can stop
            if cumulative_prob < 1e-9:
                return 0.0

        return cumulative_prob
