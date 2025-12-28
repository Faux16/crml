import pytest
from pydantic import ValidationError

from crml_lang.models.scenario_model import Scenario, CRScenario
from crml_lang.models.attack_chain_model import AttackChain, AttackStage

def test_attack_stage_valid():
    """Test valid attack stage creation."""
    stage = AttackStage(
        name="Initial Access",
        probability=0.5,
        controls=["nist.sp.800-53:ac-1"]
    )
    assert stage.name == "Initial Access"
    assert stage.probability == 0.5
    assert stage.controls == ["nist.sp.800-53:ac-1"]

def test_attack_stage_invalid_probability():
    """Test validation of probability range."""
    with pytest.raises(ValidationError):
        AttackStage(name="Test", probability=1.5)
    
    with pytest.raises(ValidationError):
        AttackStage(name="Test", probability=-0.1)

def test_attack_stage_invalid_control_id():
    """Test validation of OSCAL-aligned control IDs."""
    # ControlId requires namespace:key format
    with pytest.raises(ValidationError):
        AttackStage(name="Test", probability=0.5, controls=["invalid_id_no_namespace"])

def test_attack_chain_valid():
    """Test valid attack chain creation."""
    chain = AttackChain(
        stages=[
            AttackStage(name="Stage 1", probability=0.1),
            AttackStage(name="Stage 2", probability=0.5)
        ]
    )
    assert len(chain.stages) == 2

def test_attack_chain_empty():
    """Test chain must have at least one stage."""
    with pytest.raises(ValidationError):
        AttackChain(stages=[])

def test_scenario_integration():
    """Test integrating AttackChain into a full Scenario document."""
    yaml_content = """
    crml_scenario: "1.0"
    meta:
      name: "Attack Chain Demo"
    scenario:
      frequency:
        model: "poisson"
        parameters:
          lambda: 1.0
      severity:
        model: "lognormal"
        parameters:
          median: 10000
          sigma: 2.0
      attack_chain:
        stages:
          - name: "Phishing"
            probability: 0.2
            controls: ["cisv8:5.1"]
          - name: "Execution"
            probability: 0.8
    """
    from crml_lang.models.scenario_model import load_crml_from_yaml_str
    
    doc = load_crml_from_yaml_str(yaml_content)
    assert doc.scenario.attack_chain is not None
    assert len(doc.scenario.attack_chain.stages) == 2
    assert doc.scenario.attack_chain.stages[0].name == "Phishing"
    assert doc.scenario.attack_chain.stages[0].probability == 0.2
