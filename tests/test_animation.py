import unittest

from dragon_pet.animation import ANIMATIONS, AnimationSchedule, roam_x


class AnimationScheduleTests(unittest.TestCase):
    def test_idle_rotation_shows_every_group(self):
        schedule = AnimationSchedule()
        shown = {schedule.current(i * 8, False) for i in range(len(ANIMATIONS))}
        self.assertEqual(shown, set(ANIMATIONS))

    def test_work_rotation_stays_work_focused(self):
        schedule = AnimationSchedule()
        self.assertEqual([schedule.current(i * 8, True) for i in range(3)],
                         ['running', 'waiting', 'review'])

    def test_temporary_animation_can_wait_until_wake_finishes(self):
        schedule = AnimationSchedule()
        schedule.play('waving', 10, delay=3, duration=4)
        self.assertNotEqual(schedule.current(12, True), 'waving')
        self.assertEqual(schedule.current(13, True), 'waving')
        self.assertNotEqual(schedule.current(17, True), 'waving')

    def test_unknown_animation_is_rejected(self):
        with self.assertRaises(ValueError):
            AnimationSchedule().play('unknown', 0)

    def test_roaming_stays_inside_screen_and_does_not_snap(self):
        self.assertEqual(roam_x(695, 300, 0, 1000, 1, 10), 700)
        self.assertEqual(roam_x(3, 300, 0, 1000, -1, 10), 0)
        self.assertEqual(roam_x(-30, 300, 0, 1000, -1, 2), -30)
