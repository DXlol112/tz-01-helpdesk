#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo 'Запусти через sudo'; exit 1; }
sed -i 's/^UMASK=.*/UMASK=0027/' /etc/helpdesk/helpdesk.conf
chown root:helpdesk-dev /etc/helpdesk/helpdesk.conf
chmod 0640 /etc/helpdesk/helpdesk.conf
setfacl -m u:helpdesk:--x /etc/helpdesk /srv/helpdesk
setfacl -m u:helpdesk:r-- /etc/helpdesk/helpdesk.conf

find /srv/helpdesk/static -type d -exec chown root:helpdesk-dev {} +
find /srv/helpdesk/static -type f -exec chown root:helpdesk-dev {} +
find /srv/helpdesk/static -type d -exec chmod 2770 {} +
find /srv/helpdesk/static -type f -exec chmod 0660 {} +
find /srv/helpdesk/static -type d -exec setfacl -m 'u:helpdesk:r-x,m::rwx,d:u::rwx,d:u:helpdesk:r-x,d:g::rwx,d:m::rwx,d:o::---' {} +
find /srv/helpdesk/static -type f -exec setfacl -m 'u:helpdesk:r--,m::rw-' {} +
