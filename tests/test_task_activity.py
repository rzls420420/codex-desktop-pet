import json
import os
import tempfile
import unittest
from pathlib import Path

from dragon_pet.task_activity import ActivityTracker
from dragon_pet.state import PetState


def event(kind):
    return json.dumps({'type': 'event_msg', 'payload': {'type': kind}}) + '\n'


def tokens(input_tokens=90000, cached=45000, output=1000, window=272000):
    return json.dumps({'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
        'last_token_usage': {'input_tokens': input_tokens, 'cached_input_tokens': cached,
                             'output_tokens': output}, 'model_context_window': window}}}) + '\n'


class ActivityTests(unittest.TestCase):
    def test_large_active_session_restores_start_before_tail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rollout-large.jsonl'
            path.write_text(event('task_started') + ('{}\n' * 400000) + tokens())
            tracker = ActivityTracker(directory)
            self.assertEqual(tracker.poll(), (True, 0, 0, 0))
            self.assertEqual(tracker.context_usage(), (91000, 272000, 50.0))

    def test_most_recent_active_session_is_selected(self):
        with tempfile.TemporaryDirectory() as directory:
            older = Path(directory) / 'rollout-old.jsonl'
            newer = Path(directory) / 'rollout-new.jsonl'
            older.write_text(event('task_started') + tokens(input_tokens=10000))
            newer.write_text(event('task_started') + tokens(input_tokens=90000))
            now = older.stat().st_mtime_ns
            os.utime(older, ns=(now - 1000000000, now - 1000000000))
            os.utime(newer, ns=(now, now))
            tracker = ActivityTracker(directory)
            tracker.poll()
            self.assertEqual(tracker.context_usage(), (91000, 272000, 50.0))

    def test_active_context_usage_is_taken_from_latest_request(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rollout-test.jsonl'
            path.write_text(event('task_started') + tokens())
            tracker = ActivityTracker(directory)
            tracker.poll()
            self.assertEqual(tracker.context_usage(), (91000, 272000, 50.0))
            with path.open('a') as stream:
                stream.write(event('task_complete'))
            tracker.poll()
            self.assertIsNone(tracker.context_usage())

    def test_new_turn_does_not_reuse_previous_turn_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rollout-test.jsonl'
            path.write_text(event('task_started') + tokens() + event('task_complete') + event('task_started'))
            tracker = ActivityTracker(directory)
            tracker.poll()
            self.assertIsNone(tracker.context_usage())

    def test_invalid_usage_does_not_fabricate_cache_rate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rollout-test.jsonl'
            path.write_text(event('task_started') + tokens(input_tokens=0, cached=0))
            tracker = ActivityTracker(directory)
            tracker.poll()
            self.assertEqual(tracker.context_usage(), (1000, 272000, None))

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
