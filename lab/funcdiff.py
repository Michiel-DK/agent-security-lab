"""Function-level ground truth from a fix commit.

Given a repo, the fix SHA, its parent SHA and one file path, fetch both
versions and report every function that exists PRE-patch and whose source
changed in the fix. Functions the fix ADDED are listed separately and never
become ground truth (a model cannot name a function that is not in the file).

Languages: Python (stdlib ast), C and PHP (tree-sitter). This is the seed step
behind `target_functions` in each dataset; it is checked in so the truth set is
reproducible from metadata alone.

    python -m lab.funcdiff owner/name FIX_SHA PARENT_SHA path/to/file.c

Caveat carried from Creed (arXiv 2610.15729): about one in six functions a fix
commit touches is co-modified or a caller, not the root cause. Treat the
output as candidates and hand-check before a function becomes truth.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, asdict

from .fetch import fetch_file

_WS = re.compile(r"\s+")
_MACRO_FN = re.compile(r"^(PHP|ZEND)_(FUNCTION|METHOD|NAMED_FUNCTION|FUNCTION_LAST)$")


@dataclass
class Fn:
    name: str
    start_line: int
    end_line: int
    body: str  # whitespace-normalised full definition text


def _norm_text(s: str) -> str:
    return _WS.sub(" ", s).strip()


# ---------------------------------------------------------------- Python
def _py_functions(src: str) -> dict[str, Fn]:
    out: dict[str, Fn] = {}
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    lines = src.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            text = "\n".join(lines[node.lineno - 1 : node.end_lineno])
            out.setdefault(node.name, Fn(node.name, node.lineno, node.end_lineno, _norm_text(text)))
    return out


# ---------------------------------------------------------------- tree-sitter
def _ts_parser(language: str):
    from tree_sitter import Language, Parser

    if language == "c":
        import tree_sitter_c as tsl

        return Parser(Language(tsl.language()))
    if language == "php":
        import tree_sitter_php as tsl

        return Parser(Language(tsl.language_php()))
    raise ValueError(f"no tree-sitter grammar wired for {language!r}")


def _c_name(decl_node, src: bytes) -> str | None:
    """Walk a C declarator to its identifier. Handles pointer/function
    declarators and the PHP_FUNCTION(name)-style macro definitions, which
    tree-sitter parses as a function_declarator whose 'declarator' is the
    macro identifier and whose parameter list holds the real name."""
    node = decl_node
    while node is not None:
        if node.type == "identifier":
            return src[node.start_byte : node.end_byte].decode("utf-8", "replace")
        if node.type == "function_declarator":
            inner = node.child_by_field_name("declarator")
            inner_name = _c_name(inner, src) if inner is not None else None
            if inner_name and _MACRO_FN.match(inner_name):
                params = node.child_by_field_name("parameters")
                args = []
                if params is not None:
                    for ch in params.named_children:
                        args.append(src[ch.start_byte : ch.end_byte].decode("utf-8", "replace").strip())
                # PHP_FUNCTION(foo) -> foo ; PHP_METHOD(Cls, m) -> Cls::m
                return "::".join(a for a in args if a) or inner_name
            return inner_name
        node = node.child_by_field_name("declarator")
    return None


def _ts_functions(src: str, language: str) -> dict[str, Fn]:
    parser = _ts_parser(language)
    data = src.encode("utf-8", "replace")
    tree = parser.parse(data)
    out: dict[str, Fn] = {}

    def visit(node):
        if language == "c" and node.type == "function_definition":
            decl = node.child_by_field_name("declarator")
            name = _c_name(decl, data) if decl is not None else None
            if name:
                text = data[node.start_byte : node.end_byte].decode("utf-8", "replace")
                out.setdefault(name, Fn(name, node.start_point[0] + 1, node.end_point[0] + 1, _norm_text(text)))
        elif language == "php" and node.type in ("function_definition", "method_declaration"):
            nm = node.child_by_field_name("name")
            if nm is not None:
                name = data[nm.start_byte : nm.end_byte].decode("utf-8", "replace")
                text = data[node.start_byte : node.end_byte].decode("utf-8", "replace")
                out.setdefault(name, Fn(name, node.start_point[0] + 1, node.end_point[0] + 1, _norm_text(text)))
        for ch in node.children:
            visit(ch)

    visit(tree.root_node)
    return out


def functions(src: str, language: str) -> dict[str, Fn]:
    if language == "python":
        return _py_functions(src)
    return _ts_functions(src, language)


def guess_language(path: str) -> str:
    p = path.lower()
    if p.endswith(".py"):
        return "python"
    if p.endswith((".c", ".h", ".re", ".y", ".cc")):
        return "c"
    if p.endswith((".php", ".phtml", ".inc")):
        return "php"
    raise ValueError(f"cannot guess language for {path}")


def diff_functions(repo: str, fix_sha: str, parent_sha: str, path: str, language: str | None = None) -> dict:
    language = language or guess_language(path)
    pre_src = fetch_file(repo, parent_sha, path)
    post_src = fetch_file(repo, fix_sha, path)
    pre = functions(pre_src, language)
    post = functions(post_src, language)
    changed = sorted(n for n in pre if n in post and pre[n].body != post[n].body)
    removed = sorted(n for n in pre if n not in post)
    added = sorted(n for n in post if n not in pre)
    return {
        "repo": repo,
        "file": path,
        "language": language,
        "fix_sha": fix_sha,
        "parent_sha": parent_sha,
        "pre_chars": len(pre_src),
        "pre_lines": pre_src.count("\n") + 1,
        "pre_functions": len(pre),
        "changed_existing": changed,  # candidate ground truth
        "changed_sizes": {n: [pre[n].start_line, pre[n].end_line] for n in changed},
        "removed": removed,
        "added": added,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 2
    repo, fix_sha, parent_sha = argv[:3]
    for path in argv[3:]:
        print(json.dumps(diff_functions(repo, fix_sha, parent_sha, path), indent=None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
