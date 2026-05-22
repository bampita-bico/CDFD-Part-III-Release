"""Build simple local HTML panels for generated Part III outputs."""
from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"


def summarize_json(path: Path) -> str:
    data = json.loads(path.read_text())
    if isinstance(data, dict):
        keys = ", ".join(list(data.keys())[:8])
        return f"JSON keys: {html.escape(keys)}"
    if isinstance(data, list):
        return f"JSON rows: {len(data)}"
    return "JSON output"


def panel_for(folder: Path) -> str:
    rows = []
    for path in sorted(folder.iterdir()):
        if path.name == "interactive_panel.html" or path.name.startswith("."):
            continue
        rel = path.relative_to(OUTPUTS)
        if path.suffix.lower() == ".json":
            desc = summarize_json(path)
        elif path.suffix.lower() == ".csv":
            desc = f"CSV file: {path.name}"
        elif path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            desc = f'<img src="{html.escape(path.name)}" alt="{html.escape(path.stem)}" />'
        else:
            desc = path.name
        rows.append(
            f"<tr><td><a href='{html.escape(path.name)}'>{html.escape(path.name)}</a></td>"
            f"<td>{desc}</td></tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='2'>No generated files.</td></tr>"
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(folder.name)} - CDFD Part III outputs</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d9dde3; padding: .6rem; text-align: left; vertical-align: top; }}
    img {{ max-width: 760px; width: 100%; border: 1px solid #d9dde3; }}
    .note {{ color: #5f6368; max-width: 70rem; }}
  </style>
</head>
<body>
  <h1>{html.escape(folder.name)}</h1>
  <p class="note">Part III outputs are toy diagnostics for the CDFD/AFL manuscript archive. They are not clinical validation.</p>
  <table><thead><tr><th>File</th><th>Preview</th></tr></thead><tbody>{body}</tbody></table>
</body>
</html>
"""
    out = folder / "interactive_panel.html"
    out.write_text(page)
    return str(out.relative_to(OUTPUTS))


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    panels = []
    for folder in sorted(p for p in OUTPUTS.iterdir() if p.is_dir()):
        panels.append((folder.name, panel_for(folder)))
    links = "\n".join(
        f"<li><a href='{html.escape(path)}'>{html.escape(name)}</a></li>" for name, path in panels
    )
    index = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>CDFD Part III Interactive Output Index</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; color: #202124; }}
    li {{ margin: .35rem 0; }}
    .note {{ color: #5f6368; max-width: 70rem; }}
  </style>
</head>
<body>
  <h1>CDFD Part III Interactive Output Index</h1>
  <p class="note">Release-local diagnostic outputs for Adaptive Flux Limitation biology and medicine. These panels summarize generated files only.</p>
  <ul>{links}</ul>
</body>
</html>
"""
    (OUTPUTS / "interactive_index.html").write_text(index)


if __name__ == "__main__":
    main()
