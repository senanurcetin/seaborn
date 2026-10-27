# Seaborn #4013 — independent mixed-category histogram QA

Checked: **27 October 2026** (Europe/Istanbul).

- Upstream PR: https://github.com/mwaskom/seaborn/pull/4013
- PR HEAD tested: `62d8d1a9eb2cd717a1bbff4c18c39d2ca3e0a182`
- Unmodified upstream baseline: `c1cb287835852406691aed60ea0c62710f2c6b18`
- QA-only fork branch: `qa/seaborn-4013-category-identity-20261027`
- Test file: `qa_evidence/test_mixed_category_identity_4013.py`

**The active PR/contributor branch was not changed.** No maintainer ping, no
new upstream pull request, and no GitHub CI rerun was initiated.

## QA coverage

**78 newly authored targeted cases** (offline, Matplotlib Agg):

- **28 valid mixed-category charts**: 7 number/text input families x
  2 orientations x with/without hue. Includes ordinary signed numbers,
  `decimal.Decimal`, `fractions.Fraction`, bool, NumPy scalar values,
  and repeated levels. Verify exact rendered tick-label order, visible
  patches, and original input DataFrame integrity.
- **16 invalid identity-collision cases**: 8 numeric/text identity
  merges or splits x both orientations. Expected a descriptive
  `ValueError`, with the original pandas Series unchanged. Examples:
  `1` vs `"1"`, `False` vs `0`, `Decimal("1.0")` vs `1`,
  and the combination `[1, 1.0, "1"]` where distinct-value
  count alone fails to detect both changes.
- **16 declared category-order cases**: 4 categorical level patterns x
  2 orientations x ordered/unordered. Check the configured order,
  including **unused categories**, is preserved.
- **6 unused-category collision cases**: categorical dtypes with
  distinct declared labels that would map to the same text
  (including numeric/text, decimal/text, and bool/text).
- **8 missing value cases**: `None`, `np.nan`, `pd.NA`,
  `pd.NaT` x 2 orientations. Missing values must not become
  literal text categories.
- **4 displot facet cases**: 2 and 3 facets x both orientations.
  Shared axes intentionally suppress duplicate tick labels in
  secondary panels; tests check the full category positions,
  rendered bars, first visible labels, and DataFrame integrity.

These cover identity preservation and category order for the
specific PR change; they are not evidence of exhaustive Matplotlib
categorical behavior or all seaborn plotting functions.

## Reproduction and results

Windows / Python 3.11.9; seaborn fork 0.14.0.dev0;
NumPy 2.3.5, pandas 2.2.3, Matplotlib 3.10.9.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:MPLBACKEND = "Agg"
python -m pytest -q -o addopts= `
  qa_evidence/test_mixed_category_identity_4013.py `
  tests/test_distributions.py `
  --tb=line --disable-warnings
```

**365 passed, 1 skipped, 8 warnings, exit 0** (72.96s).
The standalone 78-case QA suite passed after correcting a test-only
shared-axis-label assumption. `ruff check` and `ruff format --check`
passed for the QA file.

## Negative control (before the PR)

A detached worktree of unchanged upstream commit `c1cb287`
ran the same QA module filtered to `-k integers`:

**4 of 4 failed** on the old code with
`ValueError: Unable to parse string "alpha" at position 1`.
The same cases pass on the PR HEAD. The remaining 74 new tests
were **not** run against the old base; do not imply otherwise.

## Notebook 1 handoff

PR #4013 remained open and mergeable at the checked HEAD.
Its upstream CI was `action_required` due to fork-workflow approval,
not a recorded failing test run. Maintain quiet review etiquette:
no artificial no-op commit, forced CI run, or repeated ping.

If reviewers request more coverage, consider porting a small set of
the strongest identity-split and unused-category tests into
`tests/test_distributions.py`. Do not cherry-pick the entire
QA-only directory into the active PR branch by default.
