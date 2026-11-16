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
                    item = {'offset': 0, 'active': False, 'partial': b'', 'usage': None}
                    self.files[path] = item
                if stat.st_size < item['offset']:
                    item.update(offset=0, active=False, partial=b'', usage=None)
                item['modified'] = stat.st_mtime_ns
                with path.open('rb') as stream:
                    stream.seek(item['offset'])
                    lines = []
                    while True:
                        line = stream.readline()
                        if not line:
                            break
                        line = item['partial'] + line
                        item['partial'] = b''
                        if not line.endswith(b'\n'):
                            item['partial'] = line
                            break
                        if b'event_msg' in line and any(kind in line for kind in
                                                       (b'task_started', b'token_count', b'task_complete', b'turn_aborted')):
                            lines.append(line)
                    item['offset'] = stream.tell()
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
                        item['usage'] = None
                    elif kind == 'token_count' and item['active']:
                        info = record['payload'].get('info')
                        if isinstance(info, dict):
                            item['usage'] = info
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

    def context_usage(self):
        active = [item for item in self.files.values() if item['active']]
        if not active:
            return None
        info = max(active, key=lambda item: item.get('modified', 0)).get('usage')
        if not isinstance(info, dict):
            return None
        usage = info.get('last_token_usage')
        window = info.get('model_context_window')
        if not isinstance(usage, dict):
            return None
        incoming = usage.get('input_tokens')
        outgoing = usage.get('output_tokens')
        cached = usage.get('cached_input_tokens')
        def valid(value):
            return isinstance(value, int) and not isinstance(value, bool) and value >= 0
        if not all(valid(value) for value in (incoming, outgoing, window)) or window == 0:
            return None
        rate = 100 * cached / incoming if valid(cached) and incoming > 0 and cached <= incoming else None
        return incoming + outgoing, window, rate
