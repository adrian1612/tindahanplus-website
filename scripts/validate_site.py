#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [ROOT / "index.html", ROOT / "privacy" / "index.html"]

class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.images = []
        self.ids = set()
        self.headings = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "img":
            self.images.append(attrs)
        if tag in {"h1","h2","h3","h4","h5","h6"}:
            self.headings.append(tag)

errors = []

for html_file in HTML_FILES:
    parser = SiteParser()
    parser.feed(html_file.read_text(encoding="utf-8"))
    for href in parser.links:
        parsed = urlparse(href)
        if parsed.scheme or href.startswith("//") or href.startswith("mailto:"):
            continue
        target = href.split("#", 1)[0]
        if not target:
            continue
        target_path = (html_file.parent / target).resolve()
        if not target_path.exists():
            errors.append(f"{html_file.relative_to(ROOT)}: missing link target {href}")
    for img in parser.images:
        src = img.get("src", "")
        if not src or urlparse(src).scheme:
            continue
        image_path = (html_file.parent / src).resolve()
        if not image_path.exists():
            errors.append(f"{html_file.relative_to(ROOT)}: missing image {src}")
        if not img.get("alt") is not None:
            errors.append(f"{html_file.relative_to(ROOT)}: image missing alt attribute: {src}")
    if parser.headings.count("h1") != 1:
        errors.append(f"{html_file.relative_to(ROOT)}: expected exactly one h1")

sitemap = ROOT / "sitemap.xml"
robots = ROOT / "robots.txt"
try:
    ET.parse(sitemap)
except Exception as exc:
    errors.append(f"sitemap.xml: invalid XML: {exc}")

robots_text = robots.read_text(encoding="utf-8")
if not re.search(r"^User-agent:\s*\*$", robots_text, re.M):
    errors.append("robots.txt: missing User-agent: *")
if not re.search(r"^Sitemap:\s*\S+$", robots_text, re.M):
    errors.append("robots.txt: missing Sitemap declaration")

if errors:
    print("\n".join(f"ERROR: {e}" for e in errors))
    sys.exit(1)

print("Static website validation passed.")
