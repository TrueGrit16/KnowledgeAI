#!/usr/bin/env python3
import os, sys, ast, json

BASE = os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else os.getcwd()
IGNORE_DIRS = {'.git','.venv','venv','__pycache__','node_modules','build','dist',
               '.mypy_cache','.pytest_cache','.ipynb_checkpoints'}

def py_files():
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        for f in files:
            if f.endswith('.py'):
                yield os.path.join(root, f)

def is_local_module(mod):
    parts = mod.split('.')
    for i in range(1, len(parts)+1):
        p = os.path.join(BASE, *parts[:i])
        if os.path.exists(p + '.py') or os.path.exists(os.path.join(p, '__init__.py')):
            return True
    return False

# Python ≥3.10 exposes stdlib names here:
stdlib = set(getattr(sys, 'stdlib_module_names', set()))
stdlib.update({'argparse','asyncio','contextlib','csv','dataclasses','datetime','functools','glob',
               'hashlib','io','itertools','json','logging','math','os','pathlib','queue','random',
               're','shutil','socket','sqlite3','string','subprocess','sys','tempfile','threading',
               'time','typing','unittest','urllib','uuid','xml','zipfile'})

MODULE_TO_PYPI = {
    # common rename mismatches
    'cv2':'opencv-python','sklearn':'scikit-learn','pil':'Pillow','pillow':'Pillow','yaml':'PyYAML',
    'bs4':'beautifulsoup4','lxml':'lxml','pymupdf':'PyMuPDF','fitz':'PyMuPDF','pyyaml':'PyYAML',
    'pdfminer':'pdfminer.six','pdf2image':'pdf2image','pypdf2':'PyPDF2','pytesseract':'pytesseract',
    'numpy':'numpy','pandas':'pandas','matplotlib':'matplotlib','seaborn':'seaborn','scipy':'scipy',
    'tqdm':'tqdm','loguru':'loguru','rich':'rich','requests':'requests','aiohttp':'aiohttp',
    'httpx':'httpx','fastapi':'fastapi','uvicorn':'uvicorn','flask':'Flask','pydantic':'pydantic',
    'openai':'openai','anthropic':'anthropic','litellm':'litellm','langchain':'langchain',
    'chromadb':'chromadb','faiss':'faiss-cpu','faiss_cpu':'faiss-cpu',
    'sentence_transformers':'sentence-transformers','transformers':'transformers',
    'torch':'torch','torchvision':'torchvision','torchaudio':'torchaudio','nltk':'nltk','spacy':'spacy',
    'redis':'redis','duckdb':'duckdb','pymongo':'pymongo','sqlalchemy':'SQLAlchemy',
    'psycopg2':'psycopg2-binary','pymysql':'PyMySQL','weaviate':'weaviate-client',
    'pinecone':'pinecone-client','tiktoken':'tiktoken','dotenv':'python-dotenv','python_dotenv':'python-dotenv',
    'typer':'typer',
}

EXECUTABLE_HINTS = ['ffmpeg','tesseract','convert','magick','pdftoppm','pdftotext','gs','soffice','wkhtmltopdf']

def scan_execs():
    hits = set()
    for f in py_files():
        try:
            txt = open(f,'r',encoding='utf-8',errors='ignore').read()
            for x in EXECUTABLE_HINTS:
                if x in txt: hits.add(x)
        except Exception: pass
    return sorted(hits)

def collect_imports():
    out, seen = [], set()
    for f in py_files():
        try:
            tree = ast.parse(open(f,'r',encoding='utf-8',errors='ignore').read(), filename=f)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    root = n.name.split('.')[0]
                    if root not in seen:
                        out.append((root, f)); seen.add(root)
            elif isinstance(node, ast.ImportFrom):
                if node.level and not node.module:   # relative import like "from . import x"
                    continue
                if node.module:
                    root = node.module.split('.')[0]
                    if root not in seen:
                        out.append((root, f)); seen.add(root)
    return out

imports = collect_imports()
third_party, local, std_ignored, unmapped = {}, set(), set(), set()

for mod, f in imports:
    mlow = mod.lower()
    if mlow in ('__future__',): continue
    if mod in stdlib or mlow in stdlib:
        std_ignored.add(mod); continue
    if is_local_module(mod):
        local.add(mod); continue
    pkg = MODULE_TO_PYPI.get(mlow, mod)
    third_party.setdefault(pkg, set()).add(mod)
    if pkg == mod and mlow not in MODULE_TO_PYPI:
        unmapped.add(mod)

reqs = sorted(third_party.keys())
report = {
  "repo": BASE,
  "python": f"{sys.version_info.major}.{sys.version_info.minor}",
  "requirements_guess": reqs,
  "stdlib_ignored": sorted(std_ignored),
  "local_modules_detected": sorted(local),
  "unmapped_modules_review": sorted(unmapped),
  "executables_detected": scan_execs(),
}

open(os.path.join(BASE,'requirements.in'),'w').write("\n".join(reqs)+"\n")
open(os.path.join(BASE,'deps_report.json'),'w').write(json.dumps(report, indent=2))

with open(os.path.join(BASE,'deps_report.md'),'w') as f:
    f.write("# Dependency Scan Report\n\n## Candidate Python packages (requirements.in)\n")
    for r in reqs: f.write(f"- {r}\n")
    f.write("\n## Unmapped/needs review\n");  [f.write(f"- {m}\n") for m in sorted(unmapped)]
    f.write("\n## Local modules detected\n"); [f.write(f"- {m}\n") for m in sorted(local)]
    f.write("\n## Stdlib imports ignored\n"); [f.write(f"- {m}\n") for m in sorted(std_ignored)]
    f.write("\n## External executables mentioned\n"); [f.write(f"- {x}\n") for x in scan_execs()]
print("Wrote requirements.in, deps_report.json and deps_report.md")