# Разработчик 2 — файлы, права и запуск службы

Выполняй шаги по порядку в своей ВМ Ubuntu 24.04 со снимком VirtualBox. Первый разработчик параллельно делает [пользователей, sudo и provision.sh](01-developer-1.md). Свои команды, ошибки и результаты передавай ему для `runbook.md`.

## 1. Подготовить стенд и ветку

```bash
sudo apt update
sudo apt install -y git wget acl nano
mkdir -p ~/projects ~/Downloads
cd ~/projects
git clone https://github.com/DXlol112/tz-01-helpdesk.git
cd tz-01-helpdesk
git switch -c codex/part-2
mkdir -p scripts screenshots

HELPDESK_MATERIALS=https://algorthimization-course-vvodnoe.vercel.app/op05-operacionnye-sistemy-i-sredy/proekty/ekspluataciya-servera/materials
wget -O ~/Downloads/helpdesk-stand.sh "$HELPDESK_MATERIALS/helpdesk-stand.sh"
wget -O ~/Downloads/helpdesk-acceptance.sh "$HELPDESK_MATERIALS/helpdesk-acceptance.sh"
sudo bash ~/Downloads/helpdesk-stand.sh
ls -lR /tmp/helpdesk-release-2.4.1
less /tmp/helpdesk-release-2.4.1/bin/helpdesk-api
less /tmp/helpdesk-release-2.4.1/bin/helpdesk-ctl
```

Если клон уже есть, используй его. Не выводи содержимое `secrets.env`. Пока первый готовит пользователей, изучи релиз и напиши следующие модули.

## 2. Получить пользователей от первого

После публикации его модуля:

```bash
git fetch origin
git show origin/codex/part-1:scripts/10-accounts.sh > /tmp/helpdesk-accounts.sh
less /tmp/helpdesk-accounts.sh
sudo bash /tmp/helpdesk-accounts.sh
```

Временную копию не добавляй в свой PR.

## 3. Создать scripts/20-layout.sh

Начинай каждый модуль с:

```bash
#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo 'Запусти через sudo'; exit 1; }
```

В `20-layout.sh` после заголовка добавь:

```bash
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
```

Релиз из `/tmp` пока сохраняется. Его удалит общий скрипт после успешного запуска.

## 4. Создать scripts/30-access.sh

После стандартного заголовка запиши:

```bash
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
```

Setgid сохраняет группу новых файлов, default ACL даёт второму разработчику запись. Служба получает только чтение static. Маска `0027` закрывает запись группе и весь доступ остальным у новых файлов службы.

```bash
bash -n scripts/20-layout.sh
bash -n scripts/30-access.sh
sudo bash scripts/20-layout.sh
sudo bash scripts/30-access.sh
```

## 5. Проверить доступ и записать матрицу

```bash
sudo -u ivanov sh -c 'umask 0077; echo ivanov > /srv/helpdesk/static/test.txt'
sudo -u petrova sh -c 'echo petrova >> /srv/helpdesk/static/test.txt'
sudo -u helpdesk cat /srv/helpdesk/static/test.txt
sudo -u helpdesk test ! -w /srv/helpdesk/static/test.txt
sudo -u petrova rm /srv/helpdesk/static/test.txt

for account in ivanov petrova smirnova; do
  sudo -u "$account" test ! -r /etc/helpdesk/secrets.env
  sudo -u "$account" test ! -x /var/lib/helpdesk
  sudo -u "$account" test -r /var/log/helpdesk/api.log
  sudo -u "$account" test ! -w /var/log/helpdesk/api.log
  sudo -u "$account" test ! -w /var/log/helpdesk
done
sudo -u nobody test ! -r /var/log/helpdesk/api.log
sudo -u nobody test ! -r /etc/helpdesk/helpdesk.conf
sudo stat -c '%A %a %U:%G %n' /etc/helpdesk/* /var/lib/helpdesk /var/log/helpdesk/api.log /srv/helpdesk/static
sudo getfacl -p /etc/helpdesk /etc/helpdesk/helpdesk.conf /srv/helpdesk/static
nano access-matrix.md
```

В матрице для каждого ресурса укажи фактический `stat`, ACL, команду и результат от имени каждой роли. Проверь и оставшиеся клетки:

| Ресурс | helpdesk | ivanov / petrova | smirnova | остальные |
| --- | --- | --- | --- | --- |
| helpdesk.conf | Чтение | Чтение | Нет | Нет |
| secrets.env | Чтение | Нет | Нет | Нет |
| Данные | Чтение/запись | Нет | Нет | Нет |
| Журналы | Запись и диагностика | Чтение | Чтение | Нет |
| Static | Чтение | Чтение/запись | Нет | Нет |

Для проверки используй `sudo -u ИМЯ test -r ПУТЬ`, `test -w`, `test -x`; для запрета — `test ! -r` и аналогично. Проверь совместную запись в обратную сторону и во вложенном новом каталоге. Запрет не считается проверенным, если сам пользователь или файл отсутствует.

## 6. Зафиксировать отказ запуска

Пока старая 2.3 работает:

```bash
sudo -u helpdesk /usr/local/bin/helpdesk-ctl start
sudo tail -n 5 /var/log/helpdesk/api.log
pgrep -af '[h]elpdesk-2[.]3/bin/helpdesk-api'
```

Ожидается отказ из-за работающей 2.3. Если причина другая, разбери фактическое сообщение. Передай первому команду, результат и исправление; сохрани настоящий снимок как `screenshots/01-start-failure.png`. Права ради запуска не расширяй.

## 7. Создать scripts/50-service.sh

После стандартного заголовка добавь:

```bash
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
sudo -u helpdesk /usr/local/bin/helpdesk-ctl start
sudo -u helpdesk /usr/local/bin/helpdesk-ctl status
HELPDESK_PID=$(cat /run/helpdesk/api.pid)
test "$(ps -o user= -p "$HELPDESK_PID" | xargs)" = helpdesk
grep -Eq '^Umask:[[:space:]]*0027$' "/proc/$HELPDESK_PID/status"
```

Останавливай только старый процесс; файлы 2.3 не меняй. В финальном модуле отказ намеренно не повторяется.

```bash
bash -n scripts/50-service.sh
sudo bash scripts/50-service.sh
git add scripts/20-layout.sh scripts/30-access.sh scripts/50-service.sh access-matrix.md screenshots/01-start-failure.png
git commit -m "feat: install helpdesk files, permissions and service"
git push -u origin codex/part-2
```

Открой на GitHub PR `codex/part-2` → `main`; укажи требования 2.2–2.4 и зависимость от пользователей первого.

## 8. Проверить PR первого и общий проект

После публикации обоих PR:

```bash
git fetch origin
git switch -c codex/check-2 origin/main
git merge --no-edit origin/codex/part-1
git merge --no-edit origin/codex/part-2
sudo bash ~/Downloads/helpdesk-stand.sh
sudo bash provision.sh
sudo visudo -c
sudo -u ivanov sudo -l
sudo -u petrova sudo -n -u helpdesk /usr/local/bin/helpdesk-ctl status
```

Оба разработчика должны выполнять ctl без пароля; shell от helpdesk, root и управление для поддержки должны быть запрещены:

```bash
sudo -u ivanov sudo -n -u helpdesk /bin/bash -c true
sudo -u petrova sudo -n -u root /usr/bin/id
sudo -u smirnova sudo -n -u helpdesk /usr/local/bin/helpdesk-ctl status
```

Последние три команды должны завершиться отказом именно от sudo. Повтори разрешения и запреты для обоих разработчиков, проверь UID/home/shell службы и пароли сотрудников. Оставь ревью в PR первого; исправления своей части отправляй в `codex/part-2`.

## 9. Пройти приёмку и завершить работу

```bash
set -o pipefail
sudo bash ~/Downloads/helpdesk-acceptance.sh 2>&1 | tee /tmp/helpdesk-acceptance-2.txt
grep -Fx 'Result: 25 of 25' /tmp/helpdesk-acceptance-2.txt
! grep -Eq '^[[:space:]]*FAIL[[:space:]]' /tmp/helpdesk-acceptance-2.txt
```

Сохрани снимок вывода как `screenshots/02-acceptance.png`. Если были ручные исправления, внеси их в модули и повтори стенд → provision → приёмку. Сверь фактическую матрицу после финального прогона.

Вернись в свою ветку, добавь снимок и обновлённую матрицу, затем отправь коммит в свой PR. Первый забирает записи для общего журнала. После взаимного ревью слейте PR первого, затем второго. Обнови `main` и повтори чистый прогон:

```bash
git switch main
git pull --ff-only
sudo bash ~/Downloads/helpdesk-stand.sh
sudo bash provision.sh
sudo bash ~/Downloads/helpdesk-acceptance.sh
```

Итог: 25/25, корректная полная матрица, скриншоты отказа и успеха. Подготовка до дня 2, PR до дня 7, ревью до дня 9, финальная проверка до дня 12, сдача в день 14. На сдаче оба объясняют свою часть и часть напарника.
