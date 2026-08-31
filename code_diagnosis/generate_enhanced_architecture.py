import ast
import sys
from pathlib import Path

# Common standard library modules to separate stdlib from third-party/internal imports
STDLIB_MODULES = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else {
    "os", "sys", "math", "time", "datetime", "pathlib", "json", "csv", 
    "re", "logging", "typing", "collections", "itertools", "functools", "ast"
}

def analyze_python_file(file_path: Path):
    """Parses a Python file to extract imports, class/method hierarchies, and functions."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as e:
        return {"error": str(e)}

    imports = {"stdlib": set(), "third_party": set(), "internal": set()}
    classes = []
    standalone_functions = []

    for node in tree.body:
        # 1. Capture Direct Imports (import numpy as np)
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                if root_pkg in STDLIB_MODULES:
                    imports["stdlib"].add(root_pkg)
                else:
                    imports["third_party"].add(root_pkg)

        # 2. Capture From Imports (from pygimli import meshtools)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:  # Relative import (e.g. from .utils import ...)
                imports["internal"].add("." * node.level + (node.module or ""))
            elif node.module:
                root_pkg = node.module.split(".")[0]
                if root_pkg in STDLIB_MODULES:
                    imports["stdlib"].add(root_pkg)
                else:
                    imports["third_party"].add(root_pkg)

        # 3. Capture Classes & Methods
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in item.args.args]
                    methods.append(f"def {item.name}({', '.join(args)})")
            
            doc = ast.get_docstring(node)
            doc_first_line = doc.splitlines()[0] if doc else ""
            classes.append({
                "name": node.name,
                "doc": doc_first_line,
                "methods": methods
            })

        # 4. Capture Standalone Functions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            doc = ast.get_docstring(node)
            doc_first_line = doc.splitlines()[0] if doc else ""
            standalone_functions.append({
                "name": node.name,
                "args": args,
                "doc": doc_first_line
            })

    return {
        "imports": imports,
        "classes": classes,
        "functions": standalone_functions
    }

def generate_deep_architecture_report(root_dir: Path, output_file: str = "PROJECT_DEEP_ARCHITECTURE.md", ignore_dirs=None):
    if ignore_dirs is None:
        ignore_dirs = {".git", "__pycache__", ".venv", "venv", ".idea", ".vscode", "build", "dist"}

    lines = [
        f"# Project Deep Architecture: {root_dir.resolve().name}\n\n",
        "## Summary of Modules & Structures\n\n"
    ]

    py_files = sorted([p for p in root_dir.rglob("*.py") if not any(part in ignore_dirs for part in p.parts)])

    for py_file in py_files:
        rel_path = py_file.relative_to(root_dir)
        analysis = analyze_python_file(py_file)
        
        lines.append(f"### `{rel_path}`\n\n")
        
        if "error" in analysis:
            lines.append(f"- **Error:** Parsing failed ({analysis['error']})\n\n")
            continue

        # Document Imports
        imp = analysis["imports"]
        if imp["third_party"] or imp["internal"]:
            lines.append("**Dependencies:**\n")
            if imp["third_party"]:
                lines.append(f"- *Third-party:* `{', '.join(sorted(imp['third_party']))}`\n")
            if imp["internal"]:
                lines.append(f"- *Internal:* `{', '.join(sorted(imp['internal']))}`\n")
            lines.append("\n")

        # Document Classes
        if analysis["classes"]:
            lines.append("**Classes:**\n")
            for cls in analysis["classes"]:
                doc_str = f" — *{cls['doc']}*" if cls['doc'] else ""
                lines.append(f"- `class {cls['name']}` ({len(cls['methods'])} methods){doc_str}\n")
                for m in cls["methods"]:
                    lines.append(f"  - `{m}`\n")
            lines.append("\n")

        # Document Standalone Functions
        if analysis["functions"]:
            lines.append("**Functions:**\n")
            for fn in analysis["functions"]:
                doc_str = f" — *{fn['doc']}*" if fn['doc'] else ""
                lines.append(f"- `def {fn['name']}({', '.join(fn['args'])})`{doc_str}\n")
            lines.append("\n")

        lines.append("---\n\n")

    Path(output_file).write_text("".join(lines), encoding="utf-8")
    print(f"Deep report generated: {output_file}")

if __name__ == "__main__":
    generate_deep_architecture_report(Path("."))