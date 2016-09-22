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
    def setUp(self):
        self.talent_str = '1000000'
        self.buffs = _buffs.Buffs('short_term_haste_buff', 'flask_wod_agi', 'food_wod_versatility')
        self.procs = _procs.ProcsList()
        self.gear_buffs = _stats.GearBuffs('gear_specialization')
        self.traits = '000000000000000000'
        self.level = 110
        self.race = 'pandaren'
        self.agi = 20909
        self.stam = 19566
        self.crit = 4402
        self.haste = 5150
        self.mastery = 5999
        self.versatility = 1515
        self.response_time = 0.5
        self.duration = 360
        self.is_demon = False
        self.num_boss_adds = 0
        self.adv_params = 0

    def buildSpecDefaults(self, spec, weapon_dps=2100):
        self.spec = spec
        if spec == "outlaw":
            self.mh = _stats.Weapon(weapon_dps * 2.6, 2.6, 'sword', None)
            self.oh = _stats.Weapon(weapon_dps * 2.6, 2.6, 'sword', None)
            self.cycle = _settings.OutlawCycle(blade_flurry=False,
                                              jolly_roger_reroll=1,
                                              grand_melee_reroll=1,
                                              shark_reroll=1,
                                              true_bearing_reroll=1,
                                              buried_treasure_reroll=1,
                                              broadsides_reroll=1)
        elif spec == "assassination":
            self.mh = _stats.Weapon(weapon_dps * 1.8, 1.8, 'dagger', None)
            self.oh = _stats.Weapon(weapon_dps * 1.8, 1.8, 'dagger', None)
            self.cycle = _settings.AssassinationCycle()
        elif spec == "subtlety":
            self.mh = _stats.Weapon(weapon_dps * 1.8, 1.8, 'dagger', None)
            self.oh = _stats.Weapon(weapon_dps * 1.8, 1.8, 'dagger', None)
            self.cycle = _settings.SubtletyCycle(cp_builder='backstab',  dance_finishers_allowed=True, positional_uptime=0.9)
        else:
            raise "Invalid spec: %s" % spec


    def buildCalculator(self):
        test_race = _race.Race(self.race)
        test_class = 'rogue'

        # Set up a calcs object..
        test_stats = _stats.Stats(self.mh, self.oh, self.procs,
                                    self.gear_buffs,
                                    agi=self.agi,
                                    stam=self.stam,
                                    crit=self.crit,
                                    haste=self.haste,
                                    mastery=self.mastery,
                                    versatility=self.versatility)

        # Initialize talents..
        test_talents = _talents.Talents(self.talent_str, self.spec, test_class, level=self.level)

        #initialize artifact traits..
        test_traits = _artifact.Artifact(self.spec, test_class, self.traits)

        # Set up settings.
        test_settings = _settings.Settings(self.cycle, response_time=self.response_time, duration=self.duration,
                                         adv_params=self.adv_params, is_demon=self.is_demon, num_boss_adds=self.num_boss_adds)

        self.calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_traits, self.buffs, test_race, self.spec, test_settings, self.level)
        self.calculator.level = 110

    def test_oh_penalty(self):
        self.assertAlmostEqual(self.calculator.oh_penalty(), 0.5)

    def test_crit_damage_modifiers(self):
        self.assertAlmostEqual(self.calculator.crit_damage_modifiers(), 1 + (2 * 1. - 1) * 1)

    def test_dps_breakdowns(self):
        # TODO: Add assertions. This at least runs it though.
        print "DPS Breakdown"
        print(self.calculator.get_dps_breakdown())

    def test_get_talents_ranking(self):
        # TODO: Add assertions. This at least runs it though.
        print "Talent ranking"
        print(self.calculator.get_talents_ranking())

    def test_get_trait_ranking(self):
        # TODO: Add assertions. This at least runs it though.
        print "Trait ranking"
        print(self.calculator.get_trait_ranking())

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

    def test_set_constants_for_level(self):
        self.assertRaises(exceptions.InvalidLevelException, self.calculator.__setattr__, 'level', 111)

## Single target

class TestOutlawRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        super(TestOutlawRogueDamageCalculator, self).setUp()
        self.buildSpecDefaults('outlaw')
        self.num_boss_adds = 0
        self.buildCalculator()


class TestAssassinationRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        super(TestAssassinationRogueDamageCalculator, self).setUp()
        self.buildSpecDefaults('assassination')
        self.num_boss_adds = 0
        self.buildCalculator()


class TestSubtletyRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        super(TestSubtletyRogueDamageCalculator, self).setUp()
        self.buildSpecDefaults('subtlety')
        self.num_boss_adds = 0
        self.buildCalculator()

## Multi-target

class TestAOEOutlawRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        super(TestAOEOutlawRogueDamageCalculator, self).setUp()
        self.buildSpecDefaults('outlaw')
        self.num_boss_adds = 3
        self.buildCalculator()


class TestAOEAssassinationRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        super(TestAOEAssassinationRogueDamageCalculator, self).setUp()
        self.buildSpecDefaults('assassination')
        self.num_boss_adds = 3
        self.buildCalculator()


class TestAOESubtletyRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        super(TestAOESubtletyRogueDamageCalculator, self).setUp()
        self.buildSpecDefaults('subtlety')
        self.num_boss_adds = 3
        self.buildCalculator()