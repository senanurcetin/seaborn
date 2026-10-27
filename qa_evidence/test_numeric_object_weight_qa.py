"""Independent QA of numeric pandas object/nullable weights in seaborn #4012."""

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
def close_figures():
    yield
    plt.close("all")


def signature(df, method, orient, with_hue):
    fig, ax = plt.subplots()
    kws = {"data": df, "weights": "w", orient: "x", "ax": ax}
    if with_hue:
        kws["hue"] = "hue"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                if method == "kde":
                    kdeplot(common_norm=True, **kws)
                else:
                    stat = method.removeprefix("hist_")
                    histplot(stat=stat, bins=4, kde=True, **kws)
        bars = np.array(
            [
                (patch.get_x(), patch.get_y(), patch.get_width(), patch.get_height())
                for patch in ax.patches
            ],
            dtype=float,
        ).reshape(-1, 4)
        curves = [line.get_xydata().copy() for line in ax.lines]
        assert np.isfinite(bars).all()
        assert all(np.isfinite(curve).all() for curve in curves)
        return bars, curves
    finally:
        plt.close(fig)


@pytest.mark.parametrize("dtype", ["object", "Float64"])
@pytest.mark.parametrize("scale", [1e-300, 1e307])
@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize("with_hue", [False, True])
@pytest.mark.parametrize("method", ["kde", "hist_density", "hist_probability"])
def test_numeric_object_and_nullable_weights_match_float64_reference(
    dtype, scale, orient, with_hue, method
):
    values = np.arange(8, dtype=float)
    weights = np.array([1, 3, 2, 4, 5, 1, 3, 2], dtype=float) * scale
    frame = pd.DataFrame(
        {
            "x": values,
            "w": weights,
            "hue": ["a", "b", "a", "b", "a", "b", "a", "b"],
        }
    )
    original = frame.copy(deep=True)
    converted = frame.copy(deep=True)
    converted["w"] = pd.Series(weights, dtype=dtype)

    numeric = signature(frame, method, orient, with_hue)
    actual = signature(converted, method, orient, with_hue)

    np.testing.assert_allclose(actual[0], numeric[0], rtol=5e-12, atol=1e-12)
    assert len(actual[1]) == len(numeric[1])
    for measured, reference in zip(actual[1], numeric[1]):
        np.testing.assert_allclose(measured, reference, rtol=5e-12, atol=1e-12)
    pd.testing.assert_frame_equal(frame, original)
    assert converted["w"].dtype == dtype
