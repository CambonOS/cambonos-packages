from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.cambonos_lib.site import write_site_metadata


class SiteExternalSourceManifestTests(unittest.TestCase):
    def test_global_manifest_records_external_snapshots_per_channel(self):
        installer_testing = "a" * 40
        installer_stable = "b" * 40
        mkiso_testing = "c" * 40
        mkiso_stable = "d" * 40
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            channels = {}
            for channel, branch, commit in (
                ("testing", "dev", "1" * 40),
                ("stable", "main", "2" * 40),
            ):
                channels[channel] = {
                    "branch": branch,
                    "commit": commit,
                    "packages": {},
                    "build_environment": {},
                    "image": "arch-image",
                    "external_sources": {
                        "cambonos-installer": {
                            "repository": "CambonOS/cambonos-installer",
                            "testing": {"branch": "dev", "commit": installer_testing},
                            "stable": {"branch": "main", "commit": installer_stable},
                        },
                        "cambonos-mkiso": {
                            "repository": "CambonOS/cambonos-mkiso",
                            "testing": {"branch": "dev", "commit": mkiso_testing},
                            "stable": {"branch": "main", "commit": mkiso_stable},
                        },
                    },
                }
            with patch("scripts.cambonos_lib.site.write_index"):
                write_site_metadata(site, channels, "https://example.invalid/pages")
            manifest = json.loads((site / "metadata/manifest.json").read_text())
            self.assertEqual(
                manifest["channels"]["testing"]["external_sources"]["cambonos-installer"]["testing"]["commit"],
                installer_testing,
            )
            self.assertEqual(
                manifest["channels"]["stable"]["external_sources"]["cambonos-mkiso"]["stable"]["commit"],
                mkiso_stable,
            )


if __name__ == "__main__":
    unittest.main()
