# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import os
from pathlib import Path

# Carpetas y archivos a ignorar
IGNORAR = {
    "venv", ".git", "__pycache__", ".pytest_cache", ".vscode", 
    "node_modules", ".mypy_cache", ".coverage"
}

def imprimir_arbol(dir_path: Path, prefix: str = ""):
    items = sorted([p for p in dir_path.iterdir() if p.name not in IGNORAR])
    entries_count = len(items)
    
    for index, path in enumerate(items):
        is_last = (index == entries_count - 1)
        connector = "└── " if is_last else "├── "
        
        if path.is_dir():
            print(f"{prefix}{connector}📁 {path.name}/")
            extension = "    " if is_last else "│   "
            imprimir_arbol(path, prefix + extension)
        else:
            print(f"{prefix}{connector}📄 {path.name}")

if __name__ == "__main__":
    raiz = Path.cwd()
    print(f"=== ESTRUCTURA DEL REPOSITORIO ({raiz.name}) ===\n")
    imprimir_arbol(raiz)