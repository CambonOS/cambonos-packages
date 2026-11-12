# CambonOS Package Versioning (CPV)

**Specification: CPV 1.0**

CPV is the versioning policy for packages maintained by CambonOS. It is
SemVer-inspired, but deliberately uses Arch Linux package fields directly.
It does not replace pacman's version model.

## Version format

Every CambonOS `PKGBUILD` must use:

```bash
pkgver=MAJOR.MINOR.PATCH
pkgrel=1
# epoch is omitted or set to 0 unless an exceptional Arch ordering repair is needed.
```

`pkgver` is exactly three non-negative decimal integers separated by dots.
Leading zeroes, additional components, and prerelease/build metadata are not
allowed. `pkgrel` is a positive integer. `epoch` is a non-negative integer.

The resulting Arch version is `[epoch:]pkgver-pkgrel`. All ordering decisions
must use pacman's `vercmp`; CPV must not substitute Python string or SemVer
ordering for Arch ordering.

## Change classification

Choose the highest applicable change class when a change contains more than
one kind of modification.

| Field | Increment when | Example |
|---|---|---|
| MAJOR | A breaking change, incompatible interface/configuration change, or substantial incompatible redesign | `1.4.2` -> `2.0.0` |
| MINOR | Any new feature or compatible functional capability/change, including new integrations, options, resources, or functional visual improvements | `1.4.2` -> `1.5.0` |
| PATCH | A fix to existing functionality or behavior, including visual bug fixes and corrections | `1.4.2` -> `1.4.3` |
| PKGREL | Packaging-only changes that do not change the package's functional behavior | `1.4.2-1` -> `1.4.2-2` |

When `pkgver` changes, `pkgrel` must reset to `1`. When only packaging changes,
`pkgver` remains unchanged and `pkgrel` increases. A functional change must
never be disguised as a `pkgrel` increment.

The MAJOR/MINOR/PATCH classification is a maintainer decision. Automation can
validate version shape, monotonic ordering, and `pkgrel` reset rules, but must
not infer feature significance from a source diff. Record the rationale in
the commit message or package changelog.

## Channels

`testing` and `stable` use the same CPV version. Channel identity is not encoded
in `pkgver` or `pkgrel`; do not add `alpha`, `beta`, `rc`, `dev`, or channel
suffixes. When a build is promoted from testing to stable, the exact same package
artifact must be promoted, identified by its SHA-256, rather than rebuilt.
The current repository pipeline builds the `dev/testing` and `main/stable`
snapshots independently; this CPV change does not redesign that workflow.
Therefore byte-identical cross-channel promotion remains a pipeline-level
requirement to implement separately, not a guarantee introduced by CPV alone.

## Artifact immutability

A published package name/version/architecture tuple identifies one immutable
binary artifact. Re-publishing the same version is allowed only when the
package SHA-256 is identical. A different binary requires a new CPV version.
Source changes under an unchanged version are rejected as well.

The publication manifest is the continuity record for each channel. A missing
previous package may be treated as a removal, but a package that remains
published cannot move backwards in Arch version order.

## Epoch

`epoch` is reserved for exceptional repairs to Arch version ordering. It is
not a release train, channel marker, or substitute for MAJOR. Do not add or
increase it during normal version increments.

## Scope and migration

CPV applies only to packages maintained in this repository. Third-party Arch
and AUR dependencies retain their upstream versioning schemes.

Existing published versions are not rewritten. The policy applies immediately
to all future package changes. Existing package versions are accepted as the
initial CPV baseline if they satisfy the numeric triplet format. Do not reset
a published `pkgrel` merely to make it look cleaner; the next `pkgver` change
starts at `pkgrel=1`.


## Initial CPV migration baseline

The immediate migration was applied against repository snapshot `e530c5d`
(11 November 2026). Existing versions were not mechanically reset. Packages
with functional changes recorded after their previous `pkgver` baseline were
reclassified under CPV; packaging-only metadata changes did not force a
functional version increment.

| Package | Previous version | CPV baseline | Classification |
|---|---:|---:|---|
| `cambonos-base` | `0.1.0-1` | `0.1.0-1` | Unchanged; metapackage baseline |
| `cambonos-branding` | `0.1.2-3` | `0.1.3-1` | PATCH: Dialog contrast correction |
| `cambonos-fastfetch` | `0.1.1-3` | `0.1.2-1` | PATCH: terminal ANSI color correction |
| `cambonos-grub` | `0.1.1-2` | `0.2.0-1` | MINOR: boot parameter behavior update |
| `cambonos-gtk-theme` | `0.6.2-12` | `0.7.0-1` | MINOR: widget styling and accessibility additions |
| `cambonos-keyring` | `0.1.0-5` | `0.1.0-5` | Unchanged; metadata-only changes |
| `cambonos-lightdm` | `0.1.0-5` | `0.2.0-1` | MINOR: CambonOS Slick Greeter theme integration |
| `cambonos-pacman` | `0.1.0-4` | `0.1.0-4` | Unchanged; dependency metadata correction |
| `cambonos-plymouth` | `0.1.1-9` | `0.2.0-1` | MINOR: resolution scaling and branding integration |
| `cambonos-release` | `0.1.1-3` | `0.1.2-1` | PATCH: os-release color correction |
| `cambonos-shell-prompt` | `0.1.0-9` | `0.2.0-1` | MINOR: custom directory prompt module |
| `cambonos-zsh` | `0.1.0-5` | `0.2.0-1` | MINOR: automatic sudo integration |

These are source-tree migration versions. Before publication, the publication
manifest must confirm that every proposed version is greater than the last
published version in its channel and that no published version is being
replaced. If a listed baseline version has already been published with a
different binary, the migration must be reconciled with that manifest rather
than bypassing the immutability rule.

## Examples

```bash
# New package
pkgver=0.1.0
pkgrel=1

# Functional bug fix
pkgver=0.1.1
pkgrel=1

# Compatible feature
pkgver=0.2.0
pkgrel=1

# Breaking change
pkgver=1.0.0
pkgrel=1

# Packaging-only correction after 1.0.0-1
pkgver=1.0.0
pkgrel=2
```
