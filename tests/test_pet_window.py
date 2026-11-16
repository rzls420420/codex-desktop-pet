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

    def context_usage(self):
        return (91000, 272000, 50.0)


class PetWindowTests(unittest.TestCase):
    def test_long_status_expands_bubble_without_moving_pet_bottom(self):
        with patch.object(self.window, 'now', return_value=30):
            self.window.move(100, 150)
            original_bottom = self.window.geometry().bottom()
            self.window.talk('还是要看本小姐的：\n上下文 108.7k / 272.0k\n本次请求缓存命中 100%')
            self.window.refresh()
            self.assertGreater(self.window.height(), 380)
            self.assertEqual(self.window.geometry().bottom(), original_bottom)
            bubble, text = self.window.speech_rectangles(self.window.speech.current(30))
            self.assertGreaterEqual(text.height(), self.window.speech_text_height(self.window.speech.current(30)) + 16)
            self.assertLessEqual(bubble.bottom(), self.window.height() - 296)

    def test_short_speech_retains_default_window_size(self):
        with patch.object(self.window, 'now', return_value=30):
            self.window.talk('本小姐来了。')
            self.window.refresh()
            self.assertEqual(self.window.size().width(), 300)
            self.assertEqual(self.window.size().height(), 380)

    def test_cache_status_has_extra_height_even_when_text_fits(self):
        bubble, _ = self.window.speech_rectangles('缓存命中 97%')
        self.assertGreaterEqual(bubble.height(), 82)

    def test_window_returns_to_default_after_long_speech_expires(self):
        with patch.object(self.window, 'now', return_value=30) as now:
            self.window.move(100, 150)
            bottom = self.window.geometry().bottom()
            self.window.talk('还是要看本小姐的：\n上下文 108.7k / 272.0k\n本次请求缓存命中 100%')
            self.window.refresh()
            now.return_value = 36
            self.window.refresh()
            self.assertEqual(self.window.height(), 380)
            self.assertEqual(self.window.geometry().bottom(), bottom)

    def test_context_speech_only_during_work(self):
        with patch.object(self.window, 'now', return_value=30):
            self.window.check_activity()
            self.assertIsNone(self.window.speech.current(30))
            self.window.state.working = True
            self.window.activity.result = (True, 0, 0, 0)
            self.window.check_activity()
            self.assertIn('91.0k / 272.0k', self.window.speech.current(30))
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
