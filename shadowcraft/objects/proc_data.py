from __future__ import division
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
    'old_war_pot': {
        'stat': 'special_model', #rppm, modeled in add_special_procs_damage
        'value': 169900, #level 110 assumed for simplicity
        'dmg_school': 'physical',
        'duration': 25,
        'proc_name': 'Potion of the Old War',
        'type': 'icd',
        'source': 'unique',
        'icd': 0,
        'proc_rate': 1.0,
        'can_crit': True,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'old_war_prepot': {
        'stat': 'special_model', #rppm, modeled in add_special_procs_damage
        'value': 169900, #level 110 assumed for simplicity
        'dmg_school': 'physical',
        'duration': 25,
        'proc_name': 'Potion of the Old War',
        'type': 'icd',
        'source': 'unique',
        'icd': 0,
        'proc_rate': 1.0,
        'can_crit': True,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'prolonged_power_pot': {
        'stat': 'stats',
        'value': {'agi': 2500, 'str': 2500, 'int': 2500},
        'duration': 60,
        'proc_name': 'Potion of Prolonged Power',
        'type': 'icd',
        'source': 'unique',
        'icd': 0,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'prolonged_power_prepot': {
        'stat': 'stats',
        'value': {'agi': 2500, 'str': 2500, 'int': 2500},
        'duration': 60,
        'proc_name': 'Potion of Prolonged Power',
        'type': 'icd',
        'source': 'unique',
        'icd': 0,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    #racials
    'touch_of_the_grave': {
        'stat': 'spell_damage',
        'dmg_school': 'shadow',
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
        'dmg_school': 'fire',
        'value': 0,
        'duration': 0,
        'max_stacks': 0,
        'proc_name': 'Rocket Barrage',
        'type': 'icd',
        'icd': 120,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'arcane_pulse': {
        'stat': 'spell_damage',
        'dmg_school': 'arcane',
        'value': 0,
        'duration': 0,
        'aoe': True,
        'proc_name': 'Arcane Pulse',
        'type': 'icd',
        'icd': 180,
        'proc_rate': 1.0,
        'trigger': 'all_attacks'
    },
    'entropic_embrace': {
        'stat': 'spell_damage',
        'value': 1, #Placeholder for uptime calculation, converted to % mod in damage breakdown
        'duration': 12,
        'proc_name': 'Entropic Embrace',
        'type': 'icd',
        'icd': 60,
        'proc_rate': 0.33,
        'trigger': 'all_attacks'
    },
    #netherlight crucible
    'chaotic_darkness': {
        'stat': 'spell_damage',
        'dmg_school': 'shadow',
        'value': 180000, #avg of range 60000 to 5*60000
        'proc_name': 'Chaotic Darkness',
        'duration': 0,
        'type': 'rppm',
        'source': 'crucible',
        'proc_rate': 2,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
    },
    'dark_sorrows': {
        'stat': 'spell_damage',
        'dmg_school': 'shadow',
        'aoe': True,
        'value': 186350,
        'proc_name': 'Dark Sorrows',
        'duration': 0,
        'type': 'rppm',
        'source': 'crucible',
        'icd': 8,
        'proc_rate': 1,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
    },
    'infusion_of_light': {
        'stat': 'spell_damage',
        'dmg_school': 'holy',
        'value': 101000,
        'proc_name': 'Infusion of Light',
        'duration': 0,
        'type': 'rppm',
        'source': 'crucible',
        'icd': 1,
        'proc_rate': 4,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
    },
    'secure_in_the_light': {
        'stat': 'spell_damage',
        'dmg_school': 'holy',
        'value': 135000,
        'proc_name': 'Secure in the Light',
        'duration': 0,
        'type': 'rppm',
        'source': 'crucible',
        'icd': 1,
        'proc_rate': 3,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
    },
    'shadowbind': {
        'stat': 'spell_damage',
        'dmg_school': 'shadow',
        'value': 200000,
        'proc_name': 'Shadowbind',
        'duration': 0,
        'type': 'rppm',
        'source': 'crucible',
        'proc_rate': 2,
        'haste_scales': True,
        'can_crit': True,
        'trigger': 'all_attacks'
    },
    'torment_the_weak': {
        'stat': 'spell_dot',
        'dmg_school': 'shadow',
        'dot_ticks': 5,
        'can_crit': True,
        'value': 16000,
        'duration': 15,
        'max_stacks': 3,
        'proc_name': 'Torment the Weak',
        'type': 'rppm',
        'proc_rate': 4,
        'source': 'crucible',
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
        'stat':'physical_dot',
        'value': 0, # AP based
        'aoe': True,
        'ap_coefficient': 2.5 / 3, # server-side, not in dbc, per tick is 2.5 / 3
        'duration': 1.5,
        'dot_ticks': 3,
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
        'stat':'physical_damage', #modeled as icd because it's active FOREVER
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
        'icd': 0, # stacks with every autohit
        'proc_rate': 1,
        'trigger': 'auto_attacks',
    },

    'chrono_shard': { #Equip: Your spells and abilities have a chance to grant you X Haste and 15% movement speed for 10 sec.
        'stat':'stats',
        'value': {'haste': 0}, #rpp-scaled
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
        'value': 3, #3 sec decrease, modeled in get_spell_cd
        'duration': 0,
        'proc_name': 'Prescience', # reduce cd of shadow blades, vendetta, adrenaline rush
        'item_level': 875,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': {'assassination': 3.51, 'outlaw': 8.4, 'subtlety': 9},
        'trigger': 'all_attacks',
    },

    'cradle_of_anguish': { #Equip: While you are above 80% health you gain X Strength or Agility per second, based on your specialization, stacking up to 10 times. If you fall below 50% health, this effect is lost.
        'stat': 'special_model', #handled in determine stats, assume 10 stacks all the time
        'value': {'agi':0}, #rpp-scaled
        'proc_name': 'Strength of Will',
        'item_level': 900,
        'scaling': 0.05585,
        'duration': 1,
        'max_stacks': 10,
        'type': 'icd',
        'icd': 1,
        'proc_rate': 1,
        'source': 'trinket',
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

    'engine_of_eradication': { #Equip: Your auto attacks have a chance to increase your Strength or Agility, based on your specialization, by 5424 for 12 sec, and expel orbs of fel energy. Collecting an orb increases the duration of this effect by 3 sec.
        'stat':'stats',
        'value': {'agi': 0},
        'duration': 24, # 12 + 4*3
        'proc_name': 'Demonic Vigor',
        'scaling': 1.314659,
        'crm_scales': False,
        'item_level': 900,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 1,
        'trigger': 'all_attacks',
    },

    'entwined_elemental_foci': { #Equip: Your attacks have a chance to grant you a Fiery, Frost, or Arcane enchants for 20 sec.
        'stat':'stats',
        'value': {'haste': 0, 'crit': 0, 'mastery': 0}, #TODO: needs special modeling, you get only one stat per proc, but can have multiple at the same time
        'duration': 20,
        'proc_name': 'Triumvirate',
        'scaling': 2.069368 / 3, #FIXME: for now using 1/3 for each stat / assume we get all 3 for 1/3 each
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
        'icd': 0, # stacks with every autohit
        'proc_rate': 1,
        'trigger': 'auto_attacks',
    },

    'faulty_countermeasure': { #Use: Sheathe your weapons in ice for 30 sec, giving your attacks a chance to cause X additional Frost damage and slow the target's movement speed by 30% for 8 sec.  (2 Min Cooldown)
        'stat':'ability_modifier', #modeled in add_special_procs_damage
        'value': 0, #rpp-scaled
        'duration': 30,
        'proc_name': 'Sheathed in Frost',
        'dmg_school': 'frost',
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

    'infernal_cinders': { #Your melee attacks have a chance to deal an additional 82910 Fire damage. The critical strike chance of this damage is increased by 10% for each ally within 10 yds who bears this item.
        'stat':'spell_damage',
        'value': 0, #rpp-scaled
        'duration': 0,
        'proc_name': 'Infernal Cinders',
        'dmg_school': 'fire',
        'scaling': 20.09453,
        'item_level': 900,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': 10,
        'haste_scales': True,
        'can_crit': True,
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
        'scaling': 2.297781 / 3, #FIXME: for now using 1/3 for each stat, similar to entwined elemental foci
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
        'scaling': 1.378778 / 3, #FIXME: for now using 1/3 for each stat, similar to entwined elemental foci
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
        'stat':'spell_dot',
        'dmg_school': 'nature',
        'value': 0, #rpp-scaled
        'duration': 5,
        'dot_ticks': 6,
        'dot_initial_tick': True,
        'proc_name': 'Wind Bolt',
        'scaling': 19.01865, #6 bolts, one every second
        'item_level': 810,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': 1,
        'haste_scales': True,
        'can_crit': True
    },

    'specter_of_betrayal': { #Use: Create a Dread Reflection at your location for 1 min and cause each of your Dread Reflections to unleash a torrent of magic that deals (111484 * 4) Shadow damage over 3 sec, split evenly among nearby enemies. (45 Sec Cooldown)
        'stat':'spell_damage',
        'dmg_school': 'shadow',
        'value': 0, #rpp-scaled
        'duration': 0, #modeled all-in-one
        'proc_name': 'Dread Torrent',
        'scaling': 4 * 24.6155,
        'item_level': 900,
        'type': 'icd',
        'source': 'trinket',
        'proc_rate': 1,
        'icd': 45,
        'can_crit': True,
        'trigger': 'all_attacks'
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

    'splinters_of_agronax': { #Equip: Your attacks have a chance to imbed Fel Barbs into your target, dealing X Fire damage over 6 sec.
        'stat': 'spell_dot',
        'dmg_school': 'fire',
        'dot_ticks': 6,
        'can_crit': True,
        'value': 0, #rpp-scaled
        'duration': 6,
        'proc_name': 'Fel Barbs',
        'scaling': 5.075319,
        'item_level': 845,
        'type': 'rppm',
        'haste_scales': True,
        'proc_rate': 3.5,
        'source': 'trinket',
    },

    'spontaneous_appendages': { #Equip: Your melee attacks have a chance to generate extra appendages for 12 sec that attack nearby enemies for X Physical damage every 0.75 sec.
        'stat':'physical_dot',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 12,
        'proc_name': 'Horrific Slam', #not the proc name but the dmg
        'can_crit': True,
        'scaling': 10.1246, #hotfixed value
        'dot_ticks': 16,
        'item_level': 850,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': .7,
        'haste_scales': True,
    },

    'tempered_egg_of_serpentrix': { #Equip: Your attacks have a chance to summon a Spawn of Serpentrix to assist you.
        'stat':'spell_dot',
        'dmg_school': 'fire',
        'value': 0, #rpp-scaled
        'duration': 15,
        'dot_ticks': 8, #pet might be scaling with haste, but most logs have 8 magma spits, assume that for now
        'proc_name': 'Magma Spit', #not the proc name but the dmg of the add
        'scaling': 8.235604,
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
        'scaling': 46.22871 * 2., #judging from logs wave damage only occurs twice (forth and back), 4 waves seem to be visual
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
        'stat':'special_model',
        'dmg_school': 'nature',
        'value': 0, #rpp-scaled, trinket damage modeled in add_special_procs_damage
        'aoe': True,
        'duration': 0,
        'proc_name': 'Fetid Regurgitation',
        'scaling': 2.853606 * 6, #hit per stack, hitting for scaled value every 0.5 for 3 seconds = 6 ticks
        'item_level': 805,
        'type': 'icd',
        'source': 'trinket',
        'proc_rate': 1, #for on use, rppm for stacks is 3 (w/ haste), max is 6 stacks
        'icd': 20,
        'can_crit': True,
        'trigger': 'all_attacks'
    },

    'tirathons_betrayal': { #Use: Empower yourself with dark energy, causing your attacks to have a chance to inflict 38847 additional Shadow damage and grant you a shield for 38847. Lasts 15 sec.  (1 Min, 15 Sec Cooldown)
        'stat':'ability_modifier', #modeled in add_special_procs_damage
        'value': 0,
        'duration': 15,
        'proc_name': 'Darkstrikes',
        'dmg_school': 'shadow',
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

    'umbral_moonglaives': { #Use: Conjure a storm of glaives at your location, causing 125220 Arcane damage every 1 sec to nearby enemies. After 8 sec the glaives shatter, causing another 313052 Arcane damage to enemies in the area. (1 Min, 30 Sec Cooldown)
        'stat':'spell_damage',
        'dmg_school': 'arcane',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 0, #modeled all-in-one
        'proc_name': 'Umbral Glaive Storm',
        'scaling': 8 * 30.34914 + 75.87286,
        'item_level': 900,
        'type': 'icd',
        'source': 'trinket',
        'proc_rate': 1,
        'icd': 90,
        'can_crit': True,
        'trigger': 'all_attacks'
    },

    'vial_of_ceaseless_toxins': { #Use: Inflict 225700 Shadow damage to an enemy in melee range, plus 366752 damage over 20 sec. If they die while this effect is active, the cooldown of this ability is reduced by 45 sec. (1 Min Cooldown)
        'stat':'spell_damage',
        'dmg_school': 'shadow',
        'value': 0, #rpp-scaled
        'duration': 0, #modeled all-in-one
        'proc_name': 'Ceaseless Toxin',
        'scaling': 10 * 8.888798 + 54.70188,
        'item_level': 900,
        'type': 'icd',
        'source': 'trinket',
        'proc_rate': 1,
        'icd': 60,
        'can_crit': True,
        'trigger': 'all_attacks'
    },

    'void_stalkers_contract': { #Use: Call upon two Void Stalkers to strike your target from two directions inflicting up to (209877 * 2) Physical damage to all enemies in their paths. (1 Min, 30 Sec Cooldown)
        'stat':'physical_damage',
        'value': 0, #rpp-scaled
        'aoe': True,
        'duration': 0,
        'proc_name': 'Void Slash',
        'scaling': 84.93605,
        'item_level': 845,
        'type': 'icd',
        'source': 'trinket',
        'icd': 90,
        'proc_rate': 1,
        'can_crit': True,
        'trigger': 'all_attacks'
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

    ### Antorus Procs ###
    'amanthuls_vision': { #PROXY PROC, only used to set empowerment
        'stat': 'special_model',
        'value': 0,
        'duration': 0,
        'proc_name': 'Aman\'thul Proxy'
    },
    'amanthuls_vision_empowered': { #When empowered by the Pantheon, your primary stat is increased by X for 15 sec.
        'stat':'stats',
        'value': {'agi': 0}, #rpp-scaled
        'duration': 15, #Ignored, use precomputed uptime values, set in set_constants
        'proc_name': 'Aman\'thul\'s Grandeur',
        'scaling': 0.639601,
        'item_level': 1000,
        'source': 'trinket',
        'type': 'icd',
        'icd': 100, #modeled as icd, duration will be set to uptime % and icd 100
        'proc_rate': 1, #Ignore RPPM
        'trigger': 'all_attacks'
    },

    'golganneths_vitality': { #Your damaging abilities have a chance to create a Ravaging Storm at your target's location, inflicting Nature damage split among all enemies within 6 yds over 6 sec.
        'stat':'spell_damage',
        'dmg_school': 'nature',
        'value': 0, #rpp-scaled
        'duration': 6,
        'proc_name': 'Ravaging Storm',
        'scaling': 14.58708 * 6, # 6 hits
        'item_level': 940,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': 1.8,
        'can_crit': True,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'golganneths_vitality_empowered': { #When empowered by the Pantheon, your autoattacks cause an explosion of lightning dealing [(Mainhand weapon base speed) * X] Nature damage to all enemies within 8 yds of the target. Lasts 15 sec.
        'stat':'special_model',
        'dmg_school': 'nature',
        'aoe': True,
        'value': 0, #rpp-scaled
        'duration': 15, #Ignored, use precomputed uptime values
        'proc_name': 'Golganneth\'s Thunderous Wrath',
        'scaling': 7.98956,
        'item_level': 940,
        'type': 'rppm',
        'source': 'trinket',
        'proc_rate': 0, #Ignore RPPM, special pantheon formula in add_special_procs_damage
        'can_crit': True,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },

    'shadowsinged_fang': { #Your melee and ranged abilities have a chance to increase your Strength or Agility by 4548 for 12 sec.
        'stat':'stats',
        'value': {'agi': 0}, #rpp-scaled
        'duration': 12,
        'proc_name': 'Flames of F\'harg',
        'scaling': 0.833441,
        'item_level': 930,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 3,
        'trigger': 'all_attacks'
    },
    'shadowsinged_fang_2': { #Your autoattacks have a chance to increase your Critical Strike by 2202 for 12 sec.
        'stat':'stats',
        'value': {'crit': 0}, #rpp+crm-scaled
        'duration': 12,
        'proc_name': 'Corruption of Shatug',
        'scaling': 0.833422,
        'crm_scales': True,
        'item_level': 930,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 3,
        'trigger': 'auto_attacks'
    },

    'seeping_scourgewing': { #Your melee attacks have a chance to deal 97539 to 107806 Shadow damage to the target. If there are no other enemies within 8 yds of them, this deals an additional 52253 to 57752 damage.
        'stat':'spell_damage',
        'dmg_school': 'shadow',
        'can_crit': True,
        'value': 0, #rpp-scaled
        'duration': 0,
        'proc_name': 'Shadow Strike',
        'scaling': 60.43111, #additional scaling 32.37356
        'item_level': 930,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 3,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },
    'seeping_scourgewing_2': { #for the additional dmg part
        'stat':'spell_damage',
        'dmg_school': 'shadow',
        'can_crit': True,
        'value': 0, #rpp-scaled
        'duration': 0,
        'proc_name': 'Isolated Strike',
        'scaling': 32.37356,
        'item_level': 930,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 3,
        'haste_scales': True,
        'trigger': 'all_attacks'
    },

    'terminus_signaling_beacon': { #Use: Call a Legion ship to bombard the target's location for 9 sec, dealing 353311 Fire damage to all targets within 12 yds, including the ship. (2 Min Cooldown)
        'stat':'spell_damage',
        'dmg_school': 'fire',
        'can_crit': True,
        'aoe': True,
        'value': 0, #rpp-scaled
        'duration': 9,
        'proc_name': 'Legion Bombardment',
        'scaling': 48.55859,
        'item_level': 930,
        'source': 'trinket',
        'type': 'icd',
        'icd': 120,
        'proc_rate': 1,
        'trigger': 'all_attacks'
    },

    'gorshalachs_legacy': { #Your melee attacks have a chance to grant an Echo of Gorshalach. On reaching 15 applications, you lash out with a devastating combination of attacks, critically striking enemies in a 15 yd cone in front of you for (578175 + 1349069) Fire damage.
        'stat':'spell_damage',
        'dmg_school': 'fire',
        'can_crit': False, #always crits, included in scaling
        'aoe': True,
        'value': 0, #rpp-scaled
        'duration': 0,
        'proc_name': 'Gorshalach\'s Legacy',
        'scaling': 105.9506 + 247.2179, #always crits, already included
        'item_level': 930,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 10 / 15, #dmg on 15th application
        'haste_scales': True,
        'trigger': 'all_attacks'
    },

    'forgefiends_fabricator': { #Your melee and ranged attacks have a chance to plant Fire Mines at the enemy's feet. Fire Mines detonate after 15 sec, inflicting 63094 Fire damage to all enemies within 12 yds. Use: Detonate all Fire Mines. (30 Sec Cooldown)
        'stat':'spell_damage',
        'dmg_school': 'fire',
        'aoe': True,
        'value': 0, #rpp-scaled
        'duration': 0,
        'proc_name': 'Fire Mines',
        'scaling': 11.56199,
        'item_level': 930,
        'source': 'trinket',
        'type': 'rppm',
        'proc_rate': 7,
        'haste_scales': True,
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

    'rogue_orderhall_8pc': { #Your finishing moves have a chance to increase your Haste by 2000 for 12 sec.
        'stat': 'stats',
        'value': {'haste': 2000},
        'duration': 12,
        'proc_name': "Jacin's Ruse",
        'type': 'rppm',
        'source': 'unique',
        'proc_rate': 2,
        'trigger': 'all_attacks' #should be only finishing moves, but since it's rppm that doesn't matter
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
}
