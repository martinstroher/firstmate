import importlib.util, unittest, os, json
from pathlib import Path
R=Path.cwd();E=Path('/Users/martinstroher/dev/firstmate/data/ado-pr-support/nm/evidence/01M6PM8Z12CR1T9WRTP3CZXSCJ')
spec=importlib.util.spec_from_file_location('azure',R/'tests/azure-pr-contract.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
f=(E/'synthetic-azure-cli.txt').open('w',buffering=1)
f.write('Synthetic Azure transport: these are real Firstmate entrypoints, NOT live Azure service evidence.\n')
original=m.AzureContract.script
def script(self,name,*args):
 p=original(self,name,*args)
 f.write('\n$ bin/'+name+' '+' '.join(args)+'\n'+p.stdout+p.stderr+'exit='+str(p.returncode)+'\n')
 for name in ('patch','state/task.meta','state/task.pr-poll','state/task.merge-authority'):
  path=self.dir/name
  f.write(name+': '+(path.read_text() if path.exists() else 'ABSENT')+'\n')
 return p
m.AzureContract.script=script
names=['test_matching_expected_head_completes_through_merge_entrypoint','test_mismatched_expected_head_refuses_without_authority','test_expected_head_still_requires_policies','test_optional_checks_do_not_block_guarded_completion','test_registration_and_guarded_merge','test_no_waivers_or_async_success']
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(m.AzureContract(name) for name in names))
f.close();raise SystemExit(0 if result.wasSuccessful() else 1)
