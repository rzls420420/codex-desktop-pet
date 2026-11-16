import json
import time
from pathlib import Path


class ActivityTracker:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path.home() / '.codex/sessions'
        self.files = {}
        self.initialized = False

    def poll(self):
        completed = 0
        aborted = 0
        missing = 0
        cutoff = time.time() - 86400
        try:
            candidates = list(self.root.rglob('rollout-*.jsonl'))
        except OSError:
            return any(item['active'] for item in self.files.values()), 0, 0, 0
        for path, item in list(self.files.items()):
            try:
                path.stat()
            except FileNotFoundError:
                if item['active']:
                    missing += 1
                del self.files[path]
            except OSError:
                pass
        for path in candidates:
            try:
                stat = path.stat()
                if stat.st_mtime < cutoff and path not in self.files:
                    continue
                item = self.files.get(path)
                if item is None:
                    item = {'offset': max(0, stat.st_size - 1024 * 1024), 'active': False, 'partial': b''}
                    self.files[path] = item
                if stat.st_size < item['offset']:
                    item.update(offset=0, active=False, partial=b'')
                with path.open('rb') as stream:
                    stream.seek(item['offset'])
                    data = item['partial'] + stream.read()
                    item['offset'] = stream.tell()
                lines = data.split(b'\n')
                item['partial'] = lines.pop()
                for line in lines:
                    try:
                        record = json.loads(line)
                        if record.get('type') != 'event_msg':
                            continue
                        kind = record.get('payload', {}).get('type')
                    except (ValueError, AttributeError):
                        continue
                    if kind == 'task_started':
                        item['active'] = True
                    elif kind in ('task_complete', 'turn_aborted'):
                        if kind == 'task_complete' and item['active'] and self.initialized:
                            completed += 1
                        elif kind == 'turn_aborted' and item['active'] and self.initialized:
                            aborted += 1
                        item['active'] = False
            except OSError:
                continue
        self.initialized = True
        return any(item['active'] for item in self.files.values()), completed, aborted, missing
