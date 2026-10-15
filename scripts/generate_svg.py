import os
import uuid
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

COUNT = 10
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

repo = os.environ["GITHUB_REPOSITORY"]
branch = os.environ.get("GITHUB_REF_NAME", "main")
output_dir.mkdir(parents=True, exist_ok=True)

created = []
for number in range(1, COUNT + 1):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:16]
    filename = f"{stamp}_{unique_id}.svg"
    output_path = output_dir / filename
    output_path.write_text(content + "\n", encoding="utf-8")

    relative_path = f"generated/{filename}"
    github_url = f"https://github.com/{repo}/blob/{branch}/{relative_path}"
    cdn_url = f"https://cdn.jsdelivr.net/gh/{repo}@{branch}/{relative_path}"
    created.append((number, filename, github_url, cdn_url))

# Commit all ten files in one commit, then publish them.
subprocess.run(["git", "add", "generated/"], check=True)
subprocess.run(
    [
        "git", "-c", "user.name=github-actions[bot]",
        "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit", "-m", f"Generate {COUNT} SVG files"
    ],
    check=True
)
subprocess.run(["git", "push"], check=True)

print(f"\nSUCCESS: GENERATED {COUNT} SVG FILES")
print("\nGITHUB LINKS")
for number, filename, github_url, cdn_url in created:
    print(f"{number}. {github_url}")

print("\nJ SDELIVR LINKS")
for number, filename, github_url, cdn_url in created:
    print(f"{number}. {cdn_url}")

print(f"\nSHA-256 of source SVG: {hashlib.sha256(content.encode()).hexdigest()}")
