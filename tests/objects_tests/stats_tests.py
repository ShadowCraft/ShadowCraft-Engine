import unittest
from shadowcraft.core import exceptions
from shadowcraft.objects import stats
from shadowcraft.objects import procs

class TestStats(unittest.TestCase):
    def setUp(self):
        mainhand = stats.Weapon(1234, 2.6, "sword")
        offhand = stats.Weapon(777, 2.6, "sword")
        self.stats = stats.Stats(mainhand, offhand, procs.ProcsList(), None, str=20, agi=3485, int=190, stam=1086, crit=899, haste=666, mastery=1234, versatility=1222, level=110)

    def test_stats(self):
        self.assertEqual(self.stats.agi, 3485)

    def test_set_constants_for_level(self):
        self.assertRaises(exceptions.InvalidLevelException, self.stats.__setattr__, 'level', 111)

    def test_get_mastery_from_rating(self):
        self.assertAlmostEqual(self.stats.get_mastery_from_rating(), 8 + 1234 / 350.0)
        self.assertAlmostEqual(self.stats.get_mastery_from_rating(100),  8 + 100 / 350.0)

    def test_get_versatility_multiplier_from_rating(self):
        self.assertAlmostEqual(self.stats.get_versatility_multiplier_from_rating(), 1 + 1222 / 40000.0)
        self.assertAlmostEqual(self.stats.get_versatility_multiplier_from_rating(100), 1 + 100 / 40000.0)

    def test_get_crit_from_rating(self):
        self.assertAlmostEqual(self.stats.get_crit_from_rating(), 899 / 35000.0)
        self.assertAlmostEqual(self.stats.get_crit_from_rating(100), 100 / 35000.0)

    def test_get_haste_multiplier_from_rating(self):
        self.assertAlmostEqual(self.stats.get_haste_multiplier_from_rating(), 1 + 666 / 32500.0)
        self.assertAlmostEqual(self.stats.get_haste_multiplier_from_rating(100), 1 + 100 / 32500.0)


class TestGearBuffs(unittest.TestCase):
    def setUp(self):
        self.gear = stats.GearBuffs('chaotic_metagem', 'gear_specialization', 'rogue_t11_2pc', 'potion_of_the_tolvir', 'engineer_glove_enchant', 'lifeblood')
        self.gear_none = stats.GearBuffs()

    def test__getattr__(self):
        self.assertTrue(self.gear.chaotic_metagem)
        self.assertTrue(self.gear.gear_specialization)
        self.assertFalse(self.gear.rogue_t16_2pc)
        self.assertRaises(AttributeError, self.gear.__getattr__, 'fake_gear_buff')

    def test_metagem_crit_multiplier(self):
        self.assertAlmostEqual(self.gear.metagem_crit_multiplier(), 1.03)
        self.assertAlmostEqual(self.gear_none.metagem_crit_multiplier(), 1.0)

    def test_gear_specialization_multiplier(self):
        self.assertAlmostEqual(self.gear.gear_specialization_multiplier(), 1.05)
        self.assertAlmostEqual(self.gear_none.gear_specialization_multiplier(), 1.0)
