#!/usr/bin/env python3
"""Targeted real-CLI verification. No runtime CLI, git, tasks-axi, or lsof mocks.
Run from the assigned worktree; all runtime state stays beneath that worktree.
Recorded task metadata is the public persisted-state input to fm-teardown.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import time

ROOT = Path.cwd()
SCRATCH = ROOT / '.adapter-validation'
EVIDENCE = Path('/Users/martinstroher/dev/firstmate/data/bash-adapter-refusal/nm/evidence/01M2R8HPK0FPEKD7YN8ENJSJA0')
CODE = SCRATCH / 'live-code'
BASE = SCRATCH / 'base-code'
SOCKET = ROOT / 'a.sock'
ENV = {
    'HOME': str(SCRATCH / 'home'),
    'PATH': str(SCRATCH / 'path') + ':/usr/bin:/bin:/usr/sbin:/sbin',
    'TMPDIR': str(SCRATCH / 'tmp'), 'SHELL': '/bin/bash', 'TERM': 'xterm-256color',
    'LC_ALL': 'C', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1',
    'GIT_AUTHOR_NAME': 'Adapter Test', 'GIT_AUTHOR_EMAIL': 'adapter@example.invalid',
    'GIT_COMMITTER_NAME': 'Adapter Test', 'GIT_COMMITTER_EMAIL': 'adapter@example.invalid',
    # Same narrowly scoped gate exemption used by the repository's behavior tests.
    'FM_GATE_REFUSE_BYPASS': '1',
    # Supervision is not launched for these isolated, finished-task records.
    'FM_TEARDOWN_GUARD_DONE': '1',
}
RESULTS = []
LOG = (EVIDENCE / 'live-cli-transcript.log').open('w')


def emit(s):
    print(s, flush=True)
    LOG.write(s + '\n')
    LOG.flush()


def run(args, cwd=ROOT, env=None, check=True, log=False, timeout=60):
    p = subprocess.run([str(a) for a in args], cwd=cwd, env=env or ENV,
                       text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=timeout)
    if log:
        emit('$ ' + shlex.join([str(a) for a in args]))
        emit('exit=' + str(p.returncode))
        if p.stdout: emit('stdout:\n' + p.stdout.rstrip())
        if p.stderr: emit('stderr:\n' + p.stderr.rstrip())
    if check and p.returncode:
        raise RuntimeError(shlex.join([str(a) for a in args]) + '\n' + p.stdout + p.stderr)
    return p


def put(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def snapshot(paths):
    result = {}
    for path in paths:
        for p in [path, *sorted(path.rglob('*'))] if path.exists() else []:
            key = str(p.relative_to(ROOT))
            s = p.lstat()
            row = {'mode': stat.S_IMODE(s.st_mode)}
            if p.is_symlink(): row['link'] = os.readlink(p)
            elif p.is_file(): row['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
            else: row['directory'] = True
            result[key] = row
    return result


def meta(home, ident, backend, wt, project, kind='ship', target_home=None):
    endpoint = {
        'tmux': ['window=adapter-live:fm-' + ident],
        'herdr': ['backend=herdr', 'window=fm-lab-adapter:w1:p1',
                  'herdr_session=fm-lab-adapter', 'herdr_workspace_id=w1',
                  'herdr_tab_id=w1:t1', 'herdr_pane_id=w1:p1'],
        'zellij': ['backend=zellij', 'window=adapter-live:7', 'zellij_session=adapter-live',
                   'zellij_tab_id=3', 'zellij_pane_id=7'],
        'cmux': ['backend=cmux', 'window=workspace-1:surface-1',
                 'cmux_workspace_id=workspace-1', 'cmux_surface_id=surface-1'],
        'orca': ['backend=orca', 'window=fm-' + ident, 'terminal=term-' + ident,
                 'orca_worktree_id=wt-' + ident + '::' + str(wt)],
    }[backend]
    lines = endpoint + ['endpoint_task_id=' + ident, 'worktree=' + str(wt),
                        'project=' + str(project), 'kind=' + kind, 'mode=local-only',
                        'spawn_gen=s' + str(time.time_ns())]
    if target_home: lines += ['home=' + str(target_home)]
    put(home / 'state' / (ident + '.meta'), '\n'.join(lines) + '\n')
    for suffix, value in [('status', 'done: adapter validation outcome\n'),
                          ('turn-ended', 'ended\n'), ('progress', 'progress\n'),
                          ('pi-ext.ts', '// per-task extension\n'),
                          ('inbox/message', 'pending steering\n')]:
        put(home / 'state' / (ident + '.' + suffix), value)
    put(home / 'data' / ident / 'report.md', 'Finished task report: keep this deliverable.\n')


def home_dirs(home):
    for name in ['state', 'data', 'config', 'projects']:
        (home / name).mkdir(parents=True, exist_ok=True)


def make_window(ident, cwd):
    run(['tmux', 'new-window', '-d', '-t', 'adapter-live:', '-n', 'fm-' + ident,
         '-c', cwd, '/bin/sleep 600'])
    run(['tmux', 'set-window-option', '-t', 'adapter-live:fm-' + ident, 'automatic-rename', 'off'])


def inventory():
    return run(['tmux', 'list-windows', '-t', 'adapter-live', '-F',
                '#{window_id} #{window_name} #{pane_pid} #{pane_current_path}']).stdout


def verify(backend, route, availability, baseline=False):
    label = ('base-' if baseline else '') + backend + '-' + route + '-' + availability
    emit('\n=== ' + label + ' ===')
    case = SCRATCH / 'live-cases' / label
    case.mkdir(parents=True)
    home = case / 'home'
    project = case / 'project'
    home_dirs(home)
    project.mkdir()
    run(['git', 'init', '-q', '-b', 'main'], cwd=project)
    run(['git', 'commit', '-q', '--allow-empty', '-m', 'local baseline'], cwd=project)
    valid = availability == 'valid'
    if valid:
        put(project / 'treehouse.toml', 'max_trees = 4\nroot = "./"\n')
        put(project / '.git/info/exclude', 'treehouse.toml\n.treehouse/\n.claude/\nsentinel\n')
        lease = run(['treehouse', 'get', '--lease', '--lease-holder', label, '--json'], cwd=project, log=True)
        wt = Path(json.loads(lease.stdout)['path'])
        run(['git', 'checkout', '-q', '-b', 'fm/task-x1'], cwd=wt)
    else:
        wt = case / 'wt'
        run(['git', 'worktree', 'add', '-q', '-b', 'fm/task-x1', wt, 'main'], cwd=project)
        put(project / '.git/info/exclude', '.claude/\nsentinel\n')
    put(wt / 'sentinel', 'Task copy must survive a prerequisite refusal.\n')
    put(wt / '.claude/settings.local.json', '{"hooks":{}}\n')
    tasktmp = case / 'tasktmp'
    put(tasktmp / 'sentinel', 'Temporary task work must survive a prerequisite refusal.\n')
    protected = [home, wt, tasktmp]
    sibling = None
    target_home = home
    secondmate = case / 'secondmate-home'
    other = 'herdr' if backend == 'tmux' and not valid else 'tmux'
    if route in ['forced-parent', 'child', 'grandchild']:
        home_dirs(secondmate)
        put(secondmate / '.fm-secondmate-home', 'task-x1\n')
        put(home / 'config/backlog-backend', 'manual\n')
        if route != 'grandchild':
            put(home / 'data/secondmates.md', '- task-x1 - adapter validation (home: ' + str(secondmate) + '; scope: test; projects: project; added 2026-09-17)\n')
        parent_backend = backend if route == 'forced-parent' else other
        meta(home, 'task-x1', parent_backend, secondmate, project, 'secondmate', secondmate)
        sibling = case / 'sibling-wt'
        run(['git', 'worktree', 'add', '-q', '-b', 'fm/a-healthy', sibling, 'main'], cwd=project)
        meta(secondmate, 'a-healthy', other, sibling, project)
        if other == 'tmux': make_window('a-healthy', sibling)
        if parent_backend == 'tmux': make_window('task-x1', secondmate)
        protected += [secondmate, sibling]
        if route in ['child', 'grandchild']:
            target_home = secondmate
            if route == 'grandchild':
                nested = secondmate / 'nested-home'
                home_dirs(nested)
                put(nested / '.fm-secondmate-home', 'nested-sm\n')
                meta(secondmate, 'nested-sm', other, nested, project, 'secondmate', nested)
                if other == 'tmux': make_window('nested-sm', nested)
                target_home = nested
            meta(target_home, 'z-broken', backend, wt, project)
            if backend == 'tmux': make_window('z-broken', wt)
            record = target_home / 'state/z-broken.meta'
            broken_id = 'z-broken'
        else:
            record = home / 'state/task-x1.meta'
            broken_id = 'task-x1'
    else:
        meta(home, 'task-x1', backend, wt, project)
        record = home / 'state/task-x1.meta'
        broken_id = 'task-x1'
        put(home / 'data/backlog.md', '# Backlog\n\n## In flight\n\n## Queued\n\n## Done\n')
        run(['tasks-axi', 'add', 'task-x1', 'Adapter refusal task', '--kind', 'ship', '--file', home / 'data/backlog.md'])
        run(['tasks-axi', 'start', 'task-x1', '--file', home / 'data/backlog.md'])
        if backend == 'tmux': make_window('task-x1', wt)
    with record.open('a') as f: f.write('tasktmp=' + str(tasktmp) + '\n')
    code = BASE if baseline else CODE
    adapter = code / 'bin/backends' / (backend + '.sh')
    adapter_mode = adapter.stat().st_mode
    backup = adapter.with_suffix('.saved')
    processes = [subprocess.Popen(['/bin/sleep', '600'], cwd=p, env=ENV) for p in [wt, tasktmp]]
    env = dict(ENV, FM_ROOT_OVERRIDE=str(code), FM_HOME=str(home))
    try:
        if availability == 'missing': adapter.rename(backup)
        elif availability == 'unreadable':
            adapter.chmod(0)
            assert not os.access(adapter, os.R_OK), 'chmod 000 did not remove readability'
        before = snapshot(protected)
        refs = run(['git', 'show-ref'], cwd=project).stdout
        branch = run(['git', 'symbolic-ref', 'HEAD'], cwd=wt).stdout
        status = run(['git', 'status', '--porcelain'], cwd=wt).stdout
        windows = inventory()
        emit('tmux before:\n' + windows.rstrip())
        if valid:
            sweep = run([code / 'bin/fm-remote-job-reap-orphans.sh', '--dry-run'], env=env)
            assert not sweep.stdout.strip(), 'Outside-worktree orphan candidates make live cleanup unsafe'
        args = ['/bin/bash', code / 'bin/fm-teardown.sh', 'task-x1']
        if route != 'task': args.append('--force')
        emit('FM_HOME=' + str(home) + ' FM_ROOT_OVERRIDE=' + str(code))
        p = run(args, env=env, check=False, log=True, timeout=120)
        row = {'name': label, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr,
               'backend_endpoint': 'real private tmux' if backend == 'tmux' else 'persisted task identity; backend runtime not launched',
               'command': shlex.join([str(a) for a in args]), 'before': before}
        if not valid:
            after = snapshot(protected)
            alive = all(proc.poll() is None for proc in processes)
            new_windows = inventory()
            row.update(after=after, processes_preserved=alive, windows_before=windows, windows_after=new_windows,
                       refs_before=refs, refs_after=run(['git', 'show-ref'], cwd=project).stdout,
                       branch_before=branch, branch_after=run(['git', 'symbolic-ref', 'HEAD'], cwd=wt).stdout,
                       status_before=status, status_after=run(['git', 'status', '--porcelain'], cwd=wt).stdout)
            assert before == after, 'Protected files or directories changed'
            assert alive and windows == new_windows, 'A live process or tmux endpoint was removed'
            assert row['refs_before'] == row['refs_after'] and row['branch_before'] == row['branch_after'] and row['status_before'] == row['status_after'], 'Git state changed'
            if baseline:
                assert p.returncode == 0, 'Original false success not reproduced'
            else:
                assert p.returncode == 1, 'Refusal did not exit 1'
                assert backend + ' teardown prerequisites are unavailable for ' + broken_id in p.stderr
                assert 'complete' not in p.stdout and 'continuing past a close' not in p.stderr
            emit('Observed preservation: every protected path mode/content, Git refs/branch/status, both task processes, and the full private tmux window inventory are unchanged; no pending-close marker.')
        else:
            assert p.returncode == 0 and 'teardown task-x1 complete' in p.stdout
            assert not (home / 'state/task-x1.meta').exists()
            emit('tmux after:\n' + inventory().rstrip())
            if route in ['task', 'forced-task']:
                assert all(proc.wait(timeout=5) is not None for proc in processes)
                assert not tasktmp.exists() and not (wt / '.claude/settings.local.json').exists()
                assert run(['git', 'show-ref', '--verify', 'refs/heads/fm/task-x1'], cwd=project, check=False).returncode != 0
                backlog = run(['tasks-axi', 'show', 'task-x1', '--file', home / 'data/backlog.md'], log=True).stdout
                assert 'state: done' in backlog
                pool = wt.parent.parent / 'treehouse-state.json'
                row['pool_after'] = json.loads(pool.read_text())
                assert all(not item.get('lease_id') and not item.get('lease_holder') for item in row['pool_after']['worktrees'])
                emit('Treehouse persisted state after cleanup:\n' + pool.read_text().rstrip())
                assert not (wt.parent / '.fm-slot-owner').exists()
                emit('Observed cleanup: task processes stopped, tasktmp and hook removed, branch deleted, pool lease released, endpoint closed, metadata removed, backlog done. Treehouse retains ignored cache files in its reusable slot.')
            else:
                assert not secondmate.exists() and not sibling.exists()
                assert 'fm-task-x1' not in inventory() and 'fm-a-healthy' not in inventory() and 'fm-z-broken' not in inventory()
                emit('Observed forced retirement: secondmate home and healthy sibling copy removed; all recorded tmux endpoints closed; parent metadata retired.')
        row['result'] = 'pass'
        RESULTS.append(row)
        (EVIDENCE / 'live-state-evidence.json').write_text(json.dumps(RESULTS, indent=2) + '\n')
    finally:
        if backup.exists(): backup.rename(adapter)
        adapter.chmod(stat.S_IMODE(adapter_mode))
        for proc in processes:
            if proc.poll() is None: proc.terminate()
            proc.wait(timeout=5)
        for ident in ['task-x1', 'a-healthy', 'z-broken', 'nested-sm']:
            run(['tmux', 'kill-window', '-t', 'adapter-live:fm-' + ident], check=False)


def main():
    if CODE.exists(): shutil.rmtree(CODE)
    shutil.copytree(ROOT / 'bin', CODE / 'bin')
    BASE.mkdir(exist_ok=True)
    archive = subprocess.run(['git', 'archive', '3eb5b6334a80e06083e3837f0032a5cec39b8e52', 'bin'], stdout=subprocess.PIPE, check=True).stdout
    subprocess.run(['/usr/bin/tar', '-xf', '-', '-C', str(BASE)], input=archive, check=True)
    assert not SOCKET.exists(), 'Private test socket already exists'
    run(['tmux', '-S', SOCKET, '-f', '/dev/null', 'new-session', '-d', '-s', 'adapter-live', '-n', 'keeper', '/bin/sleep 900'])
    server = run(['tmux', '-S', SOCKET, 'display-message', '-p', '#{pid}']).stdout.strip()
    ENV['TMUX'] = str(SOCKET) + ',' + server + ',0'
    try:
        run(['/bin/bash', '--version'], log=True)
        run(['tmux', '-V'], log=True)
        run(['treehouse', '--version'], log=True)
        verify('herdr', 'task', 'missing', baseline=True)
        for backend in ['tmux', 'herdr', 'zellij', 'cmux', 'orca']:
            for route in ['task', 'forced-task', 'forced-parent', 'child', 'grandchild']:
                if backend == 'orca' and route == 'forced-parent': continue
                for availability in ['missing', 'unreadable']:
                    verify(backend, route, availability)
        for route in ['task', 'forced-task', 'forced-parent', 'child', 'grandchild']:
            verify('tmux', route, 'valid')
        emit('\nAll targeted real-CLI checks passed.')
    finally:
        run(['tmux', '-S', SOCKET, 'kill-server'], check=False)
        if SOCKET.exists(): SOCKET.unlink()
        LOG.close()

if __name__ == '__main__':
    main()
