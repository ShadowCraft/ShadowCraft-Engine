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

    assassination_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                                    'deadly_poison', 'deadly_instant_poison', 'envenom',
                                    'fan_of_knives', 'garrote_ticks', 'hemorrhage',
                                    'kingsbane', 'kingsbane_ticks', 'mutilate',
                                    'poisoned_knife', 'rupture_ticks']
    outlaw_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                             'ambush', 'between_the_eyes', 'blunderbuss', 'cannonball_barrage',
                             'ghostly_strike', 'greed', 'killing_spree', 'main_gauche',
                             'pistol_shot', 'run_through', 'saber_slash']
    subtlety_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                               'backstab', 'eviscerate', 'finality:eviscerate', 'gloomblade', 
                               'goremaws_bite', 'nightblade', 'finality:nightblade', 'shadowstrike',
                               'shadow_blade', 'shuriken_storm', 'shuriken_toss']
    #All damage sources mitigated by armor
    physical_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                                'fan_of_knives', 'hemorrhage', 'mutilate', 'poisoned_knife',
                                'ambush, between_the_eyes', 'blunderbuss', 'cannonball_barrage',
                                'ghostly_strike', 'greed', 'killing_spree', 'main_gauche',
                                'pistol_shot', 'run_through', 'saber_slash', 'backstab',
                                'eviscerate', 'shadowstrike', 'shuriken_storm', 'shuriken_toss']
    #All damage sources the scale with mastery (assn or sub)
    mastery_scaling_damage_sources = ['deadly_poison', 'deadly_instant_poison', 'evenom',
                                      'eviscerate', 'nightblade']
    #All damage sources that deal damage with both hands
    dual_wield_damage_sources = ['kingsbane', 'mutilate', 'greed', 'killing_spree',
                                 'goremaws_bite', 'shadow_blades']
    #All damage sources that scale with cps
    finisher_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                                 'envenom', 'rupture_ticks', 'between_the_eyes',
                                 'run_through', 'eviscerate', 'finality:eviscerate',
                                'nightblade', 'finality:nightblade']

    assassination_mastery_conversion = .035
    outlaw_mastery_conversion = .022
    subtlety_mastery_conversion = .0276

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
            'finality:eviscerate': (35., 'strike'),
            'gloomblade':          (35., 'strike'),
            'nightblade':          (25., 'strike'),
            'finality:nightblade': (25., 'strike'),
            'shadowstrike':        (40., 'strike'),
            'shuriken_storm':      (35., 'strike'),
            'shuriken_toss':       (40., 'strike'),
            'symbols_of_death':    (20., 'buff'),
    }
    ability_cds = {
            #general
            'crimson_vial':             30.,
            'death_from_above':         20.,
            'kick':                     15.,
            'marked_for_death':         60.,
            'sprint':                   60.,
            'tricks_of_the_trade':      30.,
            'vanish':                   120.,
            #assassination
            'exsanguinate':              45.,
            'kingsbane':                 45.,
            'vendetta':                 120.,
            #outlaw
            'adrenaline_rush':          180.,
            'cannonball_barrage':        60.,
            'curse_of_the_dreadblades':  90.,
            'killing_spree':            120.,
            #subtlety
            'goremaws_bite':             60.,
            'shadow_dance':              60.,
            'shadow_blades':            120.,
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

    def get_base_modifier(self, current_stats):
        base_modifier = self.damage_modifier_cache
        base_modifier *= self.stats.get_versatility_multiplier_from_rating(rating=current_stats['versatility'])
        return base_modifier

    def get_dps_contribution(self, base_damage, crit_rate, frequency, crit_modifier):
        average_hit = base_damage * (1 - crit_rate) + base_damage * crit_rate * crit_modifier
        return average_hit * frequency


    #Computes a merged dps contribution for an ability
    def get_ability_dps(self, ap, ability, attacks_per_second, crit_rate, modifier, crit_modifier, both_hands=False, cps=0):
        if both_hands:
            ability_list = [hand + ability for hand in ['mh_', 'oh_']]
        else:
            ability_list = [ability]

        dps = 0
        if not cps:
            for a in ability_list:
                base_damage = self.get_formula(a)(ap) * modifier
                dps += self.get_dps_contribution(base_damage, crit_rate, attacks_per_second, crit_modifier)
        else:
            for i in xrange(1, cps+1):
                for a in ability_list:
                    base_damage = self.get_formula(a)(ap, i) * modifier
                    dps += self.get_dps_contribution(base_damage, crit_rate, attacks_per_second[i], crit_modifier)
        return dps

    def get_damage_breakdown(self, current_stats, attacks_per_second, crit_rates, damage_procs, additional_info):
        average_ap = current_stats['ap'] + current_stats['agi'] * self.stat_multipliers['ap']
        max_cps = 5 + int(self.talents.deeper_strategem)

        self.setup_unique_procs(current_stats, average_ap)

        damage_breakdown = {}

        crit_damage_modifier = self.crit_damage_modifiers()
        base_modifier = self.get_base_modifier(current_stats)
        armor_modifier = self.armor_mitigation_multiplier()

        # this removes keys with empty values, prevents errors from: attacks_per_second['sinister_strike'] = None
        for key in attacks_per_second.keys():
            if not attacks_per_second[key]:
                del attacks_per_second[key]

        if 'mh_autoattacks' in attacks_per_second:
            # Assumes mh and oh attacks are both active at the same time. As they should always be.
            # Friends don't let friends raid without gear.
            mh_base_damage = self.mh_damage(average_ap) * armor_modifier * base_modifier
            mh_hit_rate = self.dw_mh_hit_chance - crit_rates['mh_autoattacks']
            average_mh_hit = mh_hit_rate * mh_base_damage + crit_rates['mh_autoattacks'] * mh_base_damage * crit_damage_modifier
            mh_dps_tuple = average_mh_hit * attacks_per_second['mh_autoattacks']

            oh_base_damage = self.oh_damage(average_ap) * armor_modifier * base_modifier
            oh_hit_rate = self.dw_oh_hit_chance - crit_rates['oh_autoattacks']
            average_oh_hit = oh_hit_rate * oh_base_damage + crit_rates['oh_autoattacks'] * oh_base_damage * crit_damage_modifier
            oh_dps_tuple = average_oh_hit * attacks_per_second['oh_autoattacks']
            damage_breakdown['autoattack'] = mh_dps_tuple + oh_dps_tuple

        for proc in damage_procs:
            if proc.proc_name not in damage_breakdown:
                # Toss multiple damage procs with the same name (Avalanche):
                # attacks_per_second is already being updated with that key.
                damage_breakdown[proc.proc_name] = self.get_proc_damage_contribution(proc, attacks_per_second[proc.proc_name], current_stats, average_ap, damage_breakdown)

        #compute damage breakdown for each spec
        if self.spec == 'assassination':
            potent_poisons_mod = (1 + self.assassination_mastery_conversion * self.stats.get_mastery_from_rating(current_stats['mastery'])) * base_modifier

            for ability in self.assassination_damage_sources:
                if ability not in attacks_per_second:
                    continue
                aps = attacks_per_second[ability]
                crits = crit_rates[ability]
                crit_mod = crit_damage_modifier
                modifier = base_modifier
                both_hands = ability in self.dual_wield_damage_sources
                cps = max_cps if ability in self.finisher_damage_sources else 0

                if ability in self.physical_damage_sources:
                    modifier *= armor_modifier
                if ability in self.mastery_scaling_damage_sources:
                    modifier *= potent_poisons_mod

                #override for "weird" abilities
                #death from above strike is actually an envenom with 1.5 modifier
                #manually add in base modifier because DfA strike is in physical sources
                if ability == 'death_from_above_strike':
                    modifier = base_modifier * 1.5 * potent_poisons_mod
                    ability = 'envenom'
                damage_breakdown[ability] = self.get_ability_dps(average_ap, ability, aps, crits, modifier, crit_mod, both_hands, cps)

        if self.spec == 'outlaw':
            for ability in self.outlaw_damage_sources:
                if ability not in attacks_per_second:
                    continue
                aps = attacks_per_second[ability]
                crits = crit_rates[ability]
                crit_mod = crit_damage_modifier
                modifier = base_modifier
                both_hands = ability in self.dual_wield_damage_sources
                cps = max_cps if ability in self.finisher_damage_sources else 0

                if ability in self.physical_damage_sources:
                    modifier *= armor_modifier

                #override for "weird" abilities
                #death from above strike is actually an evis with 1.5 modifier
                if ability == 'death_from_above_strike':
                    modifier *= 1.5
                    ability = 'eviscerate'
                #between the eyes has additional crit damage
                #Damage modifier 3 explained here: http://beta.askmrrobot.com/wow/simulator/docs/critdamage
                if ability == 'between_the_eyes':
                    crit_mod = self.crit_damage_modifiers(3)
                damage_breakdown[ability] = self.get_ability_dps(average_ap, ability, aps, crits, modifier, crit_mod, both_hands, cps)

        if self.spec == 'subtlety':
            executioner_mod = executioner_mod = 1 + self.subtlety_mastery_conversion * self.stats.get_mastery_from_rating(current_stats['mastery'])
            shadow_fangs_mod = (1 + (0.04 * self.traits.shadow_fangs))

            for ability in self.subtlety_damage_sources:
                if ability not in attacks_per_second:
                    continue
                aps = attacks_per_second[ability]
                crits = crit_rates[ability]
                crit_mod = crit_damage_modifier
                modifier = base_modifier
                both_hands = ability in self.dual_wield_damage_sources
                cps = max_cps if ability in self.finisher_damage_sources else 0

                if ability in self.physical_damage_sources:
                    modifier *= armor_modifier
                #assume for now that all non-physical damage sources are shadow damage
                else:
                    modifier *= shadow_fangs_mod
                if ability in self.mastery_scaling_damage_sources:
                    modifier *= executioner_mod

                #override for "weird" abilities
                #death from above strike is actually an evis with 1.5 modifier and dfa pulse needs mastery
                if ability == 'death_from_above_strike':
                    modifier *= 1.5 * executioner_mod
                    ability = 'eviscerate'
                if ability == 'death_from_above_pulse':
                    modifier *= executioner_mod

                damage_breakdown[ability] = self.get_ability_dps(average_ap, ability, aps, crits, modifier, crit_mod, both_hands, cps)

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
        return .275 * ap * (1 + (0.05 * self.traits.master_alchemist)) * (1 + (0.4 * self.talents.master_poisoner))

    def deadly_instant_poison_damage(self, ap):
        return .142 * ap * (1 + (0.05 * self.traits.master_alchemist)) * (1 + (0.4 * self.talents.master_poisoner))

    #Maybe add better handling for 'rule of three' for artifact traits
    def envenom_damage(self, ap, cp):
        return .5 * cp * ap * (1 + (0.0333 * self.traits.toxic_blades))

    def fan_of_knives_damage(self, ap):
        return .8316 * ap

    def garrote_tick_damage(self, ap):
        return .9 * ap

    def hemorrhage_damage(self, ap):
        return 1 * self.get_weapon_damage('mh', ap)

    def mh_kingsbane_damage(self, ap):
       return 3 * self.get_weapon_damage('mh', ap) * (1 + (0.4 * self.talents.master_poisoner))
    def oh_kingsbane_damage(self, ap):
        return 3 * self.oh_penalty * self.get_weapon_damage('oh', ap) * (1 + (0.4 * self.talents.master_poisoner))
    def kingsbane_tick_damage(self, ap):
        return 0.45 * ap * (1 + (0.4 * self.talents.master_poisoner))
    def mh_mutilate_damage(self, ap):
        return 3.6 * self.get_weapon_damage('mh', ap) * (1 + (0.15 * self.traits.assassins_blades))

    def oh_mutilate_damage(self, ap):
        return 3.6 * self.oh_penalty() * self.get_weapon_damage('oh', ap) * (1 + (0.15 * self.traits.assassins_blades))

    def poisoned_knife_damage(self, ap):
        return 0.6 * ap

    def rupture_tick_damage(self, ap, cp):
        return .3 * cp * ap * (1 + (0.0333 * self.traits.gushing_wounds))

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
    def finality_eviscerate_damage(self, ap, cp):
        return 1.5 * cp * ap

    def gloomblade_damage(self, ap):
        return 4.25 * self.get_weapon_damage('mh', ap) * (1 + (0.0333 * self.traits.the_quiet_knife))

    def mh_goremaws_bite_damage(self, ap):
        return 5 * self.get_weapon_damage('mh', ap)

    def oh_goremaws_bite_damage(self, ap):
        return 5 * self.oh_penalty() * self.get_weapon_damage('oh', ap)

    #Nightblade doesn't actually scale with cps but passing cps for simplicity
    def nightblade_tick_damage(self, ap, cp):
        return 1.2 * ap * (1 + (0.05 * self.traits.demon_kiss))
    def finality_nightblade_tick_damage(self, ap, cp):
        return 1.4 * ap * (1 + (0.05 * self.traits.demon_kiss))

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

    def get_formula(self, name):
        formulas = {
            #general
            'mh_autoattack':             self.mh_damage,
            'oh_autoattack':             self.oh_damage,
            'death_from_above_pulse':    self.death_from_above_pulse_damage,
            #assassination
            'deadly_poison':             self.deadly_poison_tick_damage,
            'deadly_instant_poison':     self.deadly_instant_poison_damage,
            'envenom':                   self.envenom_damage,
            'fan_of_knives_damage':      self.fan_of_knives_damage,
            'garrote_ticks':             self.garrote_tick_damage,
            'hemorrhage':                self.hemorrhage_damage,
            'mh_kingsbane':              self.mh_kingsbane_damage,
            'oh_kingsbane':              self.oh_kingsbane_damage,
            'kingsbane_ticks':           self.kingsbane_tick_damage,
            'mh_mutilate':               self.mh_mutilate_damage,
            'oh_mutilate':               self.oh_mutilate_damage,
            'poisoned_knife':            self.poisoned_knife_damage,
            'rupture_ticks':             self.rupture_tick_damage,
            #outlaw
            'ambush':                    self.ambush_damage,
            'between_the_eyes':          self.between_the_eyes_damage,
            'blunderbuss':               self.blunderbuss_damage,
            'cannonball_barrage':        self.cannonball_barrage_damage,
            'ghostly_strike':            self.ghostly_strike_damage,
            'mh_greed':                  self.mh_greed_damage,
            'oh_greed':                  self.oh_greed_damage,
            'mh_killing_spree':          self.mh_killing_spree_damage,
            'oh_killing_spree':          self.oh_killing_spree_damage,
            'main_gauche':               self.main_gauche_damage,
            'pistol_shot':               self.pistol_shot_damage,
            'run_through':               self.run_through_damage,
            'saber_slash':               self.saber_slash_damage,
            #subtlety
            'backstab':                  self.backstab_damage,
            'eviscerate':                self.eviscerate_damage,
            'finality:eviscerate':       self.finality_eviscerate_damage,
            'gloomblade':                self.gloomblade_damage,
            'mh_goremaws_bite':          self.mh_goremaws_bite_damage,
            'oh_goremaws_bite':          self.oh_goremaws_bite_damage,
            'nightblade_ticks':          self.nightblade_tick_damage,
            'finality_nightblade_ticks': self.finality_nightblade_tick_damage,
            'shadowstrike':              self.shadowstrike_damage,
            'mh_shadow_blades':          self.mh_shadow_blades_damage,
            'oh_shadow_blades':          self.oh_shadow_blades_damage,
            'shuriken_storm':            self.shuriken_storm_damage,
            'shuriken_toss':             self.shuriken_toss_damage,
        }
        return formulas[name]

    def get_spell_cost(self, ability, cost_mod=1.0):
        cost = self.ability_info[ability][0] * cost_mod
        if ability == 'shadowstrike':
            cost -= 0.25 * (5 * self.traits.energetic_stabbing)
        return cost

    def get_spell_cd(self, ability):
        return self.ability_cds[ability]

    def crit_rate(self, crit=None):
        # all rogues get 10% bonus crit, .05 of base crit for everyone
        # should be coded better?
        base_crit = .15
        base_crit += self.stats.get_crit_from_rating(crit)
        return base_crit + self.race.get_racial_crit(is_day=self.settings.is_day) - self.crit_reduction
