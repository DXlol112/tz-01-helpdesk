# Разработчик 2 — размещение, права, запуск

Ветка **part-2**. Твои файлы: `scripts/20-layout.sh`, `scripts/30-access.sh`, `scripts/50-service.sh`, `access-matrix.md`, `screenshots/01-start-failure.png`. Первый параллельно выполняет [свою инструкцию](01-developer-1.md). Передавай ему для журнала время, команды, результаты, ошибки и пункты ТЗ.

**Причина текущей ошибки:** `20-layout.sh` требует уже созданные `helpdesk`, `helpdesk-dev`, `helpdesk-logs`. До этапа 3 ниже модули 20 и 30 не запускай. Одной команды `groupadd helpdesk-dev` недостаточно.

## 1. Подготовить ветку и ВМ

Прими приглашение владельца в Collaborators для отправки коммитов.

Используй существующий клон внутри **отдельной ВМ Ubuntu 24.04** со снимком. В паспорте сейчас указан ноутбук с Linux Mint: для сдачи нужны данные учебной ВМ. Стенд удаляет прежнюю установку helpdesk; запускай его только в этой ВМ.

Сначала `git status --short`: при изменениях сохрани нужные файлы отдельным коммитом. Затем из папки репозитория:

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin
git switch part-2
git merge --ff-only origin/part-2
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

## 2. Проверить свои модули, пока первый создаёт пользователей

Файлы 20 и 30 уже есть в текущей рабочей папке. Если их нет в твоём клоне, сначала получи эти два файла от напарника. Они должны попасть в твой PR.

```bash
less /tmp/helpdesk-release-2.4.1/bin/helpdesk-api
less /tmp/helpdesk-release-2.4.1/bin/helpdesk-ctl
nano scripts/20-layout.sh
nano scripts/30-access.sh
bash -n scripts/20-layout.sh
bash -n scripts/30-access.sh
```

Проверь назначение модулей:

| Модуль | Что должен делать |
| --- | --- |
| 20 | Разложить программы, конфигурацию, секреты, БД, static и журналы по FHS; создать `/run/helpdesk`; сохранить релиз в `/tmp` до общего прогона |
| 30 | Установить `UMASK=0027`, ACL для службы и static; setgid и default ACL для совместной записи разработчиков |

В текущих файлах эти действия уже записаны. Служба не входит в `helpdesk-dev`; её доступ к конфигурации и static выдаётся ACL.

## 3. Получить пользователей, затем разместить файлы

**Дождись push первого с `scripts/10-accounts.sh`.** Команды ниже запускай последовательно; при ошибке не переходи к следующей.

```bash
git fetch origin &&
git show origin/part-1:scripts/10-accounts.sh > /tmp/helpdesk-accounts.sh &&
bash -n /tmp/helpdesk-accounts.sh &&
sudo bash /tmp/helpdesk-accounts.sh &&
id helpdesk &&
getent group helpdesk-dev &&
getent group helpdesk-logs &&
sudo bash scripts/20-layout.sh &&
sudo bash scripts/30-access.sh
```

`&&` останавливает цепочку при ошибке: без аккаунтов установка файлов не начнётся. Введи пароли сотрудников при запросе. Временный модуль в Git не добавляй.

## 4. Зафиксировать отказ и сделать запуск службы

Пока версия 2.3 работает:

```bash
sudo -u helpdesk /usr/local/bin/helpdesk-ctl start
sudo tail -n 5 /var/log/helpdesk/api.log
ps -eo user,pid,args | grep '[h]elpdesk-2[.]3/bin/helpdesk-api'
```

Здесь отказ ожидаем: новая версия видит старую. Запиши фактическую причину, а не предполагаемую; права ради запуска не расширяй.

**Скриншот:** команда запуска и сообщение об отказе → `screenshots/01-start-failure.png`. Передай первому запись для журнала.

Создай модуль, который остановит 2.3, сохранит её файлы и запустит новую версию:

```bash
cat > scripts/50-service.sh <<'EOF'
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
EOF
bash -n scripts/50-service.sh
```

```bash
sudo bash scripts/50-service.sh
```

## 5. Проверить доступ и заполнить матрицу

```bash
sudo -u ivanov sh -c 'umask 0077; echo ivanov > /srv/helpdesk/static/test.txt'
sudo -u petrova sh -c 'echo petrova >> /srv/helpdesk/static/test.txt'
sudo -u helpdesk cat /srv/helpdesk/static/test.txt
sudo -u helpdesk test ! -w /srv/helpdesk/static/test.txt && echo 'OK: служба не пишет'
sudo -u petrova rm /srv/helpdesk/static/test.txt
sudo stat -c '%A %a %U:%G %n' /etc/helpdesk/helpdesk.conf /etc/helpdesk/secrets.env /var/lib/helpdesk /var/log/helpdesk /var/log/helpdesk/api.log /srv/helpdesk/static
sudo getfacl -p /etc/helpdesk /etc/helpdesk/helpdesk.conf /srv/helpdesk/static
nano access-matrix.md
```

Повтори совместную запись в обратном направлении и во вложенном новом каталоге. Для каждой клетки ниже проверь чтение и запись от имени роли; для каталогов также проход (`test -x`). Вместо «остальные» используй `nobody`.

| Ресурс | helpdesk | ivanov и petrova | smirnova | остальные |
| --- | --- | --- | --- | --- |
| helpdesk.conf | чтение | чтение | нет | нет |
| secrets.env | чтение | нет | нет | нет |
| БД и каталог данных | чтение/запись | нет | нет | нет |
| Журнал | запись и диагностика | чтение | чтение | нет |
| Static | чтение | чтение/запись | нет | нет |

Пример проверки запрета; `0` означает, что запрет подтверждён:

```bash
sudo -u smirnova test ! -r /etc/helpdesk/secrets.env
echo $?
```

Впиши в шаблон фактические права, ACL, команды и результаты каждой роли. Сначала убедись, что пользователь и проверяемый файл существуют.

## 6. Отправить свою часть на ревью

```bash
git add scripts/20-layout.sh scripts/30-access.sh scripts/50-service.sh access-matrix.md screenshots/01-start-failure.png
git commit -m "feat: add layout, permissions and service"
git push -u origin part-2
```

Открой PR **part-2 → main**. Укажи зависимость от аккаунтов в PR первого. Пока не сливай.

## 7. Проверить часть первого на своей ВМ

После открытия обоих PR, с чистым `git status`, собери временную ветку. При повторе используй новое имя вместо `codex/check-2`.

```bash
git fetch origin
git switch -c codex/check-2 origin/main
git merge --no-edit origin/part-1
git merge --no-edit origin/part-2
sudo bash ~/Downloads/helpdesk-stand.sh
sudo bash provision.sh
set -o pipefail
sudo bash ~/Downloads/helpdesk-acceptance.sh 2>&1 | tee /tmp/helpdesk-acceptance.txt
grep -Fx 'Result: 25 of 25' /tmp/helpdesk-acceptance.txt
! grep -Eq '^[[:space:]]*FAIL[[:space:]]' /tmp/helpdesk-acceptance.txt
```

Проверь разрешения sudo:

```bash
sudo visudo -c
sudo -l -U ivanov
sudo -l -U petrova
sudo -u ivanov sudo -n -u helpdesk /usr/local/bin/helpdesk-ctl status
sudo -u petrova sudo -n -u helpdesk /usr/local/bin/helpdesk-ctl status
```

Следующие команды **должны завершиться отказом sudo**:

```bash
sudo -u ivanov sudo -n -u helpdesk /bin/bash -c true
sudo -u petrova sudo -n -u root /usr/bin/id
sudo -u smirnova sudo -n -u helpdesk /usr/local/bin/helpdesk-ctl status
```

Повтори запрет shell/root для второго разработчика. Допиши правило sudo и фактический `sudo -l` в `access-matrix.md`. Проверь паспорт и аккаунты по этапам 2–3 первого. Оставь ревью в PR первого.

```bash
git switch part-2
git add access-matrix.md
git commit -m "docs: record integrated access checks"
git push
```

Если проверка не прошла, исправляй свою часть в `part-2`, отправляй push и повторяй общий прогон с обновлёнными ветками. Приёмку и её скриншот сохраняет первый. После взаимного ревью владелец сливает PR первого, затем второго; первый проверяет итоговую `main`.

```bash
git switch main
git pull --ff-only origin main
```

Сроки: PR — день 7, ревью — день 9, общий прогон — день 12, сдача — день 14.
