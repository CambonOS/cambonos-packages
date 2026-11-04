"""Generate clean pacman repositories from the newly built channel artifacts."""
from __future__ import annotations

import shutil
from pathlib import Path

from .common import CambonosError, run_command, require_commands
from .config import REPOSITORY_SECTION


def create_repository(build_root: Path, destination: Path, channel: str, image: str) -> list[Path]:
    require_commands("docker")
    packages_dir = build_root / "packages"
    archives = sorted(
        p for p in packages_dir.glob("*.pkg.tar.*")
        if p.is_file() and not p.name.endswith(".sig")
    )
    if not archives:
        raise CambonosError(f"no hay paquetes construidos para {channel}")
    unexpected = [path.name for path in archives if not path.name.endswith(".pkg.tar.zst")]
    if unexpected:
        raise CambonosError(
            "solo se admiten paquetes zstd en el repositorio: " + ", ".join(unexpected)
        )
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for archive in archives:
        shutil.copy2(archive, destination / archive.name)
        signature = Path(str(archive) + ".sig")
        if signature.exists():
            shutil.copy2(signature, Path(str(destination / archive.name) + ".sig"))
    database_name = REPOSITORY_SECTION[channel]
    command = [
        "docker", "run", "--rm", "--platform", "linux/amd64", "--network", "none",
        "-v", f"{destination.resolve()}:/repo",
        image,
        "bash", "-euc",
        f"cd /repo && repo-add --include-sigs --quiet {database_name}.db.tar.gz *.pkg.tar.zst",
    ]
    run_command(command)
    for alias, target in (
        (f"{database_name}.db", f"{database_name}.db.tar.gz"),
        (f"{database_name}.files", f"{database_name}.files.tar.gz"),
    ):
        target_path = destination / target
        if not target_path.is_file():
            raise CambonosError(f"repo-add no generó {target}")
        alias_path = destination / alias
        alias_path.unlink(missing_ok=True)
        shutil.copy2(target_path, alias_path)
    return archives
