from __future__ import division
from __future__ import print_function
# Simple test program to debug + play with subtlety models.
from builtins import str
from os import path
import sys
from pprint import pprint
sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))

from shadowcraft.calcs.rogue.Aldriana import AldrianasRogueDamageCalculator
from shadowcraft.calcs.rogue.Aldriana import settings
from shadowcraft.calcs.rogue.Aldriana import settings_data

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
test_race = race.Race('blood_elf', level=110)
test_class = 'rogue'
test_spec = 'subtlety'

# Set up buffs.
test_buffs = buffs.Buffs(
        'short_term_haste_buff',
        'flask_legion_agi',
        'food_legion_mastery_375',
        #'food_legion_feast_150'
    )

# Set up weapons.
test_mh = stats.Weapon(10064.0, 1.8, 'dagger', None)
test_oh = stats.Weapon(10064.0, 1.8, 'dagger', None)

# Set up procs. - trinkets, other things (legendary procs)
test_procs = procs.ProcsList(
    'mark_of_the_hidden_satyr',
    ('specter_of_betrayal', 925),
    #('forgefiends_fabricator', 930),
    #('kiljaedens_burning_wish', 940)
    #'old_war_pot',
    #'old_war_prepot',
    'prolonged_power_pot',
    'prolonged_power_prepot',
)

"""
# test all procs
from shadowcraft.objects import proc_data
test_procs = procs.ProcsList()
for key in proc_data.allowed_procs.keys():
    test_procs.set_proc(key)


# Debug prints for scaled trinket values
for proc in test_procs.get_all_procs_for_stat():
    if proc.scaling:
        print proc.proc_name + " - " + str(proc.item_level) + " - " + str(proc.value)
"""

# Set up gear buffs.
test_gear_buffs = stats.GearBuffs('gear_specialization',
'insignia_of_ravenholdt',
'rogue_t20_2pc',
'rogue_t20_4pc',
#'insignia_of_ravenholdt',
'mantle_of_the_master_assassin',
) #tier buffs located here

# Set up a calcs object..
test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                         agi=round(42158 * 0.95238 - test_race.racial_agi), #gear spec and racial agi are added during calc again
                         stam=54585,
                         crit=13821,
                         haste=4139,
                         mastery=5600,
                         versatility=7111,)

# Initialize talents..
test_talents = talents.Talents('1113213', test_spec, test_class, level=test_level)

# Set up settings.
test_cycle = settings.SubtletyCycle()
test_settings = settings.Settings(test_cycle, pantheon_trinket_users=0, num_boss_adds=0)

# Build a DPS object.
calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_buffs, test_race, test_spec, test_settings, test_level)

print(str(test_stats.get_character_stats(test_race)))

# Compute DPS Breakdown.
dps_breakdown = calculator.get_dps_breakdown()
total_dps = sum(entry[1] for entry in list(dps_breakdown.items()))

# Compute EP values.
ep_values = calculator.get_ep(baseline_dps=total_dps)
#ep_values = calculator.get_ep()
tier_ep_values = calculator.get_other_ep(['rogue_t20_2pc', 'rogue_t20_4pc', 'the_first_of_the_dead', 'insignia_of_ravenholdt',
'mantle_of_the_master_assassin', 'specter_of_betrayal',
'golganneths_vitality', 'amanthuls_vision', 'shadowsinged_fang', 'seeping_scourgewing', 'terminus_signaling_beacon',
'gorshalachs_legacy', 'forgefiends_fabricator'])

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
    #trinkets_ep_value,
    dps_breakdown,
]
pretty_print(dicts_for_pretty_print)
print(' ' * (max_length(dicts_for_pretty_print) + 1), total_dps, ("total damage per second."))

"""
for value in list(aps.items()):
    if type(value[1]) is float:
        val = value[1] * 300.
    else:
        val = sum(value[1]) * 300.
    print(str(value[0]) + ' - ' + str(val))
"""
