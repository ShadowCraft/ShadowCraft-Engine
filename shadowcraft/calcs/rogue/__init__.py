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
    
    normalize_ep_stat = 'agi' #use 'dps' to prevent normalization
    # removed default_ep_stats: 'str', 'spell_hit', 'spell_exp'
    default_ep_stats = ['agi', 'haste', 'crit', 'mastery', 'ap', 'multistrike', 'readiness']
    melee_attacks = ['mh_autoattack_hits', 'oh_autoattack_hits', 'autoattack',
                     'eviscerate', 'envenom', 'ambush', 'garrote',
                     'sinister_strike', 'revealing_strike', 'main_gauche', 'mh_killing_spree', 'oh_killing_spree',
                     'backstab', 'hemorrhage', 
                     'mutilate', 'mh_mutilate', 'oh_mutilate', 'dispatch']
    other_attacks = ['deadly_instant_poison']
    aoe_attacks = ['fan_of_knives', 'crimson_tempest']
    dot_ticks = ['rupture_ticks', 'garrote_ticks', 'deadly_poison', 'hemorrhage_dot']
    ranged_attacks = ['shuriken_toss', 'throw']
    non_dot_attacks = melee_attacks + ranged_attacks + aoe_attacks
    all_attacks = melee_attacks + ranged_attacks + dot_ticks + aoe_attacks + other_attacks
    
    assassination_mastery_conversion = .035
    combat_mastery_conversion = .02
    subtlety_mastery_conversion = .03
    assassination_readiness_conversion = 1.0
    combat_readiness_conversion = 0.8
    subtlety_readiness_conversion = 1.0
    
    crit_damage_cache = None
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
            'sinister_strike':     (40, 'strike'),
            'slice_and_dice':      (25, 'buff'),
            'tricks_of_the_trade': (0, 'buff'),
            'shuriken_toss':       (40, 'strike'),
            'shiv':                (20, 'strike'),
            'feint':               (20, 'buff'),
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
        }
    cd_reduction_table = {'assassination': ['vanish', 'vendetta'],
                          'combat': ['adrenaline_rush', 'killing_spree'],
                          'subtlety': ['vanish', 'shadow_dance']
                         }#Cloak, Evasion, Sprint affect all 3 specs, not needed in list
    
    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'level':
            self._set_constants_for_level()

    def _set_constants_for_level(self):
        super(RogueDamageCalculator, self)._set_constants_for_level()
        self.normalize_ep_stat = self.get_adv_param('norm_ep_stat', self.settings.default_ep_stat, ignore_bounds=True)
        self.damage_modifier_cache = 1
        # We only check race here (instead of calcs) because we can assume it's an agi food buff and it applies to every possible rogue calc
        # Otherwise we would be obligated to have a series of conditions to check for classes
        if self.race.epicurean:
            self.stats.agi += self.buffs.buff_agi(just_food=True)
        if self.settings.is_pvp:
            self.default_ep_stats.append('pvp_power')

    def get_weapon_damage_bonus(self):
        # Override this in your modeler to implement weapon damage boosts
        # such as Unheeded Warning.
        return 0

    def get_weapon_damage(self, hand, ap, is_normalized=True):
        weapon = getattr(self.stats, hand)
        if is_normalized:
            damage = weapon.normalized_damage(ap) #+ self.get_weapon_damage_bonus() looks to be a dead mechanic, commented out for now.
        else:
            damage = weapon.damage(ap) #+ self.get_weapon_damage_bonus()
        return damage

    def oh_penalty(self):
        if self.settings.is_combat_rogue():
            return .875
        else:
            return .5

    def get_modifiers(self, damage_type='physical', armor=None, executioner_modifier=1., potent_poisons_modifier=1.):
        # self.damage_modifier_cache stores common modifiers like Assassin's Resolve that won't change between calculations
        # this cuts down on repetitive if statements
        base_modifier = self.damage_modifier_cache
        
        # Raid modifiers
        if not self.raid_modifiers_cache[damage_type]:
            self.raid_modifiers_cache[damage_type] = self.raid_settings_modifiers(attack_kind=damage_type, armor=armor)
        base_modifier *= self.raid_modifiers_cache[damage_type]
        
        # potent poisons and executioner should be calculated outside, and passed in
        #print base_modifier, mastery_modifier
        base_modifier *= executioner_modifier
        base_modifier *= potent_poisons_modifier
        
        if not self.crit_damage_cache:
            self.crit_damage_cache = self.crit_damage_modifiers()

        return (base_modifier, base_modifier*self.crit_damage_cache)
    
    def get_damage_breakdown(self, current_stats, attacks_per_second, crit_rates, damage_procs):
        average_ap = current_stats['ap'] + current_stats['agi'] + current_stats['str']
        average_ap *= self.buffs.attack_power_multiplier()
        if self.settings.is_combat_rogue():
            average_ap *= 1.40 # vitality spec perk

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
        physical_modifiers = self.get_modifiers(damage_type='physical')
        spell_modifiers = self.get_modifiers(damage_type='spell')
        bleed_modifiers = self.get_modifiers(damage_type='bleed')
        
        if 'mh_autoattacks' in attacks_per_second:
            # Assumes mh and oh attacks are both active at the same time. As they should always be.
            # Friends don't let friends raid without gear.
            (mh_base_damage, mh_crit_damage) = self.mh_damage(average_ap)
            mh_base_damage *= physical_modifiers[0]
            mh_crit_damage *= physical_modifiers[1]
            mh_hit_rate = self.dw_mh_hit_chance - crit_rates['mh_autoattacks']
            average_mh_hit = mh_hit_rate * mh_base_damage + crit_rates['mh_autoattacks'] * mh_crit_damage
            crit_mh_hit = crit_rates['mh_autoattacks'] * mh_crit_damage
            mh_dps_tuple = average_mh_hit * attacks_per_second['mh_autoattacks'], crit_mh_hit * attacks_per_second['mh_autoattacks']
            
            (oh_base_damage, oh_crit_damage) = self.oh_damage(average_ap)
            oh_base_damage *= physical_modifiers[0]
            oh_crit_damage *= physical_modifiers[1]
            oh_hit_rate = self.dw_oh_hit_chance - crit_rates['oh_autoattacks']
            average_oh_hit = oh_hit_rate * oh_base_damage + crit_rates['oh_autoattacks'] * oh_crit_damage
            crit_oh_hit = crit_rates['oh_autoattacks'] * oh_crit_damage
            oh_dps_tuple = average_oh_hit * attacks_per_second['oh_autoattacks'], crit_oh_hit * attacks_per_second['oh_autoattacks']
            
            if self.settings.merge_damage:
                damage_breakdown['autoattack'] = mh_dps_tuple[0] + oh_dps_tuple[0], mh_dps_tuple[1] + oh_dps_tuple[1]
            else:
                damage_breakdown['mh_autoattack'] = mh_dps_tuple[0], mh_dps_tuple[1]
                damage_breakdown['oh_autoattack'] = oh_dps_tuple[0], oh_dps_tuple[1]
            
        for key in attacks_per_second.keys():
            if not attacks_per_second[key]:
                del attacks_per_second[key]
        
        if 'mutilate' in attacks_per_second:
            mh_dmg = self.mh_mutilate_damage(average_ap)
            mh_dmg = (mh_dmg[0] * physical_modifiers[0], mh_dmg[1] * physical_modifiers[1])
            oh_dmg = self.oh_mutilate_damage(average_ap)
            oh_dmg = (oh_dmg[0] * physical_modifiers[0], oh_dmg[1] * physical_modifiers[1])
            
            mh_mutilate_dps = self.get_dps_contribution(mh_dmg, crit_rates['mutilate'], attacks_per_second['mutilate'])
            oh_mutilate_dps = self.get_dps_contribution(oh_dmg, crit_rates['mutilate'], attacks_per_second['mutilate'])
            if self.settings.merge_damage:
                damage_breakdown['mutilate'] = mh_mutilate_dps[0] + oh_mutilate_dps[0], mh_mutilate_dps[1] + oh_mutilate_dps[1]
            else:
                damage_breakdown['mh_mutilate'] = mh_mutilate_dps[0], mh_mutilate_dps[1]
                damage_breakdown['oh_mutilate'] = oh_mutilate_dps[0], oh_mutilate_dps[1]
            
        for strike in ('hemorrhage', 'backstab', 'sinister_strike', 'revealing_strike', 'main_gauche', 'ambush', 'dispatch', 'shuriken_toss'):
            if strike in attacks_per_second:
                dps = self.get_formula(strike)(average_ap)
                dps = (dps[0] * physical_modifiers[0], dps[1] * physical_modifiers[1])
                dps = self.get_dps_contribution(dps, crit_rates[strike], attacks_per_second[strike])
                if strike in ('sinister_strike', 'backstab'):
                    dps = tuple([i * self.stats.gear_buffs.rogue_t14_2pc_damage_bonus(strike) for i in dps])
                damage_breakdown[strike] = dps

        for poison in ('venomous_wounds', 'deadly_poison', 'wound_poison', 'deadly_instant_poison', 'instant_poison'):
            if poison in attacks_per_second:
                damage = self.get_formula(poison)(average_ap)
                damage = (damage[0] * spell_modifiers[0] * potent_poisons_mod,
                          damage[1] * spell_modifiers[1] * potent_poisons_mod)
                damage = self.get_dps_contribution(damage, crit_rates[poison], attacks_per_second[poison])
                if poison == 'venomous_wounds':
                    damage = tuple([i * self.stats.gear_buffs.rogue_t14_2pc_damage_bonus('venomous_wounds') for i in damage])
                damage_breakdown[poison] = damage

        if 'mh_killing_spree' in attacks_per_second:
            mh_dmg = self.mh_killing_spree_damage(average_ap)
            mh_dmg = (mh_dmg[0] * physical_modifiers[0], mh_dmg[1] * physical_modifiers[1])
            oh_dmg = self.oh_killing_spree_damage(average_ap)
            oh_dmg = (oh_dmg[0] * physical_modifiers[0], oh_dmg[1] * physical_modifiers[1])
            mh_killing_spree_dps = self.get_dps_contribution(mh_dmg, crit_rates['killing_spree'], attacks_per_second['mh_killing_spree'])
            oh_killing_spree_dps = self.get_dps_contribution(oh_dmg, crit_rates['killing_spree'], attacks_per_second['oh_killing_spree'])
            if self.settings.merge_damage:
                damage_breakdown['killing_spree'] = mh_killing_spree_dps[0] + oh_killing_spree_dps[0], mh_killing_spree_dps[1] + oh_killing_spree_dps[1]
            else:
                damage_breakdown['mh_killing_spree'] = mh_killing_spree_dps[0], mh_killing_spree_dps[1]
                damage_breakdown['oh_killing_spree'] = oh_killing_spree_dps[0], oh_killing_spree_dps[1]
        
        if 'garrote_ticks' in attacks_per_second:
            dps_tuple = self.garrote_tick_damage(average_ap)
            dps_tuple = (dps_tuple[0] * bleed_modifiers[0], dps_tuple[1] * bleed_modifiers[1])
            damage_breakdown['garrote'] = self.get_dps_contribution(dps_tuple, crit_rates['garrote'], attacks_per_second['garrote_ticks'])        
        
        if 'hemorrhage_ticks' in attacks_per_second:
            hemo_hit = self.hemorrhage_tick_damage(average_ap, from_crit_hemo=False)
            hemo_hit = (hemo_hit[0] * bleed_modifiers[0], hemo_hit[1] * bleed_modifiers[1])
            hemo_crit = self.hemorrhage_tick_damage(average_ap, from_crit_hemo=True)
            hemo_crit = (hemo_crit[0] * bleed_modifiers[0], hemo_crit[1] * bleed_modifiers[1])
            dps_from_hit_hemo = self.get_dps_contribution(hemo_hit, crit_rates['hemorrhage'], attacks_per_second['hemorrhage_ticks'] * (1 - crit_rates['hemorrhage']))
            dps_from_crit_hemo = self.get_dps_contribution(hemo_crit, crit_rates['hemorrhage'], attacks_per_second['hemorrhage_ticks'] * crit_rates['hemorrhage'])
            damage_breakdown['hemorrhage_dot'] = dps_from_hit_hemo[0] + dps_from_crit_hemo[0], dps_from_hit_hemo[1] + dps_from_crit_hemo[1]
        
        if 'rupture_ticks' in attacks_per_second:
            average_dps = crit_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.rupture_tick_damage(average_ap, i)
                dps_tuple = (dps_tuple[0] * bleed_modifiers[0] * executioner_mod,
                             dps_tuple[1] * bleed_modifiers[1] * executioner_mod)
                dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates['rupture_ticks'], attacks_per_second['rupture_ticks'][i])
                average_dps += dps_tuple[0]
                crit_dps += dps_tuple[1]
            damage_breakdown['rupture'] = average_dps, crit_dps
    
        if 'envenom' in attacks_per_second:
            average_dps = crit_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.envenom_damage(average_ap, i)
                dps_tuple = (dps_tuple[0] * spell_modifiers[0] * potent_poisons_mod,
                             dps_tuple[1] * spell_modifiers[1] * potent_poisons_mod)
                dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates['envenom'], attacks_per_second['envenom'][i])
                average_dps += dps_tuple[0]
                crit_dps += dps_tuple[1]
            damage_breakdown['envenom'] = average_dps, crit_dps

        if 'eviscerate' in attacks_per_second:
            average_dps = crit_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.eviscerate_damage(average_ap, i)
                dps_tuple = (dps_tuple[0] * physical_modifiers[0] * executioner_mod,
                             dps_tuple[1] * physical_modifiers[1] * executioner_mod)
                dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates['eviscerate'], attacks_per_second['eviscerate'][i])
                average_dps += dps_tuple[0]
                crit_dps += dps_tuple[1]
            damage_breakdown['eviscerate'] = average_dps, crit_dps
                   
        for proc in damage_procs:
            if proc.proc_name not in damage_breakdown:
                # Toss multiple damage procs with the same name (Avalanche):
                # attacks_per_second is already being updated with that key.
                damage_breakdown[proc.proc_name] = self.get_proc_damage_contribution(proc, attacks_per_second[proc.proc_name], current_stats, average_ap, damage_breakdown)

        self.append_damage_on_use(average_ap, current_stats, damage_breakdown)

        if self.talents.nightstalker:
            nightstalker_mod = .50
            if self.settings.opener_name in ('eviscerate', 'envenom'):
                ability = attacks_per_second[self.settings.opener_name][5]
            else:
                ability = attacks_per_second[self.settings.opener_name]
            nightstalker_percent = self.total_openers_per_second / (ability)
            modifier = 1 + nightstalker_mod * nightstalker_percent
            damage_breakdown[self.settings.opener_name] = tuple([i * modifier for i in damage_breakdown[self.settings.opener_name]])
        
        #calculate multistrike here, really cheap to calculate
        #turns out the 2 chance system yields a very basic linear pattern, the damage modifier is 30% of the multistrike %!
        multistrike_multiplier = 1 + .3 * self.stats.get_multistrike_chance_from_rating(rating=current_stats['multistrike'])
        for ability in damage_breakdown:
            damage_breakdown[ability] = (damage_breakdown[ability][0] * multistrike_multiplier,
                                         damage_breakdown[ability][1] * multistrike_multiplier)
        
        self.add_exported_data(damage_breakdown)

        return damage_breakdown

    def mh_damage(self, ap, armor=None):
        weapon_damage = self.get_weapon_damage('mh', ap, is_normalized=False)

        damage = weapon_damage
        crit_damage = damage

        return damage, crit_damage

    def oh_damage(self, ap, armor=None):
        weapon_damage = self.get_weapon_damage('oh', ap, is_normalized=False)

        damage = self.oh_penalty() * weapon_damage
        crit_damage = damage

        return damage, crit_damage
    
    def mh_shuriken(self, ap, armor=None):
        return .75 * mh_damage(ap, armor=armor)
    
    def oh_shuriken(self, ap, armor=None):
        return .75 * oh_damage(ap, armor=armor)

    def backstab_damage(self, ap, armor=None):
        weapon_damage = self.get_weapon_damage('mh', ap)

        damage = 3.80 * (weapon_damage) 
        crit_damage = damage

        return damage, crit_damage

    def dispatch_damage(self, ap, armor=None):
        weapon_damage = self.get_weapon_damage('mh', ap)

        damage = [3.31, 4.80][self.stats.mh.type == 'dagger'] * (weapon_damage)
        crit_damage = damage

        return damage, crit_damage

    def mh_mutilate_damage(self, ap, armor=None):
        mh_weapon_damage = self.get_weapon_damage('mh', ap)

        mh_damage = [1.37, 2.0][self.stats.mh.type == 'dagger'] * (mh_weapon_damage)
        crit_mh_damage = mh_damage

        return mh_damage, crit_mh_damage

    def oh_mutilate_damage(self, ap, armor=None):
        oh_weapon_damage = self.get_weapon_damage('oh', ap)

        oh_damage = [1.37, 2.0][self.stats.mh.type == 'dagger'] * (self.oh_penalty() * oh_weapon_damage)
        crit_oh_damage = oh_damage

        return oh_damage, crit_oh_damage

    def sinister_strike_damage(self, ap, armor=None):
        weapon_damage = self.get_weapon_damage('mh', ap)
        
        damage = [1.3, 1.88][self.stats.mh.type == 'dagger'] * weapon_damage
        crit_damage = damage

        return damage, crit_damage

    def hemorrhage_damage(self, ap, armor=None):
        weapon_damage = self.get_weapon_damage('mh', ap)

        damage = [1.6, 2.32][self.stats.mh.type == 'dagger'] * weapon_damage
        crit_damage = damage

        return damage, crit_damage

    def hemorrhage_tick_damage(self, ap, from_crit_hemo=False, armor=None):
        # Call this function twice to get all four crit/non-crit hemo values.
        hemo_damage = self.hemorrhage_damage(ap, armor=armor)[from_crit_hemo]

        tick_conversion_factor = .5 / 8
        tick_damage = hemo_damage * tick_conversion_factor

        return tick_damage, tick_damage #can't crit

    def ambush_damage(self, ap, armor=None):
        weapon_damage = self.get_weapon_damage('mh', ap) 
        percentage_damage_bonus = 3.65 * [1, 1.447][self.stats.mh.type == 'dagger']

        damage = percentage_damage_bonus * (weapon_damage)
        crit_damage = damage

        return damage, crit_damage

    def revealing_strike_damage(self, ap, armor=None):
        weapon_damage = self.get_weapon_damage('mh', ap, is_normalized=False)

        damage = 1.60 * weapon_damage
        crit_damage = damage

        return damage, crit_damage

    def venomous_wounds_damage(self, ap):
        damage = (.160 * ap)
        crit_damage = damage

        return damage, crit_damage

    def main_gauche_damage(self, ap, armor=None):
        weapon_damage = self.get_weapon_damage('mh', ap)

        damage = 1.2 * weapon_damage
        crit_damage = damage

        return damage, crit_damage

    def mh_killing_spree_damage(self, ap, armor=None):
        mh_weapon_damage = self.get_weapon_damage('mh', ap)

        mh_damage = mh_weapon_damage
        crit_mh_damage = mh_damage

        return mh_damage, crit_mh_damage

    def oh_killing_spree_damage(self, ap, armor=None):
        oh_weapon_damage = self.get_weapon_damage('oh', ap)

        oh_damage = self.oh_penalty() * oh_weapon_damage
        crit_oh_damage = oh_damage

        return oh_damage, crit_oh_damage

    def deadly_poison_tick_damage(self, ap):
        tick_damage = (.213 * ap)
        crit_tick_damage = tick_damage

        return tick_damage, crit_tick_damage

    def deadly_instant_poison_damage(self, ap):
        damage = (.109 * ap)
        crit_damage = damage

        return damage, crit_damage

    def instant_poison_damage(self, ap):
        damage = (.15 * ap)
        crit_damage = damage

        return damage, crit_damage

    def wound_poison_damage(self, ap):
        damage = (.120 * ap)
        crit_damage = damage

        return damage, crit_damage

    def garrote_tick_damage(self, ap):
        tick_damage = (ap * 0.078)
        crit_tick_damage = tick_damage

        return tick_damage, crit_tick_damage

    def rupture_tick_damage(self, ap, cp):
        ap_multiplier_tuple = (0, .025, .04, .05, .056, .062)
        tick_damage = (ap_multiplier_tuple[cp] * ap)
        crit_tick_damage = tick_damage

        return tick_damage, crit_tick_damage

    def eviscerate_damage(self, ap, cp, armor=None):
        damage = (0.18 * cp * ap)
        crit_damage = damage
        
        return damage, crit_damage

    def envenom_damage(self, ap, cp):
        damage = (0.134 * cp * ap)
        crit_damage = damage
        
        return damage, crit_damage

    def fan_of_knives_damage(self, ap, armor=None):
        damage = (.175 * ap)
        crit_damage = damage
        
        return damage, crit_damage

    def crimson_tempest_damage(self, ap, cp, armor=None):
        damage = (.0275 * cp * ap)
        crit_damage = damage
        
        return damage, crit_damage

    def crimson_tempest_tick_damage(self, ap, cp, armor=None, from_crit_ct=False):
        ct_damage = self.crimson_tempest_damage(ap, cp, armor=armor)[from_crit_ct]

        tick_conversion_factor = 2.4 / 6
        tick_damage = ct_damage * tick_conversion_factor

        return tick_damage, tick_damage

    def shiv_damage(self, ap, armor=None):
        oh_weapon_damage = self.get_weapon_damage('oh', ap, is_normalized=False)

        oh_damage = .25 * (self.oh_penalty() * oh_weapon_damage)
        crit_oh_damage = oh_damage

        return oh_damage, crit_oh_damage

    def throw_damage(self, ap):
        damage = (.05 * ap)
        crit_damage = damage
        
        return damage, crit_damage

    def shuriken_toss_damage(self, ap):
        damage = (.6 * ap)
        crit_damage = damage
        
        return damage, crit_damage
    
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
            'instant_poison':        self.instant_poison_damage,
            'shuriken_toss':         self.shuriken_toss_damage
        }
        return formulas[name]

    def get_spell_stats(self, ability, cost_mod=1.0):
        cost = self.ability_info[ability][0] * cost_mod
        return (cost, self.ability_info[ability][1])
    
    def get_spell_cd(self, ability):
        #need to update list of affected abilities
        if ability in self.cd_reduction_table[self.settings.get_spec()]:
            return self.ability_cds[ability] * self.stats.get_readiness_multiplier_from_rating(readiness_conversion=self.readiness_spec_conversion)
        else:
            return self.ability_cds[ability]

    def melee_crit_rate(self, crit=None):
        # all rogues get 10% bonus crit, assumed to affect everything, .05 of base crit for everyone
        # should be coded better?
        base_crit = .15
        base_crit += self.stats.get_crit_from_rating(crit)
        return base_crit + self.buffs.buff_all_crit() + self.race.get_racial_crit(is_day=self.settings.is_day) - self.melee_crit_reduction

    def spell_crit_rate(self, crit=None):
        # all rogues get 10% bonus crit, assumed to affect everything, .05 of base crit for everyone
        # should be coded better?
        base_crit = .15
        base_crit += self.stats.get_crit_from_rating(crit)
        return base_crit + self.buffs.buff_all_crit() + self.race.get_racial_crit(is_day=self.settings.is_day) - self.spell_crit_reduction
