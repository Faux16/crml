#!/usr/bin/env python3
"""CRML command-line interface.

This CLI is intentionally thin:
- Validation: calls the library validator and prints a rendered report.
- Simulation: delegates to the reference runtime.

The primary, supported programmatic API lives in `crml_lang.api` and
`crml_engine.simulation.engine`.
"""

import argparse
import sys

from crml_lang import validate_document
from crml_engine.runtime import run_simulation_cli


FILE_HELP = 'Path to CRML YAML file'


def _exit_or_return(exit_code: int, *, exit_on_return: bool) -> int:
    if exit_on_return:
        raise SystemExit(exit_code)
    return exit_code


def _dispatch_command(args) -> bool:
    if args.command == 'validate':
        report = validate_document(args.file, source_kind="path")
        print(report.render_text(source_label=args.file))
        return bool(report.ok)

    if args.command == 'explain':
        from crml_engine.explainer import explain_crml

        return bool(explain_crml(args.file))

    if args.command == 'simulate':
        return bool(
            run_simulation_cli(
                args.file,
                n_runs=args.runs,
                output_format=args.format,
                fx_config_path=args.fx_config,
            )
        )

    return False

def main(argv=None, *, exit_on_return: bool = True):
    """Run the CRML CLI.

    Args:
        argv: Optional argv list (defaults to sys.argv parsing if None).
        exit_on_return: If True (default), raises SystemExit with the chosen
            exit code. If False, returns the exit code instead.
    """
    parser = argparse.ArgumentParser(
        description='CRML - Cyber Risk Modeling Language CLI'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a CRML file')
    validate_parser.add_argument('file', help=FILE_HELP)
    
    # Explain command (existing)
    explain_parser = subparsers.add_parser('explain', help='Explain a CRML model')
    explain_parser.add_argument('file', help=FILE_HELP)
    
    # Simulate command (new)
    simulate_parser = subparsers.add_parser('simulate', help='Run simulation on a CRML model')
    simulate_parser.add_argument('file', help=FILE_HELP)
    simulate_parser.add_argument('-n', '--runs', type=int, default=10000,
                                help='Number of simulation runs (default: 10000)')
    simulate_parser.add_argument('-s', '--seed', type=int, default=None,
                                help='Random seed for reproducibility')
    simulate_parser.add_argument('-f', '--format', choices=['text', 'json'], default='text',
                                help='Output format (default: text)')
    simulate_parser.add_argument('--fx-config', type=str, default=None,
                                help='Path to FX configuration YAML file for currency settings')
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return _exit_or_return(1, exit_on_return=exit_on_return)

    ok = _dispatch_command(args)
    return _exit_or_return(0 if ok else 1, exit_on_return=exit_on_return)

if __name__ == '__main__':
    main()
