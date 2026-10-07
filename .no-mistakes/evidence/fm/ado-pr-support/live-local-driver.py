import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path.cwd()
EVIDENCE = Path('/Users/martinstroher/dev/firstmate/data/ado-pr-support/nm/evidence/01M49K3325XCG3AZXM5D4E3AZ6')
BASE = ROOT / 'test-live-setup'
LAB = BASE / 'lab'
PROJECT = BASE / 'repo'
HOME = BASE / 'home'
LOG = (EVIDENCE / 'live-local-cli.log').open('w')

def run(args, *, cwd=ROOT, expected=0, show=True):
    if show:
        LOG.write('\n$ ' + ' '.join(map(str, args)) + '\n')
        LOG.flush()
    p = subprocess.run(list(map(str,args)), cwd=cwd, env=ENV, text=True, capture_output=True, timeout=150)
    if show:
        LOG.write(p.stdout + p.stderr + f'[exit {p.returncode}]\n')
        LOG.flush()
    if expected is not None and p.returncode != expected:
        raise AssertionError(f'{args}: expected {expected}, got {p.returncode}: {p.stdout} {p.stderr}')
    return p

ENV = dict(os.environ, HOME=str(HOME), GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
           GIT_AUTHOR_NAME='Validation Lab', GIT_AUTHOR_EMAIL='validation@example.invalid',
           GIT_COMMITTER_NAME='Validation Lab', GIT_COMMITTER_EMAIL='validation@example.invalid',
           PYTHONDONTWRITEBYTECODE='1', FM_HOME=str(LAB), GH_PROMPT_DISABLED='1')
for key in list(ENV):
    if key.startswith('FM_') and key.endswith('_OVERRIDE') or key in ('FM_GATE_REFUSE_BYPASS','FM_TEST_SEAM','FM_TASK_ID'):
        ENV.pop(key)
# Real executables only. This local-Git scenario intentionally has no forge or
# no-mistakes executable; the product must use its default-branch fallback.
TOOLS = BASE / 'tools'
TOOLS.mkdir(exist_ok=True, parents=True)
for name in ('awk','bash','basename','cat','chmod','cksum','cmp','comm','cp','cut','date','dirname',
             'env','find','git','grep','head','hostname','id','ln','lsof','mkdir','mktemp','mv','od',
             'perl','ps','python3','readlink','realpath','rm','rmdir','sed','sh','sleep','sort','stat',
             'tail','timeout','tmux','tr','treehouse','uname','uniq','wc','xargs'):
    executable=shutil.which(name)
    if executable and not (TOOLS/name).exists(): (TOOLS/name).symlink_to(executable)
ENV['PATH']=str(TOOLS)
ENV['TMPDIR']=str(BASE)
ENV['TMUX']='/tmp/fm-lab-validation-nonexistent-'+str(os.getpid())+'.sock,0,0'

def git(repo,*args,show=False): return run(['git','-C',repo,*args],show=show).stdout.strip()
def commit(repo,files,message):
    for name,value in files.items(): (repo/name).write_text(value)
    git(repo,'add','--all');git(repo,'commit','-qm',message)
    return git(repo,'rev-parse','HEAD')
def proof(wt,landed,expected,label):
    LOG.write('\n=== '+label+' ===\n')
    run(['git','-C',wt,'log','--all','--oneline','--graph','-8'])
    run(['git','-C',wt,'diff',landed,'HEAD','--','f.txt','g.txt','shared.txt'])
    run(['python3',ROOT/'bin/fm-content-containment.py',wt,landed],expected=expected)

def meta(wt):
    (LAB/'state/proof.meta').write_text(f'kind=ship\nmode=no-mistakes\nyolo=off\nworktree={wt}\nproject={PROJECT}\nbranch=users/martinstroher/proof\nwindow=fm-lab:fm-proof\nendpoint_task_id=proof\nspawn_gen=live-local-proof\n')

def teardown(wt,expected,label):
    LOG.write('\n=== '+label+' ===\n')
    before=git(wt,'rev-parse','HEAD')
    metadata=(LAB/'state/proof.meta').read_bytes()
    result=run([ROOT/'bin/fm-teardown.sh','proof'],expected=expected)
    if expected:
        diagnostic = ('has uncommitted changes' if 'uncommitted' in label else
                      'Azure task has no registered PR URL' if 'Azure' in label else 'not landed')
        assert diagnostic in result.stderr, result.stderr
        assert (LAB/'state/proof.meta').read_bytes()==metadata
        assert git(wt,'rev-parse','HEAD')==before
        LOG.write('Observed: refusal preserves task metadata, HEAD and local files.\n')
    else:
        assert not (LAB/'state/proof.meta').exists()
        LOG.write('Observed: task metadata retired after successful real Treehouse return.\n')
    LOG.flush()

try:
    HOME.mkdir(exist_ok=True)
    PROJECT.mkdir(exist_ok=True)
    git(PROJECT,'init','-q','-b','main')
    git(PROJECT,'commit','-qm','initial','--allow-empty')
    run(['treehouse','init'],cwd=PROJECT)
    run([ROOT/'bin/fm-lab-home.sh','create',LAB])
    (LAB/'config/backlog-backend').write_text('manual\n')
    LOG.write('Isolation: marked disposable FM_HOME, fixture HOME, real executables, local bare origin; no live forge, agent, primary, or pipeline.\n')
    # Generated worker instructions are a public emitted contract, not source.
    run([ROOT/'bin/fm-brief.sh','prefix-proof','repo','--mode','no-mistakes','--branch-prefix','users/martinstroher/'])
    run([ROOT/'bin/fm-brief.sh','default-proof','repo','--mode','no-mistakes'])
    for name in ('prefix-proof','default-proof'):
        text=(LAB/'data'/name/'brief.md').read_text()
        (EVIDENCE/(name+'-brief.md')).write_text(text)
        LOG.write('\nGenerated branch/review contract '+name+':\n')
        LOG.write('\n'.join(line for line in text.splitlines() if 'Ship branch:' in line or 'git checkout -b' in line or 'Delivery contract:' in line or 'no-mistakes axi run' in line)+'\n')
    lease=json.loads(run(['treehouse','get','--lease','--json'],cwd=PROJECT).stdout)
    wt=Path(lease['path'])
    # Local bare origin makes refreshed-default cleanup real without publication.
    origin=BASE/'origin.git'
    git(BASE,'init','--bare','-q',str(origin))
    git(PROJECT,'remote','add','origin',str(origin))
    b=commit(PROJECT,{'f.txt':'0\n','g.txt':'0\n'},'B f=0 g=0')
    git(PROJECT,'push','-q','origin','main')
    git(wt,'checkout','-qb','users/martinstroher/proof',b)
    c=commit(wt,{'f.txt':'1\n'},'C local f=1')
    u=commit(PROJECT,{'g.txt':'1\n'},'U upstream g=1')
    git(wt,'merge','--no-ff','-qm','M import upstream U',u)
    m=git(wt,'rev-parse','HEAD')
    commit(PROJECT,{'g.txt':'2\n'},'later upstream g=2')
    publication=BASE/'publication'
    git(PROJECT,'worktree','add','--detach',str(publication),m)
    git(publication,'rebase','main',show=True)
    git(PROJECT,'merge','--squash',git(publication,'rev-parse','HEAD'),show=True)
    git(PROJECT,'commit','-qm','squash rebased publication')
    landed=git(PROJECT,'rev-parse','HEAD')
    git(PROJECT,'push','-q','origin','main')
    proof(wt,landed,0,'Rebased squash with imported upstream content is contained')
    meta(wt)
    later=commit(wt,{'f.txt':'0\n'},'later unlanded restoration')
    proof(wt,landed,1,'Later restoration must not disappear from local obligations')
    teardown(wt,1,'Real cleanup refuses later unmerged restoration')
    git(wt,'checkout','--detach',m)
    (wt/'f.txt').write_text('uncommitted later edit\n')
    teardown(wt,1,'Real cleanup refuses uncommitted local edits')
    (wt/'f.txt').write_text('1\n')
    git(wt,'checkout','users/martinstroher/proof')
    # Keep the restoration commit anchored; use a separate accepted task tip.
    git(wt,'checkout','-qb','users/martinstroher/landed-proof',m)
    meta(wt)
    # Azure origins without registration must refuse before any network read.
    git(PROJECT,'remote','set-url','origin','ssh.dev.azure.com:v3/example/Project/repo')
    teardown(wt,1,'Username-free Azure SCP origin requires a completed registered PR')
    git(PROJECT,'remote','set-url','origin',str(origin))
    proof(wt,landed,0,'Clean local task remains contained before automatic cleanup')
    # Product teardown owns process cleanup; verify its global best-effort sweep
    # has no candidate before permitting the isolated lifecycle call.
    sweep=run([ROOT/'bin/fm-remote-job-reap-orphans.sh','--dry-run'])
    assert not sweep.stdout.strip(), 'external orphan candidate; do not run destructive cleanup'
    teardown(wt,0,'Real cleanup automatically returns rebased/squash-merged work')
    run(['treehouse','status'],cwd=PROJECT)
    LOG.write('\nAll live local scenarios passed; no Azure request, publication or production merge occurred.\n')
    print('Live local scenarios passed; evidence:', EVIDENCE/'live-local-cli.log')
finally:
    LOG.close()
