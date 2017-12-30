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
from shadowcraft.objects import artifact

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

#initialize artifact traits..
test_traits = artifact.Artifact(test_spec, test_class, trait_dict={'assassins_blades': 1, 'bag_of_tricks': 1, 'balanced_blades': 4, 'blood_of_the_assassinated': 1, 'fade_into_shadows': 4, 'from_the_shadows': 1, 'kingsbane': 1, 'gushing_wounds': 4, 'master_alchemist': 6, 'master_assassin': 5, 'poison_knives': 4, 'serrated_edge': 4, 'shadow_swiftness': 1, 'shadow_walker': 4, 'surge_of_toxins': 1, 'toxic_blades': 4, 'urge_to_kill': 1, 'slayers_precision': 1, 'silence_of_the_uncrowned': 1, 'strangler': 4, 'dense_concoction': 1, 'sinister_circulation': 1, 'concordance_of_the_legionfall': 24})

# Set up settings.
test_cycle = settings.AssassinationCycle()
test_settings = settings.Settings(test_cycle, response_time=.5, duration=300,
                                  finisher_threshold=4)

# Build a DPS object.
calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_traits, test_buffs, test_race, test_spec, test_settings, test_level)

print(str(calculator.stats.get_character_stats(calculator.race, test_traits)))

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
#trait_ranks = calculator.get_trait_ranking()

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

# This is the maximum ilvl + 5, because python range method doesn't include
# the max value passed in as one of the steps.
RANGE_MAX = 990

trinketGroups = {
    # Alchemist trinket
    'infernal_alchemist_stone': range(815, 885, 5),

    # Dungeon trinkets
    'chaos_talisman': range(820, RANGE_MAX, 5),
    'chrono_shard': range(820, RANGE_MAX, 5),
    'darkmoon_deck_dominion': range(815, RANGE_MAX, 5),
    'faulty_countermeasure': range(820, RANGE_MAX, 5),
    'giant_ornamental_pearl': range(820, RANGE_MAX, 5),
    'horn_of_valor': range(820, RANGE_MAX, 5),
    'mark_of_dargrul': range(820, RANGE_MAX, 5),
    'memento_of_angerboda': range(820, RANGE_MAX, 5),
    'nightmare_egg_shell': range(820, RANGE_MAX, 5),
    'spiked_counterweight': range(820, RANGE_MAX, 5),
    'tempered_egg_of_serpentrix': range(820, RANGE_MAX, 5),
    'terrorbound_nexus': range(820, RANGE_MAX, 5),
    'tiny_oozeling_in_a_jar': range(820, RANGE_MAX, 5),
    'tirathons_betrayal': range(820, RANGE_MAX, 5),
    'windscar_whetstone': range(820, RANGE_MAX, 5),

    # Emerald Nightmare
    'ravaged_seed_pod': range(850, RANGE_MAX, 5),
    'spontaneous_appendages': range(850, RANGE_MAX, 5),
    'natures_call': range(850, RANGE_MAX, 5),
    'bloodthirsty_instinct': range(850, RANGE_MAX, 5),

    # Return to Karazhan
    'bloodstained_handkerchief': range(855, RANGE_MAX, 5),
    'eye_of_command': range(860, RANGE_MAX, 5),
    'toe_knees_promise': range(855, RANGE_MAX, 5),

    # Nighthold trinkets
    'arcanogolem_digit': range(855, RANGE_MAX, 5),
    'convergence_of_fates': range(860, RANGE_MAX, 5),
    'entwined_elemental_foci': range(860, RANGE_MAX, 5),
    'nightblooming_frond': range(860, RANGE_MAX, 5),
    'draught_of_souls': range(865, RANGE_MAX, 5),

    # Legendary trinkets
    'kiljaedens_burning_wish': [910, 940, 970, 1000],

    # 7.2/Tomb of Sargeras
    'splinters_of_agronax': range(845, RANGE_MAX, 5),
    'infernal_cinders': range(885, RANGE_MAX, 5),
    'cradle_of_anguish': range(885, RANGE_MAX, 5),
    'vial_of_ceaseless_toxins': range(885, RANGE_MAX, 5),
    'umbral_moonglaives': range(885, RANGE_MAX, 5),
    'engine_of_eradication': range(885, RANGE_MAX, 5),
    'specter_of_betrayal': range(895, RANGE_MAX, 5),

    # Seat of the Triumvirate
    'void_stalkers_contract': range(865, RANGE_MAX, 5),

    # Antorus, The Burning Throne
    'amanthuls_vision': range(915, RANGE_MAX, 5),
    'golganneths_vitality': range(915, RANGE_MAX, 5),
    'terminus_signaling_beacon': range(915, RANGE_MAX, 5),
    'forgefiends_fabricator': range(915, RANGE_MAX, 5),
    'seeping_scourgewing': range(915, RANGE_MAX, 5),
    'gorshalachs_legacy': range(915, RANGE_MAX, 5),
    'shadowsinged_fang': range(915, RANGE_MAX, 5),
}
gear_rankings = calculator.get_upgrades_ep_fast(trinketGroups)

dicts_for_pretty_print = [
    ep_values,
    tier_ep_values,
    #talent_ranks,
    #trinkets_ep_value,
    dps_breakdown,
    #trait_ranks,
    gear_rankings
]

#pretty_print([dps_breakdown], total_sum=total_dps, show_percent=True)
print(' ' * (max_length([dps_breakdown]) + 1), total_dps, ("total damage per second."))

#pprint(talent_ranks)
