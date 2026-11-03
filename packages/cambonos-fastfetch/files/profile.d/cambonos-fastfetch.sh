# CambonOS Fastfetch: login shells only.
# Loaded by /etc/profile on Arch Linux; do not run in non-interactive shells.
case $- in
  *i*) ;;
  *) return 0 ;;
esac

# Set CAMBONOS_NO_FASTFETCH in the environment before starting the shell to opt out.
if [ -n "${CAMBONOS_NO_FASTFETCH:-}" ]; then
  return 0
fi

if [ ! -x /usr/bin/cambonos-fastfetch ]; then
  return 0
fi

/usr/bin/cambonos-fastfetch
