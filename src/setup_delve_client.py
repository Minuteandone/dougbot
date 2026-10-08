from pathlib import Path
import subprocess, sys
root=Path(__file__).resolve().parents[1]
dst=root/"vendor"/"interacting-with-delve-town"
dst.parent.mkdir(exist_ok=True)
if dst.exists():
    print("Delve client already exists:",dst)
    raise SystemExit(0)
url="https://tangled.org/void.comind.network/interacting-with-delve-town"
print("Cloning independent Delve client from",url)
subprocess.run(["git","clone",url,str(dst)],check=True)
print("done")
