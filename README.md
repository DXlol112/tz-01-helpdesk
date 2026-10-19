# ТЗ № 1 · Ввод в эксплуатацию сервиса заявок helpdesk 2.4.1 на сервере helpdesk-01

| | |
|---|---|
| Практикант 1 | dxlol @DXlol112 - пользователи, sudo, сборка |
| Практикант 2 | glebkuznecov @glebkuznecov - размещение, права, запуск |
| Сервер | helpdesk-01 |
| Итог приёмки |**25** из **25** [acceptance.txt](./acceptance.txt) |

## Состав репозитория

- `runbook.md` — журнал работ
- `acceptance.txt` — вывод приёмки после финального прогона
- `screenshots/` — снимки, которые требует ТЗ
- `server-passport.md` — состояние сервера до настройки
- `access-matrix.md` — права и проверки доступа
- `provision.sh`, `scripts/` — установка и настройка сервиса

## Как воспроизвести

На учебной ВМ, из корня репозитория. Стенд сбрасывает предыдущую установку helpdesk.

```bash
sudo apt update
sudo apt install -y acl
sudo bash help/helpdesk-stand.sh
sudo bash provision.sh
set -o pipefail
sudo bash help/helpdesk-acceptance.sh 2>&1 | tee acceptance.txt
```

При установке задай пароли трём сотрудникам. Ожидаемый итог: `Result: 25 of 25`, все проверки `OK`.
