import os, subprocess, json, shutil, re, sys, time
from pathlib import Path
R=Path.cwd(); W=R/'state/test-validation'; E=Path('/Users/martinstroher/dev/firstmate/data/ado-pr-support/nm/evidence/01M6PM8Z12CR1T9WRTP3CZXSCJ')
D=W/'live'; D.mkdir(exist_ok=True)
env={k:v for k,v in os.environ.items() if not k.startswith(('FM_', 'HERDR_', 'REX_', 'TASKS_AXI_', 'AZURE_', 'PI_'))}
env.update(HOME=str(W/'home'),TMPDIR=str(W/'tmp'),GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM='1',GIT_AUTHOR_NAME='Fixture',GIT_COMMITTER_NAME='Fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',GIT_COMMITTER_EMAIL='fixture@example.invalid',PYTHONDONTWRITEBYTECODE='1')
log=(E/'live-cli.txt').open('w',buffering=1)
def run(args, cwd=R, expected=0, extra=None, show=True, seconds=100):
 p=subprocess.run([str(x) for x in args],cwd=cwd,env={**env,**(extra or {})},text=True,capture_output=True,timeout=seconds)
 if show:
  log.write('$ '+' '.join(str(x) for x in args)+'\n'+p.stdout+p.stderr+'exit='+str(p.returncode)+'\n')
 if expected is not None:assert p.returncode==expected,(args,p.returncode,p.stdout,p.stderr)
 return p

def git(repo,*args):return run(['git','-C',repo,*args],show=False).stdout.strip()
results=[]
try:
 home=D/'lab';run([R/'bin/fm-lab-home.sh','create',home])
 he={'FM_HOME':str(home),'TMUX':str(D/'never-started-socket')+',0,0'}
 log.write('\n=== Branch prefix selection and actual branch creation ===\n')
 for name,mode,prefix in [('personal','no-mistakes','users/example/'),('default','local-only',None),('local-opt-in','local-only','users/example/'),('release','direct-PR','users/example/')]:
  args=[R/'bin/fm-brief.sh',name,'disposable-project','--mode',mode]
  if prefix is not None:args+=['--branch-prefix',prefix]
  if name=='release':args+=['--base-branch','release/1']
  run(args,extra=he)
  text=(home/f'data/{name}/brief.md').read_text()
  (E/f'generated-{name}-brief.md').write_text(text)
  command=re.search(r'^1\. First action: create your branch: `(.*)`$',text,re.M).group(1)
  repo=D/('branch-'+name);repo.mkdir();git(repo,'init','-q','-b','main')
  run(['bash','-c',command],cwd=repo)
  actual=git(repo,'branch','--show-current');assert actual==(prefix or 'fm/')+name
  log.write('observed branch: '+actual+'\n')
 for i,prefix in enumerate(['../bad/','users//name/','users/name.lock/']):
  p=run([R/'bin/fm-brief.sh','invalid'+str(i),'disposable-project','--mode','no-mistakes','--branch-prefix',prefix],extra=he,expected=1)
  assert not (home/f'data/invalid{i}/brief.md').exists()
 results.append({'scenario':'prefix-contract','result':'pass'})
 log.write('\n=== Review the recorded personal branch, not the current checkout ===\n')
 repo=D/'review';repo.mkdir();git(repo,'init','-q','-b','main')
 (repo/'feature.txt').write_text('base\n');git(repo,'add','.');git(repo,'commit','-qm','base')
 git(repo,'checkout','-qb','users/example/fix');(repo/'feature.txt').write_text('personal branch edit\n');git(repo,'commit','-qam','local edit');git(repo,'checkout','-q','main')
 (home/'state/review.meta').write_text(f'kind=ship\nmode=local-only\nbranch=users/example/fix\nproject={repo}\nworktree={repo}\n')
 p=run([R/'bin/fm-review-diff.sh','review'],extra=he)
 assert '+personal branch edit' in p.stdout and '-base' in p.stdout
 results.append({'scenario':'review-recorded-branch','result':'pass'})
 log.write('\n=== Final-content proof on real rewritten Git histories ===\n')
 positives={'landed-delete','successive-upstream','one-upstream','large-rebased-upstream','merge-main-upstream','merge-main-same-file','path-provenance-created','path-provenance-replaced'}
 unknowns={'missing-intermediate-tree','large-alignment-bound'}
 cases='unlanded-delete landed-delete unlanded-replace same-file-restoration literal-path ordinary-path successive-upstream one-upstream partial-two-file whole-file-restoration missing-intermediate-tree complete-enumeration large-rebased-upstream large-rebased-unlanded large-alignment-bound merge-main-upstream merge-main-same-file merge-main-resolution merge-main-merge-restoration merge-main-local-restoration path-provenance-created path-provenance-replaced path-provenance-restored path-provenance-deleted'.split()
 for name in cases:
  case=D/name;case.mkdir();origin=case/'origin.git';project=case/'project';wt=case/'wt'
  git(case,'init','-q','--bare',str(origin));git(origin,'symbolic-ref','HEAD','refs/heads/main');git(case,'clone','-q',str(origin),str(project));git(project,'commit','--allow-empty','-qm','origin base');git(project,'push','-q','origin','main');git(project,'worktree','add','-qb','fm/task-x1',str(wt),'main')
  run([sys.executable,R/'tests/containment-fixtures.py',case,name],show=False)
  inputs=json.loads((case/'input.json').read_text());log.write('\n'+json.dumps(inputs)+'\n')
  code=0 if name in positives else 2 if name in unknowns else 1
  p=run([sys.executable,R/'bin/fm-content-containment.py',wt,inputs['merged_head']],expected=code,seconds=180)
  assert git(wt,'rev-parse','HEAD')==inputs['local_head']
  for path in ('f.txt','g.txt','shared.txt'):
   if name.startswith('path-provenance-') and path in ('f.txt','g.txt'):
    for commit in (inputs['local_head'],inputs['merged_head']):
     q=run(['git','-C',wt,'show',commit+':'+path],expected=None,show=False)
     log.write(commit+':'+path+'\n'+q.stdout+q.stderr)
  results.append({'scenario':name,'result':'pass','expected_exit':code})
 (E/'live-results.json').write_text(json.dumps(results,indent=2)+'\n')
finally:
 log.close();shutil.rmtree(D)
