# None should be used to indicate unknown values
# The Proc class takes these parameters:
# stat, value, duration, proc_name, default_behaviour, max_stacks=1, can_crit=True, spell_behaviour=None
# Assumed heroic trinkets have the same behaviour as the non-heroic kin.
# behaviours must have a 'default' key so that the proc is properly initialized.
allowed_procs = {
    #generic
    'rogue_poison': {
        'stat': 'weird_proc',
        'value': 0,
        'duration': 0,
        'proc_name': 'rogue_poison',
        'type': 'perc',
        'icd': 0,
        'proc_rate': 1,
        'trigger': 'all_attacks'
    },
    #racials
    'touch_of_the_grave': {
        'stat': 'spell_damage',
        'value': 13680,
        'duration': 0,
        'max_stacks': 0,
        'proc_name': 'Touch of the Grave',
        'type': 'perc',
        'icd': 15,
        'proc_rate': .20,
        'trigger': 'all_attacks'
    },
    'lifeblood': { #triggered on demand
        'stat': 'stats',
        'value': 'varies',
        'duration': 20,
        'proc_name': 'lifeblood',
        'type': 'perc',
        'icd': 120,
        'proc_rate': 1.,
        'trigger': 'all_attacks'
    },
    #professions
    'swordguard_embroidery': {
        'stat': 'stats',
        'value': 'varies',
        'duration': 15,
        'proc_name': 'Swordguard Embroidery',
        'type': 'perc',
        'icd': 55,
        'proc_rate': .15,
        'trigger': 'all_attacks'
    },
    'synapse_springs': { #triggered on demand
        'stat': 'stats',
        'value': 'varies',
        'duration': 10,
        'proc_name': 'Synapse Springs',
        'type': 'perc',
        'icd': 60,
        'proc_rate': 1.,
        'trigger': 'all_attacks'
    },
    #gear procs
    'fury_of_xuen': {
        'stat':'physical_damage',
        'value': 1,
        'duration': 0,
        'proc_name': 'Fury of Xuen',
        'scaling': 0.0,
        'item_level': 0,
        'type': 'rppm',
        'icd': 3,
        'proc_rate': 1.74, #1.55 mut, 1.15 com, 0 sub
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'legendary_capacitive_meta': {
        'stat':'melee_spell_damage',
        'value': 280,
        'duration': 0,
        'max_stacks': 5,
        'proc_name': 'Lightning Strike (meta)',
        'scaling': 0.0,
        'item_level': 541,
        'type': 'rppm',
        'icd': 1,
        'proc_rate': 19.27, #1.789 mut, 1.136 com, 1.114 sub
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    #5.4 procs
    'assurance_of_consequence': {
        'stat': 'stats',
        'value': {'agi':14037}, # not 100% accurate
        'duration': 20,
        'proc_name': 'Assurance of Consequence',
        'upgradable': True,
        'scaling': 2.9730000496,
        'item_level': 572,
        'type': 'perc',
        'icd': 115,
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
    'haromms_talisman': {
        'stat': 'stats',
        'value': {'agi':14037}, # not 100% accurate
        'duration': 10,
        'proc_name': 'Haromms Talisman',
        'upgradable': True,
        'scaling': 2.9730000496,
        'item_level': 572,
        'type': 'rppm',
        'icd': 10,
        'proc_rate': 0.92,
        'trigger': 'all_attacks'
    },
    'sigil_of_rampage': {
        'stat': 'stats',
        'value': {'agi':14037}, # not 100% accurate
        'duration': 15,
        'proc_name': 'Sigil of Rampage',
        'upgradable': True,
        'scaling': 2.9730000496,
        'item_level': 572,
        'type': 'perc',
        'icd': 85,
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
    'ticking_ebon_detonator': {
        'stat': 'stats',
        'value': {'agi':1275 * 10.5}, # probably not accurate
        'duration': 10,
        'proc_name': 'Ticking Ebon Detonator',
        'upgradable': True,
        'scaling': 0.2703000009 * 10.5,
        'item_level': 572,
        'type': 'rppm',
        'icd': 10,
        'proc_rate': 1.00,
        'trigger': 'all_attacks'
    },
    'thoks_tail_tip': {
        'stat': 'stats',
        'value': {'str':14037}, # not 100% accurate
        'duration': 20,
        'proc_name': 'Thoks Tail Tip',
        'upgradable': True,
        'scaling': 2.9730000496,
        'item_level': 572,
        'type': 'perc',
        'icd': 115,
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
    'discipline_of_xuen': {
        'stat': 'stats',
        'value': {'mastery':9943},
        'duration': 20,
        'proc_name': 'Discipline of Xuen',
        'upgradable': True,
        'scaling': 2.9730000496,
        'item_level': 535,
        'type': 'perc',
        'icd': 115,
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
}

allowed_melee_enchants = {
    'windsong': {
        'stat': 'random',
        'value': {'haste':1500, 'mastery':1500, 'crit':1500},
        'duration': 12,
        'proc_name': 'Windsong',
        'type': 'rppm',
        'icd': 0,
        'proc_rate': 2.2,
        'trigger': 'all_attacks'
    },
    'dancing_steel': {
        'stat': 'highest',
        'value': {'agi':1650, 'str':1650},
        'duration': 12,
        'proc_name': 'Dancing Steel',
        'type': 'rppm',
        'icd': 0,
        'proc_rate': 2.53,
        'trigger': 'all_melee_attacks'
    },
    'elemental_force': {
        'stat': 'spell_damage',
        'value': 3000,
        'duration': 0,
        'proc_name': 'Elemental Force',
        'type': 'rppm',
        'icd': 0,
        'proc_rate': 9.17,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
}

# The _set_behaviour method takes these parameters:
# trigger, icd, proc_chance=False, ppm=False, on_crit=False, on_procced_strikes=True
# You can't set a value for both 'ppm' and 'proc_chance': one must be False
# Allowed triggers are: 'all_spells_and_attacks', 'all_damaging_attacks',
# 'all_attacks', 'strikes', 'auto_attacks', 'damaging_spells', 'all_spells',
# 'healing_spells', 'all_periodic_damage', 'bleeds', 'spell_periodic_damage'
# and 'hots'. The trigger 'all_melee_attacks' is sugar for 'all_attacks'.
behaviours = {
    'dead_code': {
        'hail_sithis':True
    },
}
