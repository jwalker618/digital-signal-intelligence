import os
from pathlib import Path

# ---------------------------------------------------------
# CONFIGURATION
# Set BASE_PATH to:
#   "."              → walk the entire repo
#   "frontend"       → walk only frontend/
#   "frontend/src"   → walk only that subtree
# ---------------------------------------------------------
BASE_PATH = "infrastructure/models"   # <--- change this as needed
# ---------------------------------------------------------

def resolve_base_path():
    """Resolve BASE_PATH relative to the repo root."""
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent  # development/ → repo root

    if BASE_PATH == ".":
        return repo_root

    return (repo_root / BASE_PATH).resolve()


def sanitize_filename(path: str) -> str:
    return path.replace("/", "_").replace("\\", "_")


def bundle_code():
    # Directories to ignore
    ignore_dirs = {'.git', '__pycache__', 'venv', 'env', 'node_modules', '.pytest_cache', 'results'}
    # File extensions to include
    valid_exts = {'.py', '.yaml', '.yml', '.md', '.json'}

    base_path = resolve_base_path()

    if not base_path.is_dir():
        raise ValueError(f"❌ BASE_PATH does not exist or is not a directory: {base_path}")

    # Output file lives in development/
    script_dir = Path(__file__).resolve().parent
    output_filename = f"{sanitize_filename(BASE_PATH)}_full_codebase.txt"
    output_path = script_dir / output_filename

    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# FULL PROJECT CODEBASE (root: {base_path})\n\n")

        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for file in files:
                if not any(file.endswith(ext) for ext in valid_exts):
                    continue

                filepath = Path(root) / file

                # Skip this script and the output file
                if filepath == Path(__file__).resolve():
                    continue
                if filepath == output_path:
                    continue

                outfile.write(f"\n{'='*80}\n")
                outfile.write(f"FILE: {filepath.relative_to(base_path)}\n")
                outfile.write(f"{'='*80}\n\n")

                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                except Exception as e:
                    outfile.write(f"[Error reading file: {e}]\n")

    print(f"✅ Bundled into: {output_path.name}")
    print("Upload this file when ready.")


if __name__ == "__main__":
    bundle_code()
