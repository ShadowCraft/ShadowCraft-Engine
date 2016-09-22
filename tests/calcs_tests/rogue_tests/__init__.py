import unittest
from shadowcraft.calcs.rogue.Aldriana import AldrianasRogueDamageCalculator
from shadowcraft.core import exceptions
from shadowcraft.objects import buffs as _buffs
from shadowcraft.objects import race as _race
from shadowcraft.objects import stats as _stats
from shadowcraft.objects import procs as _procs
from shadowcraft.objects import talents as _talents
from shadowcraft.objects import artifact as _artifact
from shadowcraft.objects import artifact_data as artifact_data
from shadowcraft.calcs.rogue.Aldriana import settings as _settings

class RogueDamageCalculatorFactory:
    def __init__(self, spec, **kwargs):
        self.class_name = 'rogue'
        self.talent_str = '0000000'
        self.buffs = _buffs.Buffs('short_term_haste_buff', 'flask_wod_agi', 'food_wod_versatility')
        self.procs = _procs.ProcsList()
        self.gear_buffs = _stats.GearBuffs('gear_specialization')
        self.traits = '000000000000000000'
        self.level = 110
        self.race = 'pandaren'
        self.agi = 21122
        self.stam = 28367
        self.crit = 6306
        self.haste = 3260
        self.mastery = 3706
        self.versatility = 3486
        self.response_time = 0.5
        self.duration = 360
        self.is_demon = False
        self.num_boss_adds = 0
        self.adv_params = 0
        self.finisher_threshold = 5
        self.buildSpecDefaults(spec)
        self.__dict__.update(kwargs)

    def buildSpecDefaults(self, spec, weapon_dps=2100):
        self.spec = spec
        if spec == "outlaw":
            self.talent_str = '1010022'
            self.mh = _stats.Weapon(weapon_dps * 2.6, 2.6, 'sword', None)
            self.oh = _stats.Weapon(weapon_dps * 2.6, 2.6, 'sword', None)
            self.cycle = _settings.OutlawCycle(blade_flurry=False,
                                              jolly_roger_reroll=1,
                                              grand_melee_reroll=1,
                                              shark_reroll=1,
                                              true_bearing_reroll=1,
                                              buried_treasure_reroll=1,
                                              broadsides_reroll=1,
                                              between_the_eyes_policy='never')
        elif spec == "assassination":
            self.talent_str = '2101220'
            self.mh = _stats.Weapon(weapon_dps * 1.8, 1.8, 'dagger', None)
            self.oh = _stats.Weapon(weapon_dps * 1.8, 1.8, 'dagger', None)
            self.cycle = _settings.AssassinationCycle()
        elif spec == "subtlety":
            self.talent_str = '2100120'
            self.mh = _stats.Weapon(weapon_dps * 1.8, 1.8, 'dagger', None)
            self.oh = _stats.Weapon(weapon_dps * 1.8, 1.8, 'dagger', None)
            self.cycle = _settings.SubtletyCycle(cp_builder='backstab',  dance_finishers_allowed=True, positional_uptime=0.9)
        else:
            raise "Invalid spec: %s" % spec


    def build(self, **kwargs):
        self.__dict__.update(kwargs)

        test_race = _race.Race(self.race)

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
        test_talents = _talents.Talents(self.talent_str, self.spec, self.class_name, level=self.level)

        #initialize artifact traits..
        test_traits = _artifact.Artifact(self.spec, self.class_name, self.traits)

        # Set up settings.
        test_settings = _settings.Settings(self.cycle, response_time=self.response_time, duration=self.duration,
                                         adv_params=self.adv_params, is_demon=self.is_demon, num_boss_adds=self.num_boss_adds)

        self.calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_traits, self.buffs, test_race, self.spec, test_settings, self.level)
        self.calculator.level = 110
        return self.calculator

class RogueDamageCalculatorTestBase:
    def compare(self, a, b, method=None):
        calc_a = self.factory.build(**a)
        calc_b = self.factory.build(**b)
        if method is not None:
            return (getattr(calc_a, method)(), getattr(calc_b, method)())
        else:
            return (a, b)

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

    def test_set_constants_for_level(self):
        self.assertRaises(exceptions.InvalidLevelException, self.calculator.__setattr__, 'level', 111)

## Single target

class TestOutlawRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        self.factory = RogueDamageCalculatorFactory('outlaw')
        self.calculator = self.factory.build()

    # This is a dumb test but illustrates how we can test changes in a calculator
    def test_mastery_helps_dps(self):
        a, b = self.compare({"mastery": 3706}, {"mastery": 4706}, "get_dps_breakdown")
        self.assertGreater(b["main_gauche"], a["main_gauche"])

    def test_cursed_edges_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '010000000000000000'}, 'get_dps')
        self.assertGreater(b, a)

    def test_fates_thirst_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '001000000000000000'}, 'get_dps')
        self.assertGreater(b, a)

    def test_blade_dancer_single_target_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000100000000000000', 'num_boss_adds': 0}, 'get_dps')
        self.assertEqual(b, a)

    def test_blade_dancer_multi_target_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000100000000000000', 'num_boss_adds': 3}, 'get_dps')
        self.assertGreater(b, a)

    def test_fatebringer_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000010000000000000'}, 'get_dps')
        self.assertGreater(b, a)

    def test_gunslinger_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000001000000000000'}, 'get_dps')
        self.assertGreater(b, a)

    def test_hidden_blade_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000100000000000'}, 'get_dps')
        self.assertGreater(b, a)

    def test_fortune_strikes_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000010000000000'}, 'get_dps')
        self.assertGreater(b, a)

    def test_ghostly_shell_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000001000000000'}, 'get_dps')
        self.assertEqual(b, a)

    def test_deception_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000000100000000'}, 'get_dps')
        self.assertEqual(b, a)

    def test_black_powder_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000000010000000'}, 'get_dps')
        self.assertGreater(b, a)

    def test_greed_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000000001000000'}, 'get_dps')
        self.assertGreater(b, a)

    def test_blurred_time_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000000000100000'}, 'get_dps')
        self.assertGreater(b, a)

    def test_fortunes_boon_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000000000010000'}, 'get_dps')
        self.assertGreater(b, a)

    def test_fortunes_strike_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000000000001000'}, 'get_dps')
        self.assertGreater(b, a)

        a, b2 = self.compare({'traits': '000000000000000000'}, {'traits': '000000000000002000'}, 'get_dps')
        self.assertGreater(b2, b)

        a, b3 = self.compare({'traits': '000000000000000000'}, {'traits': '000000000000003000'}, 'get_dps')
        self.assertGreater(b3, b2)

    def test_blademaster_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000000000000100'}, 'get_dps')
        self.assertEqual(b, a)

    def test_blunderbuss_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000000000000010'}, 'get_dps')
        self.assertGreater(b, a)

    def test_cursed_steel_dps(self):
        a, b = self.compare({'traits': '000000000000000000'}, {'traits': '000000000000000001'}, 'get_dps')
        self.assertGreater(b, a)

class TestAssassinationRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        self.calculator = RogueDamageCalculatorFactory('assassination').build()

class TestSubtletyRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        self.calculator = RogueDamageCalculatorFactory('subtlety').build()

## Multi-target

class TestAOEOutlawRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        self.calculator = RogueDamageCalculatorFactory('outlaw').build(num_boss_adds=3)


class TestAOEAssassinationRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        self.calculator = RogueDamageCalculatorFactory('assassination').build(num_boss_adds=3)


class TestAOESubtletyRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        self.calculator = RogueDamageCalculatorFactory('subtlety').build(num_boss_adds=3)