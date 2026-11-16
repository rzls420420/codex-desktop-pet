import unittest

from dragon_pet.monitor import is_codex_main, next_action


class MonitorTests(unittest.TestCase):
    def test_only_main_desktop_process_matches(self):
        self.assertTrue(is_codex_main(['/usr/lib/chatgpt/ChatGPT']))
        self.assertFalse(is_codex_main(['/usr/lib/chatgpt/ChatGPT', '--type=renderer']))
        self.assertFalse(is_codex_main(['/usr/lib/chatgpt/resources/codex', 'app-server']))

    def test_codex_plus_plus_combined_argv_is_recognized(self):
        args = ['/usr/lib/chatgpt/ChatGPT --remote-debugging-port=9229 --remote-allow-origins=http://127.0.0.1:9229']
        self.assertTrue(is_codex_main(args, '/usr/lib/chatgpt/ChatGPT'))

    def test_child_process_rejected_with_combined_argv(self):
        args = ['/usr/lib/chatgpt/ChatGPT --type=renderer --remote-debugging-port=9229']
        self.assertFalse(is_codex_main(args, '/usr/lib/chatgpt/ChatGPT'))

    def test_executable_path_cannot_be_spoofed_by_arguments(self):
        self.assertFalse(is_codex_main(['/usr/lib/chatgpt/ChatGPT'], '/usr/bin/other'))

    def test_start_and_stop_only_on_session_transitions(self):
        self.assertEqual(next_action(False, True, False), 'start')
        self.assertIsNone(next_action(True, True, False))
        self.assertEqual(next_action(True, False, True), 'stop')
        self.assertIsNone(next_action(False, False, False))


if __name__ == '__main__':
    unittest.main()
