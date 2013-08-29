# Simple test program to debug + play with assassination models.
from os import path
import sys
#sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))

from shadowcraft.calcs.rogue.Aldriana import AldrianasRogueDamageCalculator
from shadowcraft.calcs.rogue.Aldriana import settings

from shadowcraft.objects import buffs
from shadowcraft.objects import race
from shadowcraft.objects import stats
from shadowcraft.objects import procs
from shadowcraft.objects import talents
from shadowcraft.objects import glyphs

from shadowcraft.core import i18n

# Set up language. Use 'en_US', 'es_ES', 'fr' for specific languages.
test_language = 'local'
i18n.set_language(test_language)

# Set up level/class/race
test_level = 90
test_race = race.Race('night_elf')
test_class = 'rogue'

# Set up buffs.
test_buffs = buffs.Buffs(
        'short_term_haste_buff',
        'stat_multiplier_buff',
        'crit_chance_buff',
        'mastery_buff',
        'melee_haste_buff',
        'attack_power_buff',
        'spell_haste_buff',
        'armor_debuff',
        'physical_vulnerability_debuff',
        'spell_damage_debuff',
        'agi_flask',
        'guild_feast'
    )

# Set up weapons.
test_mh = stats.Weapon(6733, 1.8, 'dagger', 'dancing_steel')
test_oh = stats.Weapon(6733, 1.8, 'dagger', 'dancing_steel')

# Set up procs.
test_procs = procs.ProcsList( ('heroic_bottle_of_infinite_stars', 2), ('relic_of_xuen', 2) )

# Set up gear buffs.
test_gear_buffs = stats.GearBuffs('rogue_t14_2pc', 'rogue_t14_4pc', 'leather_specialization', 'virmens_bite', 'virmens_bite_prepot', 'chaotic_metagem')

# Set up a calcs object..
#                       str,   agi, int, spirit, stam,  ap, crit,  hit,  exp,haste, mast,      mh,      oh,      procs,      gear_buffs
test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                         str=80,
                         agi=18745,
                         crit=4915,
                         hit=2590,
                         exp=2502,
                         haste=6264,
                         mastery=4100)

# Initialize talents..
test_talents = talents.Talents('022212', test_class, test_level)

# Set up glyphs.
glyph_list = []
test_glyphs = glyphs.Glyphs(test_class, *glyph_list)

# Set up settings.
test_cycle = settings.SubtletyCycle(5, use_hemorrhage=24)
test_settings = settings.Settings(test_cycle, response_time=.5, duration=360, dmg_poison='dp', utl_poison='lp', is_pvp=False, adv_params="")

# Build a DPS object.
calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_glyphs, test_buffs, test_race, test_settings, test_level)

# Compute EP values.
ep_values = calculator.get_ep()
tier_ep_values = calculator.get_other_ep(['rogue_t14_4pc', 'rogue_t14_2pc', 'rogue_t15_4pc', 'rogue_t15_2pc', 'rogue_t16_2pc', 'rogue_t16_4pc'])

trinkets_list = [
    #5.2
    'heroic_rune_of_re_origination',
    'rune_of_re_origination',
    'lfr_rune_of_re_origination',
    'heroic_bad_juju',
    'bad_juju',
    'lfr_bad_juju',
    'heroic_talisman_of_bloodlust',
    'talisman_of_bloodlust',
    'lfr_talisman_of_bloodlust',
    'heroic_renatakis_soul_charm',
    'renatakis_soul_charm',
    'lfr_renatakis_soul_charm',
    'vicious_talisman_of_the_shado-pan_assault',
    #5.0-5.1
    'heroic_bottle_of_infinite_stars',
    'bottle_of_infinite_stars',
    'lfr_bottle_of_infinite_stars',
    'heroic_terror_in_the_mists',
    'terror_in_the_mists',
    'lfr_terror_in_the_mists',
    'relic_of_xuen',
]
#trinkets_ep_value = calculator.get_other_ep(trinkets_list)
#trinkets_ep_value['heroic_rune_of_re_origination'] += 1657 * ep_values['agi']
#trinkets_ep_value['rune_of_re_origination'] += 1467 * ep_values['agi']
#trinkets_ep_value['lfr_rune_of_re_origination'] += 1218 * ep_values['agi']
#trinkets_ep_value['heroic_bad_juju'] += .6 * 1657 * ep_values['mastery'] + .4 * 1657 * ep_values['haste']
#trinkets_ep_value['bad_juju'] += .6 * 1467 * ep_values['mastery'] + .4 * 1467 * ep_values['haste']
#trinkets_ep_value['lfr_bad_juju'] += .6 * 1218 * ep_values['mastery'] + .4 * 1218 * ep_values['haste']
#trinkets_ep_value['heroic_talisman_of_bloodlust'] += 1657 * ep_values['agi']
#trinkets_ep_value['talisman_of_bloodlust'] += 1467 * ep_values['agi']
#trinkets_ep_value['lfr_talisman_of_bloodlust'] += 1218 * ep_values['agi']
#trinkets_ep_value['heroic_renatakis_soul_charm'] += .6 * 1657 * ep_values['dodge_exp'] + .4 * 1657 * ep_values['haste']
#trinkets_ep_value['renatakis_soul_charm'] += .6 * 1467 * ep_values['dodge_exp'] + .4 * 1467 * ep_values['haste']
#trinkets_ep_value['lfr_renatakis_soul_charm'] += .6 * 1218 * ep_values['dodge_exp'] + .4 * 1218 * ep_values['haste']
#trinkets_ep_value['vicious_talisman_of_the_shado-pan_assault']

#trinkets_ep_value['heroic_bottle_of_infinite_stars'] += 731 * ep_values['mastery'] + 487 * ep_values['haste']
#trinkets_ep_value['bottle_of_infinite_stars'] += 648 * ep_values['mastery'] + 431 * ep_values['haste']
#trinkets_ep_value['lfr_bottle_of_infinite_stars'] += 574 * ep_values['mastery'] + 382 * ep_values['haste']
#trinkets_ep_value['heroic_terror_in_the_mists'] += 1300 * ep_values['agi']
#trinkets_ep_value['terror_in_the_mists'] += 1152 * ep_values['agi']
#trinkets_ep_value['lfr_terror_in_the_mists'] += 1021 * ep_values['agi']
#trinkets_ep_value['relic_of_xuen'] += 956 * ep_values['agi']

# Compute DPS Breakdown.
dps_breakdown = calculator.get_dps_breakdown()
total_dps = sum(entry[1] for entry in dps_breakdown.items())
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
    tier_ep_values,
    talent_ranks,
    #trinkets_ep_value,
    dps_breakdown
]
pretty_print(dicts_for_pretty_print)
print ' ' * (max_length(dicts_for_pretty_print) + 1), total_dps, _("total damage per second.")
