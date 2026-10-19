# Паспорт сервера · dxLaptop

Состояние до настройки. Дата осмотра: **19.10.2026, 18:33:44 (UTC+03:00)**.
Команда: `date --iso-8601=seconds`.

| Сведение | Команда | Что показала |
| --- | --- | --- |
| Версия системы и ядра | `hostnamectl`, `cat /etc/os-release` | Имя `dxLaptop`; Linux Mint 22.3 (Zena), база Ubuntu `noble`; ядро `7.0.0-38-generic`; архитектура `x86-64`. Lenovo IdeaPad Slim 3 15AMN8. |
| Разделы и их заполнение | `df -hT` | Корень `/`: `/dev/sda3`, ext4, всего `916G`, занято `58G`, доступно `812G`, заполнение `7%`. Остальные разделы приведены ниже. |
| Учётные записи и группы из задания | `for account in helpdesk ivanov petrova smirnova; do id "$account" \|\| true; done`; `getent group helpdesk helpdesk-dev helpdesk-support helpdesk-logs sudo \|\| true` | Пользователей `helpdesk`, `ivanov`, `petrova`, `smirnova` нет. Группы `helpdesk`, `helpdesk-dev`, `helpdesk-support`, `helpdesk-logs` отсутствуют. Выведена только `sudo:x:27:dxlol`. |
| Работающие процессы и владельцы | `ps -eo user,pid,args \| grep '[h]elpdesk-api'` | Старая версия 2.3 работает от `dxlol`, PID `32563`. Процесс `sudo`, запустивший её, работает от `root`, PID `32556`. Процесс версии 2.4.1 в выводе отсутствует. |
| Каталоги и файлы релиза | `ls -lR /tmp/helpdesk-release-2.4.1` | Релиз содержит `bin`, `conf`, `data`, `static`. У показанных файлов и подкаталогов владелец `dxlol:dxlol`; каталоги и программы имеют права `0755`, остальные файлы — `0644`. Состав приведён ниже. |

## Разделы и заполнение

Вывод `df -hT`:

| Файловая система | Тип | Размер | Использовано | Доступно | Заполнение | Точка монтирования |
| --- | --- | --- | --- | --- | --- | --- |
| tmpfs | tmpfs | 726M | 2,0M | 724M | 1% | `/run` |
| efivarfs | efivarfs | 118K | 66K | 48K | 59% | `/sys/firmware/efi/efivars` |
| /dev/sda3 | ext4 | 916G | 58G | 812G | 7% | `/` |
| tmpfs | tmpfs | 3,6G | 52M | 3,5G | 2% | `/dev/shm` |
| tmpfs | tmpfs | 5,0M | 12K | 5,0M | 1% | `/run/lock` |
| /dev/nvme0n1p1 | vfat | 196M | 38M | 159M | 20% | `/boot/efi` |
| tmpfs | tmpfs | 726M | 260K | 725M | 1% | `/run/user/1000` |
| /dev/sda2 | vfat | 1004K | 874K | 130K | 88% | `/media/dxlol/UEFI_NTFS` |

## Процессы сервиса

Вывод `ps -eo user,pid,args | grep '[h]elpdesk-api'`:

```text
root       32556 sudo -u dxlol setsid /home/dxlol/helpdesk-2.3/bin/helpdesk-api
dxlol      32563 /bin/bash /home/dxlol/helpdesk-2.3/bin/helpdesk-api
```

## Состав релиза

По выводу `ls -lR /tmp/helpdesk-release-2.4.1`. Пути указаны относительно каталога релиза; владелец всех перечисленных объектов — `dxlol:dxlol`, время изменения — 19.10, 17:46.

| Путь | Права | Размер, байт |
| --- | --- | --- |
| `bin/`, `conf/`, `data/`, `static/`, `static/css/` | `drwxr-xr-x` (`0755`) | 4096 каждый |
| `bin/helpdesk-api` | `-rwxr-xr-x` (`0755`) | 1368 |
| `bin/helpdesk-ctl` | `-rwxr-xr-x` (`0755`) | 928 |
| `conf/helpdesk.conf` | `-rw-r--r--` (`0644`) | 239 |
| `conf/secrets.env` | `-rw-r--r--` (`0644`) | 84 |
| `data/tickets.db` | `-rw-r--r--` (`0644`) | 19 |
| `static/index.html` | `-rw-r--r--` (`0644`) | 104 |
| `static/css/app.css` | `-rw-r--r--` (`0644`) | 29 |

## Что показалось неправильным

- Версия 2.3 запущена из домашнего каталога от личной учётной записи `dxlol`.
- `conf/secrets.env` имеет права `0644`: чтение разрешено остальным пользователям.
- Служебная учётная запись и аккаунты сотрудников с группами ещё не созданы; настройка доступа по ролям не выполнена.
