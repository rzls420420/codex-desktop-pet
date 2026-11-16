import os
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PyQt5.QtWidgets import QApplication

from dragon_pet.app import PetWindow
from dragon_pet.speech import SpeechQueue


class FakeActivity:
    def __init__(self):
        self.result = (False, 0, 0, 0)

    def poll(self):
        result = self.result
        self.result = (result[0], 0, 0, 0)
        return result


class PetWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        with patch('dragon_pet.app.ActivityTracker', FakeActivity):
            self.window = PetWindow()
        self.window.timer.stop()
        self.window.activity_timer.stop()
        self.window.speech = SpeechQueue()

    def tearDown(self):
        self.window.close()

    def test_task_start_and_completion_are_both_visible(self):
        with patch.object(self.window, 'now', return_value=10):
            self.window.activity.result = (True, 0, 0, 0)
            self.window.check_activity()
            start = self.window.speech.current(10)
            self.window.activity.result = (False, 1, 0, 0)
            self.window.check_activity()
            self.window.talk('自动闲聊', priority=0)
            self.assertEqual(self.window.speech.current(11), start)
            self.assertIn('一轮', self.window.speech.current(15))

    def test_aborted_turn_is_not_announced_as_complete(self):
        with patch.object(self.window, 'now', return_value=10):
            self.window.state.working = True
            self.window.activity.result = (False, 0, 1, 0)
            self.window.check_activity()
            message = self.window.speech.current(10)
            self.assertTrue('中止' in message or '中断' in message)

    def test_task_wakes_sleeping_pet(self):
        with patch.object(self.window, 'now', return_value=10):
            self.window.state.sleep(0)
            self.window.activity.result = (True, 0, 0, 0)
            self.window.check_activity()
            self.assertEqual(self.window.state.mode, 'waking')
            self.assertTrue(self.window.state.working)

    def test_roaming_moves_only_when_not_working_or_dragged(self):
        with patch.object(self.window, 'now', return_value=10):
            self.window.move(100, 100)
            self.window.animations.play('running-right', 10)
            self.window.refresh()
            self.assertEqual(self.window.x(), 102)
            self.window.drag = object()
            self.window.refresh()
            self.assertEqual(self.window.x(), 102)
            self.window.drag = None
            self.window.state.working = True
            self.window.refresh()
            self.assertEqual(self.window.x(), 102)


if __name__ == '__main__':
    unittest.main()
