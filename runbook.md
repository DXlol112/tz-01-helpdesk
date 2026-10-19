# Журнал работ · ТЗ № 1

19.10.2026. Время указано по выводу команд и скриншотам; «—» — точное время не зафиксировано.

| Время | Кто | Команда | Результат | Требование | Зачем |
|---|---|---|---|---|---|
| 18:33 | dxlol | `hostnamectl`, `cat /etc/os-release`, `df -hT`, `id`, `getent`, `ps`, `ls -lR /tmp/helpdesk-release-2.4.1` | Старая версия работает от dxlol, аккаунтов команды нет; паспорт заполнен | 4.1 | Осмотр до настройки |
| — | dxlol | `sudo bash scripts/20-layout.sh` | Ошибка: неверная группа `helpdesk-dev` | 2.1, 2.2 | Разместить файлы |
| — | glebkuznecov | `sudo bash /tmp/helpdesk-accounts.sh` | Заданы пароли сотрудников; дальнейшие проверки от их имени выполнены | 2.1.1–2.1.3 | Подготовить аккаунты |
| 19:14 | glebkuznecov | `sudo -u helpdesk /usr/local/bin/helpdesk-ctl start`; `sudo tail -n 5 /var/log/helpdesk/api.log`; `ps -eo user,pid,args` | Первый запуск отклонён: `address already in use`; работает версия 2.3 | 2.4, 4.2 И-04 | Найти причину отказа; далее остановить 2.3 модулем 50 |
| 19:28 | glebkuznecov | `sudo -u ivanov sh -c 'umask 0077; echo ivanov > /srv/helpdesk/static/test.txt'`; `sudo -u petrova sh -c 'echo petrova >> /srv/helpdesk/static/test.txt'` | Второй разработчик дописал файл первого | 2.3.2 | Проверить совместную запись |
| 19:28 | glebkuznecov | `sudo -u helpdesk cat /srv/helpdesk/static/test.txt`; `sudo -u helpdesk test ! -w /srv/helpdesk/static/test.txt`; `sudo -u petrova rm /srv/helpdesk/static/test.txt` | Служба читает обе строки, но не пишет; тестовый файл удалён | 2.3.1 | Проверить права службы |
| 19:28 | glebkuznecov | `sudo stat -c '%A %a %U:%G %n' …`; `sudo getfacl -p /etc/helpdesk /etc/helpdesk/helpdesk.conf /srv/helpdesk/static` | Права и ACL записаны в `access-matrix.md` | 2.3.1, 4.1 | Зафиксировать матрицу |
| — | dxlol | `sudo bash provision.sh` | Пароли обновлены; остановка на `chown`: нет `/etc/sudoers.d/helpdesk` | 2.1.4 | Проверить общую установку |
| — | dxlol | Исправление `scripts/40-sudoers.sh`: обработка аргумента `--` перед именем файла | Редактор проверен с `--` и без него | 2.1.4 | Исправить создание sudoers |
| 20:25 | glebkuznecov | `sudo visudo -c`; `sudo -l -U ivanov`; `sudo -l -U petrova` | Правила корректны; разрешены start, stop, status от helpdesk без пароля | 2.1.4 | Проверить sudoers |
| 20:25 | glebkuznecov | `sudo -u ivanov sudo -n -u helpdesk /usr/local/bin/helpdesk-ctl status`; аналогично для petrova | Обе команды успешны: служба от helpdesk, PID 34450 | 2.1.4, 2.4.2 | Проверить управление службой |
| 20:27 | glebkuznecov | `sudo -u ivanov sudo -n -u helpdesk /bin/bash -c true`; `sudo -u petrova sudo -n -u root /usr/bin/id`; `sudo -u smirnova sudo -n -u helpdesk /usr/local/bin/helpdesk-ctl status` | Все три попытки отклонены: «требуется указать пароль» | 2.1.4 | Проверить запреты с sudo -n |
| — | dxlol | Запуск `helpdesk-acceptance.sh` | В сохранённом `acceptance.txt`: `Result: 25 of 25` | 4.2 И-01 | Проверить итог |

## Что пошло не так и как исправили

- Модуль 20 запустили до создания `helpdesk-dev`. Исправили порядок: сначала модуль 10, затем 20 и 30.
- Редактор sudoers принял `--` за имя файла. Добавили пропуск этого аргумента; последующая проверка `visudo -c` у напарника прошла успешно.
