"""Shared process, hashing and filesystem helpers."""
from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import subprocess
from pathlib import Path


class CambonosError(RuntimeError):
    """Expected operational error suitable for concise CLI output."""


def info(message: str) -> None:
    print(f"==> {message}")


def require_commands(*commands: str) -> None:
    missing = [name for name in commands if shutil.which(name) is None]
    if missing:
        raise CambonosError("faltan herramientas necesarias: " + ", ".join(missing))


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture: bool = False,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    print("  $ " + shlex.join(command))
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            input=input_text,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CambonosError(f"no se encuentra el comando: {command[0]}") from exc
    if check and result.returncode:
        detail = (result.stderr or result.stdout or "").strip() if capture else ""
        raise CambonosError(
            f"comando fallido ({result.returncode}): {shlex.join(command)}"
            + (f"\n{detail}" if detail else "")
        )
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_directory(directory: Path) -> str:
    """Hash package source deterministically, including symlink targets and modes."""
    root = directory.resolve()
    digest = hashlib.sha256()
    excluded = {".git", "src", "pkg", "__pycache__", ".pytest_cache"}
    entries = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in excluded:
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        entries.append(path)
    for path in sorted(entries, key=lambda p: p.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        stat = path.lstat()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(str(stat.st_mode & 0o777).encode("ascii"))
        if path.is_symlink():
            digest.update(b"L")
            digest.update(os.readlink(path).encode("utf-8"))
        elif path.is_file():
            digest.update(b"F")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        else:
            digest.update(b"O")
    return digest.hexdigest()


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def compare_arch_versions(old: str, new: str, image: str) -> int:
    """Return -1, 0, 1 using pacman's vercmp implementation."""
    import shutil

    if shutil.which("vercmp"):
        result = run_command(["vercmp", old, new], capture=True)
    else:
        require_commands("docker")
        result = run_command(
            ["docker", "run", "--rm", "--platform", "linux/amd64", "--network", "none",
             image, "vercmp", old, new],
            capture=True,
        )
    try:
        value = int(result.stdout.strip())
    except (ValueError, AttributeError) as exc:
        raise CambonosError(f"vercmp devolvió una respuesta inesperada para {old} y {new}") from exc
    return (value > 0) - (value < 0)
