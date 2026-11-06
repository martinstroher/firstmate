import os,subprocess,sys,time
from pathlib import Path
root=Path.cwd(); label=sys.argv[1]; command=sys.argv[2:]
evidence=Path('/Users/martinstroher/dev/firstmate/data/ado-pr-support/nm/evidence/01M6PM8Z12CR1T9WRTP3CZXSCJ')
env={k:v for k,v in os.environ.items() if not k.startswith(('FM_', 'HERDR_', 'REX_', 'TASKS_AXI_', 'AZURE_'))}
env.update(TMPDIR=str(root/'state/test-validation/tmp'), HOME=str(root/'state/test-validation/home'), XDG_CONFIG_HOME=str(root/'state/test-validation/home/config'), PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM='1', FM_EVIDENCE=str(evidence/(label+'-product.txt')))
start=time.monotonic()
with (evidence/(label+'.log')).open('w') as f:
 f.write('$ '+' '.join(command)+'\n'); f.flush()
 p=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=850)
 f.write('\nexit='+str(p.returncode)+' elapsed_seconds='+str(round(time.monotonic()-start,1))+'\n')
print(label, 'exit',p.returncode,'seconds',round(time.monotonic()-start,1))
sys.exit(p.returncode)
