#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Запусти через sudo"; exit 1; }
mapfile -t HELPDESK_OLD_PIDS < <(pgrep -f '[h]elpdesk-2[.]3/bin/helpdesk-api' || true)
for pid in "${HELPDESK_OLD_PIDS[@]}"; do kill -TERM "$pid"; done
for attempt in {1..10}; do
  if ! pgrep -f '[h]elpdesk-2[.]3/bin/helpdesk-api' >/dev/null; then break; fi
  sleep 1
done
if pgrep -f '[h]elpdesk-2[.]3/bin/helpdesk-api' >/dev/null; then
  echo 'Не удалось остановить версию 2.3' >&2
  exit 1
fi
if ! sudo -u helpdesk /usr/local/bin/helpdesk-ctl status >/dev/null 2>&1; then
  sudo -u helpdesk /usr/local/bin/helpdesk-ctl start
fi
sudo -u helpdesk /usr/local/bin/helpdesk-ctl status
HELPDESK_PID=$(cat /run/helpdesk/api.pid)
test "$(ps -o user= -p "$HELPDESK_PID" | xargs)" = helpdesk
grep -Eq '^Umask:[[:space:]]*0027$' "/proc/$HELPDESK_PID/status"
