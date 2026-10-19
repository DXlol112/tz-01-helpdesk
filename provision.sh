#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo 'Запуск: sudo bash provision.sh'; exit 1; }
cd -- "$(dirname -- "$0")"
test -d /tmp/helpdesk-release-2.4.1
for module in 10-accounts 20-layout 30-access 40-sudoers 50-service; do
  test -f "scripts/$module.sh" || { echo "Нет scripts/$module.sh" >&2; exit 1; }
done
for module in 10-accounts 20-layout 30-access 40-sudoers 50-service; do
  bash "scripts/$module.sh"
done
sudo -u helpdesk /usr/local/bin/helpdesk-ctl status
rm -rf -- /tmp/helpdesk-release-2.4.1
test ! -e /tmp/helpdesk-release-2.4.1
