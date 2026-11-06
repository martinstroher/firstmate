# Targeted validation scope

Target: b7aa4b93c8e44f4d0d13e12ffccce21e8245843f
Base: b77b66cb999876c4db19da36b9af5baaacdd52e5

## Live product evidence

- `live-cli.txt`: real Firstmate CLI output from a disposable marked lab home; generated personal/default/explicit-local branch instructions were executed with real Git. The review command selected the recorded personal branch despite the checkout being on main.
- `generated-*-brief.md`: actual generated worker interfaces, including no-mistakes publication instructions and provider-specific release-target arguments. These prove emitted instructions, not a model's compliance or an executed publication pipeline.
- `live-results.json` and `live-cli.txt`: the real executable containment proof evaluated 24 newly constructed Git histories. Positive rewritten-history cases passed; unmerged changes/restorations/deletions were rejected; missing objects and alignment exhaustion returned unknown. No forge or Git implementation was mocked in this direct proof run.
- `live-nested-dirt.txt`: the real cleanup CLI, using a marked disposable home and no tool stubs, refused an initialized nested module's untracked source hidden by Git status and ancestor ignore settings. Source bytes, task head, and record survived. The committed head itself passed containment.

## Deterministic integration evidence — NOT live Azure

- `synthetic-azure-cli.txt`: real registration/merge entrypoints with the repository's synthetic Azure transport. Matching expected head requests completion without policy bypass; mismatched head and mandatory-policy waits request no completion and create no merge authority. Optional statuses do not block an otherwise mandatory-green revision.
- `teardown-critical-product.txt`: missing/reassigned-copy completion guard and nested tracked/hidden-untracked/clean controls. Azure and endpoint transports were fixtures. Active, abandoned, and unreadable PR responses preserved task records, monitoring, and backlog; completed records retired without touching reassigned work.
- `teardown-proof-product.txt`: unavailable-proof/fallback controls and public cleanup of path-provenance-created versus path-provenance-restored histories, using synthetic forge and pool transports.
- `interrupted-teardown-product.txt`: product outputs retained from the initial bounded cleanup batch; not represented as a completed batch.

## Commands and completeness

Initial inspection: `git status --short`, `git diff --stat <base> <target>`, targeted diffs and interface/runbook reads. No pre-existing test-command result was supplied to this turn.

- `python3 tests/azure-pr-contract.py -v`: the initial 850-second bound interrupted the final portion after 31 passing method results. The two remaining methods, `test_status_policy_selects_the_current_check` and `test_unresolved_discussions_without_policy`, both passed in a separate invocation. This was not one uninterrupted full test run.
- Five selected `tests/fm-task-delivery.test.sh` functions passed: project prefix selection, delivered definition of done, persisted promotion branch, shell-safe promotion command, and registry prefix resolution.
- `bin/fm-test-run.sh --jobs 1 --per-script-timeout-secs 300 tests/fm-brief.test.sh tests/fm-review-diff.test.sh`: incomplete. Brief exceeded the chosen 300-second bound after passing emitted-contract checks; the outer 900-second command bound interrupted the subsequent review run. No assertion failure was observed in the captured output.
- Focused brief rerun passed: `test_base_branch_is_rendered_and_bounded`, `test_ship_branch_prefix_defaults_to_legacy_fm`, and `test_branch_prefix_command_is_shell_safe`. Real manual CLI review supplemented the incomplete larger review batch.
- Initial selected cleanup batch hit its 850-second bound. Focused reruns completed `test_azure_completion_required_without_owned_copy`, `test_dirty_initialized_nested_submodule_refuses`, and `test_content_fallback_proof_capability_boundary`, plus public cleanup for path-provenance-created/restored histories.
- `python3 tests/containment-contract.py -v`: all independent alignment/history oracle cases passed.
- `python3 state/test-validation/live-checks.py` and `python3 state/test-validation/live-dirty.py`: completed successfully; their disposable directories were removed.
- An additional Azure transcript-capture invocation was interrupted by its encompassing tool-call bound after four method passes; no claim is made that this supplemental invocation finished. The corresponding cases already passed in the primary contract run.

No complete repository suite, external CI, publication, activation, real PR merge, or live Azure mutation was performed. No tracked files were changed. CLI transcripts and generated Markdown are the relevant end-user surfaces; screenshots are not applicable.

## Accepted unresolved live-service limitation

`az` is on PATH, but no approved real Azure PR URL or repository scope was supplied, and this phase may not read operator data or mutate live Azure. Disposable local Git repositories and synthetic transport covered the local behavior; they cannot establish Azure service interoperability, real colleague approvals, completion, or actual service-confirmed cleanup. Azure DevOps Services cannot be stood up as a local disposable service. Read-only validation needs a specifically approved PR and read access; live completion needs separately authorized disposable Azure infrastructure. These are the previously accepted limitations, not new findings or authorization requests. Overall live-Azure verdict remains inconclusive; broad regression coverage also remains incomplete.
