# Simple test program to debug + play with subtlety models.
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

# Set up language. Use 'en_US', 'es_ES', 'fr' for specific languages.
test_language = 'local'
i18n.set_language(test_language)

# Set up level/class/race
test_level = 110
test_race = race.Race('troll')
test_class = 'rogue'
test_spec = 'subtlety'

# Set up buffs.
test_buffs = buffs.Buffs(
        'short_term_haste_buff',
        'flask_wod_agi',
        'food_wod_versatility'
    )

# Set up weapons. mark_of_the_frostwolf mark_of_the_shattered_hand
test_mh = stats.Weapon(812.0, 1.8, 'dagger', 'mark_of_the_shattered_hand')
test_oh = stats.Weapon(812.0, 1.8, 'dagger', 'mark_of_the_frostwolf')

# Set up procs. - trinkets, other things (legendary procs)
#test_procs = procs.ProcsList(('scales_of_doom', 691), ('beating_heart_of_the_mountain', 701), ('infallible_tracking_charm', 715),
#                             'draenic_agi_pot', 'draenic_agi_prepot', 'archmages_greater_incandescence')
test_procs = procs.ProcsList()

# Set up gear buffs.
test_gear_buffs = stats.GearBuffs('gear_specialization') #tier buffs located here

# Set up a calcs object..
test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                         agi=3650,
                         stam=2426,
                         crit=1039,
                         haste=0,
                         mastery=1315,
                         versatility=122,)

# Initialize talents..
test_talents = talents.Talents('0000000', test_spec, test_class, level=test_level)

#initialize artifact traits..
test_traits = artifact.Artifact(test_spec, test_class, '0000000000000000')

# Set up settings.
test_cycle = settings.SubtletyCycle(5, use_hemorrhage='never', clip_fw=False)
test_settings = settings.Settings(test_cycle, response_time=.5, duration=360, dmg_poison='dp', utl_poison='lp', is_pvp=False,
                                 adv_params="", is_demon=True)

# Build a DPS object.
calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_traits, test_buffs, test_race, test_spec, test_settings, test_level)

# Compute DPS Breakdown.
dps_breakdown = calculator.get_dps_breakdown()
total_dps = sum(entry[1] for entry in dps_breakdown.items())

# Compute EP values.
#ep_values = calculator.get_ep(baseline_dps=total_dps)
#ep_values = calculator.get_ep()
#tier_ep_values = calculator.get_other_ep(['rogue_t17_2pc', 'rogue_t17_4pc', 'rogue_t17_4pc_lfr'])

talent_ranks = calculator.get_talents_ranking()

def max_length(dict_list):
    max_len = 0
    for i in dict_list:
        dict_values = i.items()
        if max_len < max(len(entry[0]) for entry in dict_values):
            max_len = max(len(entry[0]) for entry in dict_values)

    return max_len

def pretty_print(dict_list):
    max_len = max_length(dict_list)

    for i in dict_list:
        dict_values = i.items()
        dict_values.sort(key=lambda entry: entry[1], reverse=True)
        for value in dict_values:
            if ("{0:.2f}".format(float(value[1])/total_dps)) != '0.00':
                print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1]) + ' ('+str( "{0:.2f}".format(100*float(value[1])/total_dps) )+'%)'
            else:
                print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1])
        print '-' * (max_len + 15)

dicts_for_pretty_print = [
    ep_values,
    #tier_ep_values,
    talent_ranks,
    #trinkets_ep_value,
    dps_breakdown
]
pretty_print(dicts_for_pretty_print)
print ' ' * (max_length(dicts_for_pretty_print) + 1), total_dps, _("total damage per second.")
