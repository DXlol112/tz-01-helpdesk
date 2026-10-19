# Разработчик 1 — пользователи, sudo и общий скрипт

Выполняй шаги по порядку. Работайте на отдельных ВМ Ubuntu 24.04; перед стендом сделайте снимок VirtualBox. Второй разработчик параллельно выполняет [свою инструкцию](02-developer-2.md).

Каждую изменяющую сервер команду записывайте: время, участник, номер требования, команда, результат. Первый собирает записи обоих в `runbook.md`. Пароли и секреты в Git не добавляйте.

Шаблоны `README.md`, `server-passport.md`, `runbook.md`, `access-matrix.md` и `provision.sh` уже находятся в корне. Редактируй существующие файлы; `scripts/` и `screenshots/` создаются ниже. Все команды терминала выполняй из корня репозитория, содержимое модулей вставляй в указанные файлы через `nano`.

## 1. Подготовить репозиторий и стенд

Добавь напарника в [репозиторий](https://github.com/DXlol112/tz-01-helpdesk) → Settings → Collaborators, чтобы он мог делать push. Репозиторий публичный: просмотр и клонирование доступны без авторизации. Используй уже открытый клон; перед переключением веток закоммить свою работу. В своей ВМ:

```bash
sudo apt update
sudo apt install -y git wget ca-certificates acl nano
cd "$(git rev-parse --show-toplevel)"
git status --short
git fetch origin
git switch part-1
git pull --ff-only origin part-1
git merge --no-edit origin/main
mkdir -p scripts screenshots "$HOME/Downloads"

HELPDESK_MATERIALS=https://algorthimization-course-vvodnoe.vercel.app/op05-operacionnye-sistemy-i-sredy/proekty/ekspluataciya-servera/materials
wget -O ~/Downloads/helpdesk-stand.sh "$HELPDESK_MATERIALS/helpdesk-stand.sh"
wget -O ~/Downloads/helpdesk-acceptance.sh "$HELPDESK_MATERIALS/helpdesk-acceptance.sh"
sudo bash ~/Downloads/helpdesk-stand.sh
```

`part-1` уже существует. Если `git status --short` показывает изменения, сначала сохрани их коммитом. При конфликте слияния исправь указанные Git файлы, выполни `git add` для них и `git merge --continue`; затем продолжай. Стенд запускается только в учебной ВМ.

## 2. Сделать паспорт сервера до изменений

```bash
date --iso-8601=seconds
hostnamectl
cat /etc/os-release
df -hT
free -h
for account in helpdesk ivanov petrova smirnova; do id "$account" || true; done
getent group helpdesk helpdesk-dev helpdesk-support helpdesk-logs sudo || true
pgrep -af '[h]elpdesk-api'
ps -eo user,pid,args | grep '[h]elpdesk-api'
ls -lR /tmp/helpdesk-release-2.4.1
nano server-passport.md
```

Запиши команды и фактический вывод: ОС, разделы, пользователи/группы, процессы и владельцы, файлы релиза. Отсутствующие аккаунты тоже зафиксируй. Содержимое `secrets.env` не выводи.

## 3. Создать модуль пользователей

```bash
nano scripts/10-accounts.sh
```

В начале каждого модуля добавляй:

```bash
#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo 'Запусти через sudo'; exit 1; }
```

После заголовка в `10-accounts.sh` запиши:

```bash
getent group helpdesk >/dev/null || groupadd --system helpdesk
for group in helpdesk-dev helpdesk-support helpdesk-logs; do
  getent group "$group" >/dev/null || groupadd "$group"
done
useradd --system --gid helpdesk --home-dir /var/lib/helpdesk --no-create-home --shell /usr/sbin/nologin helpdesk
for account in ivanov petrova smirnova; do
  useradd --create-home --user-group --shell /bin/bash "$account"
done
usermod -aG helpdesk-dev,helpdesk-logs ivanov
usermod -aG helpdesk-dev,helpdesk-logs petrova
usermod -aG helpdesk-support,helpdesk-logs smirnova
passwd ivanov
passwd petrova
passwd smirnova
```

Модуль рассчитан на свежий стенд. Пароли вводятся при запуске. `helpdesk-logs` нужна обоим разработчикам и поддержке для чтения журналов. Службу в `helpdesk-dev` не добавляй.

```bash
bash -n scripts/10-accounts.sh
sudo bash scripts/10-accounts.sh
getent passwd helpdesk
id ivanov
id petrova
id smirnova
sudo passwd -S ivanov
sudo passwd -S petrova
sudo passwd -S smirnova

git add scripts/10-accounts.sh server-passport.md
git commit -m "feat: add helpdesk accounts and groups"
git push -u origin part-1
```

Проверь: UID службы меньше 1000, home `/var/lib/helpdesk`, shell `nologin`, у сотрудников пароль со статусом `P`, никто из них не в группе `sudo`. Сообщи второму: модуль пользователей доступен.

## 4. Сделать модуль sudo

Создай `scripts/40-sudoers.sh` с тем же заголовком. Добавь команды ниже: временный редактор позволяет установить правило через `visudo` без ручной правки при каждом запуске.

```bash
nano scripts/40-sudoers.sh
```

```bash
HELPDESK_EDITOR=$(mktemp /tmp/helpdesk-editor.XXXXXX)
trap 'rm -f -- "$HELPDESK_EDITOR"' EXIT
cat > "$HELPDESK_EDITOR" <<'EDITOR'
#!/bin/sh
printf '%s\n' '%helpdesk-dev ALL=(helpdesk) NOPASSWD: /usr/local/bin/helpdesk-ctl start, /usr/local/bin/helpdesk-ctl stop, /usr/local/bin/helpdesk-ctl status' > "$1"
EDITOR
chmod 0700 "$HELPDESK_EDITOR"
EDITOR="$HELPDESK_EDITOR" VISUAL="$HELPDESK_EDITOR" SUDO_EDITOR="$HELPDESK_EDITOR" visudo -f /etc/sudoers.d/helpdesk
chown root:root /etc/sudoers.d/helpdesk
chmod 0440 /etc/sudoers.d/helpdesk
visudo -c
```

Разрешены только три команды ctl от `helpdesk`. Программы и конфигурация должны быть недоступны разработчикам на запись — это обеспечивает часть второго.

## 5. Заполнить существующий provision.sh

```bash
nano provision.sh
```

Содержимое:

```bash
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
```

Модули 20, 30 и 50 делает второй. До их получения весь скрипт не запускай.

```bash
bash -n scripts/40-sudoers.sh
bash -n provision.sh
git add scripts/40-sudoers.sh provision.sh
git commit -m "feat: add restricted sudo and provisioning entry point"
git push
```

На GitHub открой PR `part-1` → `main`. Укажи требования 2.1.1–2.1.4 и зависимость от PR второго.

## 6. Проверить обе части до слияния

Когда второй открыл свой PR, сохрани свои изменения коммитом. Собери локальную ветку проверки:

```bash
git fetch origin
git switch -c "codex/check-1-$(date +%Y%m%d-%H%M%S)" origin/main
git merge --no-edit origin/part-1
git merge --no-edit origin/part-2
sudo bash ~/Downloads/helpdesk-stand.sh
sudo bash provision.sh
set -o pipefail
sudo bash ~/Downloads/helpdesk-acceptance.sh 2>&1 | tee /tmp/helpdesk-acceptance.txt
grep -Fx 'Result: 25 of 25' /tmp/helpdesk-acceptance.txt
! grep -Eq '^[[:space:]]*FAIL[[:space:]]' /tmp/helpdesk-acceptance.txt
```

Проверь часть второго: секреты закрыты, журналы доступны только на чтение, оба разработчика изменяют один файл static, служба static только читает. Оставь ревью в его PR. Второй повторяет проверку твоего PR на своей ВМ.

## 7. Оформить сдачу и слить PR

```bash
git switch part-1
cp /tmp/helpdesk-acceptance.txt acceptance.txt
nano runbook.md
nano README.md
```

Собери записи обоих в журнал: время, кто, команда, результат, требование; включи первый отказ и исправление. README начни таблицей участников, ответственности и реального результата «25 из 25». Ниже — команды подготовки, стенда, `provision.sh` и приёмки. В конце: «Не получилось: …» и «Нейросеть использовалась для: …».

```bash
git add README.md runbook.md acceptance.txt
git commit -m "docs: add work journal and acceptance results"
git push
```

После взаимного ревью слейте PR первого, затем второго через GitHub. Проверь итоговую `main`:

```bash
git switch main
git pull --ff-only origin main
sudo bash ~/Downloads/helpdesk-stand.sh
sudo bash provision.sh
sudo bash ~/Downloads/helpdesk-acceptance.sh
```

Должно быть 25/25. Исправления — через новый PR и повторный чистый прогон.

Сроки: подготовка до дня 2, свои PR до дня 7, ревью до дня 9, общий прогон до дня 12, сдача в день 14. Оба должны объяснять любую команду; решение и приёмка с нуля — до 30 минут.
