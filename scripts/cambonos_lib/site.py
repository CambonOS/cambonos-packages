"""Build and verify the static GitHub Pages tree."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote

from .common import CambonosError, sha256_file
from .config import MIRROR_BASE_URL, REPOSITORY_SECTION


INDEX_MARKER = "<!-- generated-by: cambonos-index -->"
INDEX_TITLE = "CambonOS Package Repository"
FAVICON_NAME = "cambonos-icon.svg"
FAVICON_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "packages" / "cambonos-branding" / "files" / FAVICON_NAME
)
_SITE_CSS = """
:root {
    color-scheme: light;
    --lime: #aefa50;
    --aqua: #70e7e6;
    --navy: #061c31;
    --ink: #102537;
    --muted: #526371;
    --accent: #006f78;
    --line: #d7e0e4;
    --surface: #f4f8f8;
    --page: #f7f5ec;
    font-family: "DM Sans", "Segoe UI", sans-serif;
    background: var(--page);
    color: var(--ink);
}
:root[data-theme="dark"] {
    color-scheme: dark;
    --ink: #e4edf2;
    --muted: #b6c7d1;
    --accent: #70e7e6;
    --line: #294354;
    --surface: #102b3d;
    --page: #0a1d2b;
}
@media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
        color-scheme: dark;
        --ink: #e4edf2;
        --muted: #b6c7d1;
        --accent: #70e7e6;
        --line: #294354;
        --surface: #102b3d;
        --page: #0a1d2b;
    }
}
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; line-height: 1.6; }
a { color: inherit; }
a:focus-visible { outline: 3px solid #019fa7; outline-offset: 3px; }
.skip-link { position: absolute; z-index: 2; top: 10px; left: 10px; padding: 8px 12px; transform: translateY(-150%); color: var(--navy); background: var(--lime); font-weight: 700; }
.skip-link:focus { transform: translateY(0); }
.site-header {
    color: #f7f5ec;
    background-color: var(--navy);
    background-image: repeating-linear-gradient(130deg, transparent 0 58px, rgb(112 231 230 / 5%) 59px 60px), linear-gradient(115deg, rgb(20 146 70 / 19%), transparent 58%);
}
.header-inner, main, .site-footer { width: min(1120px, calc(100% - 48px)); margin-inline: auto; }
.header-inner { padding: 48px 0 36px; }
.header-topline { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 12px; }
.eyebrow, .section-label { margin: 0 0 12px; color: var(--lime); font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.header-topline .eyebrow { margin: 0; }
.theme-toggle { width: 42px; height: 42px; display: grid; flex: 0 0 auto; place-items: center; padding: 0; border: 1px solid rgb(255 255 255 / 35%); color: #f7f5ec; background: rgb(255 255 255 / 6%); cursor: pointer; }
.theme-toggle:hover { border-color: var(--lime); color: var(--lime); }
.theme-toggle svg { width: 19px; height: 19px; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.8; }
.theme-icon-moon { display: none; }
:root[data-theme="dark"] .theme-icon-sun { display: none; }
:root[data-theme="dark"] .theme-icon-moon { display: block; }
@media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) .theme-icon-sun { display: none; }
    :root:not([data-theme="light"]) .theme-icon-moon { display: block; }
}
h1, h2 { font-family: "Space Grotesk", "Segoe UI", sans-serif; line-height: 1.12; }
h1 { margin: 0; font-size: clamp(2rem, 5vw, 3.25rem); font-weight: 600; }
.lede { max-width: 720px; margin: 14px 0 0; color: #d0e0e6; }
main { padding-block: 34px 72px; }
.section-heading { display: flex; align-items: end; justify-content: space-between; gap: 20px; margin-bottom: 14px; }
.section-heading h2 { margin: 0; font-size: 1.4rem; }
.section-label { margin-bottom: 7px; color: var(--accent); }
.table-wrap { overflow-x: auto; border-top: 2px solid var(--navy); }
table { width: 100%; border-collapse: collapse; text-align: left; }
th, td { padding: 13px 15px; border-bottom: 1px solid var(--line); vertical-align: middle; }
th { color: var(--muted); font-size: .72rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
tbody tr:hover td { background: rgb(112 231 230 / 12%); }
td a { text-decoration-color: #019fa7; text-underline-offset: 3px; }
td a:hover { color: var(--accent); }
.kind { width: 92px; color: var(--accent); font-size: .68rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.name { overflow-wrap: anywhere; font-weight: 600; }
.size { width: 125px; color: var(--muted); text-align: right; white-space: nowrap; font-size: .85rem; font-variant-numeric: tabular-nums; }
.parent td { background: var(--surface); }
.parent a { color: var(--accent); font-weight: 700; }
.breadcrumbs { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 0 0 24px; color: #d0e0e6; font-size: .86rem; }
.breadcrumbs a { text-decoration-color: var(--aqua); text-underline-offset: 3px; }
.breadcrumbs .separator { color: var(--aqua); }
.breadcrumbs [aria-current="page"] { color: white; font-weight: 700; overflow-wrap: anywhere; }
.channel-link { display: inline-flex; align-items: center; gap: 9px; font-weight: 700; text-decoration: none; }
.channel-link::before { width: 8px; height: 8px; content: ""; background: var(--aqua); }
.channel-link.testing::before { background: var(--lime); }
.branch, code { font-family: "SFMono-Regular", Consolas, monospace; font-size: .88em; overflow-wrap: anywhere; }
.config { overflow-x: auto; padding: 20px 22px; color: #e4edf2; background: var(--navy); border-left: 4px solid var(--lime); line-height: 1.65; }
.muted { color: var(--muted); }
.site-footer { display: flex; justify-content: space-between; gap: 18px; padding: 18px 0 26px; border-top: 1px solid var(--line); color: var(--muted); font-size: .78rem; }
.site-footer p { margin: 0; }
@media (max-width: 640px) {
    .header-inner, main, .site-footer { width: min(100% - 36px, 560px); }
    .header-inner { padding: 34px 0 28px; }
    .header-topline { gap: 12px; }
    main { padding-block: 25px 48px; }
    .section-heading { align-items: start; flex-direction: column; gap: 4px; }
    th, td { padding: 11px 9px; }
    .kind { width: 55px; }
    .size { width: 78px; }
    .site-footer { flex-direction: column; }
}
"""
_THEME_SCRIPT = """
(() => {
    const root = document.documentElement;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    let preference = "system";
    try { preference = localStorage.getItem("cambonos-theme") || "system"; } catch {}
    if (!["system", "light", "dark"].includes(preference)) preference = "system";
    if (preference === "system") delete root.dataset.theme;
    else root.dataset.theme = preference;

    const initializeToggle = () => {
        const toggle = document.querySelector(".theme-toggle");
        if (!toggle) return;
        const update = () => {
            const isDark = preference === "dark" || (preference === "system" && media.matches);
            const label = isDark ? "Switch to light theme" : "Switch to dark theme";
            toggle.setAttribute("aria-pressed", String(isDark));
            toggle.setAttribute("aria-label", label);
            toggle.title = label;
        };
        update();
        toggle.addEventListener("click", () => {
            const isDark = preference === "dark" || (preference === "system" && media.matches);
            preference = isDark ? "light" : "dark";
            try { localStorage.setItem("cambonos-theme", preference); } catch {}
            root.dataset.theme = preference;
            update();
        });
        media.addEventListener("change", () => {
            if (preference === "system") update();
        });
    };
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeToggle, { once: true });
    } else initializeToggle();
})();
"""


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

        parts = relative.parts if relative != Path(".") else ()
        favicon_href = "../" * len(parts) + FAVICON_NAME
        breadcrumbs = [f'<a href="{"../" * len(parts) or "./"}">Packages</a>']
        for index, part in enumerate(parts):
            breadcrumbs.append('<span class="separator" aria-hidden="true">/</span>')
            if index == len(parts) - 1:
                breadcrumbs.append(f'<span aria-current="page">{escape(part)}/</span>')
            else:
                href = "../" * (len(parts) - index - 1)
                breadcrumbs.append(f'<a href="{escape(href, quote=True)}">{escape(part)}/</a>')

        page = f"""<!doctype html>
{INDEX_MARKER}
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
    <link rel="icon" type="image/svg+xml" href="{favicon_href}">
    <title>CambonOS Packages | {escape(display_path)}</title>
    <script>{_THEME_SCRIPT}</script>
  <style>
        {_SITE_CSS}
  </style>
</head>
<body>
    <a class="skip-link" href="#main-content">Skip to content</a>
    <header class="site-header">
        <div class="header-inner">
            <div class="header-topline"><p class="eyebrow">CambonOS / Official repositories</p>
                <button class="theme-toggle" type="button" aria-label="Change color theme" title="Change color theme" aria-pressed="false">
                    <svg class="theme-icon-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/></svg>
                    <svg class="theme-icon-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.2 15.4A8.5 8.5 0 0 1 8.6 3.8 8.5 8.5 0 1 0 20.2 15.4Z"/></svg>
                </button>
            </div>
            <h1>Repository files</h1>
            <nav class="breadcrumbs" aria-label="Breadcrumb">{''.join(breadcrumbs)}</nav>
        </div>
    </header>
    <main id="main-content">
        <div class="section-heading"><div><p class="section-label">Directory contents</p><h2>{escape(display_path)}</h2></div></div>
        <div class="table-wrap"><table>
            <thead><tr><th>Type</th><th>Name</th><th class="size">Size</th></tr></thead>
            <tbody>{''.join(rows)}</tbody>
        </table></div>
    </main>
    <footer class="site-footer"><p>{INDEX_TITLE}</p><p>Official CambonOS package mirror.</p></footer>
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
    if not FAVICON_SOURCE.is_file():
        raise CambonosError(f"no se encuentra el favicon de marca: {FAVICON_SOURCE}")
    (site / FAVICON_NAME).write_bytes(FAVICON_SOURCE.read_bytes())
    rows = []
    for channel, label in (("stable", "Stable"), ("testing", "Testing")):
        data = manifest["channels"][channel]
        browse = f'<a class="channel-link {channel}" href="{channel}/">{label}</a>'
        rows.append(
            f"<tr><td>{browse}</td><td><code>{data['branch']}</code></td>"
            f"<td><code>{data['commit'][:12]}</code></td>"
            f"<td class=\"size\">{len(data['packages'])}</td></tr>"
        )
    import html as html_module
    pages_canonical_url = html_module.escape(pages_url.rstrip("/"), quote=True)
    mirror_base_url = html_module.escape(MIRROR_BASE_URL, quote=True)
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CambonOS Packages</title><link rel="canonical" href="{pages_canonical_url}">
<meta name="description" content="Official CambonOS package repositories, with signed stable and testing channels.">
<link rel="icon" type="image/svg+xml" href="{FAVICON_NAME}">
<script>{_THEME_SCRIPT}</script>
<style>{_SITE_CSS}</style></head><body>
<a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header"><div class="header-inner">
<div class="header-topline"><p class="eyebrow">CambonOS / Arch Linux</p>
<button class="theme-toggle" type="button" aria-label="Change color theme" title="Change color theme" aria-pressed="false">
<svg class="theme-icon-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/></svg>
<svg class="theme-icon-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.2 15.4A8.5 8.5 0 0 1 8.6 3.8 8.5 8.5 0 1 0 20.2 15.4Z"/></svg>
</button></div><h1>CambonOS Packages</h1>
<p class="lede">Official CambonOS package repositories.</p>
</div></header>
<main id="main-content">
<section aria-labelledby="channels-title">
<div class="section-heading"><div><p class="section-label">Repository channels</p><h2 id="channels-title">Channels</h2></div></div>
<div class="table-wrap"><table><thead><tr><th>Channel</th><th>Branch</th><th>Commit</th><th class="size">Packages</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
</section>
<section aria-labelledby="pacman-title" style="margin-top:42px">
<div class="section-heading"><div><p class="section-label">Pacman</p><h2 id="pacman-title">Repository configuration</h2></div></div>
<pre class="config"><code>#[cambonos-testing]
#SigLevel = Required TrustedOnly
#Server = {mirror_base_url}/testing/$arch

[cambonos]
SigLevel = Required TrustedOnly
Server = {mirror_base_url}/stable/$arch</code></pre>
<p class="muted">Testing is disabled by default. Use the channel links above to browse the repositories.
Signed global manifest: <a href="metadata/manifest.json">metadata/manifest.json</a>.</p>
</section>
</main>
<footer class="site-footer"><p>{INDEX_TITLE}</p><p>Official packages / x86_64</p></footer>
</body></html>
"""
    (site / "index.html").write_text(html, encoding="utf-8")


def verify_site(site: Path) -> None:
    required = (
        site / "index.html",
        site / FAVICON_NAME,
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
