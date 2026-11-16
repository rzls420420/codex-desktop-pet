import fcntl
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from dragon_pet.autostart import is_enabled

ROOT = Path(__file__).resolve().parent.parent


def is_codex_main(args, executable=None):
    if not args:
        return False
    try:
        first = shlex.split(args[0])
    except ValueError:
        return False
    if not first or (executable or first[0]) != '/usr/lib/chatgpt/ChatGPT':
        return False
    options = first[1:] + args[1:]
    return not any(arg == '--type' or arg.startswith('--type=') for arg in options)


def codex_running():
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            args = (process / 'cmdline').read_bytes().split(b'\0')
            executable = os.readlink(process / 'exe')
            if is_codex_main([arg.decode(errors='replace') for arg in args if arg], executable):
                return True
        except (OSError, ProcessLookupError):
            continue
    return False


def next_action(was_running, running, pet_running, autostart_enabled=False):
    if autostart_enabled:
        return None
    if running and not was_running and not pet_running:
        return 'start'
    if was_running and not running and pet_running:
        return 'stop'
    return None


def main():
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp'))
    lock = open(runtime / f'white-dragon-monitor-{os.getuid()}.lock', 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0
    previous = False
    pet = None
    while True:
        running = codex_running()
        active = pet is not None and pet.poll() is None
        try:
            enabled = is_enabled()
        except OSError:
            enabled = False
        action = next_action(previous, running, active, enabled)
        if action == 'start':
            pet = subprocess.Popen([sys.executable, '-m', 'dragon_pet.app'], cwd=ROOT)
        elif action == 'stop':
            pet.terminate()
            try:
                pet.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pet.kill()
                pet.wait()
            pet = None
        previous = running
        time.sleep(2)


if __name__ == '__main__':
    sys.exit(main())
