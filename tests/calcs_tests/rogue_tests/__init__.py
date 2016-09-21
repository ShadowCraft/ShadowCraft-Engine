import unittest
from shadowcraft.calcs.rogue.Aldriana import AldrianasRogueDamageCalculator
from shadowcraft.core import exceptions
from shadowcraft.objects import buffs
from shadowcraft.objects import race
from shadowcraft.objects import stats
from shadowcraft.objects import procs
from shadowcraft.objects import talents
from shadowcraft.objects import artifact
from shadowcraft.calcs.rogue.Aldriana import settings

class TestRogueDamageCalculator(unittest.TestCase):
    def setUp(self):
        test_level = 110
        test_race = race.Race('pandaren')
        test_class = 'rogue'
        test_spec = 'outlaw'

        # Set up buffs.
        test_buffs = buffs.Buffs('short_term_haste_buff',
            'flask_wod_agi',
            'food_wod_versatility')

        # Set up weapons.  mark_of_the_frostwolf mark_of_the_shattered_hand
        test_mh = stats.Weapon(4821.0, 2.6, 'sword', None)
        test_oh = stats.Weapon(4821.0, 2.6, 'sword', None)

        # Set up procs.
        #test_procs = procs.ProcsList(('assurance_of_consequence', 588),
        #('draenic_philosophers_stone', 620), 'virmens_bite', 'virmens_bite_prepot',
        #'archmages_incandescence') #trinkets, other things (legendary procs)
        test_procs = procs.ProcsList()

        # Set up gear buffs.
        test_gear_buffs = stats.GearBuffs('gear_specialization') #tier buffs located here

        # Set up a calcs object..
        test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                                 agi=20909,
                                 stam=19566,
                                 crit=4402,
                                 haste=5150,
                                 mastery=5999,
                                 versatility=1515,)

        # Initialize talents..
        test_talents = talents.Talents('1000000', test_spec, test_class, level=test_level)

        #initialize artifact traits..
        test_traits = artifact.Artifact(test_spec, test_class, '000000000000000000')

        # Set up settings.
        test_cycle = settings.OutlawCycle(blade_flurry=False,
                                          jolly_roger_reroll=1,
                                          grand_melee_reroll=1,
                                          shark_reroll=1,
                                          true_bearing_reroll=1,
                                          buried_treasure_reroll=1,
                                          broadsides_reroll=1
                                          )
        test_settings = settings.Settings(test_cycle, response_time=.5, duration=360,
                                         adv_params="", is_demon=True, num_boss_adds=0)

        # Build a DPS object.
        self.calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_traits, test_buffs, test_race, test_spec, test_settings, test_level)


    def test_oh_penalty(self):
        self.assertAlmostEqual(self.calculator.oh_penalty(), 0.5)

    def test_crit_damage_modifiers(self):
        self.assertAlmostEqual(self.calculator.crit_damage_modifiers(), 1 + (2 * 1. - 1) * 1)

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



class TestRogueDamageCalculatorLevels(TestRogueDamageCalculator):
    def setUp(self):
        super(TestRogueDamageCalculatorLevels, self).setUp()
        self.calculator.level = 110

    def test_set_constants_for_level(self):
        self.assertRaises(exceptions.InvalidLevelException, self.calculator.__setattr__, 'level', 111)
