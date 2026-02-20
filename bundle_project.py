import os
from pathlib import Path

def bundle_project(output_filename="dsi_full_codebase.txt"):
    # Directories to ignore
    ignore_dirs = {'.git', '__pycache__', 'venv', 'env', 'node_modules', '.pytest_cache', 'results'}
    # File extensions to include
    valid_exts = {'.py', '.yaml', '.yml', '.md', '.json'}
    
    output_path = Path(output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write("# DSI FULL PROJECT CODEBASE\n\n")
        
        for root, dirs, files in os.walk('.'):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in valid_exts):
                    filepath = Path(root) / file
                    
                    # Skip the script itself and the output file
                    if file == "bundle_project.py" or file == output_filename:
                        continue
                        
                    outfile.write(f"\n{'='*80}\n")
                    outfile.write(f"FILE: {filepath}\n")
                    outfile.write(f"{'='*80}\n\n")
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"[Error reading file: {e}]\n")
                        
    print(f"✅ Project successfully bundled into: {output_filename}")
    print("Please upload this file to the chat.")

if __name__ == "__main__":
    bundle_project()
