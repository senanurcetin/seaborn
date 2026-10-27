"""Independent QA for Seaborn #4013 mixed-number/text histogram categories.

Run only against the contributor revision or a detached upstream baseline.
These tests check distinct category identity, order, NA preservation, and
input immutability without modifying the active pull request.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal
from seaborn import displot, histplot


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


VALID_VALUES = [
    pytest.param([0, "alpha", 1, "beta"], ["0", "alpha", "1", "beta"], id="integers"),
    pytest.param(
        [-2, "minus", 3.5, "plus"], ["-2", "minus", "3.5", "plus"], id="signed"
    ),
    pytest.param(
        [Decimal("1.5"), "a", Decimal("2.5"), "b"],
        ["1.5", "a", "2.5", "b"],
        id="decimal",
    ),
    pytest.param(
        [Fraction(1, 2), "a", Fraction(3, 2), "b"],
        ["1/2", "a", "3/2", "b"],
        id="fraction",
    ),
    pytest.param(
        [False, "no", True, "yes"], ["False", "no", "True", "yes"], id="boolean"
    ),
    pytest.param(
        [np.int64(7), "seven", np.float64(8.25), "eight"],
        ["7", "seven", "8.25", "eight"],
        id="numpy-scalars",
    ),
    pytest.param([0, "a", 0, "b"], ["0", "a", "b"], id="repeated"),
]


@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize("with_hue", [False, True])
@pytest.mark.parametrize("values, expected_labels", VALID_VALUES)
def test_valid_categories_keep_order_and_input(
    values, expected_labels, orient, with_hue
):
    frame = pd.DataFrame(
        {"mixed": pd.Series(values, dtype=object), "group": ["a", "b", "a", "b"]}
    )
    before = frame.copy(deep=True)
    kwargs = {"data": frame, orient: "mixed"}
    if with_hue:
        kwargs["hue"] = "group"
    ax = histplot(**kwargs)

    labels = ax.get_xticklabels() if orient == "x" else ax.get_yticklabels()
    assert [item.get_text() for item in labels] == expected_labels
    assert ax.patches
    assert_frame_equal(frame, before)


INVALID_VALUES = [
    pytest.param([1, "1", "other"], id="integer-text-merge"),
    pytest.param([False, 0, "other"], id="false-zero-split"),
    pytest.param([True, 1, "other"], id="true-one-split"),
    pytest.param([Decimal("1.0"), 1, "other"], id="decimal-int-split"),
    pytest.param([Decimal("1"), "1", "other"], id="decimal-text-merge"),
    pytest.param([1, 1.0, "1"], id="merge-and-split-cancellation"),
    pytest.param([Fraction(1, 2), "1/2", "other"], id="fraction-text-merge"),
    pytest.param([0.0, "0.0", "other"], id="float-text-merge"),
]


@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize("values", INVALID_VALUES)
def test_identity_collision_is_rejected_without_changing_source(values, orient):
    original = pd.Series(values, dtype=object)
    before = original.copy(deep=True)
    with pytest.raises(ValueError, match="changing distinct category values"):
        histplot(**{orient: original})
    assert_series_equal(original, before)


CATEGORY_LEVELS = [
    pytest.param(["z", -2, "a", 4], id="signed-integer"),
    pytest.param(["z", Decimal("1.5"), "a", Decimal("2.5")], id="decimal"),
    pytest.param(["z", True, "a", False], id="boolean"),
    pytest.param(["z", 0, "a", 3.5], id="mixed-float"),
]


@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize("ordered", [True, False])
@pytest.mark.parametrize("categories", CATEGORY_LEVELS)
def test_categorical_declared_order_including_unused_levels(
    categories, ordered, orient
):
    observed = [categories[1], categories[0], categories[1]]
    series = pd.Series(pd.Categorical(observed, categories=categories, ordered=ordered))
    before = series.copy(deep=True)
    ax = histplot(**{orient: series})
    labels = ax.get_xticklabels() if orient == "x" else ax.get_yticklabels()
    assert [item.get_text() for item in labels] == list(map(str, categories))
    assert_series_equal(series, before)


@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize(
    "categories, observed",
    [
        ([0, "0", "a"], [0, "a", 0]),
        ([Decimal("1"), "1", "a"], [Decimal("1"), "a", Decimal("1")]),
        ([False, "False", "a"], [False, "a", False]),
    ],
)
def test_unused_categorical_levels_must_not_collapse(categories, observed, orient):
    series = pd.Series(pd.Categorical(observed, categories=categories))
    before = series.copy(deep=True)
    with pytest.raises(ValueError, match="changing distinct category values"):
        histplot(**{orient: series})
    assert_series_equal(series, before)


@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize("missing", [None, np.nan, pd.NA, pd.NaT])
def test_missing_entries_not_converted_to_literal_category(orient, missing):
    data = pd.DataFrame({"mixed": pd.Series([0, "alpha", missing, 1], dtype=object)})
    before = data.copy(deep=True)
    ax = histplot(data=data, **{orient: "mixed"})
    labels = ax.get_xticklabels() if orient == "x" else ax.get_yticklabels()
    assert [tick.get_text() for tick in labels] == ["0", "alpha", "1"]
    assert_frame_equal(data, before)


@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize("facets", [2, 3])
def test_displot_facets_preserve_mixed_axis_levels(orient, facets):
    values = [0, "alpha", 1, "beta"]
    data = pd.DataFrame(
        {
            "mixed": values * facets,
            "facet": [f"group_{i}" for i in range(facets) for _ in values],
        }
    )
    before = data.copy(deep=True)
    plot = displot(data=data, col="facet", kind="hist", **{orient: "mixed"})
    assert len(plot.axes.flat) == facets
    for ax in plot.axes.flat:
        # Shared axes intentionally hide repeated tick labels on other panels.
        ticks = ax.get_xticks() if orient == "x" else ax.get_yticks()
        assert len(ticks) == 4
        assert ax.patches
    first_ax = plot.axes.flat[0]
    labels = first_ax.get_xticklabels() if orient == "x" else first_ax.get_yticklabels()
    assert [tick.get_text() for tick in labels] == ["0", "alpha", "1", "beta"]
    assert_frame_equal(data, before)
