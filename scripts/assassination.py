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

# Set up language. Use 'en_US', 'es_ES', 'fr' for specific languages.
test_language = 'local'
i18n.set_language(test_language)

# Set up level/class/race
test_level = 110
test_race = race.Race('blood_elf', 'rogue', 110)
test_class = 'rogue'
test_spec = 'assassination'

# Set up buffs.
test_buffs = buffs.Buffs(
    'short_term_haste_buff',
    'flask_legion_agi',
    'food_legion_mastery_375'
)

# Set up weapons.
test_mh = stats.Weapon(7063.0, 1.8, 'dagger', None)
test_oh = stats.Weapon(7063.0, 1.8, 'dagger', None)

# Set up procs.
#test_procs = procs.ProcsList(('scales_of_doom', 691), ('beating_heart_of_the_mountain', 701),
#                             'draenic_agi_pot', 'draenic_agi_prepot', 'archmages_greater_incandescence')
test_procs = procs.ProcsList('old_war_pot', 'old_war_prepot',
                             ('engine_of_eradication', 920),
                             ('specter_of_betrayal', 915)
)

# Set up gear buffs.
test_gear_buffs = stats.GearBuffs('gear_specialization',
'rogue_t20_2pc',
'rogue_t20_4pc',
'zoldyck_family_training_shackles',
'mantle_of_the_master_assassin',
)

# Set up a calcs object..
test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                         agi=26271,
                         stam=43292,
                         crit=8206,
                         haste=3629,
                         mastery=11384,
                         versatility=4237)

# Initialize talents..
#test_talents = talents.Talents('2110031', test_spec, test_class, level=test_level)
test_talents = talents.Talents('1230011', test_spec, test_class, level=test_level)

# Set up settings.
test_cycle = settings.AssassinationCycle()
test_settings = settings.Settings(test_cycle, response_time=.5, duration=300,
                                  finisher_threshold=4)

# Build a DPS object.
calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_buffs, test_race, test_spec, test_settings, test_level)

print(str(calculator.stats.get_character_stats(calculator.race)))

# Compute DPS Breakdown.
dps_breakdown = calculator.get_dps_breakdown()
total_dps = sum(entry[1] for entry in list(dps_breakdown.items()))

# Compute EP values.
ep_values = calculator.get_ep(baseline_dps=total_dps)
tier_ep_values = calculator.get_other_ep(['rogue_t19_2pc', 'rogue_t19_4pc', 'rogue_orderhall_8pc',
                                          'rogue_t20_2pc', 'rogue_t20_4pc',
                                          'rogue_t21_2pc', 'rogue_t21_4pc',
                                          'mark_of_the_hidden_satyr', 'mark_of_the_distant_army',
                                          'mark_of_the_claw', 'march_of_the_legion_2pc',
                                          'journey_through_time_2pc', 'jacins_ruse_2pc',
                                          'kara_empowered_2pc'])


#talent_ranks = calculator.get_talents_ranking()

def max_length(dict_list):
    max_len = 0
    for i in dict_list:
        dict_values = list(i.items())
        if max_len < max(len(entry[0]) for entry in dict_values):
            max_len = max(len(entry[0]) for entry in dict_values)

    return max_len

def pretty_print(dict_list):
    max_len = max_length(dict_list)

    for i in dict_list:
        dict_values = list(i.items())
        dict_values.sort(key=lambda entry: entry[1], reverse=True)
        for value in dict_values:
            if ("{0:.2f}".format(value[1] / total_dps)) != '0.00':
                print(value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1]) + ' ('+str( "{0:.2f}".format(100*float(value[1])/total_dps) )+'%)')
            else:
                print(value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1]))
        print('-' * (max_len + 15))

dicts_for_pretty_print = [
    ep_values,
    tier_ep_values,
    #talent_ranks,
    #trinkets_ep_value,
    dps_breakdown,
]
pretty_print(dicts_for_pretty_print)

#pretty_print([dps_breakdown], total_sum=total_dps, show_percent=True)
print(' ' * (max_length([dps_breakdown]) + 1), total_dps, ("total damage per second."))

#pprint(talent_ranks)
