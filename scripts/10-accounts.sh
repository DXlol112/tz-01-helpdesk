#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Запусти через sudo"; exit 1; }
getent group helpdesk >/dev/null || groupadd --system helpdesk
for group in helpdesk-dev helpdesk-support helpdesk-logs; do
  getent group "$group" >/dev/null || groupadd "$group"
done
id helpdesk >/dev/null 2>&1 || useradd --system --gid helpdesk --home-dir /var/lib/helpdesk --no-create-home --shell /usr/sbin/nologin helpdesk
for account in ivanov petrova smirnova; do
  id "$account" >/dev/null 2>&1 || useradd --create-home --user-group --shell /bin/bash "$account"
done
usermod -aG helpdesk-dev,helpdesk-logs ivanov
usermod -aG helpdesk-dev,helpdesk-logs petrova
usermod -aG helpdesk-support,helpdesk-logs smirnova
passwd ivanov
passwd petrova
passwd smirnova
