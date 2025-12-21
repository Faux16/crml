"""Copula utilities for the reference engine.

This module intentionally contains only runtime/sampling logic.
The engine-independent *specification* lives in `crml_lang`.
"""

from __future__ import annotations

from typing import Optional

import numpy as np


def gaussian_copula_uniforms(
    corr: np.ndarray,
    n: int,
    *,
    seed: Optional[int] = None,
    jitter: float = 1e-10,
    max_tries: int = 6,
) -> np.ndarray:
    """Sample correlated uniforms using a Gaussian copula.

    Args:
        corr: Correlation matrix (dim x dim).
        n: Number of samples (rows).
        seed: Optional RNG seed.
        jitter: Diagonal jitter added if Cholesky fails.
        max_tries: Number of jitter escalation attempts.

    Returns:
        Array of shape (n, dim) with values in (0, 1).

    Raises:
        ValueError: if the correlation matrix cannot be factorized.
    """

    corr = np.asarray(corr, dtype=np.float64)
    if corr.ndim != 2 or corr.shape[0] != corr.shape[1]:
        raise ValueError("corr must be a square matrix")

    dim = int(corr.shape[0])
    if dim < 1:
        raise ValueError("corr dimension must be >= 1")

    rng = np.random.default_rng(seed)

    # Factorize correlation matrix. If numerical issues occur, add small jitter.
    cov = corr.copy()
    L = None
    for k in range(max_tries):
        try:
            L = np.linalg.cholesky(cov)
            break
        except np.linalg.LinAlgError:
            cov = cov + np.eye(dim) * (jitter * (10**k))

    if L is None:
        raise ValueError("Correlation matrix is not PSD (Cholesky failed)")

    z = rng.standard_normal(size=(n, dim))
    x = z @ L.T

    # Convert to uniforms via standard normal CDF.
    # Prefer SciPy if available; else use erf-based approximation.
    try:
        from scipy.stats import norm

        u = norm.cdf(x)
    except Exception:
        from math import erf, sqrt

        u = 0.5 * (1.0 + np.vectorize(erf)(x / sqrt(2.0)))

    # Avoid exact 0/1 due to numerical extremes.
    eps = np.finfo(np.float64).eps
    return np.clip(u, eps, 1.0 - eps)
