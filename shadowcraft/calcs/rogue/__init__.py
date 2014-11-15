import gettext
import __builtin__

__builtin__._ = gettext.gettext

from shadowcraft.calcs import DamageCalculator
from shadowcraft.core import exceptions

class RogueDamageCalculator(DamageCalculator):
    # Functions of general use to rogue damage calculation go here. If a
    # calculation will reasonably used for multiple classes, it should go in
    # calcs.DamageCalculator instead. If its a specific intermediate
    # value useful to only your calculations, when you extend this you should
    # put the calculations in your object. But there are things - like
    # backstab damage as a function of AP - that (almost) any rogue damage
    # calculator will need to know, so things like that go here.
    
    default_ep_stats = ['agi', 'haste', 'crit', 'mastery', 'ap', 'multistrike', 'versatility'] #'readiness'
    melee_attacks = ['mh_autoattack_hits', 'oh_autoattack_hits', 'autoattack',
                     'eviscerate', 'envenom', 'ambush', 'garrote',
                     'sinister_strike', 'revealing_strike', 'main_gauche', 'mh_killing_spree', 'oh_killing_spree',
                     'backstab', 'hemorrhage', 
                     'mutilate', 'mh_mutilate', 'oh_mutilate', 'dispatch', "death_from_above_strike"]
    other_attacks = ['deadly_instant_poison', 'swift_poison']
    aoe_attacks = ['fan_of_knives', 'crimson_tempest', "death_from_above_pulse"]
    dot_ticks = ['rupture_ticks', 'garrote_ticks', 'deadly_poison', 'hemorrhage_dot']
    ranged_attacks = ['shuriken_toss', 'throw']
    non_dot_attacks = melee_attacks + ranged_attacks + aoe_attacks
    all_attacks = melee_attacks + ranged_attacks + dot_ticks + aoe_attacks + other_attacks
    
    assassination_mastery_conversion = .035
    combat_mastery_conversion = .02
    subtlety_mastery_conversion = .03
    assassination_readiness_conversion = 1.0
    combat_readiness_conversion = 1.0
    subtlety_readiness_conversion = 1.0
    
    raid_modifiers_cache = {'physical':None,
                           'bleed':None,
                           'spell':None}
    
    ability_info = {
            'ambush':              (60, 'strike'),
            'backstab':            (35, 'strike'),
            'dispatch':            (30, 'strike'),
            'envenom':             (35, 'strike'),
            'eviscerate':          (35, 'strike'),
            'garrote':             (45, 'strike'),
            'hemorrhage':          (30, 'strike'),
            'mutilate':            (55, 'strike'),
            'recuperate':          (30, 'buff'),
            'revealing_strike':    (40, 'strike'),
            'rupture':             (25, 'strike'),
            'sinister_strike':     (50, 'strike'),
            'slice_and_dice':      (25, 'buff'),
            'tricks_of_the_trade': (0, 'buff'),
            'shuriken_toss':       (40, 'strike'),
            'shiv':                (20, 'strike'),
            'feint':               (20, 'buff'),
            'death_from_above':    (50, 'strike'),
    }
    ability_cds = {
            'tricks_of_the_trade': 30,
            'kick':                15,
            'shiv':                8,
            'vanish':              120,
            'vendetta':            120,
            'adrenaline_rush':     180,
            'killing_spree':       120,
            'shadow_dance':        60,
            'shadowmeld':          120,
            'marked_for_death':    60,
            'preparation':         300,
            'death_from_above':    20,
            'shadow_reflection':   120,
        }
    cd_reduction_table = {'assassination': ['vanish', 'vendetta'],
                          'combat': ['adrenaline_rush', 'killing_spree'],
                          'subtlety': ['shadow_dance']
                         }
    
    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'level':
            self._set_constants_for_level()

    def _set_constants_for_level(self):
        # this calls _set_constants_for_level() in calcs/__init__.py because this supercedes it, this is how inheretence in python works
        # any modules that expand on rogue/__init__.py and use this should do the same
        super(RogueDamageCalculator, self)._set_constants_for_level()
        self.normalize_ep_stat = self.get_adv_param('norm_ep_stat', self.settings.default_ep_stat, ignore_bounds=True)
        self.damage_modifier_cache = 1
        # We only check race here (instead of calcs) because we can assume it's an agi food buff and it applies to every possible rogue calc
        # Otherwise we would be obligated to have a series of conditions to check for classes
        if self.settings.is_pvp:
            self.default_ep_stats.append('pvp_power')

    def get_weapon_damage(self, hand, ap, is_normalized=True):
        weapon = getattr(self.stats, hand)
        if is_normalized:
            damage = weapon.normalized_damage(ap)
        else:
            damage = weapon.damage(ap)
        return damage

    def oh_penalty(self):
        return .5

    def get_modifiers(self, damage_type='physical', armor=None, executioner_modifier=1., potent_poisons_modifier=1.):
        # self.damage_modifier_cache stores common modifiers like Assassin's Resolve that won't change between calculations
        # this cuts down on repetitive if statements
        base_modifier = self.damage_modifier_cache
        
        # Raid modifiers
        if not self.raid_modifiers_cache[damage_type]:
            self.raid_modifiers_cache[damage_type] = self.raid_settings_modifiers(attack_kind=damage_type, armor=armor)
        base_modifier *= self.raid_modifiers_cache[damage_type]
        
        # potent poisons and executioner should be calculated outside, and passed in, no need to recalculate the % each time
        base_modifier *= executioner_modifier
        base_modifier *= potent_poisons_modifier
        
        #versatility is a generic damage modifier
        base_modifier *= (self.stats.get_versatility_multiplier_from_rating() + self.buffs.versatility_bonus())

        return base_modifier
    
    def get_dps_contribution(self, base_damage, crit_rate, frequency, crit_modifier):
        average_hit = base_damage * (1 - crit_rate) + base_damage * crit_rate * crit_modifier
        return average_hit * frequency
    
    def get_damage_breakdown(self, current_stats, attacks_per_second, crit_rates, damage_procs):
        average_ap = current_stats['ap'] + current_stats['agi']
        average_ap *= self.buffs.attack_power_multiplier()
        run_multistrike = True
        if self.settings.is_combat_rogue():
            average_ap *= 1.40 # vitality spec perk
            run_multistrike = False
        
        self.setup_unique_procs(current_stats, average_ap)

        damage_breakdown = {}
        
        # we calculate mastery here to reduce redundant calls
        # can't rely on spec init thread because stats change afterwards
        executioner_mod = 1.
        potent_poisons_mod = 1.
        if self.settings.is_subtlety_rogue():
            executioner_mod = 1 + self.subtlety_mastery_conversion * self.stats.get_mastery_from_rating(current_stats['mastery'])
        if self.settings.is_assassination_rogue():
            potent_poisons_mod = 1 + self.assassination_mastery_conversion * self.stats.get_mastery_from_rating(current_stats['mastery'])
        
        # these return the tuple (damage_modifier, crit_multiplier)
        crit_damage_modifier = self.crit_damage_modifiers()
        physical_modifier = self.get_modifiers(damage_type='physical')
        spell_modifier = self.get_modifiers(damage_type='spell')
        bleed_modifier = self.get_modifiers(damage_type='bleed')
        
        if 'mh_autoattacks' in attacks_per_second:
            # Assumes mh and oh attacks are both active at the same time. As they should always be.
            # Friends don't let friends raid without gear.
            mh_base_damage = self.mh_damage(average_ap) * physical_modifier
            mh_hit_rate = self.dw_mh_hit_chance - crit_rates['mh_autoattacks']
            average_mh_hit = mh_hit_rate * mh_base_damage + crit_rates['mh_autoattacks'] * mh_base_damage * crit_damage_modifier
            mh_dps_tuple = average_mh_hit * attacks_per_second['mh_autoattacks']
            
            oh_base_damage = self.oh_damage(average_ap) * physical_modifier
            oh_hit_rate = self.dw_oh_hit_chance - crit_rates['oh_autoattacks']
            average_oh_hit = oh_hit_rate * oh_base_damage + crit_rates['oh_autoattacks'] * oh_base_damage * crit_damage_modifier
            oh_dps_tuple = average_oh_hit * attacks_per_second['oh_autoattacks']
            if self.settings.merge_damage:
                damage_breakdown['autoattack'] = mh_dps_tuple + oh_dps_tuple
            else:
                damage_breakdown['mh_autoattack'] = mh_dps_tuple
                damage_breakdown['oh_autoattack'] = oh_dps_tuple
        
        # this removes keys with empty values, prevents errors from: attacks_per_second['sinister_strike'] = None
        for key in attacks_per_second.keys():
            if not attacks_per_second[key]:
                del attacks_per_second[key]
        
        if 'mutilate' in attacks_per_second:
            mh_dmg = self.mh_mutilate_damage(average_ap) * physical_modifier
            oh_dmg = self.oh_mutilate_damage(average_ap) * physical_modifier
            mh_mutilate_dps = self.get_dps_contribution(mh_dmg, crit_rates['mutilate'], attacks_per_second['mutilate'], crit_damage_modifier)
            oh_mutilate_dps = self.get_dps_contribution(oh_dmg, crit_rates['mutilate'], attacks_per_second['mutilate'], crit_damage_modifier)
            if self.settings.merge_damage:
                damage_breakdown['mutilate'] = mh_mutilate_dps + oh_mutilate_dps
            else:
                damage_breakdown['mh_mutilate'] = mh_mutilate_dps
                damage_breakdown['oh_mutilate'] = oh_mutilate_dps
            
        for strike in ('hemorrhage', 'backstab', 'sinister_strike', 'revealing_strike', 'main_gauche', 'ambush', 'dispatch', 'shuriken_toss'):
            if strike in attacks_per_second:
                dps = self.get_formula(strike)(average_ap) * physical_modifier
                dps = self.get_dps_contribution(dps, crit_rates[strike], attacks_per_second[strike], crit_damage_modifier)
                if strike in ('sinister_strike', 'backstab'):
                    dps *= self.stats.gear_buffs.rogue_t14_2pc_damage_bonus(strike)
                damage_breakdown[strike] = dps

        for poison in ('venomous_wounds', 'deadly_poison', 'wound_poison', 'deadly_instant_poison', 'swift_poison'):
            if poison in attacks_per_second:
                damage = self.get_formula(poison)(average_ap) * spell_modifier * potent_poisons_mod
                damage = self.get_dps_contribution(damage, crit_rates[poison], attacks_per_second[poison], crit_damage_modifier)
                if poison == 'venomous_wounds':
                    damage *= self.stats.gear_buffs.rogue_t14_2pc_damage_bonus('venomous_wounds')
                damage_breakdown[poison] = damage

        if 'mh_killing_spree' in attacks_per_second:
            mh_dmg = self.mh_killing_spree_damage(average_ap) * physical_modifier
            oh_dmg = self.oh_killing_spree_damage(average_ap) * physical_modifier
            mh_killing_spree_dps = self.get_dps_contribution(mh_dmg, crit_rates['killing_spree'], attacks_per_second['mh_killing_spree'], crit_damage_modifier)
            oh_killing_spree_dps = self.get_dps_contribution(oh_dmg, crit_rates['killing_spree'], attacks_per_second['oh_killing_spree'], crit_damage_modifier)
            if self.settings.merge_damage:
                damage_breakdown['killing_spree'] = mh_killing_spree_dps + oh_killing_spree_dps
            else:
                damage_breakdown['mh_killing_spree'] = mh_killing_spree_dps
                damage_breakdown['oh_killing_spree'] = oh_killing_spree_dps
        
        if 'garrote_ticks' in attacks_per_second:
            dps_tuple = self.garrote_tick_damage(average_ap) * bleed_modifier
            damage_breakdown['garrote'] = self.get_dps_contribution(dps_tuple, crit_rates['garrote'], attacks_per_second['garrote_ticks'], crit_damage_modifier)        
        
        if 'hemorrhage_ticks' in attacks_per_second:
            hemo_hit = self.hemorrhage_tick_damage(average_ap) * bleed_modifier
            hemo_crit = self.hemorrhage_tick_damage(average_ap) * bleed_modifier * crit_damage_modifier
            dps_from_hit_hemo = self.get_dps_contribution(hemo_hit, crit_rates['hemorrhage'], attacks_per_second['hemorrhage_ticks'] * (1 - crit_rates['hemorrhage']), crit_damage_modifier)
            dps_from_crit_hemo = self.get_dps_contribution(hemo_crit, crit_rates['hemorrhage'], attacks_per_second['hemorrhage_ticks'] * crit_rates['hemorrhage'], crit_damage_modifier)
            damage_breakdown['hemorrhage_dot'] = dps_from_hit_hemo + dps_from_crit_hemo
        
        if 'rupture_ticks' in attacks_per_second:
            average_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.rupture_tick_damage(average_ap, i) * bleed_modifier * executioner_mod
                dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates['rupture_ticks'], attacks_per_second['rupture_ticks'][i], crit_damage_modifier)
                average_dps += dps_tuple
            damage_breakdown['rupture'] = average_dps
    
        if 'envenom' in attacks_per_second:
            average_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.envenom_damage(average_ap, i) * potent_poisons_mod * spell_modifier
                dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates['envenom'], attacks_per_second['envenom'][i], crit_damage_modifier)
                average_dps += dps_tuple
            damage_breakdown['envenom'] = average_dps

        if 'eviscerate' in attacks_per_second:
            average_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.eviscerate_damage(average_ap, i) * physical_modifier * executioner_mod
                dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates['eviscerate'], attacks_per_second['eviscerate'][i], crit_damage_modifier)
                average_dps += dps_tuple
            damage_breakdown['eviscerate'] = average_dps
        
        if 'death_from_above_strike' in attacks_per_second:
            if self.settings.get_spec() == 'assassination':
                average_dps = 0
                for i in xrange(1, 6):
                    dps_tuple = self.envenom_damage(average_ap, i) * potent_poisons_mod * spell_modifier * 1.5
                    dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates['death_from_above_strike'], attacks_per_second['death_from_above_strike'][i], crit_damage_modifier)
                    average_dps += dps_tuple
                damage_breakdown['death_from_above_strike'] = average_dps
            else:
                average_dps = 0
                for i in xrange(1, 6):
                    dps_tuple = self.eviscerate_damage(average_ap, i) * physical_modifier * executioner_mod * 1.5
                    dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates['death_from_above_strike'], attacks_per_second['death_from_above_strike'][i], crit_damage_modifier)
                    average_dps += dps_tuple
                damage_breakdown['death_from_above_strike'] = average_dps
            
        if 'death_from_above_pulse' in attacks_per_second:
            average_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.death_from_above_pulse_damage(average_ap, i) * physical_modifier * executioner_mod
                dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates['death_from_above_pulse'], attacks_per_second['death_from_above_pulse'][i], crit_damage_modifier)
                average_dps += dps_tuple
            damage_breakdown['death_from_above_pulse'] = average_dps
        
        for ability in attacks_per_second:
            if 'sr_' in ability:
                modifier = 1.
                if ability[3:] in ('envenom'):
                    modifier *= spell_modifier
                else:
                    modifier *= physical_modifier
                crit_name = ability[3:]
                if 'mh_' in crit_name or 'oh_' in crit_name:
                    crit_name = crit_name[3:]
                if type(attacks_per_second[ability]) in (tuple, list):
                    average_dps = 0
                    for i in xrange(1, 6):
                        dps_tuple = self.get_formula(ability)(average_ap, i)
                        dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates[crit_name], attacks_per_second[ability][i], crit_damage_modifier)
                        average_dps += dps_tuple
                    damage_breakdown[ability] = average_dps
                else:
                    dps = self.get_formula(ability)(average_ap) * modifier
                    dps = self.get_dps_contribution(dps, crit_rates[crit_name], attacks_per_second[ability], crit_damage_modifier)
                    damage_breakdown[ability] = dps
                   
        for proc in damage_procs:
            if proc.proc_name not in damage_breakdown:
                # Toss multiple damage procs with the same name (Avalanche):
                # attacks_per_second is already being updated with that key.
                damage_breakdown[proc.proc_name] = self.get_proc_damage_contribution(proc, attacks_per_second[proc.proc_name], current_stats, average_ap, damage_breakdown)

        if self.talents.nightstalker:
            nightstalker_mod = .50
            if self.settings.opener_name in ('eviscerate', 'envenom'):
                ability = attacks_per_second[self.settings.opener_name][5]
            else:
                ability = attacks_per_second[self.settings.opener_name]
            nightstalker_percent = self.total_openers_per_second / (ability)
            modifier = 1 + nightstalker_mod * nightstalker_percent
            damage_breakdown[self.settings.opener_name] *= modifier
        
        #calculate multistrike here for Sub and Assassination, really cheap to calculate
        #turns out the 2 chance system yields a very basic linear pattern, the damage modifier is 30% of the multistrike %!
        if run_multistrike:
            multistrike_multiplier = .3 * 2 * (self.stats.get_multistrike_chance_from_rating(rating=current_stats['multistrike']) + self.buffs.multistrike_bonus())
            multistrike_multiplier = min(.6, multistrike_multiplier)
            for ability in damage_breakdown:
                damage_breakdown[ability] *= (1 + multistrike_multiplier)
        
        # cleave
        proc = getattr(self.stats.procs, 'sigil_of_rampage')
        if proc and proc.scaling:
            proc_chance = 2.0058600903 / 10000 * self.tools.get_random_prop_point(proc.item_level)
            dmg_cleave = 0.
            for attack in damage_breakdown:
                if attack not in ('deadly_instant_poison', 'multistrike', 'multistrike_trinket'):
                    # does not do damage to your primary target, only adds
                    dmg_cleave += damage_breakdown[attack] * proc_chance * self.settings.num_boss_adds
            damage_breakdown['cleave_trinket'] = dmg_cleave
        
        #DW DOT FIX
        if getattr(getattr(self.stats, 'mh'), 'mark_of_the_shattered_hand') and getattr(getattr(self.stats, 'oh'), 'mark_of_the_shattered_hand'):
            #damage_breakdown['Mark of the Shattered Hand'] *= 2.
            damage_breakdown['Mark of the Shattered Hand DOT'] *= 2.
        
        self.add_exported_data(damage_breakdown)

        return damage_breakdown
    
    #autoattacks
    def mh_damage(self, ap):
        return self.get_weapon_damage('mh', ap, is_normalized=False)

    def oh_damage(self, ap):
        return self.oh_penalty() * self.get_weapon_damage('oh', ap, is_normalized=False)
    
    def mh_shuriken(self, ap):
        return .75 * mh_damage(ap) #update?
    
    def oh_shuriken(self, ap):
        return .75 * oh_damage(ap) #update?
    
    #abilities
    def ambush_damage(self, ap):
        return 3.10 * [1., 1.4][self.stats.mh.type == 'dagger'] * self.get_weapon_damage('mh', ap)
    def ambush_sr_damage(self, ap):
        return 3.10 * 1.8 * 0.924 * ap / 3.5
    
    def backstab_damage(self, ap):
        return 1.80 * self.get_weapon_damage('mh', ap)
    def backstab_sr_damage(self, ap):
        return 1.80 * 1.8 * 0.924 * ap / 3.5

    def death_from_above_pulse_damage(self, ap, cp):
        return 0.266 * cp * ap
    def death_from_above_pulse_sr_damage(self, ap, cp):
        return 0.266 * cp * 0.924 * ap
    
    def dispatch_damage(self, ap):
        return 3.15 * self.get_weapon_damage('mh', ap)
    def dispatch_sr_damage(self, ap):
        return 3.15 * 1.8 * 0.924 * ap / 3.5
    
    def envenom_damage(self, ap, cp):
        return .306 * cp * ap
    def envenom_sr_damage(self, ap, cp):
        return .306 * cp * 0.924 * ap
    
    def eviscerate_damage(self, ap, cp):
        return .508 * cp * ap
    def eviscerate_sr_damage(self, ap, cp):
        return .508 * cp * 0.924 * ap
    
    def garrote_tick_damage(self, ap):
        return .2241 * ap
    def garrote_tick_sr_damage(self, ap):
        return .2241 * 0.924 * ap
    
    #20% damage more hotfix
    def hemorrhage_damage(self, ap):
        return 1.2 * .40 * [1., 1.4][self.stats.mh.type == 'dagger'] * self.get_weapon_damage('mh', ap)
    def hemorrhage_sr_damage(self, ap):
        return 1.2 * .4 * 1.8 * 0.924 * ap / 3.5

    def hemorrhage_tick_damage(self, ap):
        return .035 * ap
    def hemorrhage_tick_sr_damage(self, ap):
        return .035 * 0.924 * ap

    def mh_killing_spree_damage(self, ap):
        return 1.0 * self.get_weapon_damage('mh', ap)
    def mh_killing_spree_sr_damage(self, ap):
        return 1.0 * 1.8 * 0.924 * ap / 3.5

    def oh_killing_spree_damage(self, ap):
        return 1.0 * self.oh_penalty() * self.get_weapon_damage('oh', ap)
    def oh_killing_spree_sr_damage(self, ap):
        return 1.0 * 1.8 * 0.924 * ap / 3.5 * 0.5
    
    def main_gauche_damage(self, ap):
        return 1.4 * self.oh_penalty() * self.get_weapon_damage('oh', ap)
    def main_gauche_sr_damage(self, ap):
        return 1.4 * 1.8 * 0.924 * ap / 3.5
    
    def mh_mutilate_damage(self, ap):
        return 2.0 * self.get_weapon_damage('mh', ap)
    def mh_mutilate_sr_damage(self, ap):
        return 2.0 * 1.8 * 0.924 * ap / 3.5

    def oh_mutilate_damage(self, ap):
        return 2.0 * self.oh_penalty() * self.get_weapon_damage('oh', ap)
    def oh_mutilate_sr_damage(self, ap):
        return 2.0 * 1.8 * 0.924 * ap / 3.5 * 0.5

    def revealing_strike_damage(self, ap):
        return 1.2 * self.get_weapon_damage('mh', ap)
    def revealing_strike_sr_damage(self, ap):
        return 1.2 * 1.8 * 0.924 * ap / 3.5
    
    def rupture_tick_damage(self, ap, cp):
        return .08220 * cp * ap
    def rupture_tick_sr_damage(self, ap, cp):
        return .08220 * 0.924 * ap
    
    def sinister_strike_damage(self, ap):
        return 1.6 * self.get_weapon_damage('mh', ap)
    def sinister_strike_sr_damage(self, ap):
        return 1.6 * 1.8 * 0.924 * ap / 3.5
    
    def venomous_wounds_damage(self, ap):
        return .320 * ap
    def venomous_wounds_sr_damage(self, ap):
        return .320 * 0.924 * ap

    #poisons
    def deadly_poison_tick_damage(self, ap):
        return .25014 * ap

    def deadly_instant_poison_damage(self, ap):
        return .1287000030 * ap

    def swift_poison_damage(self, ap):
        return .264 * ap

    def wound_poison_damage(self, ap):
        return .6 * .2179999948 * ap #40% reduction hotfix
    
    #unused
    def fan_of_knives_damage(self, ap):
        return .231 * ap

    def crimson_tempest_damage(self, ap, cp):
        return .0903 * cp * ap

    def crimson_tempest_tick_damage(self, ap, cp):
        return self.crimson_tempest_damage(ap, cp) * (2.4 / 6)

    def shiv_damage(self, ap):
        return .10 * self.oh_penalty() * self.get_weapon_damage('oh', ap, is_normalized=False)

    def throw_damage(self, ap):
        return .05 * ap

    def shuriken_toss_damage(self, ap):
        return 1.2 * ap
    
    def get_formula(self, name):
        formulas = {
            'backstab':              self.backstab_damage,
            'hemorrhage':            self.hemorrhage_damage,
            'sinister_strike':       self.sinister_strike_damage,
            'revealing_strike':      self.revealing_strike_damage,
            'main_gauche':           self.main_gauche_damage,
            'ambush':                self.ambush_damage,
            'eviscerate':            self.eviscerate_damage,
            'dispatch':              self.dispatch_damage,
            'mh_mutilate':           self.mh_mutilate_damage,
            'oh_mutilate':           self.oh_mutilate_damage,
            'venomous_wounds':       self.venomous_wounds_damage,
            'deadly_poison':         self.deadly_poison_tick_damage,
            'wound_poison':          self.wound_poison_damage,
            'deadly_instant_poison': self.deadly_instant_poison_damage,
            'swift_poison':          self.swift_poison_damage,
            'shuriken_toss':         self.shuriken_toss_damage,
            'death_from_above_pulse':self.death_from_above_pulse_damage,
            #shadow reflection abilities
            'sr_backstab':           self.backstab_sr_damage,
            'sr_hemorrhage':         self.hemorrhage_sr_damage,
            'sr_sinister_strike':    self.sinister_strike_sr_damage,
            'sr_revealing_strike':   self.revealing_strike_sr_damage,
            'sr_main_gauche':        self.main_gauche_sr_damage,
            'sr_ambush':             self.ambush_sr_damage,
            'sr_eviscerate':         self.eviscerate_sr_damage,
            'sr_envenom':            self.envenom_sr_damage,
            'sr_dispatch':           self.dispatch_sr_damage,
            'sr_mh_mutilate':        self.mh_mutilate_sr_damage,
            'sr_oh_mutilate':        self.oh_mutilate_sr_damage,
            'sr_mh_killing_spree':   self.mh_killing_spree_sr_damage,
            'sr_oh_killing_spree':   self.oh_killing_spree_sr_damage,
            'sr_venomous_wounds':    self.venomous_wounds_sr_damage,
            'sr_rupture_ticks':      self.rupture_tick_sr_damage,
        }
        return formulas[name]

    def get_spell_stats(self, ability, cost_mod=1.0):
        cost = self.ability_info[ability][0] * cost_mod
        return (cost, self.ability_info[ability][1])
    
    def get_spell_cd(self, ability):
        #need to update list of affected abilities
        if ability in self.cd_reduction_table[self.settings.get_spec()]:
            #self.stats.get_readiness_multiplier_from_rating(readiness_conversion=self.readiness_spec_conversion)
            return self.ability_cds[ability] * self.get_trinket_cd_reducer()
        else:
            return self.ability_cds[ability]

    def crit_rate(self, crit=None):
        # all rogues get 10% bonus crit, .05 of base crit for everyone
        # should be coded better?
        base_crit = .15
        base_crit += self.stats.get_crit_from_rating(crit)
        return base_crit + self.buffs.buff_all_crit() + self.race.get_racial_crit(is_day=self.settings.is_day) - self.crit_reduction
