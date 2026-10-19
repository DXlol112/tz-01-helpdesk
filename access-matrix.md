# Матрица доступа · helpdesk-01

## Фактические права

| Ресурс | `stat -c "%A %U:%G"` |
|---|---|
| `/etc/helpdesk/helpdesk.conf` | `-rw-r----- root:helpdesk-dev` (640) |
| `/etc/helpdesk/secrets.env` | `-r-------- helpdesk:helpdesk` (400) |
| `/var/lib/helpdesk` | `drwx------ helpdesk:helpdesk` (700) |
| `/var/log/helpdesk` | `drwxr-s--- helpdesk:helpdesk-logs` (2750) |
| `/var/log/helpdesk/api.log` | `-rw-r----- helpdesk:helpdesk-logs` (640) |
| `/srv/helpdesk/static` | `drwxrws--- root:helpdesk-dev` (2770) |

## Проверка от имени каждой роли

| Ресурс | Роль | Команда проверки | Ожидали | Получили |
|---|---|---|---|---|
| `static/test.txt` | ivanov | `sudo -u ivanov sh -c 'umask 0077; echo ivanov > /srv/helpdesk/static/test.txt'` | Создание | Без ошибки; строка прочитана ниже |
| `static/test.txt` | petrova | `sudo -u petrova sh -c 'echo petrova >> /srv/helpdesk/static/test.txt'` | Дописывание | Без ошибки; строка прочитана ниже |
| `static/test.txt` | helpdesk | `sudo -u helpdesk cat /srv/helpdesk/static/test.txt` | Чтение | Выведены `ivanov` и `petrova` |
| `static/test.txt` | helpdesk | `sudo -u helpdesk test ! -w /srv/helpdesk/static/test.txt && echo 'OK: служба не пишет'` | Запись запрещена | `OK: служба не пишет` |
| `static/test.txt` | petrova | `sudo -u petrova rm /srv/helpdesk/static/test.txt` | Удаление | Без ошибки |

## Правило sudo

По `sudo -l -U ivanov` и `sudo -l -U petrova` обоим разрешено:

```text
(helpdesk) NOPASSWD: /usr/local/bin/helpdesk-ctl start, /usr/local/bin/helpdesk-ctl stop, /usr/local/bin/helpdesk-ctl status
```

`sudo visudo -c`: `/etc/sudoers` и `/etc/sudoers.d/helpdesk` успешно обработаны.

| Команда проверки | Ожидали | Получили |
| --- | --- | --- |
| `sudo -u ivanov sudo -n -u helpdesk /usr/local/bin/helpdesk-ctl status` | Статус без пароля | PID `34450`, пользователь `helpdesk`, `/bin/bash /usr/local/bin/helpdesk-api` |
| `sudo -u petrova sudo -n -u helpdesk /usr/local/bin/helpdesk-ctl status` | Статус без пароля | Тот же процесс, без запроса пароля |
| `sudo -u ivanov sudo -n -u helpdesk /bin/bash -c true` | Отказ | `sudo: требуется указать пароль` |
| `sudo -u petrova sudo -n -u root /usr/bin/id` | Отказ | `sudo: требуется указать пароль` |
| `sudo -u smirnova sudo -n -u helpdesk /usr/local/bin/helpdesk-ctl status` | Отказ | `sudo: требуется указать пароль` |


