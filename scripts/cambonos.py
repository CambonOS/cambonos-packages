#!/usr/bin/env python3
"""CambonOS package pipeline CLI.

Static validation never sources PKGBUILDs. Package code is executed only inside
one disposable Arch Linux Docker container per package during an explicit build.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cambonos_lib.build import build_channel
from cambonos_lib.common import CambonosError, run_command
from cambonos_lib.config import (
    ARCHITECTURE, BRANCH_CHANNELS, DEFAULT_ARCH_IMAGE,
)
from cambonos_lib.manifest import (
    load_previous_manifest, package_source_records, validate_version_policy,
    verify_previous_manifest_signature,
)
from cambonos_lib.signing import sign_and_create_site
from cambonos_lib.planner import create_build_plan
from cambonos_lib.artifacts import recover_previous_artifacts
from cambonos_lib.validation import discover_packages, validate_all


def validate_command(args: argparse.Namespace) -> None:
    source_root = args.source_root.resolve()
    if args.branch not in BRANCH_CHANNELS or BRANCH_CHANNELS[args.branch] != args.channel:
        raise CambonosError(
            f"mapeo de canal incorrecto: la rama {args.branch!r} no produce {args.channel!r}"
        )
    if args.commit:
        actual_commit = run_command(
            ["git", "-C", str(source_root), "rev-parse", "HEAD"], capture=True
        ).stdout.strip()
        if actual_commit != args.commit:
            raise CambonosError(
                f"snapshot incorrecto: se esperaba {args.commit}, se encontró {actual_commit}"
            )
    packages = discover_packages(source_root)
    validate_all(packages)
    if args.previous_manifest:
        previous_path = args.previous_manifest.resolve()
        if not previous_path.is_file():
            if not args.allow_bootstrap:
                raise CambonosError(
                    "no se encuentra el manifiesto anterior; solo se permite continuar "
                    "con CAMBONOS_BOOTSTRAP=true durante la primera publicación"
                )
            previous = None
        else:
            if not args.previous_manifest_signature or not args.keyring_public_key or not args.keyring_trusted:
                raise CambonosError(
                    "para aceptar un manifiesto anterior se requiere su .sig y el keyring público CambonOS"
                )
            verify_previous_manifest_signature(
                previous_path,
                args.previous_manifest_signature.resolve(),
                args.keyring_public_key.resolve(),
                args.keyring_trusted.resolve(),
            )
            previous = load_previous_manifest(previous_path)
        current = package_source_records(packages)
        validate_version_policy(current, previous, args.channel, args.image)
    elif args.allow_bootstrap:
        print("Bootstrap explícito: se omite la comparación con una publicación anterior.")
    else:
        print("Validación local: no se ha solicitado comparación con manifiesto anterior.")
    print(
        f"Validación completada: {len(packages)} paquetes; "
        f"rama={args.branch}; canal={args.channel}; arquitectura={ARCHITECTURE}."
    )


def build_command(args: argparse.Namespace) -> None:
    if args.branch not in BRANCH_CHANNELS or BRANCH_CHANNELS[args.branch] != args.channel:
        raise CambonosError(
            f"mapeo de canal incorrecto: la rama {args.branch!r} no produce {args.channel!r}"
        )
    if not args.commit or len(args.commit) not in (40, 64):
        raise CambonosError("--commit debe ser un SHA Git completo de 40 o 64 caracteres")
    source_root = args.source_root.resolve()
    actual_commit = run_command(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"], capture=True
    ).stdout.strip()
    if actual_commit != args.commit:
        raise CambonosError(
            f"snapshot incorrecto: se esperaba {args.commit}, se encontró {actual_commit}"
        )
    packages = discover_packages(source_root)
    validate_all(packages)
    output = args.output.resolve()
    if output.exists():
        import shutil
        shutil.rmtree(output)
    output.mkdir(parents=True)
    build_channel(
        packages=packages,
        channel=args.channel,
        branch=args.branch,
        commit=args.commit,
        image=args.image,
        output=output,
    )
    print(f"Construcción terminada: {output}")



def plan_command(args: argparse.Namespace) -> None:
    """Emit a read-only build plan; publication remains on the legacy pipeline."""
    source_root = args.source_root.resolve()
    packages = discover_packages(source_root)
    validate_all(packages)
    previous = None
    if args.previous_manifest:
        try:
            previous = json.loads(args.previous_manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CambonosError(f"no se pudo leer el manifiesto anterior: {exc}") from exc
    plan = create_build_plan(packages, args.channel, args.image, previous)
    rendered = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    print(
        f"Plan sombra ({args.channel}): {plan['summary']['build']} construir, "
        f"{plan['summary']['reuse_candidates']} candidatos a reutilización. No se ha compilado ni publicado nada.",
        file=sys.stderr,
    )


def sign_command(args: argparse.Namespace) -> None:
    private_key = os.environ.get("CAMBONOS_SIGNING_KEY", "")
    passphrase = os.environ.get("CAMBONOS_SIGNING_PASSPHRASE", "")
    fingerprint = os.environ.get("CAMBONOS_SIGNING_FINGERPRINT", "")
    if not fingerprint:
        raise CambonosError("falta la variable CAMBONOS_SIGNING_FINGERPRINT")
    sign_and_create_site(
        testing_root=args.testing_dir.resolve(),
        stable_root=args.stable_dir.resolve(),
        output_site=args.output.resolve(),
        private_key_text=private_key,
        passphrase=passphrase,
        expected_fingerprint=fingerprint,
        image=args.image,
        expected_testing_commit=args.testing_commit,
        expected_stable_commit=args.stable_commit,
        pages_url=os.environ.get("CAMBONOS_PAGES_URL", "https://<domain>"),
        previous_manifest_path=args.previous_manifest.resolve() if args.previous_manifest else None,
        previous_manifest_signature_path=(
            args.previous_manifest_signature.resolve()
            if args.previous_manifest_signature else None
        ),
    )
    print(f"Sitio completo preparado en {args.output.resolve()}")


def recover_command(args: argparse.Namespace) -> None:
    report = recover_previous_artifacts(
        manifest_path=args.previous_manifest.resolve(),
        signature_path=args.previous_manifest_signature.resolve(),
        public_key_path=args.keyring_public_key.resolve(),
        trusted_path=args.keyring_trusted.resolve(),
        channel=args.channel,
        output=args.output.resolve(),
        base_url=args.base_url,
        image=args.image,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Recuperación verificada: {report['summary']['recovered']} paquetes; canal={args.channel}.")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cambonos",
        description="Validación, construcción, firma y publicación de paquetes CambonOS.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validar un snapshot de paquetes")
    validate.add_argument("--source-root", type=Path, default=Path.cwd())
    validate.add_argument("--channel", required=True, choices=("stable", "testing"))
    validate.add_argument("--branch", required=True, choices=("main", "dev"))
    validate.add_argument("--commit")
    validate.add_argument("--previous-manifest", type=Path)
    validate.add_argument("--previous-manifest-signature", type=Path)
    validate.add_argument("--keyring-public-key", type=Path)
    validate.add_argument("--keyring-trusted", type=Path)
    validate.add_argument("--allow-bootstrap", action="store_true")
    validate.add_argument("--image", default=DEFAULT_ARCH_IMAGE)
    validate.set_defaults(func=validate_command)

    build = subparsers.add_parser("build", help="construir todos los paquetes de un canal")
    build.add_argument("--source-root", type=Path, default=Path.cwd())
    build.add_argument("--channel", required=True, choices=("stable", "testing"))
    build.add_argument("--branch", required=True, choices=("main", "dev"))
    build.add_argument("--commit", required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--image", default=DEFAULT_ARCH_IMAGE)
    build.set_defaults(func=build_command)

    plan = subparsers.add_parser(
        "plan", help="calcular un plan de build selectivo sin compilar ni publicar"
    )
    plan.add_argument("--source-root", type=Path, default=Path.cwd())
    plan.add_argument("--channel", required=True, choices=("stable", "testing"))
    plan.add_argument("--image", default=DEFAULT_ARCH_IMAGE)
    plan.add_argument("--previous-manifest", type=Path)
    plan.add_argument("--output", type=Path)
    plan.set_defaults(func=plan_command)

    recover = subparsers.add_parser(
        "recover-artifacts", help="recuperar y verificar artefactos de una publicación anterior sin modificar el mirror"
    )
    recover.add_argument("--previous-manifest", type=Path, required=True)
    recover.add_argument("--previous-manifest-signature", type=Path, required=True)
    recover.add_argument("--keyring-public-key", type=Path, required=True)
    recover.add_argument("--keyring-trusted", type=Path, required=True)
    recover.add_argument("--channel", required=True, choices=("stable", "testing"))
    recover.add_argument("--output", type=Path, required=True)
    recover.add_argument("--base-url", default="https://mirror.cambonos.org")
    recover.add_argument("--image", default=DEFAULT_ARCH_IMAGE)
    recover.set_defaults(func=recover_command)

    sign = subparsers.add_parser("sign", help="firmar ambos canales y preparar el sitio")
    sign.add_argument("--testing-dir", type=Path, required=True)
    sign.add_argument("--stable-dir", type=Path, required=True)
    sign.add_argument("--output", type=Path, required=True)
    sign.add_argument("--image", default=DEFAULT_ARCH_IMAGE)
    sign.add_argument("--testing-commit", required=True)
    sign.add_argument("--stable-commit", required=True)
    sign.add_argument("--previous-manifest", type=Path)
    sign.add_argument("--previous-manifest-signature", type=Path)
    sign.set_defaults(func=sign_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        args.func(args)
        return 0
    except CambonosError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("ERROR: operación interrumpida", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
