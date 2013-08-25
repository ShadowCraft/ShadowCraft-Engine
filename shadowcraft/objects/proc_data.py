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
        'stat': 'agi',
        'value': 14037, # not 100% accurate
        'duration': 20,
        'proc_name': 'Assurance of Consequence',
        'behaviours': {'default': 'assurance_of_consequence'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 572, 'quality': 'epic'}
    },
    'heroic_assurance_of_consequence': {
        'stat': 'agi',
        'value': 13273, # not 100% accurate
        'duration': 20,
        'proc_name': 'Assurance of Consequence',
        'behaviours': {'default': 'assurance_of_consequence'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 566, 'quality': 'epic'}
    },
    'war_assurance_of_consequence': {
        'stat': 'agi',
        'value': 12435, # not 100% accurate
        'duration': 20,
        'proc_name': 'Assurance of Consequence',
        'behaviours': {'default': 'assurance_of_consequence'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 559, 'quality': 'epic'}
    },
    'assurance_of_consequence': {
        'stat': 'agi',
        'value': 11761,
        'duration': 20,
        'proc_name': 'Assurance of Consequence',
        'behaviours': {'default': 'assurance_of_consequence'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 553, 'quality': 'epic'}
    },
    'flex_assurance_of_consequence': {
        'stat': 'agi',
        'value': 10418, # not 100% accurate
        'duration': 20,
        'proc_name': 'Assurance of Consequence',
        'behaviours': {'default': 'assurance_of_consequence'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 540, 'quality': 'epic'}
    },
    'lfr_assurance_of_consequence': {
        'stat': 'agi',
        'value': 9316, # not 100% accurate
        'duration': 20,
        'proc_name': 'Assurance of Consequence',
        'behaviours': {'default': 'assurance_of_consequence'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 528, 'quality': 'epic'}
    },
    'heroic_war_haromms_talisman': {
        'stat': 'agi',
        'value': 14037, # not 100% accurate
        'duration': 10,
        'proc_name': 'Haromms Talisman',
        'behaviours': {'default': 'haromms_talisman'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 572, 'quality': 'epic'}
    },
    'heroic_haromms_talisman': {
        'stat': 'agi',
        'value': 13273, # not 100% accurate
        'duration': 10,
        'proc_name': 'Haromms Talisman',
        'behaviours': {'default': 'haromms_talisman'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 566, 'quality': 'epic'}
    },
    'war_haromms_talisman': {
        'stat': 'agi',
        'value': 12435, # not 100% accurate
        'duration': 10,
        'proc_name': 'Haromms Talisman',
        'behaviours': {'default': 'haromms_talisman'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 559, 'quality': 'epic'}
    },
    'haromms_talisman': {
        'stat': 'agi',
        'value': 11761,
        'duration': 10,
        'proc_name': 'Haromms Talisman',
        'behaviours': {'default': 'haromms_talisman'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 553, 'quality': 'epic'}
    },
    'flex_haromms_talisman': {
        'stat': 'agi',
        'value': 10418, # not 100% accurate
        'duration': 10,
        'proc_name': 'Haromms Talisman',
        'behaviours': {'default': 'haromms_talisman'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 540, 'quality': 'epic'}
    },
    'lfr_haromms_talisman': {
        'stat': 'agi',
        'value':  9316, # not 100% accurate
        'duration': 10,
        'proc_name': 'Haromms Talisman',
        'behaviours': {'default': 'haromms_talisman'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 528, 'quality': 'epic'}
    },
    'heroic_war_sigil_of_rampage': {
        'stat': 'agi',
        'value': 14037, # not 100% accurate
        'duration': 15,
        'proc_name': 'Sigil of Rampage',
        'behaviours': {'default': 'sigil_of_rampage'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 572, 'quality': 'epic'}
    },
    'heroic_sigil_of_rampage': {
        'stat': 'agi',
        'value': 13273, # not 100% accurate
        'duration': 15,
        'proc_name': 'Sigil of Rampage',
        'behaviours': {'default': 'sigil_of_rampage'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 566, 'quality': 'epic'}
    },
    'war_sigil_of_rampage': {
        'stat': 'agi',
        'value': 12435, # not 100% accurate
        'duration': 15,
        'proc_name': 'Sigil of Rampage',
        'behaviours': {'default': 'sigil_of_rampage'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 559, 'quality': 'epic'}
    },
    'sigil_of_rampage': {
        'stat': 'agi',
        'value': 11761,
        'duration': 15,
        'proc_name': 'Sigil of Rampage',
        'behaviours': {'default': 'sigil_of_rampage'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 553, 'quality': 'epic'}
    },
    'flex_sigil_of_rampage': {
        'stat': 'agi',
        'value': 10418, # not 100% accurate
        'duration': 15,
        'proc_name': 'Sigil of Rampage',
        'behaviours': {'default': 'sigil_of_rampage'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 540, 'quality': 'epic'}
    },
    'lfr_sigil_of_rampage': {
        'stat': 'agi',
        'value': 9316, # not 100% accurate
        'duration': 15,
        'proc_name': 'Sigil of Rampage',
        'behaviours': {'default': 'sigil_of_rampage'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 528, 'quality': 'epic'}
    },
    'heroic_war_ticking_ebon_detonator': {
        'stat': 'agi',
        'value': 1275 * 10.5, # probably not accurate
        'duration': 10,
        'proc_name': 'Ticking Ebon Detonator',
        'behaviours': {'default': 'ticking_ebon_detonator'},
        'upgradable': True,
        'scaling': {'factor': 0.2703000009 * 10.5, 'item_level': 572, 'quality': 'epic'}
    },
    'heroic_ticking_ebon_detonator': {
        'stat': 'agi',
        'value': 1206 * 10.5, # probably not accurate
        'duration': 10,
        'proc_name': 'Ticking Ebon Detonator',
        'behaviours': {'default': 'ticking_ebon_detonator'},
        'upgradable': True,
        'scaling': {'factor': 0.2703000009 * 10.5, 'item_level': 566, 'quality': 'epic'}
    },
    'war_ticking_ebon_detonator': {
        'stat': 'agi',
        'value': 1130 * 10.5, # probably not accurate
        'duration': 10,
        'proc_name': 'Ticking Ebon Detonator',
        'behaviours': {'default': 'ticking_ebon_detonator'},
        'upgradable': True,
        'scaling': {'factor': 0.2703000009 * 10.5, 'item_level': 559, 'quality': 'epic'}
    },
    'ticking_ebon_detonator': {
        'stat': 'agi',
        'value': 1069 * 10.5, # probably not accurate
        'duration': 10,
        'proc_name': 'Ticking Ebon Detonator',
        'behaviours': {'default': 'ticking_ebon_detonator'},
        'upgradable': True,
        'scaling': {'factor': 0.2703000009 * 10.5, 'item_level': 553, 'quality': 'epic'}
    },
    'flex_ticking_ebon_detonator': {
        'stat': 'agi',
        'value': 946 * 10.5, # probably not accurate
        'duration': 10,
        'proc_name': 'Ticking Ebon Detonator',
        'behaviours': {'default': 'ticking_ebon_detonator'},
        'upgradable': True,
        'scaling': {'factor': 0.2703000009 * 10.5, 'item_level': 540, 'quality': 'epic'}
    },
    'lfr_ticking_ebon_detonator': {
        'stat': 'agi',
        'value': 846 * 10.5, # probably not accurate
        'duration': 10,
        'proc_name': 'Ticking Ebon Detonator',
        'behaviours': {'default': 'ticking_ebon_detonator'},
        'upgradable': True,
        'scaling': {'factor': 0.2703000009 * 10.5, 'item_level': 528, 'quality': 'epic'}
    },
    'heroic_war_thoks_tail_tip': {
        'stat': 'str',
        'value': 14037, # not 100% accurate
        'duration': 20,
        'proc_name': 'Thoks Tail Tip',
        'behaviours': {'default': 'thoks_tail_tip'},
        'upgradable': True,
        'scaling': {'factor':  2.9730000496, 'item_level': 572, 'quality': 'epic'}
    },
    'heroic_thoks_tail_tip': {
        'stat': 'str',
        'value': 13273, # not 100% accurate
        'duration': 20,
        'proc_name': 'Thoks Tail Tip',
        'behaviours': {'default': 'thoks_tail_tip'},
        'upgradable': True,
        'scaling': {'factor':  2.9730000496, 'item_level': 566, 'quality': 'epic'}
    },
    'war_thoks_tail_tip': {
        'stat': 'str',
        'value': 12435, # not 100% accurate
        'duration': 20,
        'proc_name': 'Thoks Tail Tip',
        'behaviours': {'default': 'thoks_tail_tip'},
        'upgradable': True,
        'scaling': {'factor':  2.9730000496, 'item_level': 559, 'quality': 'epic'}
    },
    'thoks_tail_tip': {
        'stat': 'str',
        'value': 11761,
        'duration': 20,
        'proc_name': 'Thoks Tail Tip',
        'behaviours': {'default': 'thoks_tail_tip'},
        'upgradable': True,
        'scaling': {'factor':  2.9730000496, 'item_level': 553, 'quality': 'epic'}
    },
    'flex_thoks_tail_tip': {
        'stat': 'str',
        'value': 10418, # not 100% accurate
        'duration': 20,
        'proc_name': 'Thoks Tail Tip',
        'behaviours': {'default': 'thoks_tail_tip'},
        'upgradable': True,
        'scaling': {'factor':  2.9730000496, 'item_level': 540, 'quality': 'epic'}
    },
    'lfr_thoks_tail_tip': {
        'stat': 'str',
        'value': 9316, # not 100% accurate
        'duration': 20,
        'proc_name': 'Thoks Tail Tip',
        'behaviours': {'default': 'thoks_tail_tip'},
        'upgradable': True,
        'scaling': {'factor':  2.9730000496, 'item_level': 528, 'quality': 'epic'}
    },
    'timeless_discipline_of_xuen': {
        'stat': 'mastery',
        'value': 9943,
        'duration': 20,
        'proc_name': 'Discipline of Xuen',
        'behaviours': {'default': 'discipline_of_xuen'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 535, 'quality': 'epic'}
    },
    'discipline_of_xuen': {
        'stat': 'mastery',
        'value': 6914,
        'duration': 20,
        'proc_name': 'Discipline of Xuen',
        'behaviours': {'default': 'discipline_of_xuen'},
        'upgradable': True,
        'scaling': {'factor': 2.9730000496, 'item_level': 496, 'quality': 'epic'}
    },
    #5.2
    'heroic_thunder_rune_of_re_origination': {
        'stat': 'multi',
        'value': 0,
        'buffs': ('none', 0),
        'duration': 10,
        'proc_name': 'Rune of Re-Origination',
        'behaviours': {'default': 'rune_of_re_origination'},
        'upgradable': True,
        'scaling': {'factor': 0.0, 'item_level': 541, 'quality': 'epic'},
    },
    'heroic_rune_of_re_origination': {
        'stat': 'multi',
        'value': 0,
        'buffs': ('none', 0),
        'duration': 10,
        'proc_name': 'Rune of Re-Origination',
        'behaviours': {'default': 'rune_of_re_origination'},
        'upgradable': True,
        'scaling': {'factor': 0.0, 'item_level': 535, 'quality': 'epic'},
    },
    'thunder_rune_of_re_origination': {
        'stat': 'multi',
        'value': 0,
        'buffs': ('none', 0),
        'duration': 10,
        'proc_name': 'Rune of Re-Origination',
        'behaviours': {'default': 'rune_of_re_origination'},
        'upgradable': True,
        'scaling': {'factor': 0.0, 'item_level': 528, 'quality': 'epic'},
    },
    'rune_of_re_origination': {
        'stat': 'multi',
        'value': 0,
        'buffs': ('none', 0),
        'duration': 10,
        'proc_name': 'Rune of Re-Origination',
        'behaviours': {'default': 'rune_of_re_origination'},
        'upgradable': True,
        'scaling': {'factor': 0.0, 'item_level': 522, 'quality': 'epic'}
    },
    'lfr_rune_of_re_origination': {
        'stat': 'multi',
        'value': 0,
        'buffs': ('none', 0),
        'duration': 10,
        'proc_name': 'Rune of Re-Origination',
        'behaviours': {'default': 'rune_of_re_origination'},
        'upgradable': True,
        'scaling': {'factor': 0.0, 'item_level': 502, 'quality': 'epic'}
    },
    'heroic_thunder_bad_juju': {
        'stat': 'agi',
        'value': 8754,
        'duration': 10,
        'proc_name': 'Bad Juju',
        'behaviours': {'default': 'bad_juju'},
        'upgradable': True,
        'scaling': {'factor': 2.4749999046, 'item_level': 541, 'quality': 'epic'}
    },
    'heroic_bad_juju': {
        'stat': 'agi',
        'value': 8279,
        'duration': 10,
        'proc_name': 'Bad Juju',
        'behaviours': {'default': 'bad_juju'},
        'upgradable': True,
        'scaling': {'factor': 2.4749999046, 'item_level': 535, 'quality': 'epic'}
    },
    'thunder_bad_juju': {
        'stat': 'agi',
        'value': 7757,
        'duration': 10,
        'proc_name': 'Bad Juju',
        'behaviours': {'default': 'bad_juju'},
        'upgradable': True,
        'scaling': {'factor': 2.4749999046, 'item_level': 528, 'quality': 'epic'}
    },
    'bad_juju': {
        'stat': 'agi',
        'value': 7333,
        'duration': 10,
        'proc_name': 'Bad Juju',
        'behaviours': {'default': 'bad_juju'},
        'upgradable': True,
        'scaling': {'factor': 2.4749999046, 'item_level': 522, 'quality': 'epic'}
    },
    'lfr_bad_juju': {
        'stat': 'agi',
        'value': 6088,
        'duration': 10,
        'proc_name': 'Bad Juju',
        'behaviours': {'default': 'bad_juju'},
        'upgradable': True,
        'scaling': {'factor': 2.4749999046, 'item_level': 502, 'quality': 'epic'}
    },
    'heroic_thunder_talisman_of_bloodlust': {
        'stat': 'haste',
        'value': 1836,
        'base_value': 1836,
        'duration': 10,
        'max_stacks': 5,
        'proc_name': 'Talisman of Bloodlust',
        'behaviours': {'default': 'talisman_of_bloodlust'},
        'upgradable': True,
        'scaling': {'factor': 0.5189999938, 'item_level': 541, 'quality': 'epic'}
    },
    'heroic_talisman_of_bloodlust': {
        'stat': 'haste',
        'value': 1736,
        'base_value': 1736,
        'duration': 10,
        'max_stacks': 5,
        'proc_name': 'Talisman of Bloodlust',
        'behaviours': {'default': 'talisman_of_bloodlust'},
        'upgradable': True,
        'scaling': {'factor': 0.5189999938, 'item_level': 535, 'quality': 'epic'}
    },
    'thunder_talisman_of_bloodlust': {
        'stat': 'haste',
        'value': 1627,
        'base_value': 1627,
        'duration': 10,
        'max_stacks': 5,
        'proc_name': 'Talisman of Bloodlust',
        'behaviours': {'default': 'talisman_of_bloodlust'},
        'upgradable': True,
        'scaling': {'factor': 0.5189999938, 'item_level': 528, 'quality': 'epic'}
    },
    'talisman_of_bloodlust': {
        'stat': 'haste',
        'value': 1538,
        'base_value': 1538,
        'duration': 10,
        'max_stacks': 5,
        'proc_name': 'Talisman of Bloodlust',
        'behaviours': {'default': 'talisman_of_bloodlust'},
        'upgradable': True,
        'scaling': {'factor': 0.5189999938, 'item_level': 522, 'quality': 'epic'}
    },
    'lfr_talisman_of_bloodlust': {
        'stat': 'haste',
        'value': 1277,
        'base_value': 1277,
        'duration': 10,
        'max_stacks': 5,
        'proc_name': 'Talisman of Bloodlust',
        'behaviours': {'default': 'talisman_of_bloodlust'},
        'upgradable': True,
        'scaling': {'factor': 0.5189999938, 'item_level': 502, 'quality': 'epic'}
    },
    'heroic_thunder_renatakis_soul_charm': {
        'stat': 'agi',
        'value': 8756,
        'duration': 10,
        'proc_name': 'Renatakis Soul Charm',
        'behaviours': {'default': 'renatakis_soul_charm'},
        'upgradable': True,
        'scaling': {'factor': 0.4499999881*5.5, 'item_level': 541, 'quality': 'epic'}
    },
    'heroic_renatakis_soul_charm': {
        'stat': 'agi',
        'value': 8277.5,
        'duration': 10,
        'proc_name': 'Renatakis Soul Charm',
        'behaviours': {'default': 'renatakis_soul_charm'},
        'upgradable': True,
        'scaling': {'factor': 0.4499999881*5.5, 'item_level': 535, 'quality': 'epic'}
    },
    'thunder_renatakis_soul_charm': {
        'stat': 'agi',
        'value': 7755, #needs verification
        'duration': 10,
        'proc_name': 'Renatakis Soul Charm',
        'behaviours': {'default': 'renatakis_soul_charm'},
        'upgradable': True,
        'scaling': {'factor': 0.4499999881*5.5, 'item_level': 528, 'quality': 'epic'}
    },
    'renatakis_soul_charm': {
        'stat': 'agi',
        'value': 7331.5,
        'duration': 10,
        'proc_name': 'Renatakis Soul Charm',
        'behaviours': {'default': 'renatakis_soul_charm'},
        'upgradable': True,
        'scaling': {'factor': 0.4499999881*5.5, 'item_level': 522, 'quality': 'epic'}
    },
    'lfr_renatakis_soul_charm': {
        'stat': 'agi',
        'value': 6088.5,
        'duration': 10,
        'proc_name': 'Renatakis Soul Charm',
        'behaviours': {'default': 'renatakis_soul_charm'},
        'upgradable': True,
        'scaling': {'factor': 0.4499999881*5.5, 'item_level': 502, 'quality': 'epic'}
    },
    'vicious_talisman_of_the_shado-pan_assault': {
        'stat': 'agi',
        'value': 8800,
        'duration': 20,
        'proc_name': 'Shado-Pan_Assault',
        'behaviours': {'default': 'vicious_talisman_of_the_shado-pan_assault'},
        'upgradable': True,
        'scaling': {'factor': 2.9700000286, 'item_level': 522, 'quality': 'epic'}
    },
    
    #5.0-5.1
    'heroic_terror_in_the_mists': {
        'stat': 'crit',
        'value': 7796,
        'duration': 20,
        'proc_name': 'Terror in the Mists',
        'behaviours': {'default': 'terror_in_the_mists'},
        'upgradable': True,
        'scaling': {'factor': 2.9700000286, 'item_level': 509, 'quality': 'epic'}
    },
    'terror_in_the_mists': {
        'stat': 'crit',
        'value': 6908,
        'duration': 20,
        'proc_name': 'Terror in the Mists',
        'behaviours': {'default': 'terror_in_the_mists'},
        'upgradable': True,
        'scaling': {'factor': 2.9700000286, 'item_level': 496, 'quality': 'epic'}
    },
    'lfr_terror_in_the_mists': {
        'stat': 'crit',
        'value': 6121,
        'duration': 20,
        'proc_name': 'Terror in the Mists',
        'behaviours': {'default': 'terror_in_the_mists'},
        'upgradable': True,
        'scaling': {'factor': 2.9700000286, 'item_level': 483, 'quality': 'epic'}
    },
    'heroic_bottle_of_infinite_stars': {
        'stat': 'agi',
        'value': 3653,
        'duration': 20,
        'proc_name': 'Full of Stars',
        'behaviours': {'default': 'bottle_of_infinite_stars'},
        'upgradable': True,
        'scaling': {'factor': 1.4850000143, 'item_level': 502, 'quality': 'epic'}
    },
    'bottle_of_infinite_stars': {
        'stat': 'agi',
        'value': 3236,
        'duration': 20,
        'proc_name': 'Full of Stars',
        'behaviours': {'default': 'bottle_of_infinite_stars'},
        'upgradable': True,
        'scaling': {'factor': 1.4850000143, 'item_level': 489, 'quality': 'epic'}
    },
    'lfr_bottle_of_infinite_stars': {
        'stat': 'agi',
        'value': 2866,
        'duration': 20,
        'proc_name': 'Full of Stars',
        'behaviours': {'default': 'bottle_of_infinite_stars'},
        'upgradable': True,
        'scaling': {'factor': 1.4850000143, 'item_level': 476, 'quality': 'epic'}
    },
    'relic_of_xuen': {
        'stat': 'agi',
        'value': 3027,
        'duration': 15,
        'proc_name': 'Relic of Xuen',
        'behaviours': {'default': 'relic_of_xuen'},
        'upgradable': True,
        'scaling': {'factor': 1.5684000254, 'item_level': 476, 'quality': 'epic'}
    },
    'corens_cold_chromium_coaster': {
        'stat': 'ap',
        'value': 10848,
        'duration': 10,
        'proc_name': 'Reflection of Torment',
        'behaviours': {'default': 'corens_cold_chromium_coaster'},
        'upgradable': True,
        'scaling': {'factor': 5.9439997673, 'item_level': 470, 'quality': 'epic'}
    },
    'searing_words': {
        'stat': 'agi',
        'value': 3386,
        'duration': 25,
        'proc_name': "Searing Words",
        'behaviours': {'default': 'searing_words'},
        'upgradable': True,
        'scaling': {'factor': 1.9800000191, 'item_level': 463, 'quality': 'blue'}
    },
    'windswept_pages': {
        'stat': 'haste',
        'value': 3386,
        'duration': 20,
        'proc_name': 'Windswept Pages',
        'behaviours': {'default': 'windswept_pages'},
        'upgradable': True,
        'scaling': {'factor': 1.9800000191, 'item_level': 463, 'quality': 'blue'}
    },
    'zen_alchemist_stone': {
        'stat': 'highest',
        'stats': ('agi', 'str', 'int'),
        'value': 4041,
        'duration': 15,
        'proc_name': 'Zen Alchemist Stone',
        'behaviours': {'default': 'zen_alchemist_stone'},
        'upgradable': True,
        'scaling': {'factor': 2.6670000553, 'item_level': 458, 'quality': 'blue'}
    },
    'the_gloaming_blade': {
        'stat': 'crit',
        'value': 375,
        'duration': 10,
        'max_stacks': 3,
        'proc_name': 'The Deepest Night',
        'behaviours': {'default': 'the_gloaming_blade'}
    },
    'jaws_of_retribution': {            # Legendary proc stage 1
        'stat': 'agi',
        'value': 2,
        'duration': 30,
        'max_stacks': 50,
        'proc_name': 'Suffering',
        'behaviours': {'default': 'rogue_t13_legendary_proc', 'assassination': 'rogue_t13_legendary_assassination', 'combat': 'rogue_t13_legendary_combat', 'subtlety': 'rogue_t13_legendary_subtlety'}
    },
    'maw_of_oblivion': {                # Legendary proc stage 2
        'stat': 'agi',
        'value': 5,
        'duration': 30,
        'max_stacks': 50,
        'proc_name': 'Nightmare',
        'behaviours': {'default': 'rogue_t13_legendary_proc', 'assassination': 'rogue_t13_legendary_assassination', 'combat': 'rogue_t13_legendary_combat', 'subtlety': 'rogue_t13_legendary_subtlety'}
    },
    'fangs_of_the_father': {            # Legendary proc stage 3. Given that the behaviour changes past the 30 stacks, this'll need an update
        'stat': 'agi',
        'value': 17,
        'duration': 30,
        'max_stacks': 50,
        'proc_name': 'Shadows of the Destroyer',
        'behaviours': {'default': 'rogue_t13_legendary_proc', 'assassination': 'rogue_t13_legendary_assassination', 'combat': 'rogue_t13_legendary_combat', 'subtlety': 'rogue_t13_legendary_subtlety'}
    },
    #Tier
    'rogue_t11_4pc': {
        'stat': 'weird_proc',
        'value': 1,
        'duration': 15,
        'proc_name': 'Deadly Scheme',
        'behaviours': {'default': 'rogue_t11_4pc'}
    },
}

allowed_melee_enchants = {
    'windsong': {
        'stat': 'random',
        'stats': ('haste', 'mastery', 'crit'),
        'value': 1500,
        'duration': 12,
        'proc_name': 'Windsong',
        'behaviours': {'default': 'windsong'}
    },
    'dancing_steel': {
        'stat': 'highest',
        'stats': ('agi', 'str'),
        'value': 1650,
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
        'icd': 0,
        'proc_chance': 1,
        'trigger': 'all_attacks'
    },
    'touch_of_the_grave': {
        'icd': 15,
        'proc_chance': .20,
        'trigger': 'all_attacks'
    },
    'fury_of_xuen': {
        'real_ppm':True,
        'icd': 3,
        'ppm': 1.74,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'fury_of_xuen_mut': {
        'real_ppm':True,
        'icd': 3,
        'ppm': 1.74 * 1.55,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'fury_of_xuen_combat': {
        'real_ppm':True,
        'icd': 3,
        'ppm': 1.74 * 1.15,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'fury_of_xuen_sub': {
        'real_ppm':True,
        'icd': 3,
        'ppm': 1.74 * 1.00, # yes no modifier but check later again
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'legendary_capacitive_meta': {
        'real_ppm':True,
        'icd': 1,
        'ppm': 19.27,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'legendary_capacitive_meta_mut': {
        'real_ppm':True,
        'icd': 1,
        'ppm': 19.27 * 1.789,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'legendary_capacitive_meta_combat': {
        'real_ppm':True,
        'icd': 1,
        'ppm': 19.27 * 1.136,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'legendary_capacitive_meta_sub': {
        'real_ppm':True,
        'icd': 1,
        'ppm': 19.27 * 1.114,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'swordguard_embroidery': {
        'icd': 55,
        'proc_chance': .15,
        'trigger': 'all_attacks'
    },
    # weapon procs
    'dancing_steel': {
        'real_ppm':True,
        'icd': 0,
        'ppm': 2.53,
        'trigger': 'all_melee_attacks'
    },
    'windsong': {
        'real_ppm':True,
        'icd': 0,
        'ppm': 2.2,
        'trigger': 'all_attacks'
    },
    'elemental_force': {
        'real_ppm':True,
        'icd': 0,
        'ppm': 9.17,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    #5.4 Procs
    'assurance_of_consequence': {
        'icd': 115,
        'proc_chance': 0.15,
        'trigger': 'all_attacks'
    },
    'haromms_talisman': {
        'real_ppm':True,
        'icd': 10,
        'ppm': 0.92,
        'trigger': 'all_attacks'
    },
    'sigil_of_rampage': {
        'icd': 85,
        'proc_chance': 0.15,
        'trigger': 'all_attacks'
    },
    'ticking_ebon_detonator': {
        'real_ppm':True,
        'icd': 10,
        'ppm': 1.00,
        'trigger': 'all_attacks'
    },
    'thoks_tail_tip': {
        'icd': 115,
        'proc_chance': 0.15,
        'trigger': 'all_attacks'
    },
    'discipline_of_xuen': {
        'icd': 115,
        'proc_chance': 0.15,
        'trigger': 'all_attacks'
    },
    #5.2 Procs
    'rune_of_re_origination': {
        'real_ppm': True,
        'icd': 10,
        'ppm': 1.1,
        'base_ppm': 1.1,
        'ppm_scale_constant': 528,
        'trigger': 'all_attacks'
    },
    'bad_juju': {
        'real_ppm':True,
        'icd': 10,
        'ppm': 1.1,
        'base_ppm': 1.1,
        'ppm_scale_constant': 528,
        'trigger': 'all_attacks'
    },
    'renatakis_soul_charm': {
        'real_ppm':True,
        'icd': 10,
        'ppm': 1.21,
        'base_ppm': 1.21,
        'ppm_scale_constant': 528,
        'trigger': 'all_attacks'
    },
    'talisman_of_bloodlust': {
        'real_ppm': True,
        'icd': 0,
        'ppm': 3.5,
        'base_ppm': 3.5,
        'ppm_scale_constant': 528,
        'trigger': 'all_attacks'
    },
    'vicious_talisman_of_the_shado-pan_assault': {
        'icd': 115,
        'proc_chance': .15,
        'trigger': 'all_attacks'
    },
    
    # 5.0 Procs
    'bottle_of_infinite_stars': {
        'icd': 55,
        'proc_chance': .15,
        'trigger': 'all_attacks'
    },
    'corens_cold_chromium_coaster': {
        'icd': 50,
        'proc_chance': .10,
        'trigger': 'all_attacks',
        'on_crit': True
    },
    'relic_of_xuen': {
        'icd': 55,
        'proc_chance': .2,
        'trigger': 'all_melee_attacks',
        'on_crit': True
    },
    'searing_words': {
        'icd': 85,
        'proc_chance': .45,
        'trigger': 'all_attacks',
        'on_crit': True
    },
    'terror_in_the_mists':{
        'icd': 115,
        'proc_chance': .15,
        'trigger': 'all_attacks'
    },
    'windswept_pages': {
        'icd': 65,
        'proc_chance': .15,
        'trigger': 'all_attacks',
    },
    'zen_alchemist_stone': {
        'icd': 55,
        'proc_chance': .35,
        'trigger': 'all_attacks',
    },
    'the_gloaming_blade': {                 # PPM/ICD is a guess and should be verified.
        'icd': 0,
        'ppm': 1,
        'trigger': 'all_attacks',
    },
}
