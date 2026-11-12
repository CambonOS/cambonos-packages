"""Validation helpers for external package update notifications."""
from __future__ import annotations

import re

from .common import CambonosError

EXTERNAL_REPOSITORIES = {
    "CambonOS/cambonos-installer": "cambonos-installer",
    "CambonOS/cambonos-mkiso": "cambonos-mkiso",
}


def validate_external_dispatch(
    repository: str,
    package: str,
    branch: str,
    commit: str,
) -> str:
    """Validate an external update event and return its target channel."""
    expected_package = EXTERNAL_REPOSITORIES.get(repository)
    if expected_package is None:
        raise CambonosError(f"repositorio externo no autorizado: {repository!r}")
    if package != expected_package:
        raise CambonosError(
            f"el repositorio {repository} no puede notificar el paquete {package!r}"
        )
    if branch not in {"dev", "main"}:
        raise CambonosError(f"rama externa no permitida: {branch!r}")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise CambonosError("el SHA del evento externo debe ser un commit Git SHA-1 de 40 caracteres")
    return "testing" if branch == "dev" else "stable"
