"""Bundling helpers.

Bundling produces a single, self-contained artifact from CRML documents by
inlining referenced documents (scenarios and optionally control packs).

This is a language/tooling concern: the output is engine-agnostic.
"""

from .portfolio_bundler import BundleReport, bundle_portfolio

__all__ = [
    "BundleReport",
    "bundle_portfolio",
]
