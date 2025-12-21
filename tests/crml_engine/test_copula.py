import numpy as np
import pytest

from crml_engine.copula import gaussian_copula_uniforms


def test_gaussian_copula_uniforms_has_expected_correlation():
    # Use normals recovered via inverse CDF to estimate correlation.
    rho = 0.7
    corr = np.array([[1.0, rho], [rho, 1.0]], dtype=np.float64)

    n = 20000
    u = gaussian_copula_uniforms(corr=corr, n=n, seed=123)

    from scipy.stats import norm

    z = norm.ppf(u)
    emp = np.corrcoef(z.T)

    assert emp[0, 1] == pytest.approx(rho, abs=0.05)
