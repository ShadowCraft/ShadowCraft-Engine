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
        'value': 2088,
        'duration': 0,
        'max_stacks': 0,
        'proc_name': 'Touch of the Grave',
        'type': 'perc',
        'icd': 15,
        'proc_rate': .20,
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
        'source': 'unique',
        'icd': 3,
        'proc_rate': 1.74, #1.55 mut, 1.15 com, 1.0 sub
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'legendary_capacitive_meta': {
        'stat':'spell_damage',
        'value': 280,
        'duration': 0,
        'max_stacks': 5,
        'proc_name': 'Lightning Strike (meta)',
        'scaling': 0.0,
        'item_level': 541,
        'type': 'rppm',
        'source': 'unique',
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
        'source': 'trinket',
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
        'source': 'trinket',
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
        'source': 'trinket',
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
        'source': 'trinket',
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
        'source': 'trinket',
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
        'source': 'trinket',
        'icd': 115,
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
}

allowed_melee_enchants = {
    #6.0
    'mark_of_the_frostwolf': {
        'stat': 'stats',
        'value': {'multistrike':500},
        'duration': 6,
        'max_stacks': 2,
        'proc_name': 'Mark of the Frostwolf',
        'type': 'rppm',
        'source': 'weapon',
        'item_level': 100,
        'icd': 0,
        'proc_rate': 3.0,
        'trigger': 'all_melee_attacks'
    },
    'mark_of_the_thunderlord': {
        'stat': 'stats',
        'value': {'crit':500},
        'duration': 6,
        'proc_name': 'Mark of the Thunderlord',
        'type': 'rppm',
        'source': 'weapon',
        'item_level': 100,
        'icd': 0,
        'proc_rate': 2.5,
        'trigger': 'all_melee_attacks'
    },
    'mark_of_the_bleeding_hollow': {
        'stat': 'stats',
        'value': {'mastery':500},
        'duration': 12,
        'proc_name': 'Mark of the Bleeding Hollow',
        'type': 'rppm',
        'source': 'weapon',
        'item_level': 100,
        'icd': 0,
        'proc_rate': 2.3,
        'trigger': 'all_melee_attacks'
    },
    #5.0
    'windsong': {
        'stat': 'random',
        'value': {'haste':75, 'mastery':75, 'crit':75},
        'duration': 12,
        'proc_name': 'Windsong',
        'type': 'rppm',
        'source': 'weapon',
        'item_level': 90,
        'icd': 0,
        'proc_rate': 2.2,
        'trigger': 'all_attacks'
    },
    'dancing_steel': {
        'stat': 'highest',
        'value': {'agi':83, 'str':83},
        'duration': 12,
        'proc_name': 'Dancing Steel',
        'type': 'rppm',
        'source': 'weapon',
        'item_level': 90, #rely on player level here, due to enchants scaling with level (to a point)
        'icd': 0,
        'proc_rate': 2.53,
        'trigger': 'all_melee_attacks'
    },
    'elemental_force': {
        'stat': 'spell_damage',
        'value': 150,
        'duration': 0,
        'proc_name': 'Elemental Force',
        'type': 'rppm',
        'source': 'weapon',
        'item_level': 90,
        'icd': 0,
        'proc_rate': 9.17,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
}