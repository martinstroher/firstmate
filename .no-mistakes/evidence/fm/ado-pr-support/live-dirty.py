import os,subprocess,shutil
from pathlib import Path
R=Path.cwd();W=R/'state/test-validation';D=W/'dirty-live';D.mkdir();E=Path('/Users/martinstroher/dev/firstmate/data/ado-pr-support/nm/evidence/01M6PM8Z12CR1T9WRTP3CZXSCJ')
env={k:v for k,v in os.environ.items() if not k.startswith(('FM_','PI_','HERDR_','REX_','TASKS_AXI_'))}
env.update(HOME=str(W/'home'),TMPDIR=str(W/'tmp'),GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM='1',GIT_AUTHOR_NAME='Fixture',GIT_COMMITTER_NAME='Fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',GIT_COMMITTER_EMAIL='fixture@example.invalid',PYTHONDONTWRITEBYTECODE='1')
f=(E/'live-nested-dirt.txt').open('w',buffering=1)
def run(args,expected=0,show=True):
 p=subprocess.run([str(x) for x in args],env=env,text=True,capture_output=True,timeout=140)
 if show:f.write('$ '+' '.join(str(x) for x in args)+'\n'+p.stdout+p.stderr+'exit='+str(p.returncode)+'\n')
 assert p.returncode==expected,(args,p.returncode,p.stdout,p.stderr)
 return p.stdout.strip()
def git(repo,*args,show=False):return run(['git','-C',repo,*args],show=show)
try:
 home=D/'lab';run([R/'bin/fm-lab-home.sh','create',home]);env.update(FM_HOME=str(home),FM_BACKEND='tmux',TMUX=str(D/'never-started-socket')+',0,0')
 (home/'config/backlog-backend').write_text('manual\n')
 inner=D/'inner';inner.mkdir();git(inner,'init','-qb','main');(inner/'tracked.txt').write_text('baseline\n');git(inner,'add','.');git(inner,'commit','-qm','inner base')
 outer=D/'outer';outer.mkdir();git(outer,'init','-qb','main');git(outer,'-c','protocol.file.allow=always','submodule','add','-q',str(inner),'nested');git(outer,'commit','-qm','outer base')
 project=D/'project';project.mkdir();git(project,'init','-qb','main');git(project,'-c','protocol.file.allow=always','submodule','add','-q',str(outer),'module');git(project,'commit','-qm','project base')
 wt=D/'wt';git(project,'worktree','add','-qb','fm/nested',str(wt),'main');git(wt,'-c','protocol.file.allow=always','submodule','update','--init','--recursive')
 git(wt,'config','diff.ignoreSubmodules','all');git(wt,'config','submodule.module.ignore','all');git(wt/'module','config','submodule.nested.ignore','all');nested=wt/'module/nested';git(nested,'config','status.showUntrackedFiles','no')
 (home/'state/nested.meta').write_text(f'kind=ship\nmode=local-only\nbackend=tmux\nwindow=fm-lab:fm-nested\nendpoint_task_id=nested\nspawn_gen=nested-fixture\nworktree={wt}\nproject={project}\n')
 before=(home/'state/nested.meta').read_bytes();head=git(wt,'rev-parse','HEAD')
 (nested/'source.txt').write_text('uncommitted source to preserve\n')
 f.write('Ordinary Git status hides the nested untracked source:\n')
 assert git(wt,'status','--porcelain',show=True)==''
 assert git(nested,'status','--porcelain',show=True)==''
 output=run([R/'bin/fm-teardown.sh','nested'],expected=1)
 assert (nested/'source.txt').read_text()=='uncommitted source to preserve\n'
 assert (home/'state/nested.meta').read_bytes()==before
 assert git(wt,'rev-parse','HEAD')==head
 f.write('Preserved source bytes, exact task record and task head after refusal.\n')
 # This control proves the committed content is landed; it deliberately does
 # not request removal of a copy containing uncommitted source.
 run(['python3',R/'bin/fm-content-containment.py',wt,head])
finally:
 f.close();shutil.rmtree(D)
