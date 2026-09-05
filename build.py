from pathlib import Path
from shutil import copy2, rmtree, copytree
import re
root=Path(__file__).parent
out=root/'dist'
if out.exists():rmtree(out)
out.mkdir()
for p in root.iterdir():
 if p.is_file() and p.suffix in {'.html','.css','.js','.pdf','.png','.txt','.xml'}:copy2(p,out/p.name)
copytree(root/'assets',out/'assets')
s=(out/'index.html').read_text()
for src in re.findall(r'src="([^"]+)"',s):
 if not src.startswith('http'):assert (out/src).exists(),src
ids=set(re.findall(r'id="([^"]+)"',s))
for href in re.findall(r'href="([^"]+)"',s):
 if href.startswith('#'):assert href[1:] in ids,href
 elif not href.startswith(('http','mailto:')):assert (out/href.split("?")[0]).exists(),href
assert 'Data &amp; Intelligence Engineer' in s
assert 'Apr 2024 — Aug 2026' in s
assert 'Aug 24, 2026 — Present' in s
print('Static site built; navigation, local assets and employment dates verified.')
