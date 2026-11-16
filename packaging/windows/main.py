import ctypes
import subprocess
import sys
import time
from pathlib import Path


def codex_running():
    query = ("Get-CimInstance Win32_Process -Filter \"Name='Codex.exe'\" | "
             "Where-Object { $_.ExecutablePath -match '\\\\app\\\\Codex\\.exe$' "
             "-and $_.CommandLine -notmatch '--type=' } | Select-Object -First 1 -ExpandProperty ProcessId")
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', query],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    return bool(result.stdout.strip())


def monitor():
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, 'Local\\WhiteDragonCodexMonitor')
    if not mutex or ctypes.windll.kernel32.GetLastError() == 183:
        return
    pet = None
    previous = False
    while True:
        try:
            running = codex_running()
        except (OSError, subprocess.TimeoutExpired):
            time.sleep(5)
            continue
        if running and not previous:
            command = [sys.executable, '--pet'] if getattr(sys, 'frozen', False) else [sys.executable, str(Path(__file__).resolve()), '--pet']
            pet = subprocess.Popen(command, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        elif previous and not running and pet and pet.poll() is None:
            pet.terminate()
            try:
                pet.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pet.kill()
                pet.wait()
            pet = None
        previous = running
        time.sleep(3)


if __name__ == '__main__':
    if '--pet' in sys.argv:
        from dragon_pet.app import main
        sys.argv = sys.argv[:1]
        sys.exit(main())
    monitor()
