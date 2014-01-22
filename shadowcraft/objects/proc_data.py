# None should be used to indicate unknown values
# The Proc class takes these parameters:
# stat, value, duration, proc_name, default_behaviour, max_stacks=1, can_crit=True, spell_behaviour=None
# Assumed heroic trinkets have the same behaviour as the non-heroic kin.
# behaviours must have a 'default' key so that the proc is properly initialized.
allowed_procs = {
    'rogue_poison': {
        'stat': 'weird_proc',
        'value': 0,
        'duration': 0,
        'proc_name': 'rogue_poison',
        'behaviours': {'default': 'rogue_poison'}
    },
    'touch_of_the_grave': {
        'stat': 'spell_damage',
        'value': 13680,
        'duration': 0,
        'max_stacks': 0,
        'proc_name': 'Touch of the Grave',
        'behaviours': {'default': 'touch_of_the_grave'}
    },
    'swordguard_embroidery': {
        'stat': 'ap',
        'value': 'varies',
        'duration': 15,
        'proc_name': 'Swordguard Embroidery',
        'behaviours': {'default': 'swordguard_embroidery'}
    },
    'fury_of_xuen': {
        'stat':'physical_damage',
        'value': 1,
        'duration': 0,
        'proc_name': 'Fury of Xuen',
        'behaviours': {'default': 'fury_of_xuen', 'assassination': 'fury_of_xuen_mut',
                       'combat': 'fury_of_xuen_combat', 'subtlety': 'fury_of_xuen_sub'},
        'scaling': {'factor': 0.0, 'item_level': 0, 'quality': 'epic'}
    },
    'legendary_capacitive_meta': {
        'stat':'melee_spell_damage',
        'value': 280,
        'duration': 0,
        'max_stacks': 5,
        'proc_name': 'Lightning Strike (meta)',
        'behaviours': {'default': 'legendary_capacitive_meta', 'assassination': 'legendary_capacitive_meta_mut',
                       'combat': 'legendary_capacitive_meta_combat', 'subtlety': 'legendary_capacitive_meta_sub'},
        'scaling': {'factor': 0.0, 'item_level': 541, 'quality': 'epic'}
    },
    'heroic_war_assurance_of_consequence': {
        'stat': 'stats',
        'value': {'agi':14037}, # not 100% accurate
        'duration': 20,
        'proc_name': 'Assurance of Consequence',
        'behaviours': {'default': 'assurance_of_consequence'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 572, 'quality': 'epic'}
    },
    'heroic_war_haromms_talisman': {
        'stat': 'stats',
        'value': {'agi':14037}, # not 100% accurate
        'duration': 10,
        'proc_name': 'Haromms Talisman',
        'behaviours': {'default': 'haromms_talisman'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 572, 'quality': 'epic'}
    },
    'heroic_war_sigil_of_rampage': {
        'stat': 'stats',
        'value': {'agi':14037}, # not 100% accurate
        'duration': 15,
        'proc_name': 'Sigil of Rampage',
        'behaviours': {'default': 'sigil_of_rampage'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 572, 'quality': 'epic'}
    },
    'heroic_war_ticking_ebon_detonator': {
        'stat': 'stats',
        'value': {'agi':1275 * 10.5}, # probably not accurate
        'duration': 10,
        'proc_name': 'Ticking Ebon Detonator',
        'behaviours': {'default': 'ticking_ebon_detonator'},
        'upgradable': True,
        'scaling': {'factor': 0.2703000009 * 10.5, 'item_level': 572, 'quality': 'epic'}
    },
    'heroic_war_thoks_tail_tip': {
        'stat': 'stats',
        'value': {'str':14037}, # not 100% accurate
        'duration': 20,
        'proc_name': 'Thoks Tail Tip',
        'behaviours': {'default': 'thoks_tail_tip'},
        'upgradable': True,
        'scaling': {'factor':  2.9730000496, 'item_level': 572, 'quality': 'epic'}
    },
    'timeless_discipline_of_xuen': {
        'stat': 'stats',
        'value': {'master':9943},
        'duration': 20,
        'proc_name': 'Discipline of Xuen',
        'behaviours': {'default': 'discipline_of_xuen'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 535, 'quality': 'epic'}
    },
    'discipline_of_xuen': {
        'stat': 'stats',
        'value': {'master':6914},
        'duration': 20,
        'proc_name': 'Discipline of Xuen',
        'behaviours': {'default': 'discipline_of_xuen'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 496, 'quality': 'epic'}
    },
}

allowed_melee_enchants = {
    'windsong': {
        'stat': 'random',
        'value': {'haste':1500, 'mastery':1500, 'crit':1500},
        'duration': 12,
        'proc_name': 'Windsong',
        'behaviours': {'default': 'windsong'}
    },
    'dancing_steel': {
        'stat': 'highest',
        'value': {'agi':1650, 'str':1650},
        'duration': 12,
        'proc_name': 'Dancing Steel',
        'behaviours': {'default': 'dancing_steel'}
    },
    'elemental_force': {
        'stat': 'spell_damage',
        'value': 3000,
        'duration': 0,
        'proc_name': 'Elemental Force',
        'behaviours': {'default': 'elemental_force'}
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
    'rogue_poison': {
        'type': 'perc',
        'icd': 0,
        'proc_chance': 1,
        'trigger': 'all_attacks'
    },
    'touch_of_the_grave': {
        'type': 'perc',
        'icd': 15,
        'proc_chance': .20,
        'trigger': 'all_attacks'
    },
    'fury_of_xuen': {
        'type': 'rppm',
        'real_ppm': True,
        'icd': 3,
        'ppm': 1.74,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'fury_of_xuen_mut': {
        'type': 'rppm',
        'real_ppm': True,
        'icd': 3,
        'ppm': 1.74 * 1.55,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'fury_of_xuen_combat': {
        'type': 'rppm',
        'real_ppm': True,
        'icd': 3,
        'ppm': 1.74 * 1.15,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'fury_of_xuen_sub': {
        'type': 'rppm',
        'real_ppm': True,
        'icd': 3,
        'ppm': 1.74 * 1.00, # yes no modifier but check later again
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'legendary_capacitive_meta': {
        'type': 'rppm',
        'real_ppm': True,
        'icd': 1,
        'ppm': 19.27,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'legendary_capacitive_meta_mut': {
        'type': 'rppm',
        'real_ppm': True,
        'icd': 1,
        'ppm': 19.27 * 1.789,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'legendary_capacitive_meta_combat': {
        'type': 'rppm',
        'real_ppm': True,
        'icd': 1,
        'ppm': 19.27 * 1.136,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'legendary_capacitive_meta_sub': {
        'type': 'rppm',
        'real_ppm': True,
        'icd': 1,
        'ppm': 19.27 * 1.114,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'swordguard_embroidery': {
        'type': 'perc',
        'icd': 55,
        'proc_chance': .15,
        'trigger': 'all_attacks'
    },
    # weapon procs
    'dancing_steel': {
        'type': 'rppm',
        'real_ppm':True,
        'icd': 0,
        'ppm': 2.53,
        'trigger': 'all_melee_attacks'
    },
    'windsong': {
        'type': 'rppm',
        'real_ppm':True,
        'icd': 0,
        'ppm': 2.2,
        'trigger': 'all_attacks'
    },
    'elemental_force': {
        'type': 'rppm',
        'real_ppm':True,
        'icd': 0,
        'ppm': 9.17,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    #5.4 Procs
    'assurance_of_consequence': {
        'type': 'perc',
        'icd': 115,
        'proc_chance': 0.15,
        'trigger': 'all_attacks'
    },
    'haromms_talisman': {
        'type': 'rppm',
        'real_ppm':True,
        'icd': 10,
        'ppm': 0.92,
        'trigger': 'all_attacks'
    },
    'sigil_of_rampage': {
        'type': 'perc',
        'icd': 85,
        'proc_chance': 0.15,
        'trigger': 'all_attacks'
    },
    'ticking_ebon_detonator': {
        'type': 'rppm',
        'real_ppm':True,
        'icd': 10,
        'ppm': 1.00,
        'trigger': 'all_attacks'
    },
    'thoks_tail_tip': {
        'type': 'perc',
        'icd': 115,
        'proc_chance': 0.15,
        'trigger': 'all_attacks'
    },
    'discipline_of_xuen': {
        'type': 'perc',
        'icd': 115,
        'proc_chance': 0.15,
        'trigger': 'all_attacks'
    },
}
