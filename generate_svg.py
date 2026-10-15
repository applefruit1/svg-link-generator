import os
import uuid
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

source = Path("source.svg")
output_dir = Path("generated")

if not source.is_file():
    raise SystemExit("ERROR: source.svg was not found.")

content = source.read_text(encoding="utf-8").lstrip("\ufeff").strip()

try:
    root = ET.fromstring(content)
except ET.ParseError as exc:
    raise SystemExit(f"ERROR: Invalid SVG/XML: {exc}")

if root.tag.split("}")[-1].lower() != "svg":
    raise SystemExit("ERROR: The root element must be <svg>.")

stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
unique_id = uuid.uuid4().hex[:16]
filename = f"{stamp}_{unique_id}.svg"

output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / filename
output_path.write_text(content + "\n", encoding="utf-8")

repo = os.environ["GITHUB_REPOSITORY"]
branch = os.environ.get("GITHUB_REF_NAME", "main")
relative_path = f"generated/{filename}"

github_url = f"https://github.com/{repo}/blob/{branch}/{relative_path}"
cdn_url = f"https://cdn.jsdelivr.net/gh/{repo}@{branch}/{relative_path}"

subprocess.run(["git", "add", str(output_path)], check=True)
subprocess.run(
    [
        "git", "-c", "user.name=github-actions[bot]",
        "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit", "-m", f"Generate SVG {filename}"
    ],
    check=True
)
subprocess.run(["git", "push"], check=True)

print("\nSVG GENERATED SUCCESSFULLY")
print(f"Filename: {filename}")
print(f"GitHub: {github_url}")
print(f"jsDelivr: {cdn_url}")
print(f"SHA-256: {hashlib.sha256(content.encode()).hexdigest()}")
