"""Behavioral contracts for the packages shipped by CambonOS.

These tests describe the package's purpose and required deliverables. They must
not freeze implementation details such as helper names, hook filenames, shell
block markers, or the exact way a PKGBUILD installs a file.
"""
from __future__ import annotations

import configparser
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"

# Required deliverables are expressed as package capabilities, not as a full
# inventory of implementation files. Optional integrations remain optional.
REQUIRED_PAYLOADS = {
    "cambonos-branding": (
        "files/cambonos-icon.svg", "files/cambonos-text.svg",
        "files/cambonos-icon.png", "files/cambonos-text.png",
    ),
    "cambonos-fastfetch": (
        "files/cambonos/fastfetch/config.jsonc",
        "files/cambonos/fastfetch/logo.txt",
    ),
    "cambonos-grub": (
        "files/defaults/60-cambonos.cfg",
        "files/themes/CambonOS/theme.txt",
    ),
    "cambonos-gtk-theme": (
        "files/src/palette.json",
        "files/themes/CambonOS-dark/index.theme",
        "files/themes/CambonOS-dark/gtk-3.0/gtk.css",
        "files/themes/CambonOS-dark/gtk-4.0/gtk.css",
    ),
    "cambonos-keyring": (
        "files/cambonos.gpg", "files/cambonos-trusted", "files/cambonos-revoked",
    ),
    "cambonos-lightdm": (
        "files/lightdm/50-cambonos.conf",
        "files/slick-greeter/slick-greeter.conf",
    ),
    "cambonos-pacman": (
        "files/cambonos.conf", "files/cambonos-options.conf",
    ),
    "cambonos-plymouth": (
        "files/themes/cambonos/cambonos.plymouth",
        "files/themes/cambonos/cambonos.script",
        "files/themes/cambonos/cambonos-icon.png",
        "files/themes/cambonos/plymouth-background.png",
        "files/themes/cambonos/progress-background.png",
        "files/themes/cambonos/progress-foreground.png",
        "files/mkinitcpio/90-cambonos-plymouth.conf",
    ),
    "cambonos-release": (
        "files/cambonos/os-release", "files/cambonos/lsb-release",
    ),
    "cambonos-shell-prompt": (
        "files/starship.toml", "files/starship-tty.toml",
        "files/cambonos/bin/cambonos-starship-directory",
        "files/bash/cambonos-shell-prompt.bash",
        "files/fish/cambonos-shell-prompt.fish",
    ),
    "cambonos-zsh": (
        "files/etc/skel/.zshrc", "files/zsh/conf.d/10-completion.zsh",
    ),
    "cambonos-base": (),
    "cambonos-graphical-base": (
        "files/bin/cambonos-configure-nsswitch",
        "files/bin/cambonos-enable-services",
        "files/libalpm/hooks/cambonos-nsswitch.hook",
        "files/xdg/autostart/cambonos-thunar-daemon.desktop",
        "files/xdg/autostart/cambonos-polkit-agent.desktop",
        "files/xfconf/xfce-perchannel-xml/thunar-volman.xml",
    ),
}


class PackageContractTests(unittest.TestCase):
    def package_dirs(self):
        return sorted(p for p in PACKAGES.iterdir() if p.is_dir() and (p / "PKGBUILD").is_file())

    def test_every_local_package_has_basic_metadata_and_documentation(self):
        dirs = self.package_dirs()
        self.assertTrue(dirs, "No se han descubierto paquetes")
        for package in dirs:
            with self.subTest(package=package.name):
                self.assertTrue((package / "README.md").is_file(), "Falta README del paquete")
                text = (package / "PKGBUILD").read_text(encoding="utf-8")
                for field in ("pkgname", "pkgver", "pkgrel", "arch"):
                    self.assertRegex(text, rf"(?m)^{field}=", f"Falta {field} en PKGBUILD")
                self.assertRegex(text, rf"(?m)^pkgname={re.escape(package.name)}$")

    def test_each_package_contains_the_deliverables_for_its_purpose(self):
        for name, paths in REQUIRED_PAYLOADS.items():
            package = PACKAGES / name
            with self.subTest(package=name):
                self.assertTrue((package / "PKGBUILD").is_file())
                for relative in paths:
                    self.assertTrue((package / relative).is_file(), f"Falta {relative}")

    def test_graphical_base_declares_the_shared_desktop_stack(self):
        text = (PACKAGES / "cambonos-graphical-base" / "PKGBUILD").read_text(encoding="utf-8")
        for dependency in (
            "avahi", "bash", "bluez", "bluez-utils", "blueman", "coreutils",
            "dbus", "desktop-file-utils", "dex", "file-roller", "gawk", "gvfs",
            "gvfs-afc", "gvfs-dnssd", "gvfs-gphoto2", "gvfs-mtp", "gvfs-nfs",
            "gvfs-smb", "gvfs-wsdd", "network-manager-applet", "networkmanager",
            "nss-mdns", "pavucontrol", "pipewire", "pipewire-audio", "pipewire-alsa",
            "pipewire-jack", "pipewire-pulse", "polkit-gnome", "shared-mime-info",
            "sof-firmware", "systemd", "thunar", "thunar-archive-plugin", "thunar-volman",
            "tumbler", "udisks2", "upower", "wireplumber", "xf86-input-libinput",
            "xfconf", "xorg-server", "xorg-xinput", "xorg-xrandr", "xdg-desktop-portal",
            "xdg-desktop-portal-gtk", "xdg-user-dirs", "xdg-utils",
        ):
            with self.subTest(dependency=dependency):
                self.assertRegex(text, rf"(?m)^[ \t]+'{re.escape(dependency)}'$")

    def test_graphical_base_nss_configuration_is_idempotent(self):
        package = PACKAGES / "cambonos-graphical-base"
        script = package / "files/bin/cambonos-configure-nsswitch"
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "nsswitch.conf"
            original = """passwd: files systemd
group: files systemd
hosts: mymachines resolve [!UNAVAIL=return] files myhostname dns
"""
            config.write_text(original, encoding="utf-8")

            first = subprocess.run(
                ["bash", str(script), str(config)], capture_output=True, text=True, check=False
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            expected = "hosts: mymachines mdns_minimal [NOTFOUND=return] resolve [!UNAVAIL=return] files myhostname dns"
            self.assertIn(expected, config.read_text(encoding="utf-8"))
            updated = config.read_bytes()

            second = subprocess.run(
                ["bash", str(script), str(config)], capture_output=True, text=True, check=False
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(config.read_bytes(), updated)

    def test_graphical_base_nss_configuration_fails_closed_without_mymachines(self):
        package = PACKAGES / "cambonos-graphical-base"
        script = package / "files/bin/cambonos-configure-nsswitch"
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "nsswitch.conf"
            original = "hosts: files resolve dns\n"
            config.write_text(original, encoding="utf-8")
            result = subprocess.run(
                ["bash", str(script), str(config)], capture_output=True, text=True, check=False
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_base_metapackage_depends_on_all_core_components(self):
        text = (PACKAGES / "cambonos-base" / "PKGBUILD").read_text(encoding="utf-8")
        # A metapackage must install the core experience through dependencies;
        # do not prescribe how those dependencies are declared in Bash.
        for name in (
            "cambonos-keyring", "cambonos-pacman", "cambonos-release",
            "cambonos-branding", "cambonos-fastfetch",
            "cambonos-shell-prompt", "cambonos-zsh",
        ):
            self.assertIn(name, text)

    def test_metapackage_does_not_ship_payload(self):
        package = PACKAGES / "cambonos-base"
        files = [p for p in package.rglob("*") if p.is_file() and p.name not in {"PKGBUILD", "README.md"}]
        self.assertEqual(files, [], "cambonos-base debe seguir siendo un metapaquete")

    def test_keyring_contains_public_trust_material(self):
        keyring = PACKAGES / "cambonos-keyring" / "files"
        for name in ("cambonos.gpg", "cambonos-trusted", "cambonos-revoked"):
            self.assertTrue((keyring / name).is_file())
        self.assertGreater((keyring / "cambonos.gpg").stat().st_size, 0)

    def test_repository_configuration_requires_signature_verification(self):
        package = PACKAGES / "cambonos-pacman"
        configs = "\n".join(p.read_text(encoding="utf-8") for p in (package / "files").glob("*.conf"))
        self.assertRegex(configs, r"(?im)^\s*SigLevel\s*=.*(Required|PackageRequired)")

    def test_release_metadata_identifies_cambonos(self):
        release = PACKAGES / "cambonos-release" / "files/cambonos/os-release"
        content = release.read_text(encoding="utf-8")
        self.assertRegex(content, r"(?m)^ID=cambonos$")
        self.assertRegex(content, r"(?m)^NAME=.*CambonOS")

    def test_gtk_theme_has_a_single_declared_theme_identity(self):
        theme = PACKAGES / "cambonos-gtk-theme/files/themes/CambonOS-dark/index.theme"
        self.assertIn("CambonOS-dark", theme.read_text(encoding="utf-8"))

    def test_branding_identity_assets_are_well_formed(self):
        import xml.etree.ElementTree as ET
        package = PACKAGES / "cambonos-branding" / "files"
        for asset in ("cambonos-icon.svg", "cambonos-text.svg"):
            with self.subTest(asset=asset):
                ET.parse(package / asset)

    def test_lightdm_configuration_is_parseable_and_selects_a_greeter(self):
        package = PACKAGES / "cambonos-lightdm" / "files"
        parser = configparser.ConfigParser()
        parser.read(package / "lightdm/50-cambonos.conf", encoding="utf-8")
        self.assertIn("Seat:*", parser)
        self.assertTrue(parser["Seat:*"].get("greeter-session"))

    def test_plymouth_theme_declares_its_script_module(self):
        package = PACKAGES / "cambonos-plymouth"
        theme = package / "files/themes/cambonos/cambonos.plymouth"
        parser = configparser.ConfigParser()
        parser.read(theme, encoding="utf-8")
        self.assertEqual(parser["Plymouth Theme"].get("ModuleName"), "script")
        self.assertTrue(parser["script"].get("ScriptFile"))
        self.assertEqual(parser["script"].get("ImageDir"), "/usr/share/plymouth/themes/cambonos")

        script = package / "files/themes/cambonos/cambonos.script"
        theme_dir = theme.parent
        for image in re.findall(r'Image\("([^"]+\.png)"\)', script.read_text(encoding="utf-8")):
            with self.subTest(image=image):
                self.assertTrue((theme_dir / image).is_file(), f"Falta el recurso Plymouth {image}")

    def test_plymouth_does_not_depend_on_branding_assets(self):
        branding = PACKAGES / "cambonos-branding"
        plymouth = PACKAGES / "cambonos-plymouth"
        for resource in (
            "plymouth-background.png",
            "progress-background.png.base64",
            "progress-foreground.png.base64",
        ):
            with self.subTest(resource=resource):
                self.assertFalse((branding / "files" / resource).exists())
        self.assertNotIn("cambonos-branding", (plymouth / "PKGBUILD").read_text(encoding="utf-8"))

    def test_plymouth_package_installs_all_theme_images(self):
        package = PACKAGES / "cambonos-plymouth"
        with tempfile.TemporaryDirectory() as temp_dir:
            pkgdir = Path(temp_dir) / "pkg"
            pkgdir.mkdir()
            env = os.environ.copy()
            env.update({"pkgdir": str(pkgdir), "startdir": str(package)})
            subprocess.run(
                ["bash", "-c", 'source "$startdir/PKGBUILD" && package'],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )

            installed_theme = pkgdir / "usr/share/plymouth/themes/cambonos"
            for image in (
                "cambonos-icon.png",
                "plymouth-background.png",
                "progress-background.png",
                "progress-foreground.png",
            ):
                with self.subTest(image=image):
                    self.assertTrue((installed_theme / image).is_file())

    def test_shell_prompt_configuration_is_valid_toml(self):
        package = PACKAGES / "cambonos-shell-prompt/files"
        for filename in ("starship.toml", "starship-tty.toml"):
            with self.subTest(filename=filename):
                config = tomllib.loads((package / filename).read_text(encoding="utf-8"))
                self.assertIn("palettes", config)
                self.assertIn("cambonos", config["palettes"])
                self.assertIn("$character", config["format"])
                self.assertEqual(config["right_format"].strip(), "$status$jobs$cmd_duration")

    def test_shell_integrations_select_console_profile_only_on_virtual_ttys(self):
        package = PACKAGES / "cambonos-shell-prompt/files"
        shells = [
            (
                "bash",
                ["bash", "--noprofile", "--norc", "-ic"],
                'printf \'%s\\n\' "$STARSHIP_CONFIG"',
                package / "bash/cambonos-shell-prompt.bash",
            ),
        ]
        zsh = shutil.which("zsh")
        if zsh:
            shells.append(("zsh", [zsh, "-f", "-i", "-c"], 'print -r -- "$STARSHIP_CONFIG"', package / "zsh/conf.d/50-shell-prompt.zsh"))
        fish = shutil.which("fish")
        if fish:
            shells.append(("fish", [fish, "--no-config", "-i", "-c"], 'printf \'%s\\n\' "$STARSHIP_CONFIG"', package / "fish/cambonos-shell-prompt.fish"))

        with tempfile.TemporaryDirectory() as temp_dir:
            bin_dir = Path(temp_dir) / "bin"
            bin_dir.mkdir()
            tty = bin_dir / "tty"
            tty.write_text('#!/bin/sh\nprintf \'%s\\n\' "$MOCK_TTY"\n', encoding="utf-8")
            starship = bin_dir / "starship"
            starship.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            tty.chmod(0o755)
            starship.chmod(0o755)
            xdg_config = Path(temp_dir) / "xdg"
            user_config = xdg_config / "starship.toml"
            user_config.parent.mkdir()
            user_config.write_text("", encoding="utf-8")

            cases = (
                ("/dev/tty2", "/usr/share/cambonos/shell-prompt/starship-tty.toml", "default"),
                ("/dev/pts/3", "/usr/share/cambonos/shell-prompt/starship.toml", "default"),
                ("/dev/tty2", "/tmp/user-starship.toml", "explicit"),
                ("/dev/tty2", "", "user"),
            )
            for shell_name, command, print_config, integration in shells:
                for device, configured_path, config_kind in cases:
                    with self.subTest(shell=shell_name, device=device, config=config_kind):
                        env = os.environ.copy()
                        env.update({
                            "HOME": temp_dir,
                            "XDG_CONFIG_HOME": str(Path(temp_dir) / "missing-xdg"),
                            "MOCK_TTY": device,
                            "PATH": f"{bin_dir}:{env['PATH']}",
                        })
                        env.pop("STARSHIP_CONFIG", None)
                        if config_kind == "explicit":
                            env["STARSHIP_CONFIG"] = configured_path
                        elif config_kind == "user":
                            env["XDG_CONFIG_HOME"] = str(xdg_config)
                        shell_command = (
                            f"source {shlex.quote(str(integration))}; {print_config}"
                        )
                        result = subprocess.run(
                            [*command, shell_command],
                            env=env,
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        actual_config = result.stdout.strip().splitlines()
                        self.assertEqual(actual_config[-1] if actual_config else "", configured_path)

    def test_starship_directory_preserves_emulator_output_and_supports_tty(self):
        helper = PACKAGES / "cambonos-shell-prompt/files/cambonos/bin/cambonos-starship-directory"
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["HOME"] = "/nonexistent"
            outputs = {}
            for mode, args in (("emulator", []), ("tty", ["--tty"])):
                result = subprocess.run(
                    [str(helper), *args],
                    cwd=temp_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs[mode] = result.stdout

            self.assertIn("", outputs["emulator"])
            self.assertIn("\x1b[38;2;112;231;230m", outputs["emulator"])
            self.assertIn("dir\x1b[0m ", outputs["tty"])
            self.assertIn("\x1b[94m", outputs["tty"])
            self.assertNotIn("\x1b[38;2;", outputs["tty"])
            self.assertTrue(all(ord(character) < 128 for character in outputs["tty"]))

    def test_zsh_package_provides_its_core_shell_configuration(self):
        package = PACKAGES / "cambonos-zsh/files/zsh/conf.d"
        for fragment in ("10-completion.zsh", "20-keybindings.zsh", "30-history.zsh"):
            with self.subTest(fragment=fragment):
                self.assertTrue((package / fragment).is_file())


if __name__ == "__main__":
    unittest.main()
