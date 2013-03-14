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
from shadowcraft.objects import glyphs

from shadowcraft.core import i18n

from time import clock

# Set up language. Use 'en_US', 'es_ES', 'fr' for specific languages.
test_language = 'local'
i18n.set_language(test_language)

start = clock()

# Set up level/class/race
test_level = 90
test_race = race.Race('pandaren')
test_class = 'rogue'

# Set up buffs.
test_buffs = buffs.Buffs(
        'short_term_haste_buff',
        'stat_multiplier_buff',
        'crit_chance_buff',
        'mastery_buff',
        'melee_haste_buff',
        'attack_power_buff',
        'armor_debuff',
        'physical_vulnerability_debuff',
        'spell_damage_debuff',
        'agi_flask_mop',
        'food_300_agi'
    )

# Set up weapons.
test_mh = stats.Weapon(10478.5, 2.6, 'fist', 'dancing_steel')
test_oh = stats.Weapon(10478.5, 2.6, 'fist', 'dancing_steel')
#test_oh = stats.Weapon(7254.0, 1.8, 'dagger', 'dancing_steel')

# Set up procs.
test_procs = procs.ProcsList('heroic_talisman_of_bloodlust', 'heroic_bad_juju', 'legendary_capacitive_meta')

# Set up gear buffs.
test_gear_buffs = stats.GearBuffs('rogue_t15_2pc', 'rogue_t15_4pc', 'leather_specialization', 'virmens_bite', 'virmens_bite_prepot')

# Set up a calcs object..
test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                         str=80,
                         agi=20131,
                         stam=25454,
                         crit=3278,
                         hit=2557,
                         exp=2549,
                         haste=13206,
                         mastery=6103)

# Initialize talents..
test_talents = talents.Talents('322213', test_class, test_level)

# Set up glyphs.
glyph_list = ['recuperate', 'adrenaline_rush']
test_glyphs = glyphs.Glyphs(test_class, *glyph_list)

# Set up settings.
test_cycle = settings.CombatCycle(stack_cds=True)
test_settings = settings.Settings(test_cycle, response_time=.5, duration=360, dmg_poison='dp', utl_poison='lp', is_pvp=False, stormlash=1)

# Build a DPS object.
calculator = AldrianasRogueDamageCalculator(test_stats, test_talents, test_glyphs, test_buffs, test_race, test_settings, test_level)

# Compute EP values.
ep_values = calculator.get_ep()
tier_ep_values = calculator.get_other_ep(['rogue_t14_4pc', 'rogue_t14_2pc', 'rogue_t15_4pc', 'rogue_t15_2pc'])
mh_enchants_and_dps_ep_values, oh_enchants_and_dps_ep_values = calculator.get_weapon_ep(dps=True, enchants=True)

trinkets_list = [
    #5.2
    'heroic_rune_of_re_origination',
    'thunder_rune_of_re_origination',
    'rune_of_re_origination',
    'lfr_rune_of_re_origination',
    'heroic_bad_juju',
    'thunder_bad_juju',
    'bad_juju',
    'lfr_bad_juju',
    'heroic_thunder_talisman_of_bloodlust',
    'heroic_talisman_of_bloodlust',
    'thunder_talisman_of_bloodlust',
    'talisman_of_bloodlust',
    'lfr_talisman_of_bloodlust',
    'heroic_renatakis_soul_charm',
    'thunder_renatakis_soul_charm',
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
trinkets_ep_value = calculator.get_upgrades_ep(trinkets_list)
glyph_values = calculator.get_glyphs_ranking()

# Compute DPS Breakdown.
dps_breakdown = calculator.get_dps_breakdown()
total_dps = sum(entry[1] for entry in dps_breakdown.items())

# Compute weapon type modifier.
weapon_type_mod = calculator.get_oh_weapon_modifier()
talent_ranks = calculator.get_talents_ranking()

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
            if show_percent and ("{0:.2f}".format(float(value[1])/total_dps)) != '0.00':
                print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1]) + ' ('+str( "{0:.2f}".format(100*float(value[1])/total_sum) )+'%)'
            else:
                print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1])
        print '-' * (max_len + 15)

dicts_for_pretty_print = [
    ep_values,
    tier_ep_values,
    mh_enchants_and_dps_ep_values,
    oh_enchants_and_dps_ep_values,
    trinkets_ep_value,
    glyph_values,
    talent_ranks,
]
pretty_print(dicts_for_pretty_print)
pretty_print([dps_breakdown], total_sum=total_dps, show_percent=True)
print ' ' * (max_length(dicts_for_pretty_print) + 1), total_dps, _("total damage per second.")
print "Request time: %s sec" % (clock() - start)
