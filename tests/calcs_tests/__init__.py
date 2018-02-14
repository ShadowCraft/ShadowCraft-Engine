from shadowcraft import calcs
import unittest
from shadowcraft.core import exceptions
from shadowcraft.objects import buffs
from shadowcraft.objects import race
from shadowcraft.objects import stats
from shadowcraft.objects import procs
from shadowcraft.objects import talents

class TestDamageCalculator(unittest.TestCase):
    def make_calculator(self, buffs_list=[], gear_buffs_list=[], race_name='night_elf', test_spec='outlaw'):
        test_buffs = buffs.Buffs(*buffs_list)
        test_gear_buffs = stats.GearBuffs(*gear_buffs_list)
        test_procs = procs.ProcsList()
        test_mh = stats.Weapon(737, 1.8, 'dagger')
        test_oh = stats.Weapon(573, 1.4, 'dagger')
        test_ranged = stats.Weapon(1104, 2.0, 'thrown')
        test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                         agi=20909,
                         stam=19566,
                         crit=4402,
                         haste=5150,
                         mastery=5999,
                         versatility=1515)
        test_race = race.Race(race_name)
        test_talents = talents.Talents('1000000', test_spec, 'rogue', level=110)
        return calcs.DamageCalculator(test_stats, test_talents, test_buffs, test_race, 'outlaw')

    def setUp(self):
        self.calculator = self.make_calculator()

    def test_melee_hit_chance(self):
        pass

    def test_one_hand_melee_hit_chance(self):
        self.assertAlmostEqual(
            self.calculator.one_hand_melee_hit_chance(dodgeable=False, parryable=False), 1.0)
        self.assertAlmostEqual(
            self.calculator.one_hand_melee_hit_chance(dodgeable=True, parryable=False), 1.0)
        self.assertAlmostEqual(
            self.calculator.one_hand_melee_hit_chance(dodgeable=True, parryable=True), 1.0 - 0.03)
        self.assertAlmostEqual(
            self.calculator.one_hand_melee_hit_chance(dodgeable=False, parryable=True), 1.0 - 0.03)

    def test_dual_wield_mh_hit_chance(self):
        self.assertAlmostEqual(self.calculator.dual_wield_mh_hit_chance(dodgeable=False, parryable=False), 1.0 - 0.19)
        self.assertAlmostEqual(self.calculator.dual_wield_mh_hit_chance(dodgeable=True, parryable=False), 1.0 - 0.19)
        self.assertAlmostEqual(self.calculator.dual_wield_mh_hit_chance(dodgeable=False, parryable=True), 1.0 - 0.19 - 0.03)
        self.assertAlmostEqual(self.calculator.dual_wield_mh_hit_chance(dodgeable=True, parryable=True), 1.0 - 0.19 - 0.03)
