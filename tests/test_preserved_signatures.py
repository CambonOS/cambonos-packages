from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.cambonos_lib.common import CambonosError
from scripts.cambonos_lib.signing import _verify_preserved_package_signature


class PreservedSignatureTests(unittest.TestCase):
    def test_valid_preserved_signature_is_accepted_without_resigning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "pkg.pkg.tar.zst"
            signature = root / "pkg.pkg.tar.zst.sig"
            archive.write_bytes(b"package")
            signature.write_bytes(b"original-signature")
            digest = hashlib.sha256(signature.read_bytes()).hexdigest()
            result = subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout="[GNUPG:] VALIDSIG ABCDEF0123456789 20261111 1 0 4 0 1 10 00\\n",
                stderr="",
            )
            with patch("scripts.cambonos_lib.signing.subprocess.run", return_value=result) as run:
                _verify_preserved_package_signature(
                    archive, signature, "ABCDEF0123456789", root / "gnupg", digest
                )
            self.assertEqual(run.call_count, 1)
            self.assertIn("--verify", run.call_args.args[0])

    def test_wrong_signer_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "pkg.pkg.tar.zst"
            signature = root / "pkg.pkg.tar.zst.sig"
            archive.write_bytes(b"package")
            signature.write_bytes(b"signature")
            digest = hashlib.sha256(signature.read_bytes()).hexdigest()
            result = subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout="[GNUPG:] VALIDSIG BADF00D 20261111 1 0 4 0 1 10 00\\n",
                stderr="",
            )
            with patch("scripts.cambonos_lib.signing.subprocess.run", return_value=result):
                with self.assertRaisesRegex(CambonosError, "no procede de la subclave"):
                    _verify_preserved_package_signature(
                        archive, signature, "ABCDEF0123456789", root / "gnupg", digest
                    )

    def test_modified_preserved_signature_is_rejected_before_gpg(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "pkg.pkg.tar.zst"
            signature = root / "pkg.pkg.tar.zst.sig"
            archive.write_bytes(b"package")
            signature.write_bytes(b"modified")
            with patch("scripts.cambonos_lib.signing.subprocess.run") as run:
                with self.assertRaisesRegex(CambonosError, "SHA-256"):
                    _verify_preserved_package_signature(
                        archive, signature, "ABCDEF0123456789", root / "gnupg", "0" * 64
                    )
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
