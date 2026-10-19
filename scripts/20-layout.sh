#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo 'Запусти через sudo'; exit 1; }
HELPDESK_RELEASE=/tmp/helpdesk-release-2.4.1
install -d -o root -g helpdesk-dev -m 0750 /etc/helpdesk /srv/helpdesk
install -d -o helpdesk -g helpdesk -m 0700 /var/lib/helpdesk /run/helpdesk
install -d -o root -g helpdesk-dev -m 2770 /srv/helpdesk/static
install -d -o helpdesk -g helpdesk-logs -m 2750 /var/log/helpdesk
for program in helpdesk-api helpdesk-ctl; do
  install -o root -g root -m 0755 "$HELPDESK_RELEASE/bin/$program" "/usr/local/bin/$program"
done
install -o root -g helpdesk-dev -m 0640 "$HELPDESK_RELEASE/conf/helpdesk.conf" /etc/helpdesk/helpdesk.conf
install -o helpdesk -g helpdesk -m 0400 "$HELPDESK_RELEASE/conf/secrets.env" /etc/helpdesk/secrets.env
install -o helpdesk -g helpdesk -m 0600 "$HELPDESK_RELEASE/data/tickets.db" /var/lib/helpdesk/tickets.db
cp -R "$HELPDESK_RELEASE/static/." /srv/helpdesk/static/
if [ ! -e /var/log/helpdesk/api.log ]; then
  install -o helpdesk -g helpdesk-logs -m 0640 /dev/null /var/log/helpdesk/api.log
fi
