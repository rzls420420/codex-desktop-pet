import os
import sys
import time
from pathlib import Path

from PyQt5.QtCore import QRect, Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt5.QtWidgets import QApplication, QMenu, QWidget

from dragon_pet.state import PetState
from dragon_pet.animation import ANIMATIONS, AnimationSchedule, roam_x
from dragon_pet.dialogue import pick_line, read_limits
from dragon_pet.speech import SpeechQueue
from dragon_pet.task_activity import ActivityTracker

def resource_root():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))


class LimitsWorker(QThread):
    result = pyqtSignal(str)

    def run(self):
        try:
            self.result.emit(read_limits())
        except (OSError, ValueError, KeyError, TimeoutError):
            self.result.emit('额度暂时查不到，稍后再试。')


def load_hd_frames(state, count):
    root = resource_root() / 'assets/transparent-v2' / state
    frames = [QPixmap(str(root / f'{index:02d}.png')) for index in range(count)]
    if any(frame.isNull() for frame in frames):
        raise RuntimeError(f'找不到白龙小姐动作素材：{state}')
    return frames


class PetWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowTitle('白龙小姐桌面宠物')
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(300, 380)
        self.origin = time.monotonic()
        self.state = PetState()
        self.animations = AnimationSchedule()
        self.activity = ActivityTracker()
        self.sleep_images = load_hd_frames('sleep', 8)
        self.images = {}
        for name, (count, _) in ANIMATIONS.items():
            self.images[name] = load_hd_frames(name, count)
        self.animations.play('waving', 0, duration=4)
        self.current_animation = None
        self.next_auto_speech = 45
        self.speech = SpeechQueue()
        self.talk(pick_line('startup'))
        self.drag = None
        self.limits_worker = None
        geometry = QApplication.primaryScreen().availableGeometry()
        self.move(geometry.right() - self.width() - 30, geometry.bottom() - self.height() - 30)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(120)
        self.activity_timer = QTimer(self)
        self.activity_timer.timeout.connect(self.check_activity)
        self.check_activity()
        self.activity_timer.start(2000)

    def now(self):
        return time.monotonic() - self.origin

    def refresh(self):
        previous = self.state.mode
        self.state.tick(self.now())
        if previous == 'idle' and self.state.mode == 'sleeping':
            self.talk(pick_line('sleep'))
        if self.state.mode == 'idle':
            name = self.animations.current(self.now(), self.state.working)
            if (not self.state.working and name != self.current_animation and name != 'idle'
                    and self.now() >= self.next_auto_speech):
                category = f'ambient-{name}' if name in ('running', 'waiting', 'review') else name
                self.talk(pick_line(category), priority=0)
                self.next_auto_speech = self.now() + 60
            self.current_animation = name
            if not self.state.working and self.drag is None and name in ('running-left', 'running-right'):
                screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
                area = screen.availableGeometry()
                direction = 1 if name == 'running-right' else -1
                x = roam_x(self.x(), self.width(), area.left(), area.right() + 1, direction)
                self.move(x, self.y())
        else:
            self.current_animation = None
        self.update()

    def play_animation(self, name, duration=4):
        now = self.now()
        delay = max(0, self.state.started + 3 - now) if self.state.mode == 'waking' else 0
        self.animations.play(name, now, delay=delay, duration=duration)

    def talk(self, text, priority=1, delay=0):
        self.speech.add(text, self.now(), priority=priority, delay=delay)

    def check_activity(self):
        working, completed, aborted, missing = self.activity.poll()
        was_working = self.state.working
        self.state.set_working(working, self.now())
        if working and not was_working:
            self.play_animation('running-right')
            self.talk(pick_line('task-start'), priority=2)
        if completed:
            self.play_animation('jumping')
            self.talk(pick_line('task-complete'), priority=2)
        if aborted:
            self.play_animation('failed')
            self.talk(pick_line('task-aborted'), priority=2)
        if missing:
            self.talk(pick_line('task-unknown'), priority=2)

    def paintEvent(self, event):
        now = self.now()
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        speech = self.speech.current(now)
        if speech:
            p.setBrush(QColor(255, 255, 255, 240))
            p.setPen(QColor('#a394bc'))
            p.drawRoundedRect(QRect(12, 8, 276, 66), 9, 9)
            p.setFont(QFont('Sans Serif', 11))
            p.setPen(QColor('#30263b'))
            p.drawText(QRect(22, 14, 256, 54), Qt.AlignCenter | Qt.TextWordWrap, speech)
        if self.state.mode == 'idle':
            name = self.animations.current(now, self.state.working)
            images = self.images[name]
            image = images[int(now * 4) % len(images)]
        else:
            image = self.sleep_images[self.state.frame(now)]
        target = image.size().scaled(286, 296, Qt.KeepAspectRatio)
        p.drawPixmap((self.width() - target.width()) // 2, self.height() - target.height(),
                     target.width(), target.height(), image)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = event.globalPos() - self.frameGeometry().topLeft()
            was_sleeping = self.state.mode == 'sleeping'
            self.state.wake(self.now())
            self.play_animation('waving')
            self.talk(pick_line('wake' if was_sleeping else 'interaction'), delay=3 if was_sleeping else 0)

    def mouseMoveEvent(self, event):
        if self.drag is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag)

    def mouseReleaseEvent(self, event):
        self.drag = None

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        sleep = menu.addAction('立即睡觉')
        wake = menu.addAction('叫醒')
        limits = menu.addAction('查看 Codex 剩余额度')
        preview = menu.addMenu('预览动作')
        previews = {preview.addAction(label): name for name, (_, label) in ANIMATIONS.items()}
        menu.addSeparator()
        quit_action = menu.addAction('退出')
        chosen = menu.exec_(event.globalPos())
        if chosen == sleep:
            if self.state.working:
                self.talk('本小姐正在处理任务，暂时不能睡。')
            else:
                self.state.sleep(self.now())
                self.talk(pick_line('sleep'))
        elif chosen == wake:
            was_sleeping = self.state.mode == 'sleeping'
            self.state.wake(self.now())
            self.talk(pick_line('wake'), delay=3 if was_sleeping else 0)
        elif chosen == limits:
            if self.limits_worker is None or not self.limits_worker.isRunning():
                self.talk('本小姐正在查额度……')
                self.limits_worker = LimitsWorker(self)
                self.limits_worker.result.connect(lambda text: self.talk(text, priority=2))
                self.limits_worker.start()
        elif chosen in previews:
            self.state.wake(self.now())
            name = previews[chosen]
            self.play_animation(name)
            self.talk(pick_line(name))
        elif chosen == quit_action:
            QApplication.quit()


def main():
    app = QApplication(sys.argv)
    window = PetWindow()
    window.show()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
