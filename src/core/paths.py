from pathlib import Path

def find_repo_root():
    p = Path.cwd()
    for parent in [p, *p.parents]:
        if (parent / "config" / "app.yaml").exists():
            return parent
    raise RuntimeError("Repo root not found")

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
