"""Code file parser — extracts structure via AST (Python) or regex (JS/TS)."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


def _ast_parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST | None]:
    parents: dict[ast.AST, ast.AST | None] = {tree: None}

    def visit(node: ast.AST, parent: ast.AST | None) -> None:
        for child in ast.iter_child_nodes(node):
            parents[child] = node
            visit(child, node)

    visit(tree, None)
    return parents


def parse_python(path: Path) -> dict[str, Any]:
    """Parse a Python file using AST to extract classes, functions, and docstrings."""
    source = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source, filename=str(path))
    parents = _ast_parent_map(tree)

    classes = []
    functions = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [
                n.name
                for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            docstring = ast.get_docstring(node) or ""
            classes.append(
                {
                    "name": node.name,
                    "methods": methods,
                    "docstring": docstring[:200],
                    "line": node.lineno,
                }
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if isinstance(parents.get(node), ast.ClassDef):
                continue
            docstring = ast.get_docstring(node) or ""
            args = [a.arg for a in node.args.args if a.arg != "self"]
            decorators = [
                ast.dump(d) if not isinstance(d, ast.Name) else d.id
                for d in node.decorator_list
            ]
            functions.append(
                {
                    "name": node.name,
                    "args": args,
                    "docstring": docstring[:200],
                    "line": node.lineno,
                    "decorators": decorators,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                }
            )
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

    # Build text summary for LLM consumption
    text_parts = [f"# Python module: {path.name}"]
    if classes:
        text_parts.append(f"\n## Classes ({len(classes)})")
        for c in classes:
            text_parts.append(f"- class {c['name']}: {c['docstring'][:100]}")
            for m in c["methods"]:
                text_parts.append(f"  - method {m}()")
    if functions:
        text_parts.append(f"\n## Functions ({len(functions)})")
        for f in functions:
            prefix = "async " if f.get("is_async") else ""
            text_parts.append(
                f"- {prefix}def {f['name']}({', '.join(f['args'])}): {f['docstring'][:100]}"
            )

    return {
        "type": "python",
        "source": str(path),
        "classes": classes,
        "functions": functions,
        "imports": imports,
        "text": "\n".join(text_parts),
    }


def parse_javascript(path: Path) -> dict[str, Any]:
    """Parse JS/TS files using regex to extract classes, functions, exports."""
    source = path.read_text(encoding="utf-8", errors="replace")

    # Extract classes
    classes = []
    for m in re.finditer(
        r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?", source
    ):
        classes.append(
            {
                "name": m.group(1),
                "extends": m.group(2) or "",
                "line": source[: m.start()].count("\n") + 1,
            }
        )

    # Extract functions (named, arrow, exported)
    functions = []
    func_patterns = [
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
        r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
        r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?function",
    ]
    for pattern in func_patterns:
        for m in re.finditer(pattern, source):
            name = m.group(1)
            if name not in [f["name"] for f in functions]:
                functions.append(
                    {"name": name, "line": source[: m.start()].count("\n") + 1}
                )

    # Extract imports
    imports = []
    for m in re.finditer(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", source):
        imports.append(m.group(1))

    # Build text
    suffix = path.suffix.lower()
    lang = "TypeScript" if suffix in (".ts", ".tsx") else "JavaScript"
    text_parts = [f"# {lang} module: {path.name}"]
    if classes:
        text_parts.append(f"\n## Classes ({len(classes)})")
        for c in classes:
            ext = f" extends {c['extends']}" if c["extends"] else ""
            text_parts.append(f"- class {c['name']}{ext}")
    if functions:
        text_parts.append(f"\n## Functions ({len(functions)})")
        for f in functions:
            text_parts.append(f"- {f['name']}()")

    return {
        "type": lang.lower(),
        "source": str(path),
        "classes": classes,
        "functions": functions,
        "imports": imports,
        "text": "\n".join(text_parts),
    }
