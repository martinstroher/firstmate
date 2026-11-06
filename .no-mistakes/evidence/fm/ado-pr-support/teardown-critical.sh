. "/Users/martinstroher/dev/firstmate/data/ado-pr-support/nm/worktrees/324a78b3a755/01M6PM8Z12CR1T9WRTP3CZXSCJ/state/test-validation/teardown-functions.sh"
test_azure_completion_required_without_owned_copy
test_dirty_initialized_nested_submodule_refuses

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
