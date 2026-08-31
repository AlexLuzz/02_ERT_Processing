import ast
import subprocess
import sys
from pathlib import Path

STDLIB_MODULES = (
    set(sys.stdlib_module_names)
    if hasattr(sys, "stdlib_module_names")
    else {
        "os", "sys", "math", "time", "datetime", "pathlib", "json",
        "csv", "re", "logging", "typing", "collections", "itertools",
        "functools", "ast", "subprocess"
    }
)

def analyze_python_file(file_path: Path):
    """Extracts imports, classes, and functions using AST."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as e:
        return {"error": str(e)}

    imports = {"stdlib": set(), "third_party": set(), "internal": set()}
    classes = []
    functions = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                if root_pkg in STDLIB_MODULES:
                    imports["stdlib"].add(root_pkg)
                else:
                    imports["third_party"].add(root_pkg)

        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                imports["internal"].add("." * node.level + (node.module or ""))
            elif node.module:
                root_pkg = node.module.split(".")[0]
                if root_pkg in STDLIB_MODULES:
                    imports["stdlib"].add(root_pkg)
                else:
                    imports["third_party"].add(root_pkg)

        elif isinstance(node, ast.ClassDef):
            methods = [
                f"def {item.name}({', '.join(a.arg for a in item.args.args)})"
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            doc = ast.get_docstring(node)
            classes.append({
                "name": node.name,
                "doc": doc.splitlines()[0] if doc else "",
                "methods": methods
            })

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            doc = ast.get_docstring(node)
            functions.append({
                "name": node.name,
                "args": args,
                "doc": doc.splitlines()[0] if doc else ""
            })

    return {"imports": imports, "classes": classes, "functions": functions}

def run_external_tool(module_name: str, args: list) -> str:
    """Runs a Python module tool using the current Python environment."""
    cmd = [sys.executable, "-m", module_name] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        output = (result.stdout or "").strip() or (result.stderr or "").strip()
        return output if output else "No issues flagged."
    except Exception as e:
        return f"Error executing `{module_name}`: {e}"

def build_full_audit(target_dir: Path, output_file: Path, ignore_dirs=None):
    if ignore_dirs is None:
        ignore_dirs = {".git", "__pycache__", ".venv", "venv", ".idea", ".vscode", "build", "dist"}

    lines = [
        f"# Complete Architecture & Quality Audit: `{target_dir.resolve().name}`\n\n",
        f"**Target Directory:** `{target_dir.resolve()}`\n\n",
        "## 1. Directory Tree & Module Signatures\n\n"
    ]

    py_files = sorted([
        p for p in target_dir.rglob("*.py")
        if not any(part in ignore_dirs for part in p.parts)
    ])

    for py_file in py_files:
        rel_path = py_file.relative_to(target_dir)
        analysis = analyze_python_file(py_file)

        lines.append(f"### `{rel_path}`\n\n")

        if "error" in analysis:
            lines.append(f"- **Error parsing:** `{analysis['error']}`\n\n")
            continue

        imp = analysis["imports"]
        if imp["third_party"] or imp["internal"]:
            lines.append("**Dependencies:**\n")
            if imp["third_party"]:
                lines.append(f"- *Third-party:* `{', '.join(sorted(imp['third_party']))}`\n")
            if imp["internal"]:
                lines.append(f"- *Internal:* `{', '.join(sorted(imp['internal']))}`\n")
            lines.append("\n")

        if analysis["classes"]:
            lines.append("**Classes:**\n")
            for cls in analysis["classes"]:
                doc_str = f" — *{cls['doc']}*" if cls['doc'] else ""
                lines.append(f"- `class {cls['name']}` ({len(cls['methods'])} methods){doc_str}\n")
                for m in cls["methods"]:
                    lines.append(f"  - `{m}`\n")
            lines.append("\n")

        if analysis["functions"]:
            lines.append("**Functions:**\n")
            for fn in analysis["functions"]:
                doc_str = f" — *{fn['doc']}*" if fn['doc'] else ""
                lines.append(f"- `def {fn['name']}({', '.join(fn['args'])})`{doc_str}\n")
            lines.append("\n")

        lines.append("---\n\n")

    # Section 2: Radon
    lines.append("## 2. Cyclomatic Complexity Analysis (Radon)\n\n")
    lines.append("> Scores: **A** (1-5, simple) to **F** (>41, extremely complex/bug-prone).\n\n")
    radon_out = run_external_tool("radon", ["cc", str(target_dir), "-a", "-s"])
    lines.append(f"```text\n{radon_out}\n```\n\n---\n\n")

    # Section 3: Vulture
    lines.append("## 3. Potential Dead Code & Unused Items (Vulture)\n\n")
    vulture_out = run_external_tool("vulture", [str(target_dir)])
    lines.append(f"```text\n{vulture_out}\n```\n")

    output_file.write_text("".join(lines), encoding="utf-8")
    print(f"Audit successfully generated at: {output_file.resolve()}")

if __name__ == "__main__":
    # Target path can be passed via command line, defaults to current directory
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    out_path = target / "ARCHITECTURE_AUDIT.md"
    build_full_audit(target, out_path)