# Seaborn #4012 — Independent weighted-density QA

Checked: **27 October 2026**. Tested contribution head:
`0a353e351c2744f8cab6646239e11d3c67f6e9e6`.

- Upstream PR: https://github.com/mwaskom/seaborn/pull/4012
- Baseline commit: `c1cb287835852406691aed60ea0c62710f2c6b18`
- Separate fork branch: `qa/seaborn-4012-scale-invariance-20261027`
- QA-only tests: `qa_evidence/test_weighted_density_scale_qa.py`.
- **The active contributor branch was not modified, and no upstream workflow rerun was requested.**

## Technical focus

The PR prevents overflow in normalized weighted histograms and singular /
concentrated weighted KDE estimators. The additional independent tests
validate the scale-invariance property: multiplying all strictly positive
weights by the same nonzero constant should not change the output of
a normalized histogram or weighted KDE, within floating-point tolerance.

The **72 new parametrized tests** comprise:

- **64 histogram tests**: 2 scales (`1e-300`, `1e307`) x 2 orientations
  x 2 hue layouts x 4 normalized statistics (density, probability,
  proportion, percent) x KDE overlay enabled/disabled. The unscaled
  reference is computed using the same fixed observations/weights;
  both patch geometry and, when present, KDE curve coordinates are
  compared element by element.
- **8 weighted KDE tests**: 2 scales x 2 orientations x 2 hue layouts.
  The curves' coordinates must agree with the unscaled reference.
- Both modes demand finite output and elevate numerical overflow,
  invalid division, and RuntimeWarning during plotting to errors.

Ordinary weights are `[1, 3, 2, 4, 5, 1, 3, 2]`; the scaled largest
weight is `5e307`, within float64 range, but the **total** weighted
mass overflows float64 if summed without numerical protection.

## Evidence and reproduction

Local: Windows / Python 3.11.9, NumPy 2.3.5, pandas 2.2.3,
SciPy 1.17.0, Matplotlib 3.10.9; `MPLBACKEND=Agg`.
Run with no network or credentials:

```powershell
$env:MPLBACKEND = 'Agg'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest -q -o addopts= `
  qa_evidence/test_weighted_density_scale_qa.py `
  tests/test_distributions.py `
  --disable-warnings --tb=line
```

**Observed result: 362 passed, 1 skipped, 10 warnings, exit 0**
(80.44 seconds).

The isolated new QA suite by itself: **72 passed**.
`ruff check` and `ruff format --check` passed for the QA test file.

### Baseline negative control

The same QA test file was copied into a **detached baseline worktree**
at `c1cb287`. Running with `pytest -x` produced:

- One early `1e-300` scale case passed.
- The next `1e307` normalized-density histogram case failed with
  `FloatingPointError: overflow encountered in reduce`, originating
  at the old `all_weights.sum()` in `seaborn/distributions.py`.
- The exact case passes on PR #4012.

The baseline run intentionally stopped at the first failure. It is
**not** accurate to claim that all 72 tests were run against the base,
nor that full repository-wide test coverage was performed.

## Boundary and handoff

The PR remains open and GitHub Actions displays `action_required`, an
external approval state rather than a test failure. Notebook 1 should
wait for maintainer review / CI approval without no-op commits or
repeated requests. Notebook 2 must not overwrite the contribution head.

No requirement to merge this large QA-only suite upstream unless a
maintainer asks for additional coverage. If needed, port targeted
invariance cases into the existing `tests/test_distributions.py`
structure and rerun supported environments.

The exploratory local diagnostic also showed unnormalized `count`
and `frequency` statistics can exceed finite float64 range for
huge raw sums. Those statistics are **not** covered by this PR's
claim of normalized-scale invariance and are **not** classified here
as a newly introduced regression.
