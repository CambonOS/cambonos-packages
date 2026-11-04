"""Build and verify the static GitHub Pages tree."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .common import CambonosError, sha256_file
from .config import REPOSITORY_SECTION


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
        rows.append(
            f"<tr><td>{label}</td><td><code>{data['branch']}</code></td>"
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
<pre><code>[cambonos]
SigLevel = Required
Server = {base_url}/stable/$arch

#[cambonos-testing]
#SigLevel = Required
#Server = {base_url}/testing/$arch</code></pre>
<p class="muted">Testing está deshabilitado por defecto. Manifiesto:
<a href="metadata/manifest.json">metadata/manifest.json</a>.</p>
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
