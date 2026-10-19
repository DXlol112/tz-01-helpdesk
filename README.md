| Участник | Ответственность | Итог приёмки |
| --- | --- | --- |
| Практикант 1 — указать ФИО | Пользователи, sudo, общий скрипт и журнал | Не проверено, — из 25 |
| Практикант 2 — указать ФИО | Размещение, права и запуск службы | Не проверено, — из 25 |

# ТЗ-01 — helpdesk 2.4.1

В [репозитории](https://github.com/DXlol112/tz-01-helpdesk) уже созданы ветки `main`, `part-1`, `part-2`. Репозиторий публичный: просмотр и клонирование доступны без авторизации. Для push участникам нужен доступ на запись.

Последовательность работы: [разработчик 1](docs/01-developer-1.md), [разработчик 2](docs/02-developer-2.md). Изменения объединяются через PR в `main`.

В корне находятся шаблоны [паспорта](server-passport.md), [журнала](runbook.md), [матрицы доступа](access-matrix.md) и каркас [provision.sh](provision.sh). Скрипт пока содержит TODO. Модули `scripts/10-accounts.sh`, `20-layout.sh`, `30-access.sh`, `40-sudoers.sh`, `50-service.sh`, каталог `screenshots/` и `acceptance.txt` появятся при выполнении заданий.

## Проверка готового решения

Выполнять после заполнения `provision.sh` и создания всех пяти модулей. Нужна отдельная ВМ Ubuntu 24.04 со снимком VirtualBox: скрипт стенда сбрасывает пользователей и файлы учебного сервиса.

Из корня существующего клона, после сохранения своей работы коммитом:

```bash
cd "$(git rev-parse --show-toplevel)"
git switch main
git pull --ff-only origin main
sudo apt update
sudo apt install -y git wget ca-certificates acl nano
mkdir -p "$HOME/Downloads"
HELPDESK_MATERIALS=https://algorthimization-course-vvodnoe.vercel.app/op05-operacionnye-sistemy-i-sredy/proekty/ekspluataciya-servera/materials
wget -O "$HOME/Downloads/helpdesk-stand.sh" "$HELPDESK_MATERIALS/helpdesk-stand.sh"
wget -O "$HOME/Downloads/helpdesk-acceptance.sh" "$HELPDESK_MATERIALS/helpdesk-acceptance.sh"
bash -n provision.sh
bash -ec 'for file in scripts/[0-9][0-9]-*.sh; do bash -n "$file"; done'
sudo bash "$HOME/Downloads/helpdesk-stand.sh"
sudo bash provision.sh
set -o pipefail
sudo bash "$HOME/Downloads/helpdesk-acceptance.sh" 2>&1 | tee acceptance.txt
grep -Fx 'Result: 25 of 25' acceptance.txt
! grep -Eq '^[[:space:]]*FAIL[[:space:]]' acceptance.txt
```

Пароли сотрудников вводятся при запуске решения. После успешного прогона обновите таблицу результатов и добавьте настоящие снимки отказа запуска и приёмки.

Не получилось: выполнение решения и приёмка на ВМ ещё не проверены.

Нейросеть использовалась для: подготовки и проверки инструкций, ссылок и команд.
