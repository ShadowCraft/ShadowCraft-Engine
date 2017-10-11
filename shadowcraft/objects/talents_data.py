talents = {
    ('death_knight', 'blood'): (
        ('bloodworms', 'heart_strike', 'consume_vitality'),
        ('bloody_reprisal', 'bloodbolt', 'ossuary'),
        ('rapid_decomposition', 'red_thirst', 'anti-magic_barrier'),
        ('rune_tap', 'purgatory', 'mark_of_blood'),
        ('tightening_grasp', 'tremble_before_me', 'march_of_the_damned'),
        ('will_of_the_necropolis', 'exhume', 'foul_bulwark'),
        ('bonestorm', 'blood_mirror', 'blood_beasts')
    ),
    ('demon_hunter', 'havoc'): (
        ('fel_mastery', 'first_blood', 'blind_fury'),
        ('prepared', 'demon_blades', 'master_of_the_glaive'),
        ('demon_reborn', 'bloodlet', 'feed_the_demon'),
        ('desperate_instincts', 'netherwalk', 'soul_rending'),
        ('nemesis', 'chaos_cleave', 'momentum'),
        ('improved_chaos_nova', "ill_swallow_your_soul", 'cull_the_weak'),
        ('place_holder1', 'place_holder2', 'place_holder3')
    ),
    ('druid', 'balance'): (
        ('force_of_nature', 'warrior_of_elune', 'starlord'),
        ('renewal', 'displacer_beast', 'wild_charge'),
        ('feral_affinity', 'guardian_affinity', 'restoration_affinity'),
        ('mighty_bash', 'mass_entanglement', 'typhoon'),
        ('soul_of_the_forest', 'incarnation_chosen_of_elune', 'stellar_flare'),
        ('shooting_starts', 'astral_communion', 'blessing_of_the_ancients'),
        ('collapsing_stars', 'stellar_drift', 'natures_balance')
    ),
    ('hunter', 'beast_mastery'): (
        ('one_with_the_pack', 'way_of_the_cobra', 'dire_stable'),
        ('posthaste', 'farstrider', 'dash'),
        ('stomp', 'exptic_munitions', 'chimaera_shot'),
        ('binding_shot', 'wyvern_sting', 'intimidation'),
        ('big_game_hunter', 'bestial_fury', 'blink_strikes'),
        ('a_murder_of_crows', 'barrage', 'volley'),
        ('stampede', 'killer_cobra', 'aspect_of_the_beast')
    ),
    ('mage', 'arcane'): (
        ('arcane_familiar', 'presence_of_mind', 'torrent'),
        ('shimmer', 'cauterize', 'ice_block'),
        ('mirror_image', 'rune_of_power', 'incanters_flow'),
        ('supernova', 'charged_up', 'words_of_power'),
        ('ice_floes', 'ring_of_frost', 'ice_ward'),
        ('nether_tempest', 'unstable_magic', 'erosion'),
        ('overpowered', 'quickening', 'arcane_orb')
    ),
    ('monk', 'windwalker'): (
        ('chi_burst', 'eye_of_the_tiger', 'chi_wave'),
        ('chi_torpedo', 'tiger_lust', 'celerity'),
        ('energizing_elixer', 'ascension', 'power_strikes'),
        ('ring_of_peace', 'dizzying_kicks', 'leg_sweep'),
        ('healing_elixirs', 'diffuse_magic', 'dampen_harm'),
        ('rushing_jade_wind', 'invoke_xuen_the_white_tiger', 'hit_combo'),
        ('chi_orbit', 'spinning_dragon_strike', 'serenity')
    ),
    ('paladin', 'retribution'): (
        ('execution_sentence', 'turalyons_might', 'consecration'),
        ('the_fires_of_justice', 'crusaders_flurry', 'zeal'),
        ('fist_of_justice', 'repentance', 'blinding_light'),
        ('virtues_blade', 'blade_of_wrath', 'divine_hammer'),
        ('judgements_of_the_bold', 'might_of_the_virtue', 'mass_judgement'),
        ('blaze_of_light', 'divine_speed', 'eye_for_an_eye'),
        ('final_verdict', 'seal_of_light', 'holy_wrath')
    ),
    ('priest', 'shadow'): (
        ('twist_of_fate', 'fortress_of_the_mind', 'shadow_word_void'),
        ('mania', 'body_and_soul', 'masochism'),
        ('mind_bomb', 'psychic_voice', 'dominate_mind'),
        ('desperate_prayer', 'spectral_guise', 'angelic_bulwark'),
        ('twist_of_fate', 'power_infusion', 'divine_insight'),
        ('cascade', 'divine_star', 'halo')
    ),
    ('rogue', 'assassination'): (
        ('master_poisoner', 'elaborate_planning', 'hemorrhage'),
        ('nightstalker', 'subterfuge', 'shadow_focus'),
        ('deeper_stratagem', 'anticipation', 'vigor'),
        ('leeching_poison', 'elusiveness', 'cheat_death'),
        ('thuggee', 'prey_on_the_weak', 'internal_bleeding'),
        ('toxic_blade', 'alacrity', 'exsanguinate'),
        ('venom_rush', 'marked_for_death', 'death_from_above')
    ),
    ('rogue', 'outlaw'): (
        ('ghostly_strike', 'swordmaster', 'quick_draw'),
        ('grappling_hook', 'acrobatic_strikes', 'hit_and_run'),
        ('deeper_stratagem', 'anticipation', 'vigor'),
        ('iron_stomach', 'elusiveness', 'cheat_death'),
        ('parley', 'prey_on_the_weak', 'dirty_tricks'),
        ('cannonball_barrage', 'alacrity', 'killing_spree'),
        ('slice_and_dice', 'marked_for_death', 'death_from_above')
    ),
    ('rogue', 'subtlety'): (
        ('master_of_subtlety', 'weaponmaster', 'gloomblade'),
        ('nightstalker', 'subterfuge', 'shadow_focus'),
        ('deeper_stratagem', 'anticipation', 'vigor'),
        ('soothing_darkness', 'elusiveness', 'cheat_death'),
        ('strike_from_the_shadows', 'prey_on_the_weak', 'tangled_shadow'),
        ('dark_shadow', 'alacrity', 'enveloping_shadows'),
        ('master_of_shadows', 'marked_for_death', 'death_from_above')
    ),
    ('shaman', 'elemental'): (
        ('path_of_flame', 'path_of_elements', 'maelstrom_totem'),
        ('gust_of_wind', 'fleet_of_foot', 'wind_rush_totem'),
        ('lightening_surge_totem', 'earthgrab_totem', 'voodoo_totem'),
        ('elemental_blast', 'ancestral_swiftness', 'echo_of_the_elements'),
        ('elemental_fusion', 'sons_of_flame', 'magnitude'),
        ('lightning_rod', 'storm_elemental', 'liquid_magma_totem'),
        ('ascendance', 'primal_elementalist', 'totemic_fury')
    ),
    ('affliction', 'warlock'): (
        ('haunt', 'writhe_in_agony', 'drain_soul'),
        ('contagion', 'absolute_corruption', 'mana_tap'),
        ('soul_leech', 'mortal_coil', 'howl_of_terror'),
        ('siphon_life', 'sow_the_seeds', 'soul_harvest'),
        ('demonic_circle', 'burning_rush', 'dark_pact'),
        ('grimore_of_supremacy', 'grimore_of_service', 'grimore_of_sacrifce'),
        ('soul_effigy', 'phantom_singularity', 'demonic_servitude')
    ),
    ('warrior', 'arms'): (
        ('shockwave', 'storm_bolt', 'sweeping_strikes'),
        ('impending_victory', 'bounding_stride', 'die_by_the_sword'),
        ('dauntless', 'overpower', 'avatar'),
        ('second_wind', 'double_time', 'imposing_roar'),
        ('fervor_of_battle', 'rend', 'bladestorm'),
        ('heroic_strike', 'mortal_combo', 'titanic_might'),
        ('anger_management', 'opportunity_strikes', 'ravager')
    ),
}
