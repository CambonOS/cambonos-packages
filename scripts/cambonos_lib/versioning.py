"""CambonOS Package Versioning (CPV).

CPV uses a strict MAJOR.MINOR.PATCH pkgver and Arch's pkgrel/epoch fields.
Version ordering is always delegated to pacman's vercmp implementation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from .common import CambonosError, compare_arch_versions

CPV_PKGVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
PKGREL_RE = re.compile(r"^[1-9][0-9]*$")
EPOCH_RE = re.compile(r"^(0|[1-9][0-9]*)$")


@dataclass(frozen=True)
class CPVVersion:
    major: int
    minor: int
    patch: int

    @property
    def pkgver(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def parse_pkgver(value: str) -> CPVVersion:
    """Parse the CPV MAJOR.MINOR.PATCH portion of an Arch pkgver."""
    match = CPV_PKGVER_RE.fullmatch(value)
    if not match:
        raise CambonosError(
            f"pkgver CPV inválido: {value!r}; se requiere MAJOR.MINOR.PATCH "
            "con tres componentes numéricos sin ceros iniciales"
        )
    return CPVVersion(*(int(part) for part in match.groups()))


def validate_package_version(pkgver: str, pkgrel: str, epoch: str = "0") -> None:
    """Validate static CPV fields as represented in a PKGBUILD."""
    parse_pkgver(pkgver)
    if not PKGREL_RE.fullmatch(pkgrel):
        raise CambonosError(f"pkgrel CPV inválido: {pkgrel!r}; debe ser un entero positivo")
    if not EPOCH_RE.fullmatch(epoch):
        raise CambonosError(f"epoch inválido: {epoch!r}; debe ser un entero no negativo")


def format_arch_version(pkgver: str, pkgrel: str, epoch: str = "0") -> str:
    validate_package_version(pkgver, pkgrel, epoch)
    prefix = f"{epoch}:" if epoch != "0" else ""
    return f"{prefix}{pkgver}-{pkgrel}"


def validate_version_transition(
    old_version: str,
    new_pkgver: str,
    new_pkgrel: str,
    new_epoch: str,
    image: str,
    comparator: Callable[[str, str, str], int] = compare_arch_versions,
) -> int:
    """Enforce monotonic Arch ordering for CPV versions.

    Classification of a change as MAJOR/MINOR/PATCH remains a maintainer
    decision; this function validates the machine-checkable invariants.
    """
    validate_package_version(new_pkgver, new_pkgrel, new_epoch)
    new_version = format_arch_version(new_pkgver, new_pkgrel, new_epoch)
    ordering = comparator(old_version, new_version, image)
    if ordering > 0:
        raise CambonosError(
            f"retroceso de versión {old_version} -> {new_version}"
        )

    return ordering
