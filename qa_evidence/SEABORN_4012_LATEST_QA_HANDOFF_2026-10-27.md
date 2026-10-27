# Seaborn #4012 — updated-head independent QA handoff

Checked on 27 October 2026. Latest tested upstream contribution commit:
`f819994ed5153b15596f9c1c75cc44fb6deb5630`.

- Upstream PR: https://github.com/mwaskom/seaborn/pull/4012
- Prior contribution commit: `0a353e351c2744f8cab6646239e11d3c67f6e9e6`
- Before-PR baseline: `c1cb287835852406691aed60ea0c62710f2c6b18`
- Isolated QA branch: `qa/seaborn-4012-numeric-weights-20261027` in
  `senanurcetin/seaborn`, rooted at `f819994`.
- Active contributor branch is **untouched**; no new upstream PR, ping,
  no-op commit, or CI rerun was created.

## Regression coverage

**120 independent QA tests**, all passed on `f819994`:

- `qa_evidence/test_weighted_density_scale_qa.py`: 72 tests for weighted
  histogram and KDE invariance when weights are multiplied by `1e-300`
  or `1e307` (up to `5e307` per observation) across x/y orientation,
  hue groups, four normalized histogram statistics, and KDE overlays.
  Reference output is an ordinary-weight plot; compare histogram patch
  geometry and KDE line coordinates; reject nonfinite output and
  numerical-overflow warnings.
- `qa_evidence/test_numeric_object_weight_qa.py`: 48 tests comparing
  pandas numeric `object` and nullable `Float64` weights against
  float64 weights, across both weight scales, both orientations, hue
  enabled/disabled, and KDE/density/probability plotting. Inputs must
  remain unchanged.

Full bounded distribution test run, offline on Windows / Python 3.11.9
(NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0, Matplotlib 3.10.9):

```powershell
$env:MPLBACKEND = 'Agg'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest -q -o addopts= `
  qa_evidence/test_weighted_density_scale_qa.py `
  qa_evidence/test_numeric_object_weight_qa.py `
  tests/test_distributions.py `
  --disable-warnings --tb=line
```

**Result: 434 passed, 1 skipped, 10 warnings, exit 0** in 86.62 s.
Both QA Python files passed `ruff check` and `ruff format --check`.

## Independent A/B negative controls

1. The before-PR baseline `c1cb287` with the original 72 QA cases:
   the first `1e-300` example passed, but with `pytest -x` the
   `1e307` density case raised
   `FloatingPointError: overflow encountered in reduce` at the old
   `all_weights.sum()` expression; that case passes on PR code.
   The baseline run stopped at the first failure; don't imply all
   cases were run on that revision.
2. The intermediate PR head `0a353e3` with the new 48 numeric
   object/nullable QA cases: `pytest -x` failed on the very first
   numeric `object` KDE case because `np.isfinite` did not accept
   the Series values, raising `TypeError`. The same test passes on
   `f819994` following the two numeric-object support commits
   (`549dbad`, `f819994`).
   Again, this is a **one-case negative control**, not a claim all
   48 variants were run on the intermediate code.

The test result is specific to `f819994` and the above local runtime.
It is not a full repository suite or a claim that upstream GitHub Actions
ran. Recheck the upstream HEAD before cherry-picking anything, as the
contributor branch changed during the QA exercise.

## Handoff

At the last observed upstream HEAD `f819994`, PR #4012 remained open
and mergeable; the PR-triggered CI run showed `action_required`
(maintainer approval), not a completed failed test run.

Notebook 1 can select a small group of boundary tests from either QA
file if a maintainer requests stronger regression coverage. Notebook 2
should keep its active branch intact. Avoid no-op CI commits or repeated
maintainer pings. The user is pursuing genuine open-source contributor
work, not artificial test-count inflation or noise.

Unnormalized `count` and `frequency` with raw weights beyond finite
float64 sums were not added to this normalized-density QA scope; their
magnitude overflow is not asserted to be a new #4012 regression.
