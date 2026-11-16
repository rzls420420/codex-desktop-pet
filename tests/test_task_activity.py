import json
import tempfile
import unittest
from pathlib import Path

from dragon_pet.task_activity import ActivityTracker
from dragon_pet.state import PetState


def event(kind):
    return json.dumps({'type': 'event_msg', 'payload': {'type': kind}}) + '\n'


class ActivityTests(unittest.TestCase):
    def test_initial_state_and_completion_notification(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rollout-test.jsonl'
            path.write_text(event('task_started'))
            tracker = ActivityTracker(Path(directory))
            self.assertEqual(tracker.poll(), (True, 0, 0, 0))
            with path.open('a') as f:
                f.write(event('task_complete'))
            self.assertEqual(tracker.poll(), (False, 1, 0, 0))
            self.assertEqual(tracker.poll(), (False, 0, 0, 0))

    def test_aborted_does_not_report_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rollout-test.jsonl'
            path.write_text(event('task_started'))
            tracker = ActivityTracker(Path(directory))
            tracker.poll()
            with path.open('a') as f:
                f.write(event('turn_aborted'))
            self.assertEqual(tracker.poll(), (False, 0, 1, 0))

    def test_missing_active_log_releases_state_but_reports_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rollout-test.jsonl'
            path.write_text(event('task_started'))
            tracker = ActivityTracker(Path(directory))
            tracker.poll()
            path.unlink()
            self.assertEqual(tracker.poll(), (False, 0, 0, 1))
            self.assertEqual(tracker.poll(), (False, 0, 0, 0))

    def test_active_task_wakes_and_prevents_sleep(self):
        state = PetState(idle_seconds=10)
        state.tick(10)
        state.set_working(True, 11)
        self.assertEqual(state.mode, 'waking')
        state.tick(14)
        state.tick(100)
        self.assertEqual(state.mode, 'idle')
        state.set_working(False, 100)
        state.tick(109)
        self.assertEqual(state.mode, 'idle')
        state.tick(110)
        self.assertEqual(state.mode, 'sleeping')


if __name__ == '__main__':
    unittest.main()
