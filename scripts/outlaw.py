# Simple test program to debug + play with assassination models.
from os import path
import sys
sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))

from shadowcraft.calcs.rogue.Aldriana import AldrianasRogueDamageCalculator
from shadowcraft.calcs.rogue.Aldriana import settings

from shadowcraft.objects import buffs
from shadowcraft.objects import race
from shadowcraft.objects import stats
from shadowcraft.objects import procs
from shadowcraft.objects import talents
from shadowcraft.objects import artifact

from shadowcraft.core import i18n

# Set up language.  Use 'en_US', 'es_ES', 'fr' for specific languages.
test_language = 'local'
i18n.set_language(test_language)

# Set up level/class/race
test_level = 110
test_race = race.Race('pandaren')
test_class = 'rogue'
test_spec = 'outlaw'

# Set up buffs.
test_buffs = buffs.Buffs('short_term_haste_buff',
    'flask_wod_agi',
    'food_wod_versatility')

# Set up weapons.  mark_of_the_frostwolf mark_of_the_shattered_hand
test_mh = stats.Weapon(812.0, 2.6, 'sword', 'mark_of_the_shattered_hand')
test_oh = stats.Weapon(812.0, 2.6, 'sword', 'mark_of_the_shattered_hand')

# Set up procs.
#test_procs = procs.ProcsList(('assurance_of_consequence', 588),
#('draenic_philosophers_stone', 620), 'virmens_bite', 'virmens_bite_prepot',
#'archmages_incandescence') #trinkets, other things (legendary procs)
test_procs = procs.ProcsList()

# Set up gear buffs.
test_gear_buffs = stats.GearBuffs('gear_specialization') #tier buffs located here

# Set up a calcs object..
test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                         agi=7655,
                         stam=19566,
                         crit=2665,
                         haste=1594,
                         mastery=3350,
                         versatility=6522,)

# Initialize talents..
test_talents = talents.Talents('0000000', test_spec, test_class, level=test_level)

#initialize artifact traits..
test_traits = artifact.Artifact(test_spec, test_class, '100000000000100000')

# Set up settings.
test_cycle = settings.OutlawCycle(blade_flurry=False, dfa_during_ar=True)
test_settings = settings.Settings(test_cycle, response_time=.5, duration=360,
                                 adv_params="", is_demon=True, num_boss_adds=0)

# Build a DPS object.
calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_traits, test_buffs, test_race, test_spec, test_settings, test_level)

# Compute DPS Breakdown.
dps_breakdown = calculator.get_dps_breakdown()
total_dps = sum(entry[1] for entry in dps_breakdown.items())

# Compute EP values.
ep_values = calculator.get_ep(baseline_dps=total_dps)
#tier_ep_values = calculator.get_other_ep(['rogue_t16_2pc', 'rogue_t16_4pc'])
#mh_enchants_and_dps_ep_values, oh_enchants_and_dps_ep_values =
#calculator.get_weapon_ep(dps=True, enchants=True)

talent_ranks = calculator.get_talents_ranking()
trait_ranks = calculator.get_trait_ranking()

def max_length(dict_list):
    max_len = 0
    for i in dict_list:
        dict_values = i.items()
        if max_len < max(len(entry[0]) for entry in dict_values):
            max_len = max(len(entry[0]) for entry in dict_values)

    return max_len

def pretty_print(dict_list, total_sum=1., show_percent=False):
    max_len = max_length(dict_list)

    for i in dict_list:
        dict_values = i.items()
        dict_values.sort(key=lambda entry: entry[1], reverse=True)
        for value in dict_values:
            #print value[0] + ':' + ' ' * (max_len - len(value[0])),
            #str(value[1])
            if show_percent and ("{0:.2f}".format(float(value[1]) / total_dps)) != '0.00':
                print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1]) + ' (' + str("{0:.2f}".format(100 * float(value[1]) / total_sum)) + '%)'
            else:
                print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1])
        print '-' * (max_len + 15)

dicts_for_pretty_print = [ep_values,
    #tier_ep_values,
    talent_ranks,
    #trinkets_ep_value,
    dps_breakdown,
    trait_ranks
]
pretty_print(dicts_for_pretty_print)
print ' ' * (max_length(dicts_for_pretty_print) + 1), total_dps, _("total damage per second.")
