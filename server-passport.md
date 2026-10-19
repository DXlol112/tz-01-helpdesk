# Паспорт сервера · dxLaptop · 19.10.2026

| Сведение | Команда | Что показала |
| --- | --- | --- |
| Версия системы и ядра | `hostnamectl`, `cat /etc/os-release`, `uname -r` | Имя `dxLaptop`, Linux Mint 22.3 (Zena), база Ubuntu `noble`, ядро `7.0.0-38-generic`, архитектура `x86_64`. Устройство Lenovo IdeaPad Slim 3 15AMN8, тип `laptop`. |
| Процессор и память | `lscpu`, `free -h` | AMD Ryzen 3 7320U with Radeon Graphics: 4 ядра, 8 потоков. ОЗУ: всего `7.1Gi`, занято `5.6Gi`, доступно `1.5Gi`. Swap: всего `5.3Gi`, занято `3.1Gi`. |
| Разделы и их заполнение | `df -hT` | Корень `/`: `/dev/sda3`, ext4, всего `916G`, занято `58G`, доступно `812G`, заполнение `7%`. EFI: `/dev/nvme0n1p1`, vfat, `196M`, занято `38M`, заполнение `20%`. Полный вывод ниже. |
| Учётные записи и группы из задания | `for account in helpdesk ivanov petrova smirnova; do id "$account" \|\| true; done` и `getent group helpdesk helpdesk-dev helpdesk-support helpdesk-logs sudo \|\| true` | Все четыре пользователя отсутствуют: `no such user`. Группы `helpdesk`, `helpdesk-dev`, `helpdesk-support`, `helpdesk-logs` не найдены. Найдена группа `sudo`: `sudo:x:27:dxlol`. |
| Работающие процессы из задания и их владельцы | `pgrep -af '[h]elpdesk-api'`, `ps -eo user,pid,args \| grep '[h]elpdesk-api'` | API 2.3 работает с PID `32563` от `dxlol` из `/home/dxlol/helpdesk-2.3/bin/helpdesk-api`. PID `32556` от root — процесс запуска `sudo`, не сам API. Процесс установленной версии 2.4.1 не обнаружен. |
| Каталоги релиза и права на них | `ls -lR /tmp/helpdesk-release-2.4.1`, `ls -ld /tmp/helpdesk-release-2.4.1 /etc/helpdesk /var/lib/helpdesk /srv/helpdesk /var/log/helpdesk /run/helpdesk` | Релиз находится в `/tmp/helpdesk-release-2.4.1`, владелец `dxlol:dxlol`. Каталоги имеют режим `0755`, программы — `0755`, настройки, секреты, БД и файлы static — `0644`. Целевые каталоги службы пока отсутствуют. Состав приведён ниже. |

## Что показалось неправильным

- Файл релиза `conf/secrets.env` имеет режим `0644`: чтение разрешено остальным пользователям. Сод