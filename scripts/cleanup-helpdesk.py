#!/usr/bin/env python3
"""Удаление только учебного стенда. По умолчанию показывает план."""
import argparse
import grp
import hashlib
import os
from pathlib import Path
import pwd
import shutil
import signal
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parent.parent
USERS = {'helpdesk': ('/var/lib/helpdesk', '/usr/sbin/nologin'),
         'ivanov': ('/home/ivanov', '/bin/bash'),
         'petrova': ('/home/petrova', '/bin/bash'),
         'smirnova': ('/home/smirnova', '/bin/bash')}
GROUPS = {'helpdesk', 'helpdesk-dev', 'helpdesk-support', 'helpdesk-logs',
          'ivanov', 'petrova', 'smirnova'}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).digest()


def guard(path):
    """Запрет ссылок в пути, точек монтирования и удаления репозитория."""
    require(path.is_absolute(), f'Не абсолютный путь: {path}')
    for part in (path, *path.parents):
        require(not part.is_symlink(), f'Символическая ссылка: {part}')
        if part == Path('/'):
            break
    require(path != REPO and path not in REPO.parents and REPO not in path.parents,
            f'Путь пересекается с репозиторием: {path}')
    require(not path.is_mount(), f'Точка монтирования: {path}')


def checked_tree(path, allowed):
    guard(path)
    if not path.exists():
        return
    require(path.is_dir(), f'Ожидался каталог: {path}')
    for item in path.rglob('*'):
        guard(item)
        rel = item.relative_to(path).as_posix()
        require(rel in allowed, f'Неизвестный файл, удаление отменено: {item}')
        require(item.is_file() or item.is_dir(), f'Особый файл: {item}')


def process_args(pid):
    try:
        return Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')[:-1]
    except (FileNotFoundError, ProcessLookupError):
        return []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='выполнить показанный план')
    args = parser.parse_args()
    require(os.geteuid() == 0, 'Запусти через sudo для проверки защищённых каталогов.')
    admin = os.environ.get('SUDO_USER', '')
    require(admin and admin != 'root' and admin not in USERS,
            'Запусти через sudo от своего обычного пользователя.')
    admin_home = Path(pwd.getpwnam(admin).pw_dir)
    accounts = []
    for name, (home, shell) in USERS.items():
        try:
            account = pwd.getpwnam(name)
        except KeyError:
            continue
        require(account.pw_dir == home and account.pw_shell == shell,
                f'Неожиданные home/shell у {name}')
        require(0 < account.pw_uid < 1000 if name == 'helpdesk' else account.pw_uid >= 1000,
                f'Неожиданный UID у {name}')
        memberships = {g.gr_name for g in grp.getgrall()
                       if name in g.gr_mem or g.gr_gid == account.pw_gid}
        require(memberships <= GROUPS, f'{name} состоит в сторонних группах: {memberships - GROUPS}')
        require(not any(p.pw_uid == account.pw_uid and p.pw_name != name for p in pwd.getpwall()),
                f'UID {name} используется другим аккаунтом')
        accounts.append(account)
    for group in grp.getgrall():
        if group.gr_name in GROUPS:
            members = set(group.gr_mem) | {p.pw_name for p in pwd.getpwall() if p.pw_gid == group.gr_gid}
            require(members <= USERS.keys(), f'В группе {group.gr_name} есть сторонние участники: {members}')

    release = {'bin', 'bin/helpdesk-api', 'bin/helpdesk-ctl', 'conf', 'conf/helpdesk.conf',
               'conf/secrets.env', 'data', 'data/tickets.db', 'static', 'static/index.html',
               'static/css', 'static/css/app.css'}
    trees = {Path('/etc/helpdesk'): {'helpdesk.conf', 'secrets.env'},
             Path('/var/lib/helpdesk'): {'tickets.db'},
             Path('/var/log/helpdesk'): {'api.log'},
             Path('/srv/helpdesk'): {'static', 'static/index.html', 'static/css', 'static/css/app.css'},
             Path('/run/helpdesk'): {'api.pid'},
             Path('/tmp/helpdesk-release-2.4.1'): release,
             admin_home / 'helpdesk-2.3': {'bin', 'bin/helpdesk-api'}}
    # Домашние папки сотрудников удаляются только с неизменённым содержимым /etc/skel.
    skel = Path('/etc/skel')
    skeleton = {p.relative_to(skel).as_posix(): p for p in skel.rglob('*')}
    for name in ('ivanov', 'petrova', 'smirnova'):
        home = Path(USERS[name][0])
        if not home.exists():
            continue
        require(any(p.pw_name == name for p in accounts), f'Папка без проверенного аккаунта: {home}')
        checked_tree(home, skeleton.keys())
        for item in home.rglob('*'):
            source = skeleton[item.relative_to(home).as_posix()]
            require(item.is_dir() == source.is_dir(), f'Тип файла изменён: {item}')
            if item.is_file():
                require(digest(item) == digest(source), f'Личные изменения, удаление отменено: {item}')
        trees[home] = set(skeleton)
    for path, allowed in trees.items():
        checked_tree(path, allowed)

    files = [Path(p) for p in ('/usr/local/bin/helpdesk-api', '/usr/local/bin/helpdesk-ctl',
                              '/etc/sudoers.d/helpdesk', '/etc/sudoers.d/helpdesk.tmp')]
    for path in files:
        guard(path)
        require(not path.exists() or path.is_file(), f'Ожидался обычный файл: {path}')
    # Внешние копии удаляем только при точном совпадении с файлами проекта.
    copies = [(admin_home / 'Downloads/helpdesk-stand.sh', REPO / 'help/helpdesk-stand.sh'),
              (admin_home / 'Downloads/helpdesk-acceptance.sh', REPO / 'help/helpdesk-acceptance.sh'),
              (Path('/tmp/helpdesk-accounts.sh'), REPO / 'scripts/10-accounts.sh'),
              (Path('/tmp/helpdesk-acceptance.txt'), REPO / 'acceptance.txt'),
              (Path('/tmp/helpdesk-acceptance-2.txt'), REPO / 'acceptance.txt')]
    for path, source in copies:
        guard(path)
        if path.is_file():
            if source.is_file() and digest(path) == digest(source):
                files.append(path)
            else:
                print(f'СОХРАНИТЬ (отличается от проекта): {path}')

    targets = {b'/usr/local/bin/helpdesk-api', os.fsencode(admin_home / 'helpdesk-2.3/bin/helpdesk-api')}
    processes = []
    for entry in Path('/proc').iterdir():
        if entry.name.isdigit():
            argv = process_args(entry.name)
            if len(argv) == 2 and argv[0] in (b'/bin/bash', b'/usr/bin/bash', b'bash') and argv[1] in targets:
                processes.append((int(entry.name), argv))
    print(f'СОХРАНИТЬ репозиторий: {REPO}')
    for pid, argv in processes:
        print(f'ОСТАНОВИТЬ PID {pid}: {os.fsdecode(argv[1])}')
    for account in accounts:
        print(f'УДАЛИТЬ аккаунт: {account.pw_name}')
    for name in sorted(GROUPS):
        try:
            grp.getgrnam(name)
            print(f'УДАЛИТЬ группу: {name}')
        except KeyError:
            pass
    for path in [*trees, *files]:
        if path.exists():
            print(f'УДАЛИТЬ путь: {path}')
    if not args.apply:
        print('\nЭто просмотр. Ничего не изменено. Для удаления добавь --apply.')
        return

    require(hasattr(os, 'pidfd_open') and hasattr(signal, 'pidfd_send_signal'),
            'Нет безопасного механизма pidfd. Удаление отменено.')
    require(shutil.rmtree.avoids_symlink_attacks, 'Недоступно безопасное удаление каталогов')
    subprocess.run(['/usr/sbin/visudo', '-c'], check=True)
    for pid, argv in processes:
        try:
            fd = os.pidfd_open(pid)
        except ProcessLookupError:
            continue
        try:
            if process_args(pid) == argv:
                signal.pidfd_send_signal(fd, signal.SIGTERM)
        except ProcessLookupError:
            pass
        finally:
            os.close(fd)
    time.sleep(6)
    for pid, argv in processes:
        require(process_args(pid) != argv, f'Служба PID {pid} не остановилась. Удаление отменено.')
    uids = {a.pw_uid for a in accounts}
    for entry in Path('/proc').iterdir():
        if entry.name.isdigit():
            try:
                require(entry.stat().st_uid not in uids, f'У учебного пользователя остался процесс {entry.name}. Удаление отменено.')
            except FileNotFoundError:
                pass
    # Повторная проверка непосредственно перед удалением файлов.
    for path, allowed in trees.items():
        checked_tree(path, allowed)
    for path in files:
        guard(path)
    for account in accounts:
        subprocess.run(['/usr/sbin/userdel', account.pw_name], check=True)  # без -r
    for name in sorted(GROUPS):
        try:
            grp.getgrnam(name)
        except KeyError:
            continue
        subprocess.run(['/usr/sbin/groupdel', name], check=True)
    for path in files:
        path.unlink(missing_ok=True)
    for path in trees:
        if path.exists():
            shutil.rmtree(path)
    subprocess.run(['/usr/sbin/visudo', '-c'], check=True)
    print('Готово. Репозиторий сохранён. Неизвестные внешние файлы не удалялись.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f'ОСТАНОВКА: {error}', file=sys.stderr)
        sys.exit(1)
