import unittest
from shadowcraft.calcs.rogue.Aldriana import AldrianasRogueDamageCalculator
from shadowcraft.core import exceptions
from shadowcraft.objects import buffs as _buffs
from shadowcraft.objects import race as _race
from shadowcraft.objects import stats as _stats
from shadowcraft.objects import procs as _procs
from shadowcraft.objects import talents as _talents
from shadowcraft.objects import artifact as _artifact
from shadowcraft.calcs.rogue.Aldriana import settings as _settings

class RogueDamageCalculatorTestBase(object):
    def setUp(self, spec, mh, oh, cycle,
                talent_str='1000000',
                buffs=_buffs.Buffs('short_term_haste_buff', 'flask_wod_agi', 'food_wod_versatility'),
                procs=_procs.ProcsList(),
                gear_buffs=_stats.GearBuffs('gear_specialization'),
                traits='000000000000000000',
                level=110,
                race='pandaren',
                agi=20909,
                stam=19566,
                crit=4402,
                haste=5150,
                mastery=5999,
                versatility=1515,
                response_time=0.5,
                duration=360,
                is_demon=False,
                num_boss_adds=0):

        test_race = _race.Race(race)
        test_class = 'rogue'

        # Set up a calcs object..
        test_stats = _stats.Stats(mh, oh, procs, gear_buffs, agi=agi, stam=stam, crit=crit, haste=haste, mastery=mastery, versatility=versatility)

        # Initialize talents..
        test_talents = _talents.Talents(talent_str, spec, test_class, level=level)

        #initialize artifact traits..
        test_traits = _artifact.Artifact(spec, test_class, traits)

        # Set up settings.
        test_settings = _settings.Settings(cycle, response_time=response_time, duration=duration,
                                         adv_params="", is_demon=is_demon, num_boss_adds=num_boss_adds)

        # Build a DPS object.
        self.calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_traits, buffs, test_race, spec, test_settings, level)


    def test_oh_penalty(self):
        self.assertAlmostEqual(self.calculator.oh_penalty(), 0.5)

    def test_crit_damage_modifiers(self):
        self.assertAlmostEqual(self.calculator.crit_damage_modifiers(), 1 + (2 * 1. - 1) * 1)

    def test_dps_breakdowns(self):
        # TODO: Add assertions. This at least runs it though.
        self.calculator.get_dps_breakdown()

    def test_get_talents_ranking(self):
        # TODO: Add assertions. This at least runs it though.
        self.calculator.get_talents_ranking()

    def test_get_trait_ranking(self):
        # TODO: Add assertions. This at least runs it though.
        self.calculator.get_trait_ranking()

    def test_ep(self):
        ep_values = self.calculator.get_ep()

        self.assertTrue(ep_values['agi'] < 1.5)
        self.assertTrue(ep_values['agi'] > 1.0)
        self.assertTrue(ep_values['mastery'] < 1.0)
        self.assertTrue(ep_values['mastery'] > 0.0)
        self.assertTrue(ep_values['haste'] < 1.0)
        self.assertTrue(ep_values['haste'] > 0.0)
        self.assertTrue(ep_values['versatility'] < 1.0)
        self.assertTrue(ep_values['versatility'] > 0.0)
        self.assertTrue(ep_values['crit'] < 1.0)
        self.assertTrue(ep_values['crit'] > 0.0)


class TestOutlawRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        mh = _stats.Weapon(4821.0, 2.6, 'sword', None)
        oh = _stats.Weapon(4821.0, 2.6, 'sword', None)
        cycle = _settings.OutlawCycle(blade_flurry=False,
                                          jolly_roger_reroll=1,
                                          grand_melee_reroll=1,
                                          shark_reroll=1,
                                          true_bearing_reroll=1,
                                          buried_treasure_reroll=1,
                                          broadsides_reroll=1)

        super(TestOutlawRogueDamageCalculator, self).setUp('outlaw', mh, oh, cycle)
        self.calculator.level = 110

    def test_set_constants_for_level(self):
        self.assertRaises(exceptions.InvalidLevelException, self.calculator.__setattr__, 'level', 111)


class TestAssassinationRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        mh = _stats.Weapon(4821.0, 1.8, 'dagger', None)
        oh = _stats.Weapon(4821.0, 1.8, 'dagger', None)
        cycle = _settings.AssassinationCycle()
        super(TestAssassinationRogueDamageCalculator, self).setUp('assassination', mh, oh, cycle)
        self.calculator.level = 110

    def test_set_constants_for_level(self):
        self.assertRaises(exceptions.InvalidLevelException, self.calculator.__setattr__, 'level', 111)


class TestSubtletyRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        mh = _stats.Weapon(4821.0, 2.6, 'sword', None)
        oh = _stats.Weapon(4821.0, 2.6, 'sword', None)
        cycle = _settings.SubtletyCycle(cp_builder='backstab',  dance_finishers_allowed=True, positional_uptime=0.9)

        super(TestSubtletyRogueDamageCalculator, self).setUp('subtlety', mh, oh, cycle)
        self.calculator.level = 110

    def test_set_constants_for_level(self):
        self.assertRaises(exceptions.InvalidLevelException, self.calculator.__setattr__, 'level', 111)
