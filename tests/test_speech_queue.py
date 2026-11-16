import unittest

from dragon_pet.speech import SpeechQueue


class SpeechQueueTests(unittest.TestCase):
    def test_important_message_preempts_chatter_and_is_not_overwritten(self):
        q = SpeechQueue()
        q.add('闲聊', 0, priority=0)
        q.add('完成', 1, priority=2)
        q.add('闲聊2', 2, priority=0)
        self.assertEqual(q.current(2), '完成')
        self.assertIsNone(q.current(6))

    def test_important_messages_are_queued(self):
        q = SpeechQueue()
        q.add('开始', 0, priority=2)
        q.add('结束', 1, priority=2)
        self.assertEqual(q.current(1), '开始')
        self.assertEqual(q.current(5), '结束')
        self.assertIsNone(q.current(10))

    def test_delayed_wakeup_message(self):
        q = SpeechQueue()
        q.add('醒了', 0, priority=1, delay=3)
        self.assertIsNone(q.current(2))
        self.assertEqual(q.current(3), '醒了')


if __name__ == '__main__':
    unittest.main()
