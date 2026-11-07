"""Isolated Arch Linux container builds, one disposable container per package."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .common import CambonosError, run_command, sha256_directory, sha256_file, require_commands
from .config import ARCHITECTURE
from .manifest import write_build_manifest
from .models import Package
from .validation import dependency_name, extract_function


PACMAN_TESTING_OVERLAY = r'''
if [[ "${EXPECTED_PACKAGE}" == "cambonos-pacman" && "${CHANNEL}" == "testing" ]]; then
    config="${PACMAN_CONFIG:-/build/package/files/cambonos.conf}"
    test "$(grep -Fxc '#[cambonos-testing]' "${config}")" -eq 1
    test "$(grep -Fxc '#SigLevel = Required TrustedOnly' "${config}")" -eq 1
    test "$(grep -Fxc '#Server = https://mirror.cambonos.org/testing/$arch' "${config}")" -eq 1
    test "$(grep -Fxc '[cambonos]' "${config}")" -eq 1
    test "$(grep -Fxc 'SigLevel = Required TrustedOnly' "${config}")" -eq 1
    test "$(grep -Fxc 'Server = https://mirror.cambonos.org/stable/$arch' "${config}")" -eq 1
    sed -i \
        -e '/^#\[cambonos-testing\]$/ { s/^#\[cambonos-testing\]$/[cambonos-testing]/; n; s/^#SigLevel = Required TrustedOnly$/SigLevel = Required TrustedOnly/; n; s|^#Server = https://mirror.cambonos.org/testing/\$arch$|Server = https://mirror.cambonos.org/testing/$arch|; }' \
        -e '/^\[cambonos\]$/ { s/^\[cambonos\]$/#[cambonos]/; n; s/^SigLevel = Required TrustedOnly$/#SigLevel = Required TrustedOnly/; n; s|^Server = https://mirror.cambonos.org/stable/\$arch$|#Server = https://mirror.cambonos.org/stable/$arch|; }' \
        "${config}"
fi
'''

CONTAINER_BUILD_SCRIPT = r"""
set -Eeuo pipefail
pacman -Syu --noconfirm
pacman -S --needed --noconfirm base-devel
useradd --create-home --shell /bin/bash builder
mkdir -p /build/package /out /internal
cp -a /input/. /build/package/
find /build/package -exec touch -h -d "@${SOURCE_DATE_EPOCH}" {} +
chown -R builder:builder /build
chown builder:builder /out
find /out -mindepth 1 -maxdepth 1 ! -name .internal -exec chown -R builder:builder {} +
if compgen -G '/internal/*.pkg.tar.*' >/dev/null; then
    pacman -U --noconfirm --nodeps /internal/*.pkg.tar.*
fi
runuser -u builder -- bash -lc 'cd /build/package && makepkg --printsrcinfo > /tmp/cambonos.SRCINFO'
mapfile -t raw_dependencies < <(
    awk -v check="${CHECK_PRESENT}" '
      ($1 ~ /^makedepends(_|$)/ || (check == "1" && $1 ~ /^checkdepends(_|$)/)) && $2 == "=" { print $3 }
    ' /tmp/cambonos.SRCINFO
)
external_dependencies=()
for dependency in "${raw_dependencies[@]}"; do
    dep_name="${dependency%%[<>=]*}"
    case " ${INTERNAL_NAMES} " in
        *" ${dep_name} "*) ;;
        *) external_dependencies+=("${dependency}") ;;
    esac
done
if ((${#external_dependencies[@]})); then
    pacman -S --needed --noconfirm -- "${external_dependencies[@]}"
fi
if ((${#raw_dependencies[@]})); then
    if ! pacman -T -- "${raw_dependencies[@]}"; then
        echo "Unsatisfied build dependencies (including internal package version constraints)." >&2
        exit 1
    fi
fi
{
    echo "Build timestamp (UTC): $(date -u +%FT%TZ)"
    echo "Image: ${BUILD_IMAGE}"
    echo "Architecture: $(uname -m)"
    echo
    pacman -Q
} > /out/build-environment.txt
cat > /tmp/cambonos-makepkg.conf <<'EOF'
source /etc/makepkg.conf
BUILDDIR=/build/work
PKGDEST=/out
PKGEXT='.pkg.tar.zst'
BUILDENV=("${BUILDENV[@]/!check/check}")
if [[ ! " ${BUILDENV[*]} " =~ (^|[[:space:]])check([[:space:]]|$) ]]; then
    BUILDENV+=(check)
fi
EOF
chown builder:builder /tmp/cambonos-makepkg.conf
__PACMAN_TESTING_OVERLAY__
runuser -u builder -- env SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH}" bash -lc \
    'cd /build/package && makepkg --config /tmp/cambonos-makepkg.conf --nodeps --cleanbuild --clean --noconfirm'
mapfile -t built_packages < <(find /out -maxdepth 1 -type f -name '*.pkg.tar.*' ! -name '*.sig' -print | sort)
if ((${#built_packages[@]} != 1)); then
    printf 'Expected exactly one package archive, found %s\n' "${#built_packages[@]}" >&2
    printf '%s\n' "${built_packages[@]}" >&2
    exit 1
fi
actual_name="$(pacman -Qqp "${built_packages[0]}")"
if [[ "${actual_name}" != "${EXPECTED_PACKAGE}" ]]; then
    echo "Unexpected package name: ${actual_name}; expected ${EXPECTED_PACKAGE}" >&2
    exit 1
fi
read -r queried_name actual_version < <(pacman -Qp "${built_packages[0]}")
actual_arch="$(pacman -Qip "${built_packages[0]}" | awk -F': ' '/^Architecture[[:space:]]*:/ {print $2; exit}')"
if [[ "${queried_name}" != "${EXPECTED_PACKAGE}" || "${actual_version}" != "${EXPECTED_VERSION}" ]]; then
    echo "Unexpected package version: ${queried_name} ${actual_version}; expected ${EXPECTED_PACKAGE} ${EXPECTED_VERSION}" >&2
    exit 1
fi
if [[ "${actual_arch}" != "${EXPECTED_ARCH}" ]]; then
    echo "Unexpected package architecture: ${actual_arch}; expected ${EXPECTED_ARCH}" >&2
    exit 1
fi
if [[ "${EXPECTED_PACKAGE}" == "cambonos-keyring" ]]; then
    mkdir -p /out/keyring-material
    for keyfile in cambonos.gpg cambonos-trusted cambonos-revoked; do
        archive_path="usr/share/pacman/keyrings/${keyfile}"
        tar --zstd -xOf "${built_packages[0]}" "${archive_path}" > "/out/keyring-material/${keyfile}"
        cmp "/input/files/${keyfile}" "/out/keyring-material/${keyfile}"
    done
    test -s /out/keyring-material/cambonos.gpg
    test -s /out/keyring-material/cambonos-trusted
fi
chown "${HOST_UID}:${HOST_GID}" /out
find /out -mindepth 1 -maxdepth 1 ! -name .internal -exec chown -R "${HOST_UID}:${HOST_GID}" {} +
"""


def build_order(packages: dict[str, Package]) -> list[str]:
    """Topologically order only internal build-time dependencies."""
    graph: dict[str, set[str]] = {}
    for name, package in packages.items():
        deps = set()
        pkgb_path = package.directory / "PKGBUILD"
        has_check = (
            extract_function(pkgb_path.read_text(encoding="utf-8"), "check")
            is not None
        ) if pkgb_path.is_file() else False
        build_dependencies = package.makedepends + (package.checkdepends if has_check else ())
        for raw in build_dependencies:
            dep = dependency_name(raw)
            if dep and dep.startswith("cambonos-"):
                if dep not in packages:
                    raise CambonosError(f"{name}: dependencia interna de construcción inexistente: {dep}")
                deps.add(dep)
        graph[name] = deps
    ordered: list[str] = []
    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(name: str, chain: list[str]) -> None:
        if name in permanent:
            return
        if name in temporary:
            start = chain.index(name) if name in chain else 0
            raise CambonosError(
                "ciclo de dependencias internas de construcción: "
                + " -> ".join(chain[start:] + [name])
            )
        temporary.add(name)
        for dep in sorted(graph[name]):
            visit(dep, chain + [name])
        temporary.remove(name)
        permanent.add(name)
        ordered.append(name)

    for name in sorted(packages):
        visit(name, [])
    return ordered


def _build_one(
    package: Package,
    channel: str,
    image: str,
    output: Path,
    internal_artifacts: list[tuple[str, Path]],
    source_date_epoch: int,
) -> tuple[Path, dict]:
    require_commands("docker")
    output.mkdir(parents=True, exist_ok=True)
    internal_dir = output / ".internal"
    internal_dir.mkdir(exist_ok=True)
    for _name, artifact in internal_artifacts:
        shutil.copy2(artifact, internal_dir / artifact.name)

    check_present = "1" if extract_function(
        (package.directory / "PKGBUILD").read_text(encoding="utf-8"), "check"
    ) is not None else "0"
    internal_names = " ".join(sorted(name for name, _path in internal_artifacts))
    host_uid, host_gid = os.getuid(), os.getgid()
    command = [
        "docker", "run", "--rm", "--platform", "linux/amd64",
        "-e", f"CHECK_PRESENT={check_present}",
        "-e", f"CHANNEL={channel}",
        "-e", f"INTERNAL_NAMES={internal_names}",
        "-e", f"EXPECTED_PACKAGE={package.name}",
        "-e", f"EXPECTED_VERSION={package.epoch + ':' if package.epoch != '0' else ''}{package.pkgver}-{package.pkgrel}",
        "-e", f"EXPECTED_ARCH={'any' if 'any' in package.architecture else ARCHITECTURE}",
        "-e", f"BUILD_IMAGE={image}",
        "-e", f"SOURCE_DATE_EPOCH={source_date_epoch}",
        "-e", f"HOST_UID={host_uid}",
        "-e", f"HOST_GID={host_gid}",
        "-v", f"{package.directory.resolve()}:/input:ro",
        "-v", f"{output.resolve()}:/out",
        "-v", f"{internal_dir.resolve()}:/internal:ro",
        image, "bash", "-euc",
        CONTAINER_BUILD_SCRIPT.replace("__PACMAN_TESTING_OVERLAY__", PACMAN_TESTING_OVERLAY),
    ]
    run_command(command)
    archives = sorted(
        p for p in output.glob("*.pkg.tar.*")
        if p.is_file() and not p.name.endswith(".sig")
    )
    if len(archives) != 1:
        raise CambonosError(f"{package.name}: se esperaba un único paquete generado")
    archive = archives[0]
    record = {
        "version": f"{package.epoch}:{package.pkgver}-{package.pkgrel}" if package.epoch != "0"
                   else f"{package.pkgver}-{package.pkgrel}",
        "pkgver": package.pkgver,
        "pkgrel": package.pkgrel,
        "epoch": package.epoch,
        "architecture": "any" if "any" in package.architecture else ARCHITECTURE,
        "source_hash": sha256_directory(package.directory),
        "source_date_epoch": source_date_epoch,
        "package_file": archive.name,
        "package_hash": sha256_file(archive),
    }
    metadata_path = package.directory / ".cambonos-source.json"
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        record["source_repository"] = metadata["repository"]
        record["source_commit"] = metadata["commit"]
    env_file = output / "build-environment.txt"
    if not env_file.is_file():
        raise CambonosError(f"{package.name}: falta build-environment.txt")
    return archive, record




def _package_source_date_epoch(package: Package, commit: str) -> int:
    metadata_path = package.directory / ".cambonos-source.json"
    if metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            value = metadata.get("source_date_epoch")
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            raise CambonosError(
                f"{package.name}: metadata de origen externo inválida"
            ) from exc
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise CambonosError(
                f"{package.name}: source_date_epoch externo ausente o inválido"
            )
        return value
    source_root = package.directory.parent.parent
    relative_path = package.directory.relative_to(source_root).as_posix()
    result = run_command(
        ["git", "-C", str(source_root), "log", "-1", "--format=%at",
         commit, "--", relative_path],
        capture=True,
    )
    value = result.stdout.strip()
    if not value.isdigit():
        raise CambonosError(
            f"{package.name}: no se pudo obtener SOURCE_DATE_EPOCH desde el historial Git"
        )
    return int(value)

def build_channel(
    packages: dict[str, Package],
    channel: str,
    branch: str,
    commit: str,
    image: str,
    output: Path,
) -> Path:
    if channel not in {"stable", "testing"}:
        raise CambonosError(f"canal no válido: {channel}")
    output.mkdir(parents=True, exist_ok=True)
    package_output = output / "packages"
    package_output.mkdir(exist_ok=True)
    ordered = build_order(packages)
    built_by_name: dict[str, Path] = {}
    records: dict[str, dict] = {}
    environment_record = {}
    for name in ordered:
        package = packages[name]
        info = f"Construyendo {name} ({channel})"
        print(f"==> {info}")
        internal: list[tuple[str, Path]] = []
        pkgb_path = package.directory / "PKGBUILD"
        has_check = (
            extract_function(pkgb_path.read_text(encoding="utf-8"), "check")
            is not None
        ) if pkgb_path.is_file() else False
        build_dependencies = package.makedepends + (package.checkdepends if has_check else ())
        for raw in build_dependencies:
            dep = dependency_name(raw)
            if dep in built_by_name:
                internal.append((dep, built_by_name[dep]))
        per_package_output = output / ".work" / name
        if per_package_output.exists():
            shutil.rmtree(per_package_output)
        source_date_epoch = _package_source_date_epoch(package, commit)
        archive, record = _build_one(
            package, channel, image, per_package_output, internal, source_date_epoch
        )
        destination = package_output / archive.name
        shutil.copy2(archive, destination)
        record["package_file"] = destination.name
        record["package_hash"] = sha256_file(destination)
        records[name] = record
        built_by_name[name] = destination
        env_file = per_package_output / "build-environment.txt"
        if env_file.is_file():
            environment_record[name] = (
                f"SOURCE_DATE_EPOCH={source_date_epoch}\n"
                + env_file.read_text(encoding="utf-8")
            )
        if name == "cambonos-keyring":
            material_source = per_package_output / "keyring-material"
            material_dest = output / "keyring-material"
            if material_dest.exists():
                shutil.rmtree(material_dest)
            shutil.copytree(material_source, material_dest)
    (output / ".work").exists() and shutil.rmtree(output / ".work")
    (output / "build-environment.txt").write_text(
        "\n\n".join(f"### {name}\n{content}" for name, content in sorted(environment_record.items()))
        + "\n",
        encoding="utf-8",
    )
    write_build_manifest(
        output, channel, branch, commit, ARCHITECTURE, image, records,
        {"packages": environment_record},
    )
    return output


