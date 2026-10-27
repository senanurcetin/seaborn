"""Offline QA for scale-invariant weighted distributions in seaborn #4012.

Compare identical observations and strictly positive weights at ordinary,
near-underflow, and near-overflow scales, with/without hue and a KDE overlay.
No network, GPU, or interactive graphical backend is required.
"""

from __future__ import annotations

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from seaborn import histplot, kdeplot


@pytest.fixture(autouse=True)
def close_plot_windows():
    yield
    plt.close("all")


def frame(scale):
    # Max scaled weight is 5e307, but total scaled weight overflows float64.
    values = np.array([0, 1, 2, 3, 4, 5, 6, 7], dtype=float)
    weights = np.array([1, 3, 2, 4, 5, 1, 3, 2], dtype=float)
    return pd.DataFrame(
        {
            "value": values,
            "weight": weights * scale,
            "group": ["a", "b", "a", "b", "a", "b", "a", "b"],
        }
    )


def plot_signature(kind, data, *, orient, hue, stat="density", kde=False):
    fig, ax = plt.subplots()
    try:
        kwargs = dict(data=data, weights="weight", ax=ax)
        kwargs[orient] = "value"
        if hue:
            kwargs["hue"] = "group"
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                if kind == "kde":
                    kdeplot(common_norm=True, **kwargs)
                else:
                    histplot(stat=stat, bins=4, kde=kde, **kwargs)

        bars = np.array(
            [
                (patch.get_x(), patch.get_y(), patch.get_width(), patch.get_height())
                for patch in ax.patches
            ],
            dtype=float,
        ).reshape(-1, 4)
        curves = [np.asarray(line.get_xydata()) for line in ax.lines]
        assert np.isfinite(bars).all()
        assert all(np.isfinite(curve).all() for curve in curves)
        return bars, curves
    finally:
        plt.close(fig)


@pytest.mark.parametrize("scale", [1e-300, 1e307])
@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize("hue", [False, True])
@pytest.mark.parametrize("stat", ["density", "probability", "proportion", "percent"])
@pytest.mark.parametrize("kde", [False, True])
def test_normalized_histogram_invariant_to_weight_scale(scale, orient, hue, stat, kde):
    normal = plot_signature(
        "hist", frame(1.0), orient=orient, hue=hue, stat=stat, kde=kde
    )
    scaled = plot_signature(
        "hist", frame(scale), orient=orient, hue=hue, stat=stat, kde=kde
    )
    np.testing.assert_allclose(scaled[0], normal[0], rtol=5e-12, atol=1e-12)
    assert len(scaled[1]) == len(normal[1]) == (2 if hue and kde else int(kde))
    for scaled_curve, normal_curve in zip(scaled[1], normal[1]):
        np.testing.assert_allclose(scaled_curve, normal_curve, rtol=5e-12, atol=1e-12)


@pytest.mark.parametrize("scale", [1e-300, 1e307])
@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize("hue", [False, True])
def test_kde_invariant_to_weight_scale(scale, orient, hue):
    normal = plot_signature("kde", frame(1.0), orient=orient, hue=hue)
    scaled = plot_signature("kde", frame(scale), orient=orient, hue=hue)
    assert len(scaled[1]) == len(normal[1]) == (2 if hue else 1)
    for scaled_curve, normal_curve in zip(scaled[1], normal[1]):
        np.testing.assert_allclose(scaled_curve, normal_curve, rtol=5e-12, atol=1e-12)
