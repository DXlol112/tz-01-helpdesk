# Разработчик 1 — пользователи, sudo, сборка

Ветка **part-1**. Ты координируешь сдачу; владелец GitHub может выполнять любую часть. Владелец приглашает второго в Collaborators. Второй параллельно выполняет [свою инструкцию](02-developer-2.md).

Твои файлы: `scripts/10-accounts.sh`, `scripts/40-sudoers.sh`, `provision.sh`, `server-passport.md`, `runbook.md`, `README.md`, `acceptance.txt`. В журнал по ходу работы записывай время, участника, команду, результат и пункт ТЗ; добавляй записи напарника. Секреты и пароли в Git не сохраняй.

## 1. Подготовить ветку и ВМ

Используй существующий клон внутри **отдельной ВМ Ubuntu 24.04** со снимком. В паспорте сейчас указан ноутбук с Linux Mint: для сдачи нужны данные учебной ВМ. Стенд удаляет прежнюю установку helpdesk; запускай его только в этой ВМ.

Сначала `git status --short`: при изменениях сохрани нужные файлы отдельным коммитом. Затем из папки репозитория:

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin
git switch part-1
git merge --ff-only origin/part-1
git merge --no-edit origin/main
sudo apt update
sudo apt install -y git wget ca-certificates acl nano
mkdir -p scripts screenshots "$HOME/Downloads"
HELPDESK_MATERIALS=https://algorthimization-course-vvodnoe.vercel.app/op05-operacionnye-sistemy-i-sredy/proekty/ekspluataciya-servera/materials
wget -O ~/Downloads/helpdesk-stand.sh "$HELPDESK_MATERIALS/helpdesk-stand.sh"
wget -O ~/Downloads/helpdesk-acceptance.sh "$HELPDESK_MATERIALS/helpdesk-acceptance.sh"
sudo bash ~/Downloads/helpdesk-stand.sh
```

Если на этой ВМ стенд уже подготовлен и работа начата, пропусти его повторный запуск. При ошибке любой команды остановись и исправь причину. При конфликте Git исправь файлы, затем `git add ПУТЬ` и `git merge --continue`.

## 2. Заполнить паспорт до настройки

```bash
date --iso-8601=seconds
hostnamectl
cat /etc/os-release
df -hT
for account in helpdesk ivanov petrova smirnova; do id "$account" || true; done
getent group helpdesk helpdesk-dev helpdesk-support helpdesk-logs sudo || true
ps -eo user,pid,args | grep '[h]elpdesk-api'
ls -lR /tmp/helpdesk-release-2.4.1
nano server-passport.md
```

Впиши фактические выводы в шаблон: ОС, разделы, аккаунты, группы, процессы и владельцы файлов. Отсутствие аккаунтов до установки — нормальный результат. `secrets.env` не открывай.

## 3. Создать пользователей и сразу отправить модуль второму

Выполни весь блок: он запишет содержимое файла.

```bash
cat > scripts/10-accounts.sh <<'EOF'
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
EOF
bash -n scripts/10-accounts.sh
```

```bash
sudo bash scripts/10-accounts.sh
getent passwd helpdesk
for account in ivanov petrova smirnova; do
  id "$account"
  sudo passwd -S "$account"
done
git add scripts/10-accounts.sh server-passport.md
git commit -m "feat: add helpdesk accounts"
git push -u origin part-1
```

Пароли вводи при запросе. Проверь UID службы < 1000, home `/var/lib/helpdesk`, shell `nologin`; у сотрудников статус пароля `P` и нет группы `sudo`. Сообщи второму, что модуль опубликован: теперь он может запускать размещение файлов. Группа `helpdesk-logs` даёт сотрудникам чтение журналов.

## 4. Создать правило sudo и общий скрипт

```bash
cat > scripts/40-sudoers.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Запусти через sudo"; exit 1; }
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
EOF
bash -n scripts/40-sudoers.sh
```

Правило устанавливается через `visudo`: только `start`, `stop`, `status` от имени `helpdesk`.

```bash
cat > provision.sh <<'EOF'
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
EOF
bash -n provision.sh
```

`provision.sh` запускается на свежем стенде, когда получены все пять модулей. Пароли запрашиваются во время выполнения; релиз удаляется только после успешного запуска.

```bash
git add scripts/40-sudoers.sh provision.sh
git commit -m "feat: add sudo rules and provisioning"
git push
```

Открой на GitHub PR **part-1 → main**. Пока не сливай. Второй в это время заканчивает модули 20, 30, 50.

## 5. Проверить общий проект и PR второго

После открытия обоих PR, с чистым `git status`, собери временную ветку проверки. Если она уже есть, выбери другое имя вместо `codex/check-1`.

```bash
git fetch origin
git switch -c codex/check-1 origin/main
git merge --no-edit origin/part-1
git merge --no-edit origin/part-2
sudo bash ~/Downloads/helpdesk-stand.sh
sudo bash provision.sh
set -o pipefail
sudo bash ~/Downloads/helpdesk-acceptance.sh 2>&1 | tee /tmp/helpdesk-acceptance.txt
grep -Fx 'Result: 25 of 25' /tmp/helpdesk-acceptance.txt
! grep -Eq '^[[:space:]]*FAIL[[:space:]]' /tmp/helpdesk-acceptance.txt
```

Нужно **25 из 25**, без `FAIL`. Повтори проверки доступа из этапа 5 второго разработчика и оставь ревью в его PR. Исправления делай в своей `part-1`, отправляй push и повторяй проверку с обновлёнными ветками.

**Скриншот:** полный вывод приёмки со всеми `OK` → `screenshots/02-acceptance.png` (несколько кадров, если не помещается).

## 6. Оформить результат и слить PR

```bash
git switch part-1
cp /tmp/helpdesk-acceptance.txt acceptance.txt
nano runbook.md
nano README.md
```

В журнал добавь записи второго, первый отказ запуска и исправление. README: таблица участников и обязанностей, фактический итог приёмки, команды «стенд → provision → приёмка». В конце: «Не получилось: …», «Нейросеть использовалась для: …».

```bash
git add README.md runbook.md acceptance.txt screenshots/02-acceptance*.png
git commit -m "docs: record journal and acceptance"
git push
```

После взаимного ревью владелец сливает PR **part-1**, затем **part-2** через GitHub. Только первый выполняет итоговый прогон объединённой `main`:

```bash
git switch main
git pull --ff-only origin main
sudo bash ~/Downloads/helpdesk-stand.sh
sudo bash provision.sh
sudo bash ~/Downloads/helpdesk-acceptance.sh
```

Сверь 25/25 с отчётом. Если результат изменился, исправь причину и обнови отчёт через PR. Для каждого нового прогона нужен свежий стенд.

Сроки: подготовка — день 2, PR — день 7, ревью — день 9, общий прогон — день 12, сдача — день 14. Оба объясняют команды любой части.
