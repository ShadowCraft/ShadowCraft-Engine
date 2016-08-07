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

    default_ep_stats = ['agi', 'haste', 'crit', 'mastery', 'ap', 'versatility']

    assassination_mastery_conversion = .035
    combat_mastery_conversion = .022
    subtlety_mastery_conversion = .0276

    raid_modifiers_cache = {'physical':None,
                           'bleed':None,
                           'spell':None}

    ability_info = {
            #general
            'crimson_vial':        (30.,  'buff'),
            'death_from_above':    (25., 'strike'),
            'feint':               (20., 'buff'),
            'kick':                (15., 'strike'),
            #assassination
            'envenom':             (35., 'strike'),
            'fan_of_knives':       (35., 'strike'),
            'garrote':             (45., 'strike'),
            'hemorrhage':          (30., 'strike'),
            'kingsbane':           (35., 'strike'),
            'mutilate':            (55., 'strike'),
            'poisoned_knife':      (40., 'strike'),
            'rupture':             (25., 'strike'),
            #outlaw
            'ambush':              (60., 'strike'),
            'between_the_eyes':    (35., 'strike'),
            'blunderbuss':         (40., 'strike'),
            'ghostly_stike':       (30., 'strike'),
            'pistol_shot':         (40., 'strike'),
            'roll_the_bones':      (25., 'buff'),
            'run_through':         (35., 'strike'),
            'saber_slash':         (50., 'strike'),
            'slice_and_dice':      (25., 'buff'),
            #subtlety
            'backstab':            (35., 'strike'),
            'eviscerate':          (35., 'strike'),
            'gloomblade':          (35., 'strike'),
            'nightblade':          (25., 'strike'),
            'shuriken_storm':      (35., 'strike'),
            'shuriken_toss':       (40., 'strike'),
            'symbols_of_death':    (20., 'buff'),
    }
    ability_cds = {
            #general
            'crimson_vial':             30,
            'death_from_above':         20,
            'kick':                     15,
            'marked_for_death':         60,
            'sprint':                   60,
            'tricks_of_the_trade':      30,
            'vanish':                   120,
            #assassination
            'exsanguinate':              45,
            'kingsbane':                 45,
            'vendetta':                 120,
            #outlaw            
            'adrenaline_rush':          180,
            'cannonball_barrage':        60,
            'curse_of_the_dreadblades':  90,
            'killing_spree':            120,
            #subtlety
            'goremaws_bite':             60,
            'shadow_dance':              60,
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

    def get_weapon_damage(self, hand, ap, is_normalized=True):
        weapon = getattr(self.stats, hand)
        if is_normalized:
            damage = weapon.normalized_damage(ap)
        else:
            damage = weapon.damage(ap)
        return damage

    def oh_penalty(self):
        return .5

    def get_modifiers(self, current_stats, damage_type='physical', armor=None, executioner_modifier=1., potent_poisons_modifier=1.):
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
        base_modifier *= (self.stats.get_versatility_multiplier_from_rating(rating=current_stats['versatility']) + self.buffs.versatility_bonus())

        return base_modifier

    def get_dps_contribution(self, base_damage, crit_rate, frequency, crit_modifier):
        average_hit = base_damage * (1 - crit_rate) + base_damage * crit_rate * crit_modifier
        return average_hit * frequency

    def get_damage_breakdown(self, current_stats, attacks_per_second, crit_rates, damage_procs, additional_info):
        average_ap = current_stats['ap'] + current_stats['agi'] * self.stat_multipliers['ap']

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
        physical_modifier = self.get_modifiers(current_stats, damage_type='physical')
        spell_modifier = self.get_modifiers(current_stats, damage_type='spell')
        bleed_modifier = self.get_modifiers(current_stats, damage_type='bleed')

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
            dps_from_hit_hemo = self.get_dps_contribution(hemo_hit, crit_rates['hemorrhage'], attacks_per_second['hemorrhage_ticks'], crit_damage_modifier)
            damage_breakdown['hemorrhage_dot'] = dps_from_hit_hemo

        if 'rupture_ticks' in attacks_per_second:
            average_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.rupture_tick_damage(average_ap, i) * bleed_modifier * executioner_mod
                dps_tuple = self.get_dps_contribution(dps_tuple, crit_rates['rupture_ticks'], attacks_per_second['rupture_ticks'][i], crit_damage_modifier)
                average_dps += dps_tuple
            damage_breakdown['rupture'] = average_dps
        if 'rupture_ticks_sc' in attacks_per_second:
            average_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.rupture_tick_damage(average_ap, i) * bleed_modifier * executioner_mod
                dps_tuple = self.get_dps_contribution(dps_tuple, 0, attacks_per_second['rupture_ticks_sc'][i], crit_damage_modifier)
                average_dps += dps_tuple
            damage_breakdown['rupture_sc'] = average_dps

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

        for proc in damage_procs:
            if proc.proc_name not in damage_breakdown:
                # Toss multiple damage procs with the same name (Avalanche):
                # attacks_per_second is already being updated with that key.
                damage_breakdown[proc.proc_name] = self.get_proc_damage_contribution(proc, attacks_per_second[proc.proc_name], current_stats, average_ap, damage_breakdown)

        return damage_breakdown, additional_info

    #autoattacks
    def mh_damage(self, ap):
        return self.get_weapon_damage('mh', ap, is_normalized=False)

    def oh_damage(self, ap):
        return self.oh_penalty() * self.get_weapon_damage('oh', ap, is_normalized=False)

    #general abilities
    def death_from_above_pulse_damage(self, ap, cp):
        return 0.3666 * cp * ap

    #assassination
    def deadly_poison_tick_damage(self, ap):
        return .275 * ap + (1 + (0.05 * self.traits.master_alchemist))

    def deadly_instant_poison_damage(self, ap):
        return .142 * ap + (1 + (0.05 * self.traits.master_alchemist))

    #Maybe add better handling for "rule of three" for artifact traits
    def envenom_damage(self, ap, cp):
        return .5 * cp * ap * (1 + (0.0333 * self.traits.toxic_blades))

    def fan_of_knives_damage(self, ap):
        return .8316 * ap

    def garrote_tick_damage(self, ap):
        return .9 * ap

    def hemorrhage_damage(self, ap):
        return 1 * self.get_weapon_damage('mh', ap)

    def mh_kingsbane_damage(self, ap):
        return 3 * self.get_weapon_damage('mh', ap)

    def oh_kingsbane_damage(self, ap):
        return 3 * self.oh_penalty * self.get_weapon_damage('oh', ap) 

    def kingsbane_tick_damage(self, ap):
        return 0.45 * ap

    def mh_mutilate_damage(self, ap):
        return 3.6 * self.get_weapon_damage('mh', ap) * (1 + (0.15 * self.traits.assassins_blades))

    def oh_mutilate_damage(self, ap):
        return 3.6 * self.oh_penalty() * self.get_weapon_damage('oh', ap) * (1 + (0.15 * self.traits.assassins_blades))

    def poisoned_knife_damage(self, ap):
        return 0.6 * ap

    def rupture_tick_damage(self, ap):
        return .3 * ap * (1 + (0.0333 * self.traits.toxic_blades))

    #outlaw
    def ambush_damage(self, ap):
        return 4.5 * self.get_weapon_damage('mh', ap)
    
    def between_the_eyes_damage(self, ap, cp):
        return .75 * cp * ap * (1 + (0.08 / self.traits.black_powder))

    #7*55% AP
    def blunderbuss_damage(self, ap):
        return 3.85 * ap
    
    #Ignoring that this behaves as a dot for simplicity
    def cannonball_barrage_damage(self, ap):
        return 7.2 * ap

    def ghostly_strike_damage(self, ap):
        return 1.76 * self.get_weapon_damage('mh', ap)

    def mh_greed_damage(self, ap):
        return 3.5 * self.get_weapon_damage('mh', ap)

    def oh_greed_damage(self, ap):
        return 3.5 * self.oh_penalty * self.get_weapon_damage('oh', ap)

    #For KsP treat each hit individually
    def mh_killing_spree_damage(self, ap):
        return 2.108 * self.get_weapon_damage('mh', ap)

    def oh_killing_spree_damage(self, ap):
        return 2.018* self.oh_penalty() * self.get_weapon_damage('oh', ap)

    def main_gauche_damage(self, ap):
        return 2.1 * self.oh_penalty() * self.get_weapon_damage('oh', ap) * (1 + (0.1 * self.traits.fortunes_strike))

    def pistol_shot_damage(self, ap):
        return 1.5 * ap

    def run_through_damage(self, ap, cp):
        return 1.2 * ap * cp * (1 * (0.08 * self.traits.fates_thirst))

    def saber_slash_damage(self, ap):
        return 2.6 * self.get_weapon_damage('mh', ap) * (1 + (0.15 * self.traits.cursed_edges))
 
    #subtlety
    #Ignore positional modifier for now  
    def backstab_damage(self, ap):
        return 3.7 * self.get_weapon_damage('mh', ap) * (1 + (0.0333 * self.traits.the_quiet_knife))

    def eviscerate_damage(self, ap, cp):
        return 1.28 * cp * ap

    def gloomblade_damage(self, ap):
        return 4.25 * self.get_weapon_damage('mh', ap) * (1 + (0.0333 * self.traits.the_quiet_knife))

    def mh_goremaws_bite_damage(self, ap):
        return 5 * self.get_weapon_damage('mh', ap)

    def oh_goremaws_bite_damage(self, ap):
        return 5 * self.oh_penalty() * self.get_weapon_damage('oh', ap)

    def nightblade_tick_damage(self, ap):
        return 1.2 * ap * (1 + (0.05 * self.traits.demon_kiss))

    def shadowstrike_damage(self, ap):
        return 8.5 * self.get_weapon_damage('mh', ap) * (1 + (0.05 * self.traits.precision_strike))

    def mh_shadow_blades_damage(self, ap):
        return self.get_weapon_damage('mh', ap, is_normalized=False)

    def oh_shadow_blades_damage(self, ap):
        return self.oh_penalty() * self.get_weapon_damage('oh', ap, is_normalized=False)

    def shuriken_storm_damage(self, ap):
        return 0.5544 * ap

    def shuriken_toss_damage(self, ap):
        return 1.2 * ap

    def get_spell_cost(self, ability, cost_mod=1.0):
        cost = self.ability_info[ability][0] * cost_mod
        return cost

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