# Seaborn #4022 — Independent Stack baseline QA

Checked: 27 October 2026 (Europe/Istanbul).

- Upstream PR: https://github.com/mwaskom/seaborn/pull/4022
- Tested PR HEAD: `37c428e62d111f6c69555d1b27447ff5671d6670`
- Compared with unchanged upstream base: `c1cb287835852406691aed60ea0c62710f2c6b18`
- QA branch: `qa/seaborn-4022-baseline-invariants-20261027`
- QA test source: `qa_evidence/test_stack_baseline_invariants_4022.py`

**The original contribution branch was not edited.** No additional upstream
PR, maintainer ping, or CI rerun was created.

## What was verified

The code change in `seaborn/_core/moves.py:Stack._stack` adds the original
nonzero baseline to the cumulative endpoint:
`df[other] = df["baseline"] + stacked_lengths` rather than just assigning
`stacked_lengths`.

Independent tests check the following invariant:

If the source endpoints and baseline of an entire stack are translated
by the same constant `b`, the output endpoints and baselines must
both translate by `b`, while individual segment lengths and all
unrelated source columns remain unchanged.

**500 independent QA cases**:

- 480 parametrized translation checks: 2 orientations (`x`, `y`) x
  3 grouping layouts (position, column facets, row facets) x 5 baselines
  (`-50`, `-2.5`, `0`, `11.5`, `1000`) x 4 missing-data patterns x
  4 shuffled input orders. Non-default index labels help uncover hidden
  index-alignment assumptions. The original data frames must not mutate.
- 20 independent prefix-sum oracle checks: 2 orientations x 5 baselines x
  2 missing-data variants. For a single stack, compare both cumulative
  endpoints and predecessor baselines against an independently calculated
  running sum, ignoring missing segments.

The existing upstream `tests/_core/test_moves.py` and
`tests/_marks/test_bar.py` were also executed together with the new QA
module:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:MPLBACKEND='Agg'
python -m pytest -q -o addopts= `
  qa_evidence/test_stack_baseline_invariants_4022.py `
  tests/_core/test_moves.py tests/_marks/test_bar.py `
  --disable-warnings --tb=line
```

**Result: 565 passed, 0 failed, 7 warnings (22.87s)** on Windows /
Python 3.11.9, NumPy 2.3.5, pandas 2.2.3, Matplotlib 3.10.9.
The standalone QA module passed 500 cases. `ruff check` and
`ruff format --check` both passed for the QA Python file.

## Unmodified baseline negative control

The same QA file was copied to a detached worktree at `c1cb287` and
the selected `baseline=2.75` prefix-sum variants were run. **4 of 4
failed on the old base**, covering `x` and `y` orientations with
and without missing values. The old implementation returned cumulative
endpoints as though the baseline were zero; new PR HEAD passes.

The full 500-case suite was *not* run against the old base. Do not
extrapolate from the four-case negative control.

## Handoff

The upstream PR remained open and mergeable at the checked HEAD.
Its latest PR CI run was marked `action_required` (fork workflow
approval requirement), not a test failure. Avoid artificial commit
churn or repeated maintainer approval requests. If reviewers want
additional coverage, select the strongest translation and prefix-sum
cases rather than automatically importing all 500 parameters.

This is scoped to positive or zero segment lengths in the generated
translation cases; it does not prove every possible mixed-sign stacking
behavior or complete project-wide regression coverage. The independent
tests are on a QA-only fork branch, not the active contribution branch.
