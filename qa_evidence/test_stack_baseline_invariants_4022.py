"""Independent metamorphic checks for seaborn #4022 Stack baseline behavior.

In a given stack, translating every baseline and endpoint by a constant must
translate the output baselines and endpoints by that same constant. Other
columns and the stacked segment lengths must remain unchanged.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from seaborn._core.moves import Stack


def make_frame(
    orient: str, layout: str, missing: str, permutation: int
) -> pd.DataFrame:
    rows = []
    for facet in range(2):
        for position in range(3):
            for element in range(4):
                rows.append(
                    {
                        "x": position,
                        "y": float((element + 1) * (facet + 1)),
                        "col": f"col-{facet}",
                        "row": f"row-{facet}",
                        "case_id": f"{facet}-{position}-{element}",
                    }
                )
    frame = pd.DataFrame(rows)
    if missing != "none":
        selectors = {
            "first": [0, 12],
            "middle": [2, 14, 22],
            "last": [11, 23],
        }[missing]
        frame.loc[selectors, "y"] = np.nan

    if layout == "position":
        frame = frame.drop(columns=["col", "row"])
    elif layout == "column":
        frame = frame.drop(columns=["row"])
    elif layout == "row":
        frame = frame.drop(columns=["col"])

    if orient == "y":
        frame = frame.rename(columns={"x": "y", "y": "x"})

    # A stable within-group shuffle detects accidental reliance on index labels
    # or the order of unrelated stacks.
    frame = frame.sample(frac=1, random_state=permutation).copy()
    frame.index = np.arange(1000, 1000 + len(frame)) * 3
    return frame


@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize("layout", ["position", "column", "row"])
@pytest.mark.parametrize("baseline", [-50.0, -2.5, 0.0, 11.5, 1000.0])
@pytest.mark.parametrize("missing", ["none", "first", "middle", "last"])
@pytest.mark.parametrize("permutation", [2, 13, 42, 97])
def test_stack_translation_invariant_across_groups(
    orient, layout, baseline, missing, permutation
):
    original = make_frame(orient, layout, missing, permutation)
    other = {"x": "y", "y": "x"}[orient]
    source = original.copy(deep=True)

    reference_input = original.assign(baseline=0.0)
    translated_input = original.assign(
        baseline=baseline, **{other: original[other] + baseline}
    )
    before = translated_input.copy(deep=True)

    expected = Stack()(reference_input, None, orient, {})
    actual = Stack()(translated_input, None, orient, {})

    assert_frame_equal(translated_input, before)
    assert_frame_equal(original, source)
    assert_series_equal(actual[other], expected[other] + baseline, check_names=False)
    assert_series_equal(
        actual["baseline"], expected["baseline"] + baseline, check_names=False
    )
    assert_series_equal(
        actual[other] - actual["baseline"],
        expected[other] - expected["baseline"],
        check_names=False,
    )
    for column in original.columns:
        if column != other:
            assert_series_equal(actual[column], expected[column], check_names=False)


@pytest.mark.parametrize("orient", ["x", "y"])
@pytest.mark.parametrize("baseline", [-100.0, -0.5, 0.0, 2.75, 200.0])
@pytest.mark.parametrize("missing", [False, True])
def test_direct_single_group_matches_independent_prefix_sum(orient, baseline, missing):
    lengths = np.array([3.0, 1.0, 0.0, 4.0, 5.0])
    if missing:
        lengths[2] = np.nan
    other = {"x": "y", "y": "x"}[orient]
    frame = pd.DataFrame(
        {orient: [0] * len(lengths), other: lengths + baseline, "baseline": baseline}
    )
    original = frame.copy(deep=True)
    result = Stack()(frame, None, orient, {})
    assert_frame_equal(frame, original)

    cumulative = 0.0
    end_values = []
    bottom_values = []
    for length in lengths:
        if np.isnan(length):
            end_values.append(np.nan)
            bottom_values.append(np.nan)
        else:
            bottom_values.append(baseline + cumulative)
            cumulative += length
            end_values.append(baseline + cumulative)
    np.testing.assert_allclose(result[other], end_values, equal_nan=True)
    np.testing.assert_allclose(result["baseline"], bottom_values, equal_nan=True)
