import ast
from pathlib import Path

def extract_signatures(file_path: Path) -> list:
    """Extracts top-level and class-level definitions from a Python file using AST."""
    signatures = []
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as e:
        return [f"    └── [Error parsing file: {e}]"]

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            signatures.append(f"    └── class {node.name}:")
            # Extract docstring if present
            doc = ast.get_docstring(node)
            if doc:
                signatures.append(f'        """{doc.splitlines()[0]}"""')
            # Extract methods
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in item.args.args]
                    signatures.append(f"        └── def {item.name}({', '.join(args)})")

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            doc = ast.get_docstring(node)
            signatures.append(f"    └── def {node.name}({', '.join(args)})")
            if doc:
                signatures.append(f'        """{doc.splitlines()[0]}"""')

    return signatures

def generate_full_architecture(root_dir: Path, output_file: str = "PROJECT_ARCHITECTURE.md", ignore_dirs=None):
    if ignore_dirs is None:
        ignore_dirs = {".git", "__pycache__", ".venv", "venv", ".idea", ".vscode", "build", "dist"}

    lines = [
        f"# Project Architecture: {root_dir.resolve().name}\n\n",
        "## Directory Tree & Signatures\n\n",
        "```text\n"
    ]

    def walk_directory(path: Path, prefix: str = ""):
        items = [p for p in path.iterdir() if p.name not in ignore_dirs]
        items.sort(key=lambda s: (s.is_file(), s.name.lower()))
        
        pointers = [("├── ", "│   ")] * (len(items) - 1) + [("└── ", "    ")]
        
        for (connector, extension), item in zip(pointers, items):
            lines.append(f"{prefix}{connector}{item.name}\n")
            
            if item.is_file() and item.suffix == ".py":
                signatures = extract_signatures(item)
                for sig in signatures:
                    lines.append(f"{prefix}{extension}{sig}\n")
                    
            elif item.is_dir():
                walk_directory(item, prefix + extension)

    walk_directory(root_dir)
    lines.append("```\n")

    Path(output_file).write_text("".join(lines), encoding="utf-8")
    print(f"Architecture overview generated: {output_file}")

if __name__ == "__main__":
    generate_full_architecture(Path("."))