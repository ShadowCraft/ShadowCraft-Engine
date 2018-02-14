from __future__ import division
from __future__ import print_function
# Simple test program to debug + play with assassination models.
from builtins import str
from os import path
import sys
from pprint import pprint
sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))

from shadowcraft.calcs.rogue.Aldriana import AldrianasRogueDamageCalculator
from shadowcraft.calcs.rogue.Aldriana import settings

from shadowcraft.objects import buffs
from shadowcraft.objects import race
from shadowcraft.objects import stats
from shadowcraft.objects import procs
from shadowcraft.objects import talents

from shadowcraft.core import i18n

# Set up language.  Use 'en_US', 'es_ES', 'fr' for specific languages.
test_language = 'local'
i18n.set_language(test_language)

# Set up level/class/race
test_level = 110
test_race = race.Race('pandaren', 'rogue', 110)
test_class = 'rogue'
test_spec = 'outlaw'

# Set up buffs.
test_buffs = buffs.Buffs(
    'short_term_haste_buff',
    'flask_legion_agi',
    'food_legion_versatility_375'
)

# Set up weapons.  mark_of_the_frostwolf mark_of_the_shattered_hand
test_mh = stats.Weapon(4821.0, 2.6, 'sword', None)
test_oh = stats.Weapon(4821.0, 2.6, 'sword', None)

# Set up procs.
#test_procs = procs.ProcsList(('assurance_of_consequence', 588),
#('draenic_philosophers_stone', 620), 'virmens_bite', 'virmens_bite_prepot',
#'archmages_incandescence') #trinkets, other things (legendary procs)
test_procs = procs.ProcsList(
    'mark_of_the_hidden_satyr',
    'old_war_pot',
    'old_war_prepot',
    ('nightblooming_frond', 895),
    ('memento_of_angerboda', 885)
)

# Set up gear buffs.
test_gear_buffs = stats.GearBuffs(
    'gear_specialization',
    'rogue_t19_2pc',
    'rogue_t19_4pc',
    'mantle_of_the_master_assassin',
    'greenskins_waterlogged_wristcuffs'
)

# Set up a calcs object..
test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                         agi=round(35872 * 0.95238 - test_race.racial_agi),
                         stam=28367,
                         crit=9070,
                         haste=2476,
                         mastery=6254,
                         versatility=5511,)

# Initialize talents..
test_talents = talents.Talents('3213122', test_spec, test_class, level=test_level)

# Set up settings.
test_cycle = settings.OutlawCycle(blade_flurry=False,
                                  jolly_roger_reroll=2,
                                  grand_melee_reroll=2,
                                  shark_reroll=2,
                                  true_bearing_reroll=0,
                                  buried_treasure_reroll=2,
                                  broadsides_reroll=2,
                                  between_the_eyes_policy='never'
                                  )
test_settings = settings.Settings(test_cycle, response_time=.5, duration=300,
                                 adv_params="", is_demon=True, num_boss_adds=0,
                                 finisher_threshold=5)

# Build a DPS object.
calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_buffs, test_race, test_spec, test_settings, test_level)

print(str(test_stats.get_character_stats(test_race)))

# Compute DPS Breakdown.
dps_breakdown = calculator.get_dps_breakdown()
total_dps = sum(entry[1] for entry in list(dps_breakdown.items()))

# Compute EP values.
ep_values = calculator.get_ep(baseline_dps=total_dps)
tier_ep_values = calculator.get_other_ep(['rogue_t16_2pc', 'rogue_t16_4pc', 'mantle_of_the_master_assassin'])
#mh_enchants_and_dps_ep_values, oh_enchants_and_dps_ep_values =
#calculator.get_weapon_ep(dps=True, enchants=True)

#talent_ranks = calculator.get_talents_ranking()

def max_length(dict_list):
    max_len = 0
    for i in dict_list:
        dict_values = list(i.items())
        if max_len < max(len(entry[0]) for entry in dict_values):
            max_len = max(len(entry[0]) for entry in dict_values)

    return max_len

def pretty_print(dict_list, total_sum=1., show_percent=False):
    max_len = max_length(dict_list)

    for i in dict_list:
        dict_values = list(i.items())
        dict_values.sort(key=lambda entry: entry[1], reverse=True)
        for value in dict_values:
            #print value[0] + ':' + ' ' * (max_len - len(value[0])),
            #str(value[1])
            if show_percent and ("{0:.2f}".format(value[1] / total_dps)) != '0.00':
                print(value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1]) + ' (' + str("{0:.2f}".format(100 * float(value[1]) / total_sum)) + '%)')
            else:
                print(value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1]))
        print('-' * (max_len + 15))

dicts_for_pretty_print = [ep_values,
    tier_ep_values,
    #talent_ranks,
    #trinkets_ep_value,
    dps_breakdown,
]
pretty_print(dicts_for_pretty_print)
print(' ' * (max_length(dicts_for_pretty_print) + 1), total_dps, ("total damage per second."))

#pprint(talent_ranks)
