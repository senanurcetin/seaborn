"""Regression coverage for consistent Dodge positions across plot layers."""

import pandas as pd
import seaborn.objects as so


def test_dodge_keeps_category_positions_after_aggregation():
    # Deliberately order the raw color values differently from the groups
    # created by Agg when the x scale orders the positions.
    groups = [
        ("A", "alpha"),
        ("C", "gamma"),
        ("B", "beta"),
        ("B", "alpha"),
        ("C", "alpha"),
    ]
    data = pd.DataFrame(
        [
            {"site": site, "species": species, "value": float(10 + offset)}
            for site, species in groups
            for offset in range(3)
        ]
    )
    positions = []

    class RecordingDodge(so.Dodge):
        def __call__(self, data, groupby, orient, scales):
            result = super().__call__(data, groupby, orient, scales)
            df = result.assign(position=result["x"].round().astype(int))
            positions.append(
                df.groupby(["position", "color"], observed=True)["x"].mean().to_dict()
            )
            return result

    (
        so.Plot(data, x="site", y="value", color="species")
        .scale(x=so.Nominal(order=["A", "B", "C"]))
        .add(so.Bar(), so.Agg(), RecordingDodge())
        .add(so.Dot(), RecordingDodge())
        .plot()
    )
    assert positions[0] == positions[1]
