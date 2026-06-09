"""Structural tests that enforce layering rules and code quality invariants."""

import ast
from pathlib import Path

APP_ROOT = Path(__file__).parent.parent / "app"

# Layer ordering: lower layers must not import from higher layers
LAYER_ORDER = ["types", "config", "repo", "service", "runtime"]

# Heavy ML / external-inference SDKs. The starter contains boto3 to repo/; this
# app extends that invariant to its ML stack so the core train->generate loop
# can never leak its dependencies into the lighter layers (and so `pnpm dev`
# and import-time stay cheap). These must be imported ONLY inside app/repo/ and
# ONLY lazily (inside function/method bodies), never at module top level.
ML_SDK_PREFIXES = (
    "torch",
    "diffusers",
    "transformers",
    "peft",
    "accelerate",
    "replicate",
    "anthropic",
)

# Map of layer -> set of layers it must NOT import from
FORBIDDEN_IMPORTS: dict[str, set[str]] = {}
for i, layer in enumerate(LAYER_ORDER):
    # Each layer cannot import from layers above it
    FORBIDDEN_IMPORTS[layer] = set(LAYER_ORDER[i + 1 :])


def _get_python_files(directory: Path) -> list[Path]:
    """Get all .py files in a directory recursively."""
    return list(directory.rglob("*.py"))


def _get_imports(filepath: Path) -> list[str]:
    """Extract all import module names from a Python file."""
    try:
        tree = ast.parse(filepath.read_text())
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _module_level_imports(filepath: Path) -> list[str]:
    """Extract import names reachable at module import time.

    "Module level" = a direct statement in the module body, or one nested only
    inside top-level ``if`` / ``try`` / ``with`` blocks (which still execute on
    import). Imports inside a function or method body are excluded — those are
    the "lazy" imports we want to allow.
    """
    try:
        tree = ast.parse(filepath.read_text())
    except SyntaxError:
        return []

    imports: list[str] = []

    def walk(body: list[ast.stmt]) -> None:
        for node in body:
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, (ast.If, ast.Try, ast.With)):
                # These execute at import time, so imports inside them still
                # count as module level. Recurse into all their statement lists.
                for attr in ("body", "orelse", "finalbody", "handlers"):
                    block = getattr(node, attr, None)
                    if not block:
                        continue
                    if attr == "handlers":
                        for handler in block:
                            walk(handler.body)
                    else:
                        walk(block)
            # FunctionDef / AsyncFunctionDef / ClassDef bodies are NOT walked:
            # imports there run lazily, not at module import.

    walk(tree.body)
    return imports


def _matches_ml_sdk(module: str) -> bool:
    """True if an import module name belongs to a tracked ML/external SDK."""
    return any(
        module == prefix or module.startswith(prefix + ".")
        for prefix in ML_SDK_PREFIXES
    )


def _layer_of_import(module: str) -> str | None:
    """Return the layer name if the import is from app.<layer>, else None."""
    if not module.startswith("app."):
        return None
    parts = module.split(".")
    if len(parts) >= 2:
        return parts[1]
    return None


def test_no_backward_imports():
    """Verify no layer imports from a higher layer."""
    violations = []
    for layer in LAYER_ORDER:
        layer_dir = APP_ROOT / layer
        if not layer_dir.exists():
            continue
        for pyfile in _get_python_files(layer_dir):
            for imp in _get_imports(pyfile):
                imported_layer = _layer_of_import(imp)
                if imported_layer and imported_layer in FORBIDDEN_IMPORTS[layer]:
                    rel = pyfile.relative_to(APP_ROOT.parent)
                    violations.append(
                        f"{rel}: {layer}/ imports from {imported_layer}/ ({imp})"
                    )
    assert violations == [], "Backward import violations:\n" + "\n".join(violations)


def test_boto3_only_in_repo():
    """Verify boto3 is only imported in app/repo/."""
    violations = []
    for layer in LAYER_ORDER:
        if layer == "repo":
            continue
        layer_dir = APP_ROOT / layer
        if not layer_dir.exists():
            continue
        for pyfile in _get_python_files(layer_dir):
            for imp in _get_imports(pyfile):
                if imp == "boto3" or imp.startswith("boto3.") or imp == "botocore" or imp.startswith("botocore."):
                    rel = pyfile.relative_to(APP_ROOT.parent)
                    violations.append(f"{rel}: boto3/botocore imported outside repo/")
    assert violations == [], "boto3 boundary violations:\n" + "\n".join(violations)


def test_ml_sdks_only_in_repo():
    """Verify the heavy ML stack is imported only within app/repo/.

    Mirrors test_boto3_only_in_repo. torch/diffusers/transformers/peft/
    accelerate/replicate/anthropic must never leak into types/config/service/
    runtime — only the repo/ adapters that own the train->generate core may
    touch them.
    """
    violations = []
    for layer in LAYER_ORDER:
        if layer == "repo":
            continue
        layer_dir = APP_ROOT / layer
        if not layer_dir.exists():
            continue
        for pyfile in _get_python_files(layer_dir):
            for imp in _get_imports(pyfile):
                if _matches_ml_sdk(imp):
                    rel = pyfile.relative_to(APP_ROOT.parent)
                    violations.append(
                        f"{rel}: ML SDK '{imp}' imported outside repo/"
                    )
    assert violations == [], "ML SDK boundary violations:\n" + "\n".join(violations)


def test_ml_sdks_lazy_in_repo():
    """Verify the ML stack is imported lazily, never at module top level.

    Even inside repo/, the heavy SDKs must be imported inside the adapter
    method bodies (e.g. LocalTrainer.train) so importing the module — which
    happens at app startup and during test collection — stays cheap and does
    not require torch/diffusers to be installed.
    """
    repo_dir = APP_ROOT / "repo"
    violations = []
    if repo_dir.exists():
        for pyfile in _get_python_files(repo_dir):
            for imp in _module_level_imports(pyfile):
                if _matches_ml_sdk(imp):
                    rel = pyfile.relative_to(APP_ROOT.parent)
                    violations.append(
                        f"{rel}: ML SDK '{imp}' imported at module level "
                        "(must be lazy, inside a function/method body)"
                    )
    assert violations == [], "ML SDK eager-import violations:\n" + "\n".join(
        violations
    )


def test_file_size_limits():
    """Verify no Python file exceeds 300 lines."""
    violations = []
    for pyfile in _get_python_files(APP_ROOT):
        line_count = len(pyfile.read_text().splitlines())
        if line_count > 300:
            rel = pyfile.relative_to(APP_ROOT.parent)
            violations.append(f"{rel}: {line_count} lines (max 300)")
    assert violations == [], "File size violations:\n" + "\n".join(violations)


def test_all_layers_exist():
    """Verify all expected layer directories exist."""
    for layer in LAYER_ORDER:
        layer_dir = APP_ROOT / layer
        assert layer_dir.exists(), f"Missing layer directory: app/{layer}/"
        init_file = layer_dir / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py in app/{layer}/"
