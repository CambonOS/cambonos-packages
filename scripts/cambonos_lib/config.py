"""Central configuration for CambonOS package builds."""

ARCHITECTURE = "x86_64"
MIRROR_BASE_URL = "https://mirror.cambonos.org"
BRANCH_CHANNELS = {"main": "stable", "dev": "testing"}
PACKAGE_DIR = "packages"
DEFAULT_ARCH_IMAGE = (
    "archlinux:base-devel-20261011.0.609700"
    "@sha256:d6979123107e7a9f52c2de19104966b5f809e13a4593017780bd8c0b140f80ff"
)
MANIFEST_SCHEMA_VERSION = 1
REPOSITORY_SECTION = {"stable": "cambonos", "testing": "cambonos-testing"}
REQUIRED_PACKAGES = {"cambonos-keyring"}
KEYRING_FILES = {
    "cambonos.gpg": "usr/share/pacman/keyrings/cambonos.gpg",
    "cambonos-trusted": "usr/share/pacman/keyrings/cambonos-trusted",
    "cambonos-revoked": "usr/share/pacman/keyrings/cambonos-revoked",
}
