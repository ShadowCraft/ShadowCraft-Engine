import unittest
from shadowcraft.core import exceptions
from shadowcraft.objects import buffs

class TestBuffsTrue(unittest.TestCase):
    def setUp(self):
        self.buffs = buffs.Buffs(*buffs.Buffs.allowed_buffs)

    def test_exception(self):
        self.assertRaises(buffs.InvalidBuffException, buffs.Buffs, 'fake_buff')

    def test__getattr__(self):
        self.assertRaises(AttributeError, self.buffs.__getattr__, 'fake_buff')
        self.assertTrue(self.buffs.flask_wod_agi_200)

    def test_buff_agi(self):
        self.assertEqual(self.buffs.buff_agi(), 2100)


class TestBuffsFalse(unittest.TestCase):
    def setUp(self):
        self.buffs = buffs.Buffs()

    def test__getattr__(self):
        self.assertRaises(AttributeError, self.buffs.__getattr__, 'fake_buff')
        self.assertFalse(self.buffs.flask_legion_agi)

    def test_flask_legion_agi(self):
        self.assertEqual(self.buffs.flask_legion_agi, False)

    def test_food_legion_mastery_225(self):
        self.assertEqual(self.buffs.food_legion_mastery_225, False)

    def test_food_legion_crit_225(self):
        self.assertEqual(self.buffs.food_legion_crit_225, False)

    def test_food_legion_haste_225(self):
        self.assertEqual(self.buffs.food_legion_haste_225, False)

    def test_food_legion_versatility_225(self):
        self.assertEqual(self.buffs.food_legion_versatility_225, False)

    def test_food_legion_mastery_300(self):
        self.assertEqual(self.buffs.food_legion_mastery_300, False)

    def test_food_legion_crit_300(self):
        self.assertEqual(self.buffs.food_legion_crit_300, False)

    def test_food_legion_haste_300(self):
        self.assertEqual(self.buffs.food_legion_haste_300, False)

    def test_food_legion_versatility_300(self):
        self.assertEqual(self.buffs.food_legion_versatility_300, False)

    def test_food_legion_mastery_375(self):
        self.assertEqual(self.buffs.food_legion_mastery_375, False)

    def test_food_legion_crit_375(self):
        self.assertEqual(self.buffs.food_legion_crit_375, False)

    def test_food_legion_haste_375(self):
        self.assertEqual(self.buffs.food_legion_haste_375, False)

    def test_food_legion_versatility_375(self):
        self.assertEqual(self.buffs.food_legion_versatility_375, False)

    def test_food_legion_damage_1(self):
        self.assertEqual(self.buffs.food_legion_damage_1, False)

    def test_food_legion_damage_2(self):
        self.assertEqual(self.buffs.food_legion_damage_2, False)

    def test_food_legion_damage_3(self):
        self.assertEqual(self.buffs.food_legion_damage_3, False)

    def test_food_legion_feast_150(self):
        self.assertEqual(self.buffs.food_legion_feast_150, False)

    def test_food_legion_feast_200(self):
        self.assertEqual(self.buffs.food_legion_feast_200, False)