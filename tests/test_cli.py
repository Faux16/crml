import pytest
from unittest.mock import patch
import sys
from crml.cli import main

def test_cli_validate_success(valid_crml_file):
    with patch.object(sys, 'argv', ['crml', 'validate', valid_crml_file]):
        with pytest.raises(SystemExit) as cm:
            main()
        assert cm.value.code == 0

def test_cli_validate_failure(tmp_path):
    p = tmp_path / "invalid.yaml"
    p.write_text("invalid content")
    with patch.object(sys, 'argv', ['crml', 'validate', str(p)]):
        with pytest.raises(SystemExit) as cm:
            main()
        assert cm.value.code == 1

def test_cli_no_args():
    with patch.object(sys, 'argv', ['crml']):
        with pytest.raises(SystemExit) as cm:
            main()
        assert cm.value.code == 1

def test_cli_explain_success(valid_crml_file):
    with patch.object(sys, 'argv', ['crml', 'explain', valid_crml_file]):
        with pytest.raises(SystemExit) as cm:
            main()
        assert cm.value.code == 0
