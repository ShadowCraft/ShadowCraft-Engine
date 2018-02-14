from builtins import object
import unittest
from shadowcraft.calcs.rogue.Aldriana import AldrianasRogueDamageCalculator
from shadowcraft.core import exceptions
from shadowcraft.objects import buffs as _buffs
from shadowcraft.objects import race as _race
from shadowcraft.objects import stats as _stats
from shadowcraft.objects import procs as _procs
from shadowcraft.objects import talents as _talents
from shadowcraft.calcs.rogue.Aldriana import settings as _settings

class RogueDamageCalculatorFactory(object):
    def __init__(self, spec, **kwargs):
        self.class_name = 'rogue'
        self.talent_str = '0000000'
        self.buffs = _buffs.Buffs('short_term_haste_buff', 'flask_wod_agi', 'food_wod_versatility')
        self.procs = _procs.ProcsList()
        self.gear_buffs = _stats.GearBuffs('gear_specialization')
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

        # Set up settings.
        test_settings = _settings.Settings(self.cycle, response_time=self.response_time, duration=self.duration,
                                         adv_params=self.adv_params, is_demon=self.is_demon, num_boss_adds=self.num_boss_adds, finisher_threshold=self.finisher_threshold)

        self.calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, self.buffs, test_race, self.spec, test_settings, self.level)
        self.calculator.level = 110
        return self.calculator

class RogueDamageCalculatorTestBase(object):
    def compare_dps(self, a, b):
        return self.compare(a, b, "get_dps")

    def compare(self, a, b, method=None):
        calc_a = self.factory.build(**a)
        calc_b = self.factory.build(**b)
        if method is not None:
            return (getattr(calc_a, method)(), getattr(calc_b, method)())
        else:
            return (calc_a, calc_b)

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


    def test_get_talents_ranking_does_not_change_talents(self):
        active_talents = self.calculator.talents.get_active_talents()
        self.assertEqual(self.calculator.talents.get_active_talents(), active_talents)

## Single target

class TestOutlawRogueDamageCalculator(RogueDamageCalculatorTestBase, unittest.TestCase):
    def setUp(self):
        self.factory = RogueDamageCalculatorFactory('outlaw')
        self.calculator = self.factory.build()


    # This is a dumb test but illustrates how we can test changes in a calculator
    def test_mastery_helps_dps(self):
        a, b = self.compare({"mastery": 3706}, {"mastery": 4706}, 'get_dps_breakdown')
        self.assertGreater(b["main_gauche"], a["main_gauche"])


    def test_energy_regen(self):
        self.calculator.set_constants()
        # This is 12.4 base because the calculator currently averages Heroism out over the course of the fight.
        # Should fix at some point.
        self.assertAlmostEqual(self.calculator.get_energy_regen({'haste': 0}), 12.4)
        self.assertAlmostEqual(self.calculator.get_energy_regen({'haste': 5000}), 14.3076923)
        self.assertAlmostEqual(self.calculator.get_energy_regen({'haste': 5000}, buried=True), 17.8846153846)
        self.assertAlmostEqual(self.calculator.get_energy_regen({'haste': 5000}, ar=True), 28.615384615384613)
        self.assertAlmostEqual(self.calculator.get_energy_regen({'haste': 5000}, buried=True, ar=True), 35.76923076923077)
        self.assertAlmostEqual(self.calculator.get_energy_regen({'haste': 5000}, alacrity_stacks=10), 15.50769230769231)
        cycle = _settings.OutlawCycle(blade_flurry=True)
        self.assertEqual(self.factory.build(cycle=cycle).set_constants().get_energy_regen({'haste': 0}), 12.4 * 0.8)


    def test_blade_flurry_hurts_single_target_dps(self):
        cycle = _settings.OutlawCycle(blade_flurry=True)
        base, rank1 = self.compare_dps({}, {'num_boss_adds': 0, 'cycle': cycle})
        self.assertLess(rank1, base)


    # These are sanity checks; they are what is expected from current modeling, so they're included to help
    # guard against regressions in the calculator.
    def test_best_rank_1(self):
        base = self.factory.build(talent_str='0000000').get_dps()
        gstrike = self.factory.build(talent_str='1000000').get_dps()
        swords = self.factory.build(talent_str='2000000').get_dps()
        quick = self.factory.build(talent_str='3000000').get_dps()
        self.assertGreater(gstrike, base, 'No Talents %s >= Ghostly Strike %s' % (base, gstrike))
        self.assertGreater(gstrike, swords, 'Swordmaster %s >= Ghostly Strike %s' % (swords, gstrike))
        self.assertGreater(gstrike, quick, 'Quick Draw %s >= Ghostly Strike %s' % (quick, gstrike))


    def test_best_rank_3(self):
        base = self.factory.build(talent_str='0010000').get_dps()
        stratagem = self.factory.build(talent_str='0010000').get_dps()
        anticipation = self.factory.build(talent_str='0020000').get_dps()
        vigor = self.factory.build(talent_str='0030000').get_dps()
        self.assertGreater(stratagem, base, 'No Talents %s >= Stratagem %s' % (base, stratagem))
        self.assertGreater(stratagem, anticipation, 'Anticipation %s >= Stratagem %s' % (anticipation, stratagem))
        self.assertGreater(stratagem, vigor, 'Vigor %s >= Stratagem %s' % (vigor, stratagem))


    def test_best_rank_6(self):
        base = self.factory.build(talent_str='0000000').get_dps()
        cannons = self.factory.build(talent_str='0000010').get_dps()
        alacrity = self.factory.build(talent_str='0000020').get_dps()
        kspree = self.factory.build(talent_str='0000030').get_dps()
        self.assertGreater(alacrity, base, 'No Talents %s >= Alacrity %s' % (base, alacrity))
        self.assertGreater(alacrity, kspree, 'KSpree %s >= Alacrity %s' % (kspree, alacrity))
        self.assertGreater(alacrity, cannons, 'Cannons %s >= Alacrity %s' % (cannons, alacrity))


    def test_best_rank_7(self):
        base = self.factory.build(talent_str='0000000').get_dps()
        snd = self.factory.build(talent_str='0000001').get_dps()
        mfd = self.factory.build(talent_str='0000002').get_dps()
        dfa = self.factory.build(talent_str='0000003').get_dps()
        self.assertGreater(mfd, base, 'No Talents %s >= Marked for Death %s' % (base, mfd))
        self.assertGreater(mfd, snd, 'SnD %s >= Marked for Death %s' % (snd, mfd))
        self.assertGreater(mfd, dfa, 'Death From Above %s >= mfd %s' % (dfa, mfd))

    def test_get_talents_ranking_does_not_persist_talents_in_same_row(self):
        self.calculator.talents.initialize_talents("0000000")
        ranking_without_existing = self.calculator.get_talents_ranking()

        self.calculator.talents.initialize_talents("1000000")
        ranking_with_existing = self.calculator.get_talents_ranking()

        self.assertEqual(ranking_without_existing[15], ranking_with_existing[15])


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
