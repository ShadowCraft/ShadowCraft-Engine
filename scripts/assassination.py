# Simple test program to debug + play with assassination models.
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
from shadowcraft.objects import artifact

from shadowcraft.core import i18n

# Set up language. Use 'en_US', 'es_ES', 'fr' for specific languages.
test_language = 'local'
i18n.set_language(test_language)

# Set up level/class/race
test_level = 100
test_race = race.Race('none')
test_class = 'rogue'
test_spec = 'assassination'

# Set up buffs.
test_buffs = buffs.Buffs(
        'short_term_haste_buff',
        'flask_wod_agi',
        'food_wod_versatility'
    )

# Set up weapons.
test_mh = stats.Weapon(4821.0, 1.8, 'dagger', None)
test_oh = stats.Weapon(4821.0, 1.8, 'dagger', None)

# Set up procs.
#test_procs = procs.ProcsList(('scales_of_doom', 691), ('beating_heart_of_the_mountain', 701),
#                             'draenic_agi_pot', 'draenic_agi_prepot', 'archmages_greater_incandescence')
test_procs = procs.ProcsList()

# Set up gear buffs.
test_gear_buffs = stats.GearBuffs('gear_specialization')

# Set up a calcs object..
test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                         agi=20909,
                         stam=19566,
                         crit=4402,
                         haste=5150,
                         mastery=5999,
                         versatility=1515,)
# Initialize talents..
test_talents = talents.Talents('3010023', test_spec, test_class, level=test_level)

#initialize artifact traits..
test_traits = artifact.Artifact(test_spec, test_class, '100000000000000000')

# Set up settings.
test_cycle = settings.AssassinationCycle()
test_settings = settings.Settings(test_cycle, response_time=.5, duration=360,
                                  finisher_threshold=5)

# Build a DPS object.
calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_traits, test_buffs, test_race, test_spec, test_settings, test_level)

# Compute DPS Breakdown.
dps_breakdown = calculator.get_dps_breakdown()
total_dps = sum(entry[1] for entry in dps_breakdown.items())

# Compute EP values.
#ep_values = calculator.get_ep(baseline_dps=total_dps)
#tier_ep_values = calculator.get_other_ep(['rogue_t14_4pc', 'rogue_t14_2pc', 'rogue_t15_4pc', 'rogue_t15_2pc', 'rogue_t16_2pc', 'rogue_t16_4pc'])


talent_ranks = calculator.get_talents_ranking()
#trait_ranks = calculator.get_trait_ranking()

def max_length(dict_list):
    max_len = 0
    for i in dict_list:
        dict_values = i.items()
        if max_len < max(len(entry[0]) for entry in dict_values):
            max_len = max(len(entry[0]) for entry in dict_values)

    return max_len

def pretty_print(dict_list, total_sum = 1., show_percent=False):
    max_len = max_length(dict_list)

    for i in dict_list:
        dict_values = i.items()
        dict_values.sort(key=lambda entry: entry[1], reverse=True)
        for value in dict_values:
            #print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1])
            if show_percent and ("{0:.2f}".format(float(value[1])/total_sum)) != '0.00':
                print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1]) + ' ('+str( "{0:.2f}".format(100*float(value[1])/total_sum) )+'%)'
            else:
                print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1])
        print '-' * (max_len + 15)

dicts_for_pretty_print = [
    #ep_values,
    #tier_ep_values,
    #talent_ranks,
    #trinkets_ep_value,
    dps_breakdown,
    #trait_ranks
]
pretty_print(dicts_for_pretty_print)

#pretty_print([dps_breakdown], total_sum=total_dps, show_percent=True)
print ' ' * (max_length([dps_breakdown]) + 1), total_dps, ("total damage per second.")

pprint(talent_ranks)
