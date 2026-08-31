from pathlib import Path

def save_tree_to_file(root_dir: Path, output_file: str, ignore_dirs=None):
    if ignore_dirs is None:
        ignore_dirs = {".git", "__pycache__", ".venv", "venv", ".ipynb_checkpoints"}

    lines = [f"# Project Tree: {root_dir.resolve().name}\n\n```text\n"]

    def build_tree(path: Path, prefix: str = ""):
        items = [p for p in path.iterdir() if p.name not in ignore_dirs]
        items.sort(key=lambda s: (s.is_file(), s.name.lower()))
        
        pointers = [("├── ", "│   ")] * (len(items) - 1) + [("└── ", "    ")]
        for (connector, extension), item in zip(pointers, items):
            lines.append(f"{prefix}{connector}{item.name}\n")
            if item.is_dir():
                build_tree(item, prefix + extension)

    build_tree(root_dir)
    lines.append("```\n")

    Path(output_file).write_text("".join(lines), encoding="utf-8")
    print(f"Tree saved successfully to {output_file}")

save_tree_to_file(Path("."), "PROJECT_STRUCTURE.md")