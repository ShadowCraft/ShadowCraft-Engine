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
    #potions
    'draenic_agi_pot': {
        'stat': 'stats',
        'value': {'agi':1000},
        'duration': 25,
        'proc_name': 'Draenic Agi Potion',
        'item_level': 100,
        'type': 'icd',
        'source': 'unique',
        'icd': 0,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'draenic_agi_prepot': {
        'stat': 'stats',
        'value': {'agi':1000},
        'duration': 23,
        'proc_name': 'Draenic Agi Prepot',
        'item_level': 100,
        'type': 'icd',
        'source': 'unique',
        'icd': 0,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'virmens_bite': {
        'stat': 'stats',
        'value': {'agi':456},
        'duration': 25,
        'proc_name': 'Virmens Bite',
        'item_level': 90,
        'type': 'icd',
        'source': 'unique',
        'icd': 0,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'virmens_bite_prepot': {
        'stat': 'stats',
        'value': {'agi':456},
        'duration': 23,
        'proc_name': 'Virmens Bite',
        'item_level': 90,
        'type': 'icd',
        'source': 'unique',
        'icd': 0,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    #racials
    'touch_of_the_grave': {
        'stat': 'spell_damage',
        'value': 0,
        'duration': 0,
        'max_stacks': 0,
        'proc_name': 'Touch of the Grave',
        'type': 'icd',
        'icd': 15,
        'proc_rate': .20,
        'trigger': 'all_attacks'
    },
    'rocket_barrage': {
        'stat': 'spell_damage',
        'value': 0,
        'duration': 0,
        'max_stacks': 0,
        'proc_name': 'Rocket Barrage',
        'type': 'icd',
        'icd': 120,
        'proc_rate': 1.0,
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
    'archmages_incandescence': {
        'stat':'stats_modifier',
        'value': {'agi':.10},
        'duration': 10,
        'proc_name': 'Archmages Incandescence',
        'scaling': 0.0,
        'item_level': 541,
        'type': 'rppm',
        'source': 'unique',
        'icd': 1,
        'proc_rate': 0.92,
        'trigger': 'all_attacks'
    },

    'archmages_greater_incandescence': {
        'stat':'stats_modifier',
        'value': {'agi':.15},
        'duration': 10,
        'proc_name': 'Archmages Greater Incandescence',
        'scaling': 0.0,
        'item_level': 541,
        'type': 'rppm',
        'source': 'unique',
        'icd': 1,
        'proc_rate': 0.92,
        'trigger': 'all_attacks'
    },

    #7.0 neck enchants
    'mark_of_the_hidden_satyr': {
        'stat':'spell_damage',
        'value': 0, # AP based
        'ap_coefficient': 2.5, # server-side, not in dbc
        'dmg_school': 'fire',
        'duration': 0,
        'proc_name': 'Mark of the Hidden Satyr',
        'type': 'rppm',
        'source': 'neck',
        'proc_rate': 2.5,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
   },

    'mark_of_the_distant_army': { #A distant army fires a volley of arrows, dealing 3 ticks of damage over 1.5 sec.
        'stat':'physical_damage',
        'value': 0, # AP based
        'aoe': True,
        'ap_coefficient': 2.5, # server-side, not in dbc, per tick is 2.5 / 3
        'duration': 0,
        'proc_name': 'Mark of the Distant Army',
        'type': 'rppm',
        'source': 'neck',
        'proc_rate': 2.5,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
   },

    'mark_of_the_claw': { #Permanently enchants a necklace to sometimes increase critical strike and haste by 1000 for 6 sec.
        'stat':'stats',
        'value': {'haste': 1000, 'crit': 1000},
        'duration': 6,
        'proc_name': 'Mark of the Claw',
        'source': 'neck',
        'type': 'rppm',
        'proc_rate': 3,
        'trigger': 'all_attacks',
   },

     #Legion trinket procs
    'arcanogolem_digit': { #Equip: Your attacks have a chance to rake all enemies in front of you for X Arcane damage.
        'stat':'spell_damage',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 0,
        'proc_name': 'Arcane Swipe',
        'dmg_school': 'arcane',
        'scaling': 14.21082, #hotfixed value
        'item_level': 870,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': 5,
        'icd': 1,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
   },

    'bloodstained_handkerchief': { #Use: Garrote your target from behind, causing them to bleed for X Physical damage every 3 sec until they die. (1 Min Cooldown)
        'stat':'physical_damage',
        'value': 0, #rpp-scaled, TODO: could be applied to adds as well, after CD
        'duration': 0,
        'proc_name': 'Cruel Garrote',
        'scaling': 3.474452,
        'item_level': 855,
        'type': 'icd',
        'source': 'trinket',
        'proc_rate': 1,
        'icd': 3,
        'can_crit': True,
        'trigger': 'all_attacks'
   },

    'bloodthirsty_instinct': { #Equip: Your melee attacks have a chance to increase your Haste by X for 10 sec.  This effect occurs more often against targets at low health.
        'stat':'stats',
        'value': {'haste': 0}, #rpp-scaled
        'duration': 10,
        'proc_name': 'Bloodthirsty Instinct',
        'scaling': 1.470561,
        'crm_scales': True,
        'item_level': 850,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 3,
        'trigger': 'all_attacks',
   },

    'chaos_talisman': { #Equip: Your melee autoattacks grant you Chaotic Energy, increasing your Strength or Agility by X, stacking up to 20 times. If you do not autoattack an enemy for 4 sec, this effect will decrease by 1 stack every sec.
        'stat':'stats',
        'value': {'agi': 0}, #rpp-scaled
        'duration': 23, #decays by 1 stack after 4s without autoattacks (assume we can ignore decay)
        'max_stacks': 20,
        'proc_name': 'Chaotic Energy',
        'scaling': 0.029595,
        'item_level': 805,
        'source': 'trinket',
        'type': 'icd',
        'icd': 1,
        'proc_rate': 1,
        'trigger': 'auto_attacks',
   },

    'chrono_shard': { #Equip: Your spells and abilities have a chance to grant you X Haste and 15% movement speed for 10 sec.
        'stat':'stats',
        'value': {'haste': 0}, #rpp-scaled, TODO: set bonus?
        'duration': 10,
        'proc_name': 'Acceleration',
        'scaling': 2.741159,
        'crm_scales': True,
        'item_level': 805,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 1,
        'trigger': 'all_attacks',
   },

    'convergence_of_fates': { #Equip: Your attacks have a chance to reduce the remaining cooldown on one of your powerful abilities by 5 sec.
        'stat':'ability_modifier',
        'value': 5, #5 sec decrease, modeled in get_spell_cd
        'duration': 0,
        'proc_name': 'Prescience', # reduce cd of shadow blades, vendetta, adrenaline rush
        'item_level': 875,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': {'assassination': 3.51, 'outlaw': 8.4, 'subtlety': 9},
        'trigger': 'all_attacks',
   },

    #removed the ":" not sure which way it should be
    'darkmoon_deck_dominion': { #Equip: Increase critical strike by X-Y. The amount of critical strike depends on the topmost card in the deck. Equip: Periodically shuffle the deck while in combat.
        'stat': 'stats',
        'value': {'crit':0}, #rpp-scaled, TODO: not accurate, it should be shuffled every 20s
        'duration': 20,
        'proc_name': 'Dominion Deck', #this does some wierd shuffling crit values /wrists
        'scaling': 0.5627245, #use average for now, min 0.375134, max 0.750315
        'item_level': 815,
        'type': 'icd',
        'icd': 20, #slight loss? should change value instantly, not on attack trigger
        'source': 'trinket',
        'proc_rate': 1,
        'trigger': 'all_attacks'
    },

    'draught_of_souls': { #Use: Enter a fel-crazed rage, dealing X damage to a random nearby enemy every 0.25sec for 3 sec.  You cannot move or use abilities during your rage. (1 Min, 20 Sec Cooldown)
        'stat':'spell_damage',
        'value': 0, #rpp-scaled
        'duration': 3, #3sec ability downtime modeled in add_special_aps_penalties
        'proc_name': 'Fel-Crazed Rage',
        'dmg_school': 'shadow',
        'scaling': 33. * 13., #13 hits total
        'item_level': 880,
        'source': 'trinket',
        'type': 'icd',
        'icd': 80,
        'proc_rate': 1,
        'can_crit': True,
        'trigger': 'all_attacks',
   },

    'entwined_elemental_foci': { #Equip: Your attacks have a chance to grant you a Fiery, Frost, or Arcane enchants for 20 sec.
        'stat':'stats',
        'value': {'haste': 0, 'crit': 0, 'mastery': 0}, #TODO: needs special modeling, you get only one stat per proc, but can have multiple at the same time
        'duration': 20,
        'proc_name': 'Triumvirate',
        'scaling': 2.069368 / 3., #FIXME: for now using 1/3 for each stat / assume we get all 3 for 1/3 each
        'crm_scales': True,
        'item_level': 875,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 0.7,
        'trigger': 'all_attacks',
   },

    'eye_of_command': { #Equip: Your melee auto attacks increase your Critical Strike by 148 for 10 sec, stacking up to 10 times. This effect is reset if you auto attack a different target.
        'stat':'stats',
        'value': {'crit': 0}, #rpp-scaled
        'duration': 10, #decays when autoattacking different target, assume we can ignore
        'max_stacks': 10,
        'proc_name': "Legion's Gaze",
        'scaling': 0.072857,
        'crm_scales': True,
        'item_level': 860,
        'source': 'trinket',
        'type': 'icd',
        'icd': 1,
        'proc_rate': 1,
        'trigger': 'auto_attacks',
   },

    'faulty_countermeasure': { #Use: Sheathe your weapons in ice for 30 sec, giving your attacks a chance to cause X additional Frost damage and slow the target's movement speed by 30% for 8 sec.  (2 Min Cooldown)
        'stat':'ability_modifier',
        'value': 0, #rpp-scaled
        'duration': 30,
        'proc_name': 'Sheathed in Frost', #TODO: need special handling, rppm during uptime is 20 and scales with haste
        'scaling': 17.47413,
        'item_level': 805,
        'type': 'icd',
        'source': 'trinket',
        'proc_rate': 1,
        'icd': 120,
        'can_crit': True,
        'trigger': 'all_attacks'
   },

    'giant_ornamental_pearl': { #Use: Become enveloped by a Gaseous Bubble that absorbs up to X damage for 8 sec.  When the bubble is consumed or expires, it explodes and deals Y Frost damage to all nearby enemies within 10 yards.  (1 Min Cooldown)
        'stat':'spell_damage',
        'dmg_school': 'frost',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 0,
        'proc_name': 'Gaseous Bubble',
        'dmg_school': 'frost',
        'scaling': 55.83131,
        'item_level': 805,
        'type': 'icd',
        'source': 'trinket',
        'icd': 60,
        'proc_rate': 1,
        'can_crit': True,
        'trigger': 'all_attacks',
   },

    'horn_of_valor': { #Use: Sound the horn, increasing your primary stat by X for 30 sec. (2 Min Cooldown)
        'stat':'stats',
        'value': {'agi': 0}, #rpp-scaled
        'duration': 30,
        'proc_name': "Valarjar's Path",
        'scaling': 1.2,
        'item_level': 805,
        'type': 'icd',
        'source': 'trinket',
        'icd': 120,
        'proc_rate': 1,
        'trigger': 'all_attacks',
   },

    'infernal_alchemist_stone': { #Equip: When you heal or deal damage you have a chance to increase your Strength, Agility, or Intellect by X for 15 sec.  Your highest stat is always chosen.
        'stat': 'stats',
        'value': {'agi': 0}, #rpp-scaled
        'duration': 15,
        'proc_name': 'Infernal Alchemist Stone',
        'scaling': 1.839772,
        'item_level': 815,
        'type': 'rppm', #yes, it is rppm now
        'source': 'trinket',
        'proc_rate': 1,
        'trigger': 'all_attacks'
    },

    'kiljaedens_burning_wish': { #Use: Launch a vortex of destruction that seeks your current enemy. When it reaches the target, it explodes, dealing a critical strike to all enemies within 10 yds for X Fire damage. (1 Min, 15 Sec Cooldown)
        'stat':'spell_damage',
        'dmg_school': 'fire',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 0,
        'proc_name': "Kil'jaeden's Burning Wish",
        'scaling': 70 * 2, #always crits, hotfixed value
        'item_level': 910,
        'type': 'icd',
        'source': 'trinket',
        'proc_rate': 1,
        'icd': 75,
        'trigger': 'all_attacks'
   },

    'mark_of_dargrul': { #Equip: Your melee attacks have a chance to trigger a Landslide, dealing X Physical damage to all enemies directly in front of you.
        'stat':'physical_damage',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 0,
        'proc_name': 'Landslide',
        'scaling': 21.66943,
        'item_level': 805,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': 4,
        'icd': 2,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
   },

    'memento_of_angerboda': { #Equip: Your melee attacks have a chance to activate Screams of the Dead, granting you a random combat enhancement for 8 sec.
        'stat':'stats',
        'value': {'mastery': 0, 'crit': 0, 'haste': 0}, #TODO: actually 1-3 stat buffs each time
        'duration': 8,
        'proc_name': 'Screams of the Dead',
        'scaling': 2.297781 / 3., #FIXME: for now using 1/3 for each stat, similar to entwined elemental foci
        'crm_scales': True,
        'item_level': 805,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 1.5,
        'trigger': 'all_attacks',
   },

    'natures_call': { #Equip: Your melee attacks have a chance to grant you a blessing of one of the Allies of Nature for 10 sec.
        'stat':'stats',
        'value': {'mastery': 0, 'crit': 0, 'haste': 0}, #rpp-scaled, TODO: needs special modeling, you get only one stat per proc, but can have multiple at the same time
        'duration': 10,
        'proc_name': 'Allies of Nature',
        'scaling': 1.378778 / 3., #FIXME: for now using 1/3 for each stat, similar to entwined elemental foci
        'crm_scales': True,
        'item_level': 850,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 2,
        'can_crit': True, #TODO: according to wowhead this can also proc Cleansed Drake's Breath for (scale factor 48.72993) damage
        'trigger': 'all_attacks',
   },

    'nightblooming_frond': { #Equip: Your attacks have a chance to grant Recursive Strikes for 15 sec, causing your auto attacks to deal an additional X damage and increase the intensity of Recursive Strikes.
        'stat':'ability_modifier',
        'value': 0, #rpp-scaled, modeled in add_special_procs_damage
        'duration': 15,
        'max_stacks': 15,
        'dmg_school': 'physical',
        'proc_name': 'Recursive Strikes',
        'scaling': 2.12,
        'item_level': 875,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 1,
        'can_crit': True,
        'trigger': 'all_attacks',
   },

    'nightmare_egg_shell': { #Equip: Your melee attacks have a chance to grant you X Haste every 1 sec for 20 sec.
        'stat':'stats',
        'value': {'haste': 0}, #rpp-scaled
        'duration': 20,
        'proc_name': 'Down Draft',
        'scaling': 0.187677 * 10.5, # avg should be 10.5 stacks for 20 sec, melee attacks only needed to proc, not for stacks
        'item_level': 805,
        'source': 'trinket',
        'type': 'rppm',
        'icd': 20,
        'proc_rate': .7,
        'trigger': 'all_attacks',
   },

    'ravaged_seed_pod': { #Use: Contaminate the ground beneath your feet for 10 sec, dealing X Shadow damage to enemies in the area each second.  While you remain in this area, you gain Y Leech.  (1 Min Cooldown)
        'stat':'spell_damage',
        'value': 0, #rpp-scaled
        'aoe': True,
        'dmg_school': 'shadow',
        'duration': 10,
        'proc_name': 'Infested Ground',
        'scaling': 6.624573,
        'item_level': 850,
        'type': 'icd',
        'icd': 60,
        'source': 'trinket',
        'proc_rate': 1,
   },

    'six_feather_fan': { #Equip: Your attacks have a chance to launch a volley of 6 Wind Bolts, each dealing X Nature damage and slowing your target by 30% for 6 sec.
        'stat':'spell_damage',
        'dmg_school': 'nature',
        'value': 0, #rpp-scaled
        'duration': 0,
        'proc_name': 'Wind Bolt',
        'scaling': 19.01865 * 6., #6 bolts, one every second
        'item_level': 810,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': 1,
        'haste_scales': True,
        'can_crit': True
   },

    'spiked_counterweight': { #Your melee attacks have a chance to deal X Physical damage and increase all damage the target takes from you by 15% for 15 sec, up to Y extra damage dealt.
        'stat':'physical_damage',
        'value': 0, #rpp-scaled
        'duration': 0,
        'proc_name': 'Brutal Haymaker',
        'scaling': 49.4631 + 185.487, #scaling for initial + extra damage. can we just add full extra dmg? what about crits?
        'item_level': 805,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': .92,
   },

    'spontaneous_appendages': { #Equip: Your melee attacks have a chance to generate extra appendages for 12 sec that attack nearby enemies for X Physical damage every 0.75 sec.
        'stat':'physical_damage',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 0, #accumulate all dmg
        'proc_name': 'Horrific Slam', #not the proc name but the dmg
        'can_crit': True,
        'scaling': 10.1246 * 16., # 16 hits overall, hotfixed value
        'item_level': 850,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': .7,
        'haste_scales': True,
   },

    'tempered_egg_of_serpentrix': { #Equip: Your attacks have a chance to summon a Spawn of Serpentrix to assist you.
        'stat':'spell_damage',
        'dmg_school': 'fire',
        'value': 0, #rpp-scaled
        'duration': 15,
        'proc_name': 'Magma Spit', #not the proc name but the dmg of the add
        'scaling': 8.235604 * 8., # pet might be scaling with haste, but most logs have 8 magma spits, assume that for now
        'item_level': 805,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 1,
        'can_crit': True,
        'haste_scales': True,
        'trigger': 'all_attacks',
   },

      'terrorbound_nexus': { #Equip: Your melee attacks have a chance to unleash 4 Shadow Waves that deal X Shadow damage to enemies in their path.  The waves travel 15 yards away from you, and then return.
        'stat':'spell_damage',
        'dmg_school': 'shadow',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 0,
        'proc_name': 'Shadow Wave',
        'scaling': 46.22871 * 8., #assuming 4 hits out and 4 in
        'item_level': 805,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': 1,
        'icd': 10,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
   },

    'the_devilsaurs_bite': { #Equip: Your attacks have a chance to inflict X Physical damage and stun the target for 1 sec.
        'stat':'physical_damage',
        'value': 0, #rpp-scaled
        'duration': 0,
        'proc_name': "Devilsaur's Bite",
        'scaling': 65.,
        'item_level': 805,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': 2,
        'haste_scales': True,
        'can_crit': True
   },

    'tiny_oozeling_in_a_jar': { #Equip: Your melee attacks have a chance to grant you Congealing Goo, stacking up to 6 times.  Use: Consume all Congealing Goo to vomit on enemies in front of you for 3 sec, inflicting X Nature damage per Goo consumed.  (20 Sec Cooldown)
        'stat':'spell_damage',
        'dmg_school': 'nature',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 0,
        #'max_stacks': 6,
        'proc_name': 'Fetid Regurgitation',
        'scaling': 17.123 * 6., #assume 6 stacks, scaling value not found in DBC, server-side/hotfixed? calculated by hand
        'item_level': 805,
        'type': 'icd', #actually rppm
        'source': 'trinket',
        #'proc_rate': 3,
        'icd': 20, #modeled as used on cooldown with max stacks every time
        #'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
   },

    'tirathons_betrayal': { #Use: Empower yourself with dark energy, causing your attacks to have a chance to inflict 38847 additional Shadow damage and grant you a shield for 38847. Lasts 15 sec.  (1 Min, 15 Sec Cooldown)
        'stat':'ability_modifier',
        'value': 0,
        'duration': 15,
        'proc_name': 'Darkstrikes', #TODO: need special handling
        'scaling': 16.11315,
        'item_level': 805,
        'type': 'icd',
        'source': 'trinket',
        'proc_rate': 1,
        'icd': 75,
        'can_crit': True,
        'trigger': 'all_attacks'
   },

    'toe_knees_promise': { #Use: Create a Flame Gale at an enemy's location, dealing X Fire damage over 8 sec. If Flame Gale strikes an enemy affected by Thunder Ritual, Flame Gale's damage is increased by 30%, and its radius by 50%. (1 Min Cooldown)
        'stat':'spell_damage',
        'dmg_school': 'fire',
        'value': 0, #rpp-scaled, TODO: only modeled base damage without Thunder Ritual
        'duration': 0,
        'proc_name': 'Flame Gale',
        'scaling': 9.768856 * 8.,
        'item_level': 855,
        'source': 'trinket',
        'type': 'icd',
        'icd': 60,
        'proc_rate': 1,
        'can_crit': True,
        'trigger': 'all_attacks',
   },

    'windscar_whetstone': { #Use: A Slicing Maelstrom surrounds you, inflicting X Physical damage to nearby enemies over 6 sec.  (2 Min Cooldown)
        'stat':'physical_damage',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 0,
        'proc_name': 'Slicing Maelstrom',
        'scaling': 19.93953 * 7., # 7 hits
        'item_level': 805,
        'type': 'icd',
        'source': 'trinket',
        'icd': 120,
        'proc_rate': 1,
        'can_crit': True,
        'trigger': 'all_attacks'
   },

   #Other Legion procs
   'jacins_ruse_2pc': { #Equip:  Your spells and attacks have a chance to increase your Mastery by 3000 for 15 sec.
    	'stat':'stats',
    	'value':{'mastery':3000},
    	'duration':15,
    	'proc_name': "Jacin's Ruse",
    	'item_level': 820,
    	'type': 'rppm',
    	'source': 'unique',
    	'icd': 0,
    	'proc_rate': 1,
    	'can_crit': False,
    	'trigger': 'all_attacks'
    },

    'march_of_the_legion_2pc': { #Equip: Your spells and attacks against Demons have a chance to deal an additional 27200 to 36800 Fire damage.
        'stat':'spell_damage',
        'value': 35000,
        'duration':0,
        'proc_name': "March of the Legion",
        'item_level': 820,
        'type': 'rppm',
        'source': 'unique',
        'icd': 0,
        'proc_rate': 6,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
    },

    #6.2.3 procs
    'infallible_tracking_charm': {
        'stat':'spell_damage',
        'value': 42872,
        'duration': 0,
        'proc_name': "Cleansing Flame",
        #'scaling': 61.1583452211,
        'item_level': 715,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': 3,
        'haste_scales': False,
        'can_crit': False,
        'trigger': 'all_attacks'
   },

    'infallible_tracking_charm_mod': {
        'stat':'damage_modifier',
        'value': {'damage_mod': 10},
        'proc_name': "Cleansing Flame",
        'scaling': 0.0,
        'item_level': 715,
        'type': 'rppm',
        'source': 'trinket',
        'duration': 5,
        'proc_rate': 3,
        'haste_scales': False,
        'trigger': 'all_attacks'
   },
    #6.2 procs
    'maalus': {
        'stat': 'damage_modifier',
        'value': {'damage_mod': 2500},
        'duration': 15,
        'proc_name': 'Maalus',
        'upgradable': True,
        'scaling': 2.95857988166,
        'item_level': 735,
        'type': 'icd',
        'source': 'trinket',
        'icd': 120,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },

    'felmouth_frenzy': {
        'stat':'spell_damage',
        'value': 1,
        'duration': 0,
        'proc_name': 'Fel Lash',
        'scaling': 0.0,
        'type': 'rppm',
        'source': 'unique',
        'icd': 0,
        'proc_rate': 2,
        'haste_scales': True,
        'can_crit': False,
        'trigger': 'all_attacks'
    },

    'malicious_censer': {
        'stat': 'stats',
        'value': {'agi':1093},
        'duration': 20,
        'proc_name': 'Malicious Censer',
        'upgradable': True,
        'scaling': 1.79180327869,
        'item_level': 700,
        'type': 'rppm',
        'source': 'trinket',
        'icd': 0,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },

    'soul_capacitor': {
        'stat': 'damage_modifier',
        'value': {'damage_mod': 2677},
        'duration': 10,
        'proc_name': 'Soul Capacitor',
        'upgradable': True,
        'scaling': 4.59965635,
        'item_level': 695,
        'type': 'rppm',
        'source': 'trinket',
        'icd': 0,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },

    'mirror_of_the_blademaster': {
        'stat': 'physical_damage',
        'value': {'damage': 1},
        'duration': 20,
        'proc_name': 'Mirror of the Blademaster',
        'upgradable': True,
        'scaling': 1.0,
        'item_level': 695,
        'type': 'icd',
        'source': 'trinket',
        'icd': 60,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },

    'bleeding_hollow_toxin_vessel': {
        'stat': 'ability_modifer',
        'value': {'ability_mod':5149},
        'duration': 0,
        'proc_name': 'Bleeding Hollow Toxin Vessel',
        'upgradable': True,
        'scaling': 8.05790297,
        'item_level': 705,
        'type': 'perk',
        'source': 'trinket',
        'icd': 0,
        'proc_rate': 0.0,
        'trigger': 'all_attacks'
    },

    #all alchemy trinket upgrades are just scales
    #with different names, collapsed into single proc
    'alchemy_stone': {
        'stat': 'stats',
        'value': {'agi':1350},
        'duration': 15,
        'proc_name': 'Alchemy Trinket Proc',
        'upgradable': True,
        'scaling': 2.6670000553,
        'item_level': 680,
        'type': 'icd',
        'source': 'trinket',
        'icd': 55,
        'proc_rate': 0.35,
        'trigger': 'all_attacks'
    },
    #6.0 procs
    'humming_blackiron_trigger': {
        'stat': 'stats',
        'value': {'crit':131},
        'duration': 10,
        'proc_name': 'Humming Blackiron Trigger',
        'upgradable': True,
        'scaling': 0.2969999909 * 10.5,
        'item_level': 665,
        'type': 'rppm',
        'source': 'trinket',
        'icd': 0,
        'proc_rate': 0.92,
        'trigger': 'all_attacks'
    },
    'meaty_dragonspine_trophy': {
        'stat': 'stats',
        'value': {'haste':1913},
        'duration': 10,
        'proc_name': 'Meaty Dragonspine Trophy',
        'upgradable': True,
        'scaling': 4.3477997780,
        'item_level': 665,
        'type': 'rppm',
        'source': 'trinket',
        'icd': 0,
        'proc_rate': 0.92,
        'trigger': 'all_attacks'
    },
    'formidable_jar_of_doom': {
        'stat': 'stats',
        'value': {'mastery':1743},
        'duration': 10,
        'proc_name': 'Formidable Jar of Doom',
        'upgradable': True,
        'scaling': 4.3477997780,
        'item_level': 665,
        'type': 'rppm',
        'source': 'trinket',
        'icd': 0,
        'proc_rate': 0.92,
        'trigger': 'all_attacks'
    },
    'scales_of_doom': {
        'stat': 'stats',
        'value': {'mastery':1743},
        'duration': 10,
        'proc_name': 'Scales of Doom',
        'upgradable': True,
        'scaling': 4.3477997780,
        'item_level': 665,
        'type': 'rppm',
        'source': 'trinket',
        'icd': 0,
        'proc_rate': 0.92,
        'trigger': 'all_attacks'
    },
    'blackheart_enforcers_medallion': {
        'stat': 'stats',
        'value': {'haste':1665},
        'duration': 10,
        'proc_name': 'Blackheart Enforcers Medallion',
        'upgradable': True,
        'scaling': 4.3477997780,
        'item_level': 665,
        'type': 'rppm',
        'source': 'trinket',
        'icd': 0,
        'proc_rate': 0.92,
        'trigger': 'all_attacks'
    },
    'lucky_doublesided_coin': {
        'stat': 'stats',
        'value': {'agi':1467},
        'duration': 20,
        'proc_name': 'Lucky Double-sided Coin',
        'upgradable': True,
        'scaling': 3.3333330154,
        'item_level': 665,
        'type': 'icd',
        'source': 'trinket',
        'icd': 120,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'beating_heart_of_the_mountain': {
        'stat': 'stats',
        'value': {'crit':1467},
        'duration': 20,
        'proc_name': 'Beating Heart of the Mountain',
        'upgradable': True,
        'scaling': 3.3333330154,
        'item_level': 665,
        'type': 'icd',
        'source': 'trinket',
        'icd': 120,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'skull_of_war': {
        'stat': 'stats',
        'value': {'crit':1396},
        'duration': 20,
        'proc_name': 'Skull of War',
        'upgradable': True,
        'scaling': 4.0000000000,
        'item_level': 640,
        'type': 'icd',
        'source': 'trinket',
        'icd': 115,
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
    'primal_combatants_ioc': {
        'stat': 'stats',
        'value': {'agi':505},
        'duration': 20,
        'proc_name': 'Primal Combatants Insignia of Conquest',
        'upgradable': True,
        'scaling': 1.7480000257,
        'item_level': 620,
        'type': 'icd',
        'source': 'trinket',
        'icd': 55,
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
    'primal_combatants_boc': {
        'stat': 'stats',
        'value': {'versatility':358},
        'duration': 20,
        'proc_name': 'Primal Combatants Badge of Conquest',
        'upgradable': True,
        'scaling': 1.2384999990,
        'item_level': 620,
        'type': 'icd',
        'source': 'trinket',
        'icd': 60,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'gorashans_lodestone_spike': {
        'stat': 'stats',
        'value': {'crit':1060},
        'duration': 15,
        'proc_name': 'Gorashans Lodestone Spike',
        'upgradable': True,
        'scaling': 3.3333330154,
        'item_level': 630,
        'type': 'icd',
        'source': 'trinket',
        'icd': 90,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'turbulent_vial_of_toxin': {
        'stat': 'stats',
        'value': {'mastery':1060},
        'duration': 15,
        'proc_name': 'Turbulent Vial of Toxin',
        'upgradable': True,
        'scaling': 3.3333330154,
        'item_level': 630,
        'type': 'icd',
        'source': 'trinket',
        'icd': 90,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'kihras_adrenaline_injector': {
        'stat': 'stats',
        'value': {'mastery':1060},
        'duration': 20,
        'proc_name': 'Kihras Adrenaline Injector',
        'upgradable': True,
        'scaling': 3.3333330154,
        'item_level': 630,
        'type': 'icd',
        'source': 'trinket',
        'icd': 120,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'witherbarks_branch': {
        'stat': 'stats',
        'value': {'haste':1383},
        'duration': 10,
        'proc_name': 'Witherbarks Branch',
        'upgradable': True,
        'scaling': 4.3477997780,
        'item_level': 630,
        'type': 'rppm',
        'source': 'trinket',
        'icd': 0,
        'proc_rate': 0.92,
        'trigger': 'all_attacks'
    },
    'munificent_emblem_of_terror': {
        'stat': 'stats',
        'value': {'crit':1200},
        'duration': 10,
        'proc_name': 'Munificent Emblem of Terror',
        'upgradable': True,
        'scaling': 4.3477997780,
        'item_level': 615,
        'type': 'rppm',
        'source': 'trinket',
        'icd': 0,
        'proc_rate': 0.92,
        'trigger': 'all_attacks'
    },
    'void-touched_totem': {
        'stat': 'stats',
        'value': {'mastery':540},
        'duration': 20,
        'proc_name': 'Void-Touched Totem',
        'upgradable': True,
        'scaling': 2.3333330154,
        'item_level': 604,
        'type': 'icd',
        'source': 'trinket',
        'icd': 115, #correct?
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
    'smoldering_heart_of_hyperious': {
        'stat': 'stats',
        'value': {'mastery':540},
        'duration': 20,
        'proc_name': 'Smoldering Heart of Hyperious',
        'upgradable': True,
        'scaling': 2.3333330154,
        'item_level': 607,
        'type': 'icd',
        'source': 'trinket',
        'icd': 115, #correct?
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
    'draenic_philosophers_stone': {
        'stat': 'stats',
        'value': {'agi':771},
        'duration': 15,
        'proc_name': 'Draenic Philosophers Stone',
        'upgradable': True,
        'scaling': 2.6670000553,
        'item_level': 620,
        'type': 'icd',
        'source': 'trinket',
        'icd': 55, #correct?
        'proc_rate': 0.35,
        'trigger': 'all_attacks'
    },
    'rabid_talbuk_horn': {
        'stat': 'stats',
        'value': {'agi':430},
        'duration': 20,
        'proc_name': 'Rabid Talbuk Horn',
        'upgradable': True,
        'scaling': 2.0000000000,
        'item_level': 608,
        'type': 'icd',
        'source': 'trinket',
        'icd': 55,
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
    'excavated_highmaul_knicknack': {
        'stat': 'stats',
        'value': {'agi':430},
        'duration': 20,
        'proc_name': 'Excavated Highmaul Knicknack',
        'upgradable': True,
        'scaling': 2.0000000000,
        'item_level': 608,
        'type': 'icd',
        'source': 'trinket',
        'icd': 55,
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
    'springrain_stone_of_rage': {
        'stat': 'stats',
        'value': {'mastery':572},
        'duration': 20,
        'proc_name': 'Springrain Stone of Rage',
        'upgradable': True,
        'scaling': 2.3333330154,
        'item_level': 608,
        'type': 'icd',
        'source': 'trinket',
        'icd': 55, #correct?
        'proc_rate': 0.15,
        'trigger': 'all_attacks'
    },
    'tormented_tooth_of_ferocity': {
        'stat': 'stats',
        'value': {'haste':800},
        'duration': 20,
        'proc_name': 'Tormented Tooth of Ferocity',
        'upgradable': True,
        'scaling': 3.3333330154,
        'item_level': 608,
        'type': 'icd',
        'source': 'trinket',
        'icd': 120,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
}

allowed_melee_enchants = {
    #6.0
    'mark_of_the_frostwolf': {
        'stat': 'stats',
        'value': {'crit':500},
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
    'mark_of_the_shattered_hand': {
        'stat': 'bleed_damage',
        'value': 1500, #triggers mark_of_the_shattered_hand_dot
        'duration': 0,
        'proc_name': 'Mark of the Shattered Hand',
        'type': 'rppm',
        'source': 'weapon',
        'item_level': 100,
        'icd': 0,
        'proc_rate': 2.5,
        'haste_scales': True,
        'trigger': 'all_attacks',
    },
    'mark_of_the_thunderlord': {
        'stat': 'stats',
        'value': {'crit':500},
        'duration': 12,
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
    'mark_of_warsong': {
        'stat': 'stats',
        'value': {'haste':5.5 * 100},
        'duration': 20,
        'proc_name': 'Mark of the Bleeding Hollow',
        'type': 'rppm',
        'source': 'weapon',
        'item_level': 100,
        'icd': 0,
        'proc_rate': 1.15,
        'trigger': 'all_melee_attacks'
    },
    #5.0
    'dancing_steel': {
        'stat': 'stats',
        'value': {'agi':103},
        'duration': 12,
        'proc_name': 'Dancing Steel',
        'type': 'rppm',
        'source': 'weapon',
        'item_level': 90,
        'icd': 0,
        'proc_rate': 2.53,
        'trigger': 'all_melee_attacks'
    },
}
