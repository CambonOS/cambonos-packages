"""Build and verify the static GitHub Pages tree."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote

from .common import CambonosError, sha256_file
from .config import REPOSITORY_SECTION


INDEX_MARKER = "<!-- generated-by: cambonos-index -->"
INDEX_TITLE = "CambonOS Package Repository"


def _human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    value = float(size)
    for unit in ("KiB", "MiB", "GiB", "TiB"):
        value /= 1024
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
    return f"{value:.1f} TiB"


def generate_directory_indexes(site: Path) -> tuple[int, int]:
    """Generate Apache-style browsable indexes without replacing authored pages."""
    site = site.resolve()
    if not site.is_dir():
        raise CambonosError(f"no existe el directorio del sitio: {site}")

    generated = skipped = 0
    for directory, dirs, files in os.walk(site, topdown=True, followlinks=False):
        dirs[:] = sorted(name for name in dirs if not name.startswith("."))
        files = sorted(
            name for name in files
            if not name.startswith(".") and name != "index.html"
        )
        current = Path(directory)
        output = current / "index.html"

        # Keep the branded root landing page and any other hand-authored index.
        if output.exists() and INDEX_MARKER not in output.read_text(
            encoding="utf-8", errors="ignore"
        ):
            skipped += 1
            continue

        relative = current.relative_to(site)
        display_path = "/" if relative == Path(".") else f"/{relative.as_posix()}/"
        rows: list[str] = []
        if relative != Path("."):
            rows.append(
                '<tr class="parent"><td class="kind">Directory</td>'
                '<td><a href="../">../</a></td><td>—</td></tr>'
            )

        for name in dirs:
            href = quote(name, safe="") + "/"
            rows.append(
                f'<tr><td class="kind">Directory</td>'
                f'<td><a href="{escape(href, quote=True)}">{escape(name)}/</a></td>'
                f'<td>—</td></tr>'
            )

        for name in files:
            file_path = current / name
            href = quote(name, safe="")
            rows.append(
                f'<tr><td class="kind">File</td>'
                f'<td><a href="{escape(href, quote=True)}">{escape(name)}</a></td>'
                f'<td class="size">{_human_size(file_path.stat().st_size)}</td></tr>'
            )
        if not dirs and not files:
            rows.append('<tr><td colspan="3">This directory is empty.</td></tr>')

        page = f"""<!doctype html>
{INDEX_MARKER}
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>Index of {escape(display_path)}</title>
  <style>
    :root {{ color-scheme: dark light; font-family: system-ui, sans-serif; }}
    body {{ max-width: 960px; margin: 3rem auto; padding: 0 1.25rem; line-height: 1.6; }}
    header {{ margin-bottom: 1.5rem; }}
    h1 {{ margin-bottom: .15rem; font-size: 1.65rem; }}
    .path {{ color: GrayText; overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: .55rem .75rem; border-bottom: 1px solid color-mix(in srgb, CanvasText 15%, transparent); text-align: left; }}
    th {{ font-size: .85rem; color: GrayText; }}
    tr:hover td {{ background: color-mix(in srgb, CanvasText 6%, transparent); }}
    a {{ color: LinkText; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .kind {{ width: 7rem; color: GrayText; font-size: .85rem; }}
    .size {{ width: 7rem; text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }}
    footer {{ margin-top: 1.5rem; color: GrayText; font-size: .85rem; }}
    @media (max-width: 600px) {{ body {{ margin: 1.5rem auto; }} th, td {{ padding: .45rem .35rem; }} .kind {{ width: auto; }} }}
  </style>
</head>
<body>
  <header>
    <h1>{INDEX_TITLE}</h1>
    <div class="path">Index of {escape(display_path)}</div>
  </header>
  <table>
    <thead><tr><th>Type</th><th>Name</th><th class="size">Size</th></tr></thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  <footer>Directory listing generated automatically by CambonOS package pipeline.</footer>
</body>
</html>
"""
        output.write_text(page, encoding="utf-8")
        generated += 1

    return generated, skipped


def write_site_metadata(
    site: Path, channel_manifests: dict[str, dict], pages_url: str
) -> dict:
    if set(channel_manifests) != {"stable", "testing"}:
        raise CambonosError("el sitio debe contener exactamente stable y testing")
    if not pages_url.startswith("https://"):
        raise CambonosError("CAMBONOS_PAGES_URL debe utilizar HTTPS")
    global_manifest = {
        "schema_version": 1,
        "publication": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "architecture": "x86_64",
        },
        "channels": {},
    }
    for channel, data in channel_manifests.items():
        global_manifest["channels"][channel] = {
            "branch": data["branch"],
            "commit": data["commit"],
            "packages": data["packages"],
            "build_environment": data["build_environment"],
            "image": data["image"],
        }
    metadata = site / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    (metadata / "manifest.json").write_text(
        json.dumps(global_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_index(site, global_manifest, pages_url)
    return global_manifest


def write_index(site: Path, manifest: dict, pages_url: str) -> None:
    rows = []
    for channel, label in (("stable", "Stable"), ("testing", "Testing")):
        data = manifest["channels"][channel]
        browse = f'<a href="{channel}/">Browse {label.lower()}</a>'
        rows.append(
            f"<tr><td>{browse}</td><td><code>{data['branch']}</code></td>"
            f"<td><code>{data['commit'][:12]}</code></td>"
            f"<td>{len(data['packages'])}</td></tr>"
        )
    import html as html_module
    base_url = html_module.escape(pages_url.rstrip("/"), quote=True)
    html = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CambonOS Packages</title>
<style>
:root{color-scheme:dark light;font-family:system-ui,sans-serif}body{max-width:920px;margin:4rem auto;padding:0 1.25rem;line-height:1.6}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:.7rem;border-bottom:1px solid #8885}
code{overflow-wrap:anywhere}a{color:inherit} .muted{opacity:.75}
</style></head><body><h1>CambonOS Packages</h1>
<p>Repositorios oficiales de paquetes para CambonOS, basados en Arch Linux.</p>
<h2>Canales</h2><table><thead><tr><th>Canal</th><th>Rama</th><th>Commit</th><th>Paquetes</th></tr></thead>
<tbody>""" + "".join(rows) + """</tbody></table>
<h2>Configuración de pacman</h2>
<pre><code>#[cambonos-testing]
#SigLevel = Required
#Server = {base_url}/testing/$arch

[cambonos]
SigLevel = Required
Server = {base_url}/stable/$arch</code></pre>
<p class="muted">Testing está deshabilitado por defecto. Explora los canales desde la tabla superior.
Manifiesto: <a href="metadata/manifest.json">metadata/manifest.json</a>.</p>
</body></html>
""".replace("{base_url}", base_url)
    (site / "index.html").write_text(html, encoding="utf-8")


def verify_site(site: Path) -> None:
    required = (
        site / "index.html",
        site / "metadata" / "manifest.json",
        site / "metadata" / "manifest.json.sig",
        site / "stable" / "x86_64",
        site / "testing" / "x86_64",
        site / "stable" / "index.html",
        site / "stable" / "x86_64" / "index.html",
        site / "testing" / "index.html",
        site / "testing" / "x86_64" / "index.html",
        site / "metadata" / "index.html",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise CambonosError("sitio incompleto: " + ", ".join(missing))
    symlinks = [str(path) for path in site.rglob("*") if path.is_symlink()]
    if symlinks:
        raise CambonosError("GitHub Pages no debe recibir enlaces simbólicos: " + ", ".join(symlinks))
    try:
        manifest = json.loads((site / "metadata" / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CambonosError(f"manifiesto global inválido: {exc}") from exc
    if set(manifest.get("channels", {})) != {"stable", "testing"}:
        raise CambonosError("el manifiesto global no contiene los dos canales")
    for channel in ("stable", "testing"):
        repository = site / channel / "x86_64"
        channel_data = manifest["channels"][channel]
        expected = {
            record["package_file"]: record
            for record in channel_data.get("packages", {}).values()
        }
        actual = {
            path.name: path
            for path in repository.glob("*.pkg.tar.zst")
            if path.is_file()
        }
        if set(actual) != set(expected):
            raise CambonosError(
                f"{channel}: los paquetes publicados no coinciden con el manifiesto "
                f"(esperados={sorted(expected)}, encontrados={sorted(actual)})"
            )
        for filename, record in expected.items():
            archive = actual[filename]
            if sha256_file(archive) != record.get("package_hash"):
                raise CambonosError(f"{channel}: SHA256 incorrecto para {filename}")
            signature = Path(str(archive) + ".sig")
            if not signature.is_file():
                raise CambonosError(f"{channel}: falta la firma de {filename}")
            if sha256_file(signature) != record.get("signature_hash"):
                raise CambonosError(f"{channel}: hash de firma incorrecto para {filename}")
        channel_manifest = site / channel / "manifest.json"
        if not channel_manifest.is_file() or not Path(str(channel_manifest) + ".sig").is_file():
            raise CambonosError(f"{channel}: falta el manifiesto de canal firmado")
        db_name = REPOSITORY_SECTION[channel]
        for filename in (
            f"{db_name}.db", f"{db_name}.db.sig",
            f"{db_name}.db.tar.gz", f"{db_name}.db.tar.gz.sig",
            f"{db_name}.files", f"{db_name}.files.sig",
            f"{db_name}.files.tar.gz", f"{db_name}.files.tar.gz.sig",
        ):
            if not (repository / filename).is_file():
                raise CambonosError(f"{channel}: falta el archivo de repositorio {filename}")
