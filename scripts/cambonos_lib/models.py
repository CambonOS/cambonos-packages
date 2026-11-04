"""Typed data structures shared by the package manager."""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Package:
    name: str
    directory: Path
    pkgver: str
    pkgrel: str
    epoch: str = "0"
    architecture: tuple[str, ...] = ("x86_64",)
    depends: tuple[str, ...] = ()
    makedepends: tuple[str, ...] = ()
    checkdepends: tuple[str, ...] = ()
    optdepends: tuple[str, ...] = ()
    install_script: str | None = None


@dataclass(frozen=True)
class SourceSnapshot:
    branch: str
    channel: str
    commit: str
    root: Path


@dataclass(frozen=True)
class BuildArtifact:
    path: Path
    package_name: str
    version: str
    architecture: str
    source_hash: str
    package_hash: str


@dataclass
class BuildManifest:
    channel: str
    branch: str
    commit: str
    architecture: str
    image: str
    packages: dict[str, dict] = field(default_factory=dict)
    build_environment: dict = field(default_factory=dict)
