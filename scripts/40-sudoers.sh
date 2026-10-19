#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Запусти через sudo"; exit 1; }
HELPDESK_EDITOR=$(mktemp /tmp/helpdesk-editor.XXXXXX)
trap 'rm -f -- "$HELPDESK_EDITOR"' EXIT
cat > "$HELPDESK_EDITOR" <<'EDITOR'
#!/bin/sh
# visudo может передать -- перед именем файла.
if [ "${1:-}" = -- ]; then shift; fi
printf '%s\n' '%helpdesk-dev ALL=(helpdesk) NOPASSWD: /usr/local/bin/helpdesk-ctl start, /usr/local/bin/helpdesk-ctl stop, /usr/local/bin/helpdesk-ctl status' > "$1"
EDITOR
chmod 0700 "$HELPDESK_EDITOR"
EDITOR="$HELPDESK_EDITOR" VISUAL="$HELPDESK_EDITOR" SUDO_EDITOR="$HELPDESK_EDITOR" visudo -f /etc/sudoers.d/helpdesk
chown root:root /etc/sudoers.d/helpdesk
chmod 0440 /etc/sudoers.d/helpdesk
visudo -c
