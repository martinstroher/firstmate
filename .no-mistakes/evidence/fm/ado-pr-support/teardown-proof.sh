. "/Users/martinstroher/dev/firstmate/data/ado-pr-support/nm/worktrees/324a78b3a755/01M6PM8Z12CR1T9WRTP3CZXSCJ/state/test-validation/teardown-functions.sh"

set -e
test_content_fallback_proof_capability_boundary
for scenario in path-provenance-created path-provenance-restored; do
  case_dir=$(make_case "proof-$scenario")
  write_meta "$case_dir" no-mistakes ship
  add_lsof_no_holder "$case_dir"
  python3 "$ROOT/tests/containment-fixtures.py" "$case_dir" "$scenario"
  merged=$(cat "$case_dir/merged-sha")
  add_azure_pr_result "$case_dir" completed "$merged"
  printf 'base_branch=unavailable-fallback\n' >> "$case_dir/state/task-x1.meta"
  rc=0
  run_teardown "$case_dir" > "$case_dir/stdout" 2> "$case_dir/stderr" || rc=$?
  expected=0
  [ "$scenario" != path-provenance-restored ] || expected=1
  expect_code "$expected" "$rc" "$scenario: unexpected cleanup result"
  if [ "$expected" = 1 ]; then
    assert_refusal_retained_task_state "$case_dir" "$scenario" "$(git -C "$case_dir/wt" rev-parse HEAD)"
  else
    assert_absent "$case_dir/state/task-x1.meta" "landed work retained its record"
  fi
  pass "$scenario: public teardown exit $rc"
done

python3 - "$TMP_ROOT" "$FM_EVIDENCE" <<'EVIDENCE'
from pathlib import Path
import sys
root=Path(sys.argv[1]); dest=Path(sys.argv[2])
with dest.open('w') as f:
 for p in sorted(root.glob('*/stdout')):
  case=p.parent;f.write('\n=== '+case.name+' ===\n')
  for name in ('input.json','stdout','stderr','azure.log'):
   source=case/name
   if source.is_file():f.write('--- '+name+' ---\n'+source.read_text(errors='replace')+'\n')
  f.write('retained task record: '+str((case/'state/task-x1.meta').exists())+'\n')
EVIDENCE
