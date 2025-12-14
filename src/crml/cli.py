#!/usr/bin/env python3
import argparse
import sys
from crml.validator import validate_crml
from crml.runtime import run_simulation_cli

def main():
    parser = argparse.ArgumentParser(
        description='CRML - Cyber Risk Modeling Language CLI'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a CRML file')
    validate_parser.add_argument('file', help='Path to CRML YAML file')
    
    # Explain command (existing)
    explain_parser = subparsers.add_parser('explain', help='Explain a CRML model')
    explain_parser.add_argument('file', help='Path to CRML YAML file')
    
    # Simulate command (new)
    simulate_parser = subparsers.add_parser('simulate', help='Run simulation on a CRML model')
    simulate_parser.add_argument('file', help='Path to CRML YAML file')
    simulate_parser.add_argument('-n', '--runs', type=int, default=10000,
                                help='Number of simulation runs (default: 10000)')
    simulate_parser.add_argument('-s', '--seed', type=int, default=None,
                                help='Random seed for reproducibility')
    simulate_parser.add_argument('-f', '--format', choices=['text', 'json'], default='text',
                                help='Output format (default: text)')
    simulate_parser.add_argument('--fx-config', type=str, default=None,
                                help='Path to FX configuration YAML file for currency settings')
    
    # Legacy 'run' command (alias for simulate)
    run_parser = subparsers.add_parser('run', help='Run a Monte Carlo simulation (alias for simulate)')
    run_parser.add_argument('file', help='Path to CRML YAML file')
    run_parser.add_argument('--runs', type=int, default=10000,
                           help='Number of simulation runs (default: 10000)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'validate':
        success = validate_crml(args.file)
        return 0 if success else 1
    
    elif args.command == 'explain':
        from crml.explainer import explain_crml
        success = explain_crml(args.file)
        return 0 if success else 1
    
    elif args.command == 'simulate':
        success = run_simulation_cli(args.file, n_runs=args.runs, output_format=args.format, fx_config_path=args.fx_config)
        return 0 if success else 1
    
    elif args.command == 'run':
        # Legacy command - use text format
        success = run_simulation_cli(args.file, n_runs=args.runs, output_format='text')
        return 0 if success else 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
