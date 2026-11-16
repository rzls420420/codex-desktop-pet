import json
import math
import random
import os
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path

DIALOGUE = {
    'task-start': ('本小姐已经开始处理了。', '有任务了？还是要看本小姐的。', '哼，交给本小姐吧。'),
    'task-complete': ('本小姐这一轮回复结束了，结果等你检查。', '这一轮说完了，快看看结果吧。', '本小姐已经回复完这一轮，别忘了检查。'),
    'task-aborted': ('这一轮被中止了，具体情况请看看记录。', '这次回复中断了，本小姐没有把它算作完成。'),
    'task-unknown': ('有一份会话记录不见了，任务状态暂时无法确认。',),
    'ambient-running': ('哼，本小姐练习一下。', '活动一下筋骨，才不是在忙什么任务。'),
    'ambient-review': ('安静一点，本小姐正欣赏风景。', '唔，让本小姐想点有趣的事。'),
    'ambient-waiting': ('本小姐在这里陪着你。', '哼，才不是特意等你呢。'),
    'idle': ('本小姐正在这里陪着你。', '哼，才不是特意等你呢。'),
    'running-right': ('本小姐已经出发了，让开让开。', '看好了，龙娘跑起来可是很快的。'),
    'running-left': ('本小姐绕回来看看你。', '哼，追得上本小姐吗？'),
    'waving': ('本小姐在这里，看到没有？', '喂，杂鱼，跟本小姐打个招呼。'),
    'jumping': ('本小姐跳得怎么样？', '哼，本小姐心情不错。'),
    'failed': ('唔，刚才那个表情不许笑。', '本小姐才没有闹别扭。'),
    'waiting': ('本小姐等一会儿，你慢慢来。', '哼，本小姐可是很有耐心的。'),
    'running': ('有事就交给本小姐。', '还是要看本小姐的本领。'),
    'review': ('本小姐正在思考。', '让我仔细瞧瞧，哼。'),
    'startup': ('本小姐已经来了，别太感动。', '哼，还是要看本小姐的。', '本小姐已经准备好了。',
                '杂鱼，今天也要乖乖听本小姐指挥。', '让你久等了？才没有特意赶来呢。',
                '本小姐登场，今天也交给我吧。', '哼，没有本小姐你可怎么办。',
                '准备好了吗？本小姐可是干劲十足。'),
    'interaction': ('你个杂鱼，可别太依赖本小姐。', '有什么事？本小姐正忙着呢。',
                    '哼，这次就勉为其难帮你。', '看什么看，本小姐可是很厉害的。',
                    '你放心，本小姐才不会出错呢。', '唔，再碰一下试试看？',
                    '这么简单的问题，也要麻烦本小姐吗？', '别误会，本小姐只是顺手帮忙。',
                    '哼，夸奖的话，再多说几句也不是不行。', '本小姐可是龙娘，当然无所不能。',
                    '你又在偷看本小姐？真拿你没办法。', '遇到难题了？让本小姐瞧瞧。',
                    '杂鱼，记得适当休息，别让本小姐担心。', '本小姐的尾巴可不是玩具。',
                    '你看起来很闲嘛，要不要给本小姐讲个笑话？', '本小姐已经注意到你了，满意了吗？',
                    '再摸头的话，本小姐可是会记仇的。', '哼，看在你这么努力的份上。',
                    '本小姐的耐心可是很珍贵的。', '有什么想法就说，本小姐听着呢。',
                    '才不是一直在等你，只是刚好在这里。', '今天也要好好表现哦，杂鱼。',
                    '别急，事情一件一件来。', '本小姐的眼光可是很准的。',
                    '哼，偶尔依靠你一下也不是不可以。', '偷偷告诉你，本小姐正在观察你哦。'),
    'sleep': ('本小姐要休息了，别吵。', '工作什么的，醒来再说。', '本小姐只眯一会儿。',
              '困了……床，快到本小姐身边来。', '杂鱼，记得替本小姐看好这里。',
              '不是偷懒，是龙娘的必要休息。', '呼……再忙也得好好睡觉。',
              '本小姐的床准备好了，晚点再见。'),
    'wake': ('本小姐已经醒了，吵什么呀。', '哈啊……这么快就想本小姐了？',
             '哼，还是得本小姐出马。', '唔……是谁打扰本小姐的美梦？',
             '本小姐已经休息好了，继续吧。', '哈啊……才没有睡迷糊呢。',
             '床先收起来，有事就快说。', '哼，醒了醒了，别再叫啦。'),
}

_last_lines = {}


def pick_line(category):
    options = DIALOGUE[category]
    candidates = [line for line in options if line != _last_lines.get(category)]
    selected = random.choice(candidates or options)
    _last_lines[category] = selected
    return selected


def format_limits(result):
    limits = result.get('rateLimits') or {}
    parts = []
    remaining_values = []
    for key, label, duration in (('primary', '五小时', 300), ('secondary', '每周', 10080)):
        window = limits.get(key) or {}
        used = window.get('usedPercent')
        if (window.get('windowDurationMins') == duration and
                isinstance(used, (int, float)) and not isinstance(used, bool) and math.isfinite(used)):
            remaining = max(0, min(100, 100 - used))
            remaining_values.append(remaining)
            parts.append(f'{label}剩余 {remaining:g}%')
        else:
            parts.append(f'{label}额度不可用')
    if not remaining_values:
        prefix = '本小姐暂时查不到额度：\n'
    elif min(remaining_values) <= 10:
        prefix = '本小姐查到了，额度不多了：\n'
    else:
        prefix = '本小姐查到了：\n'
    return prefix + '，'.join(parts)


def find_codex_executable():
    if os.name == 'nt':
        executable = shutil.which('codex.exe')
        if executable:
            return executable
        candidates = list((Path.home() / 'AppData/Local/OpenAI/Codex/bin').glob('*/codex.exe'))
        return str(max(candidates, key=lambda p: p.stat().st_mtime)) if candidates else None
    bundled = Path('/usr/lib/chatgpt/resources/codex')
    return str(bundled) if bundled.is_file() else shutil.which('codex')


def read_limits(timeout=10):
    state_path = Path.home() / '.codex/.codex-global-state.json'
    state = json.loads(state_path.read_text())
    expected = state['electron-persisted-atom-state']['cloud-pet-artwork-cache']['accountId']
    requests = [
        {'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'white_dragon_pet', 'version': '1.0'}}},
        {'method': 'initialized'},
        {'id': 2, 'method': 'account/rateLimits/read'},
    ]
    executable = find_codex_executable()
    if not executable:
        raise FileNotFoundError('Codex CLI 不可用')
    process = subprocess.Popen([executable, 'app-server'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    try:
        process.stdin.write(('\n'.join(map(json.dumps, requests)) + '\n').encode())
        process.stdin.flush()
        lines = queue.Queue()
        def read_output():
            for line in process.stdout:
                lines.put(line)
        threading.Thread(target=read_output, daemon=True).start()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                line = lines.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty:
                break
            response = json.loads(line)
            if response.get('id') == 2:
                result = response.get('result') or {}
                if not expected or result.get('accountId') != expected:
                    raise ValueError('Codex 账号不一致')
                return format_limits(result)
        raise TimeoutError('额度查询超时')
    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
