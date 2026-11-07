from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cambonos_lib.common import CambonosError
from cambonos_lib.signing import (
    _fingerprints, _materialize_and_sign_aliases, _secret_signing_fingerprints,
    _sign_file, validate_source_version_policy, sign_and_create_site,
)

PRIMARY = "A" * 40
SUBKEY = "B" * 40


class SigningHelperTests(unittest.TestCase):
    @patch("cambonos_lib.signing.run_command")
    def test_fingerprints_maps_valid_signing_subkey_to_primary(self, run):
        run.return_value.stdout = (
            f"pub:u: rsa:4096:1:2:3:u:::scSC::::::23::0:\n"
            f"fpr:::::::::{PRIMARY}:\n"
            f"sub:u: rsa:4096:1:2:3:::::s::::::23:\n"
            f"fpr:::::::::{SUBKEY}:\n"
        )
        all_fprs, signing, mapping = _fingerprints(Path("public.gpg"))
        self.assertEqual(all_fprs, {PRIMARY, SUBKEY})
        self.assertEqual(signing, {SUBKEY})
        self.assertEqual(mapping, {SUBKEY: PRIMARY})

    @patch("cambonos_lib.signing.run_command")
    def test_fingerprints_ignores_revoked_signing_subkey(self, run):
        run.return_value.stdout = (
            f"pub:u: rsa:4096:1:2:3:u:::scSC::::::23::0:\n"
            f"fpr:::::::::{PRIMARY}:\n"
            f"sub:r: rsa:4096:1:2:3:::::s::::::23:\n"
            f"fpr:::::::::{SUBKEY}:\n"
        )
        _all, signing, mapping = _fingerprints(Path("public.gpg"))
        self.assertEqual(signing, set())
        self.assertEqual(mapping, {})

    @patch("cambonos_lib.signing.run_command")
    def test_secret_signing_fingerprints_only_returns_signing_subkeys(self, run):
        run.return_value.stdout = (
            "sec:u: rsa:4096:1:2:3:u:::scSC::::::23::0:\n"
            f"fpr:::::::::{PRIMARY}:\n"
            "ssb:u: rsa:4096:1:2:3:::::s::::::23:\n"
            f"fpr:::::::::{SUBKEY}:\n"
            "ssb:u: rsa:4096:1:2:3:::::e::::::23:\n"
            f"fpr:::::::::{'C' * 40}:\n"
        )
        self.assertEqual(_secret_signing_fingerprints(Path("gnupg")), {SUBKEY})

    @patch("cambonos_lib.signing._gpg")
    def test_sign_file_creates_detached_signature_and_verifies(self, gpg):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "sample.pkg.tar.zst"
            archive.write_bytes(b"payload")
            def sign(args, _home, *_optional):
                if "--detach-sign" in args:
                    Path(args[args.index("--output") + 1]).write_bytes(b"signature")
            gpg.side_effect = sign
            signature = _sign_file(archive, SUBKEY, Path(temporary), Path(temporary) / "pass")
            self.assertEqual(signature.read_bytes(), b"signature")
            self.assertEqual(gpg.call_count, 2)
            self.assertIn("--verify", gpg.call_args_list[1].args[0])

    def test_sign_file_rejects_missing_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(CambonosError):
                _sign_file(Path(temporary) / "missing", SUBKEY, Path(temporary), Path(temporary) / "pass")

    def test_materialize_aliases_requires_signed_database_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            with self.assertRaises(CambonosError):
                _materialize_and_sign_aliases(repository, "cambonos")

    @patch("cambonos_lib.signing.validate_version_policy")
    def test_source_policy_calls_each_channel_separately(self, validate):
        manifests = {
            "stable": {"packages": {"a": {}}},
            "testing": {"packages": {"b": {}}},
        }
        validate_source_version_policy(manifests, {"channels": {}}, "image")
        self.assertEqual(validate.call_count, 2)
        self.assertEqual(validate.call_args_list[0].args[2], "stable")
        self.assertEqual(validate.call_args_list[1].args[2], "testing")

    @patch("cambonos_lib.signing.require_commands")
    @patch("cambonos_lib.signing.verify_build_manifest")
    @patch("cambonos_lib.signing._fingerprints", return_value=(set(), {SUBKEY}, {SUBKEY: PRIMARY}))
    @patch("cambonos_lib.signing.verify_previous_manifest_signature")
    @patch("cambonos_lib.signing.load_previous_manifest", return_value={"channels": {}})
    @patch("cambonos_lib.signing.validate_source_version_policy", side_effect=CambonosError("source policy rejected"))
    @patch("cambonos_lib.signing._gpg")
    def test_source_policy_failure_happens_before_private_key_import(
        self, gpg, _policy, _load, _verify_signature, _fingerprints_mock, verify_build,
        _require,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            testing = root / "testing"; stable = root / "stable"
            for channel_root, channel, branch, commit in (
                (testing, "testing", "dev", "d" * 40),
                (stable, "stable", "main", "m" * 40),
            ):
                (channel_root / "packages").mkdir(parents=True)
                material = channel_root / "keyring-material"; material.mkdir()
                (material / "cambonos.gpg").write_bytes(b"public key")
                (material / "cambonos-trusted").write_text(f"{PRIMARY}:6:\n")
                (material / "cambonos-revoked").write_text("")
            def build_manifest(path, _package_dir):
                channel = path.parent.name
                branch = "dev" if channel == "testing" else "main"
                commit = "d" * 40 if channel == "testing" else "m" * 40
                return {
                    "channel": channel, "branch": branch, "commit": commit,
                    "architecture": "x86_64", "image": "arch-image",
                    "packages": {"cambonos-keyring": {}},
                }
            verify_build.side_effect = build_manifest
            previous = root / "previous.json"; previous.write_text("{}")
            previous_sig = root / "previous.json.sig"; previous_sig.write_bytes(b"sig")
            output = root / "site"; output.mkdir()
            sentinel = output / "keep.txt"; sentinel.write_text("must remain on preflight failure")
            with self.assertRaisesRegex(CambonosError, "source policy rejected"):
                sign_and_create_site(
                    testing, stable, output, "PRIVATE KEY", "passphrase", SUBKEY,
                    "arch-image", "d" * 40, "m" * 40, "https://example.invalid",
                    previous, previous_sig,
                )
            gpg.assert_not_called()
            self.assertEqual(sentinel.read_text(), "must remain on preflight failure")


if __name__ == "__main__":
    unittest.main()
