"""Static 'modernisation score' — measures what the sub-agents were asked to do."""

import ast


def modernisation_metrics(files: dict[str, str]) -> dict:
    funcs = typed = documented = classes = documented_classes = prints = 0
    for src in files.values():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs += 1
                args = [a for a in node.args.args + node.args.kwonlyargs if a.arg not in ("self", "cls")]
                if node.returns is not None and all(a.annotation is not None for a in args):
                    typed += 1
                documented += ast.get_docstring(node) is not None
            elif isinstance(node, ast.ClassDef):
                classes += 1
                documented_classes += ast.get_docstring(node) is not None
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                prints += 1
    return {
        "functions": funcs,
        "fully_typed": typed,
        "docstrings": documented + documented_classes,
        "docstrings_expected": funcs + classes,
        "print_calls": prints,
    }


def score_text(m: dict) -> str:
    return (f"typed {m['fully_typed']}/{m['functions']} · docstrings {m['docstrings']}/{m['docstrings_expected']} "
            f"· print() calls {m['print_calls']}")
