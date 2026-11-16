import unittest

from dragon_pet.state import PetState


class PetStateTests(unittest.TestCase):
    def test_sleep_sequence_loops_until_woken(self):
        state = PetState(idle_seconds=10)
        state.tick(10)
        self.assertEqual(state.mode, 'sleeping')
        self.assertEqual(state.frame(10), 0)
        self.assertEqual(state.frame(14), 4)
        self.assertIn(state.frame(30), (3, 4))
        state.wake(40)
        self.assertEqual(state.mode, 'waking')
        self.assertEqual(state.frame(40), 5)
        state.tick(44)
        self.assertEqual(state.mode, 'idle')

    def test_interaction_resets_idle_timer(self):
        state = PetState(idle_seconds=10)
        state.wake(8)
        state.tick(10)
        self.assertEqual(state.mode, 'idle')
        state.tick(18)
        self.assertEqual(state.mode, 'sleeping')


if __name__ == '__main__':
    unittest.main()
