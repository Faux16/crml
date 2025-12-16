__version__ = "1.1.0"

# Stable, supported public API surface
from .api import (
	CRModel,
	load_from_yaml,
	load_from_yaml_str,
	dump_to_yaml,
	dump_to_yaml_str,
	validate,
)

__all__ = [
	"__version__",
	"CRModel",
	"load_from_yaml",
	"load_from_yaml_str",
	"dump_to_yaml",
	"dump_to_yaml_str",
	"validate"
]
