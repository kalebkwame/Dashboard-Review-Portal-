from pathlib import Path

SECRET_MARKERS = (
    "admin12345",
    "admin@local.dev",
    "first-admin-demo-key",
    "dev-only-change-me",
)

root = Path(__file__).resolve().parents[1]
found = []

for path in root.rglob("*"):
    if not path.is_file() or path.name == "sanitize_for_public.py" or any(part in {".venv", ".git", "backups", "__pycache__"} for part in path.parts):
        continue
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        continue
    for marker in SECRET_MARKERS:
        if marker in text:
            found.append((str(path.relative_to(root)), marker))

if found:
    print("Potential public-secret/demo markers found:")
    for path, marker in found:
        print(f"- {path}: {marker}")
    raise SystemExit(1)

print("No known demo credentials or secret markers found.")
