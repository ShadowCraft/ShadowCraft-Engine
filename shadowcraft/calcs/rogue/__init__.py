from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import range
import gettext
import builtins

_ = gettext.gettext

from shadowcraft.calcs import DamageCalculator
from shadowcraft.core import exceptions

class RogueDamageCalculator(DamageCalculator):
    # Functions of general use to rogue damage calculation go here.  If a
    # calculation will reasonably used for multiple classes, it should go in
    # calcs.DamageCalculator instead.  If its a specific intermediate
    # value useful to only your calculations, when you extend this you should
    # put the calculations in your object.  But there are things - like
    # backstab damage as a function of AP - that (almost) any rogue damage
    # calculator will need to know, so things like that go here.

    default_ep_stats = ['agi', 'haste', 'crit', 'mastery', 'ap', 'versatility']

    assassination_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                                    'deadly_poison', 'deadly_instant_poison', 'envenom',
                                    'fan_of_knives', 'garrote_ticks', 'hemorrhage',
                                    'kingsbane', 'kingsbane_ticks', 'mutilate',
                                    'poisoned_knife', 'poison_bomb', 'rupture_ticks', 'from_the_shadows',
                                    'wound_poison', 'toxic_blade']
    outlaw_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                             'ambush', 'between_the_eyes', 'blunderbuss', 'cannonball_barrage',
                             'ghostly_strike', 'greed', 'killing_spree', 'main_gauche',
                             'pistol_shot', 'run_through', 'saber_slash']
    subtlety_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                               'backstab', 'eviscerate', 'gloomblade',
                               'goremaws_bite', 'nightblade', 'shadowstrike',
                               'shadow_blades', 'shuriken_storm', 'shuriken_toss',
                               'nightblade_ticks', 'soul_rip', 'shadow_nova', 'second_shuriken']
    #All damage sources mitigated by armor
    physical_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                                'fan_of_knives', 'hemorrhage', 'mutilate', 'poisoned_knife',
                                'ambush', 'between_the_eyes', 'blunderbuss', 'cannonball_barrage',
                                'ghostly_strike', 'greed', 'killing_spree', 'main_gauche',
                                'pistol_shot', 'run_through', 'saber_slash', 'backstab',
                                'eviscerate', 'shadowstrike', 'shuriken_storm', 'shuriken_toss']
    #All damage sources that deal damage with both hands
    dual_wield_damage_sources = ['kingsbane', 'mutilate', 'greed', 'killing_spree',
                                 'goremaws_bite', 'shadow_blades']
    #All damage sources that scale with cps
    finisher_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                                 'envenom', 'rupture_ticks', 'between_the_eyes',
                                 'run_through', 'eviscerate',
                                'nightblade', 'nightblade_ticks',
                                'roll_the_bones', 'slice_and_dice']
    #All damage source that are replicated by Blade Flurry
    blade_flurry_damage_sources = ['death_from_above_pulse', 'death_from_above_strike',
                             'ambush', 'between_the_eyes', 'blunderbuss', 'ghostly_strike', 'greed', 'killing_spree',
                             'main_gauche','pistol_shot', 'run_through', 'saber_slash']

    #probability of getting X buffs with rtb
    rtb_probabilities = {
        1: 0.5923,
        2: 0.3537,
        3: 0.0386,
        6: 0.0154,
    }

    #probabilities of getting X buffs from RtB with loaded dice
    #assume we reroll/blacklist one buff rolls instead of adding a second buff to one rolls
    #so far this assumption could neither be confirmed nor disproved
    #TODO: actually plug these into the model :/
    rtb_loaded_dice_probabilities = {
        1: 0,
        2: 0.8675,
        3: 0.0946,
        6: 0.0379,
    }

    #number of unique rtb buffs of each amount
    rtb_buff_count = {
        1: 6,
        2: 15,
        3: 20,
        6: 1,
    }

    assassination_mastery_conversion = .04
    outlaw_mastery_conversion = .022
    subtlety_mastery_conversion = .0276

    ability_info = {
            #general
            'crimson_vial':        (30.,  'buff'),
            'death_from_above':    (25., 'strike'),
            'feint':               (35., 'buff'),
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
            'toxic_blade':         (20., 'strike'),
            'exsanguinate':        (25., 'buff'),
            #outlaw
            'ambush':              (60., 'strike'),
            'between_the_eyes':    (35., 'strike'),
            'blunderbuss':         (40., 'strike'),
            'ghostly_strike':       (30., 'strike'),
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
            'shadowstrike':        (40., 'strike'),
            'shuriken_storm':      (35., 'strike'),
            'shuriken_toss':       (40., 'strike'),
            'symbols_of_death':    (35., 'buff'),
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
            'garrote':                   15.,
            'kingsbane':                 45.,
            'vendetta':                 120.,
            'toxic_blade':               25.,
            #outlaw
            'adrenaline_rush':          180.,
            'cannonball_barrage':        60.,
            'curse_of_the_dreadblades':  90.,
            'killing_spree':            120.,
            #subtlety
            'goremaws_bite':             60.,
            'shadow_dance':              60.,
            'shadow_blades':            180.,
        }

    # Vendetta CDR for number of points in trait
    master_assassin_cdr = {
            0: 0,
            1: 10,
            2: 20,
            3: 30,
            4: 38,
            5: 44,
            6: 48,
            7: 52,
            8: 56
    }

    # Adrenaline Rush CDR for number of points in trait
    fortunes_boon_cdr = {
            0: 0,
            1: 10,
            2: 18,
            3: 25,
            4: 31,
            5: 37,
            6: 42,
            7: 46,
            8: 49
    }

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'level':
            self._set_constants_for_level()

    def _set_constants_for_level(self):
        # this calls _set_constants_for_level() in calcs/__init__.py because
        # this supercedes it, this is how inheretence in python works
        # any modules that expand on rogue/__init__.py and use this should do
        # the same
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
            for i in range(1, cps + 1):
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

        modifier_dict = self.damage_modifiers.compile_modifier_dict()

        # this removes keys with empty values, prevents errors from:
        # attacks_per_second['sinister_strike'] = None
        for key in list(attacks_per_second.keys()):
            if not attacks_per_second[key]:
                del attacks_per_second[key]

        if 'mh_autoattacks' in attacks_per_second:
            # Assumes mh and oh attacks are both active at the same time.  As
            # they should always be.
            # Friends don't let friends raid without gear.
            mh_base_damage = self.mh_damage(average_ap) * modifier_dict['autoattacks']
            mh_hit_rate = self.dw_mh_hit_chance - crit_rates['mh_autoattacks']
            average_mh_hit = mh_hit_rate * mh_base_damage + crit_rates['mh_autoattacks'] * mh_base_damage * crit_damage_modifier
            mh_dps_tuple = average_mh_hit * attacks_per_second['mh_autoattacks']

            oh_base_damage = self.oh_damage(average_ap) * modifier_dict['autoattacks']
            oh_hit_rate = self.dw_oh_hit_chance - crit_rates['oh_autoattacks']
            average_oh_hit = oh_hit_rate * oh_base_damage + crit_rates['oh_autoattacks'] * oh_base_damage * crit_damage_modifier
            oh_dps_tuple = average_oh_hit * attacks_per_second['oh_autoattacks']
            damage_breakdown['autoattack'] = mh_dps_tuple + oh_dps_tuple

        for proc in damage_procs:
            if proc.proc_name not in damage_breakdown:
                # Toss multiple damage procs with the same name (Avalanche):
                # attacks_per_second is already being updated with that key.
                if proc.stat in ['physical_dot', 'spell_dot']:
                    self.set_uptime(proc, attacks_per_second, crit_rates)
                damage_breakdown[proc.proc_name] = self.get_proc_damage_contribution(proc, attacks_per_second[proc.proc_name], current_stats, average_ap, modifier_dict)

        self.add_special_procs_damage(current_stats, attacks_per_second, crit_rates, modifier_dict, damage_breakdown)

        #compute damage breakdown for each spec
        if self.spec == 'assassination':

            for ability in self.assassination_damage_sources:
                if ability not in attacks_per_second:
                    continue
                aps = attacks_per_second[ability]
                crits = crit_rates[ability]
                crit_mod = crit_damage_modifier
                modifier = modifier_dict[ability]
                both_hands = ability in self.dual_wield_damage_sources
                cps = max_cps if ability in self.finisher_damage_sources else 0

                #override for "weird" abilities
                #death from above strike is actually an envenom with 1.5
                #modifier
                #manually add in base modifier because DfA strike is in
                #physical sources
                if ability == 'death_from_above_strike':
                    modifier *= 1.5
                    ability = 'envenom'
                damage_breakdown[ability] = self.get_ability_dps(average_ap, ability, aps, crits, modifier, crit_mod, both_hands, cps)

        if self.spec == 'outlaw':
            for ability in self.outlaw_damage_sources:
                if ability not in attacks_per_second:
                    continue
                aps = attacks_per_second[ability]
                crits = crit_rates[ability]
                crit_mod = crit_damage_modifier
                modifier = modifier_dict[ability]
                both_hands = ability in self.dual_wield_damage_sources
                cps = max_cps if ability in self.finisher_damage_sources else 0

                #override for "weird" abilities
                #death from above strike is actually an evis with 1.5 modifier
                if ability == 'death_from_above_strike':
                    modifier *= 1.5
                    ability = 'run_through'
                #between the eyes has additional crit damage
                #Damage modifier 3 explained here:
                #http://beta.askmrrobot.com/wow/simulator/docs/critdamage
                if ability == 'between_the_eyes':
                    crit_mod = self.crit_damage_modifiers(3)
                if ability == 'saber_slash' and self.traits.sabermetrics:
                    crit_mod = self.crit_damage_modifiers(1 + self.traits.sabermetrics * 0.05)
                damage_breakdown[ability] = self.get_ability_dps(average_ap, ability, aps, crits, modifier, crit_mod, both_hands, cps)

        if self.spec == 'subtlety':

            for ability in self.subtlety_damage_sources:
                if ability not in attacks_per_second:
                    continue
                aps = attacks_per_second[ability]
                crits = crit_rates[ability]
                crit_mod = crit_damage_modifier
                modifier = modifier_dict[ability]
                both_hands = ability in self.dual_wield_damage_sources
                cps = max_cps if ability in self.finisher_damage_sources else 0

                #override for "weird" abilities
                #death from above strike is actually an evis with 1.5 modifier
                #and dfa pulse needs mastery
                if ability == 'death_from_above_strike':
                    modifier *= 1.5
                    ability = 'eviscerate'

                damage_breakdown[ability] = self.get_ability_dps(average_ap, ability, aps, crits, modifier, crit_mod, both_hands, cps)

        return damage_breakdown, additional_info

    #autoattacks
    def mh_damage(self, ap):
        return self.get_weapon_damage('mh', ap, is_normalized=False)

    def oh_damage(self, ap):
        return self.oh_penalty() * self.get_weapon_damage('oh', ap, is_normalized=False)

    #general abilities
    def death_from_above_pulse_damage(self, ap, cp):
        return 0.8784 * cp * ap #20% buff in 7.1.5

    #assassination
    def deadly_poison_tick_damage(self, ap):
        return 0.3575 * ap * (1 + (0.05 * self.traits.master_alchemist)) * (1 + (0.3 * self.talents.master_poisoner))

    def deadly_instant_poison_damage(self, ap):
        return 0.221 * ap * (1 + (0.05 * self.traits.master_alchemist)) * (1 + (0.3 * self.talents.master_poisoner))

    #Maybe add better handling for 'rule of three' for artifact traits
    def envenom_damage(self, ap, cp):
        return .6 * cp * ap * (1 + (0.0333 * self.traits.toxic_blades))

    def fan_of_knives_damage(self, ap):
        return 1.5 * ap

    #Lumping 40 ticks together for simplicity
    def from_the_shadows_damage(self, ap):
        return 40 * 0.35 * ap

    def garrote_tick_damage(self, ap):
        return .9 * ap * (1 + 0.04 * self.traits.strangler)

    def hemorrhage_damage(self, ap):
        return 1 * self.get_weapon_damage('mh', ap)

    def mh_kingsbane_damage(self, ap):
        return 2.4 * self.get_weapon_damage('mh', ap) * (1 + (0.3 * self.talents.master_poisoner))
    def oh_kingsbane_damage(self, ap):
        return 2.4 * self.oh_penalty() * self.get_weapon_damage('oh', ap) * (1 + (0.3 * self.talents.master_poisoner))
    def kingsbane_tick_damage(self, ap):
        return 0.36 * ap * (1 + (0.3 * self.talents.master_poisoner))
    def mh_mutilate_damage(self, ap):
        return 3.6 * self.get_weapon_damage('mh', ap) * (1 + (0.15 * self.traits.assassins_blades))

    def oh_mutilate_damage(self, ap):
        return 3.6 * self.oh_penalty() * self.get_weapon_damage('oh', ap) * (1 + (0.15 * self.traits.assassins_blades))

    def poisoned_knife_damage(self, ap):
        return 0.6 * ap

    def toxic_blade_damage(self, ap):
        return 6 * self.get_weapon_damage('mh', ap)

    #Lumping 6 ticks together for simplicity
    def poison_bomb_damage(self, ap):
        return 6 * 1.2 * ap * (1 + (0.3 * self.talents.master_poisoner))

    def rupture_tick_damage(self, ap, cp):
        return 1.5 * ap * (1 + (0.0333 * self.traits.gushing_wounds))

    def wound_poison_damage(self, ap):
        return 0.13 * ap * (1 + (0.05 * self.traits.master_alchemist)) * (1 + (0.3 * self.talents.master_poisoner))

    #outlaw
    def ambush_damage(self, ap):
        return 4.5 * self.get_weapon_damage('mh', ap)

    def between_the_eyes_damage(self, ap, cp):
        return .85 * cp * ap * (1 + (0.06 * self.traits.black_powder))

    #7*121% AP
    def blunderbuss_damage(self, ap):
        return 8.47 * ap

    #Ignoring that this behaves as a dot for simplicity, 6*150%
    def cannonball_barrage_damage(self, ap):
        return 9 * ap

    def ghostly_strike_damage(self, ap):
        return 1.94 * self.get_weapon_damage('mh', ap)

    def mh_greed_damage(self, ap):
        return 3.5 * self.get_weapon_damage('mh', ap)

    def oh_greed_damage(self, ap):
        return 3.5 * self.oh_penalty() * self.get_weapon_damage('oh', ap)

    #For KsP treat each hit individually
    def mh_killing_spree_damage(self, ap):
        return 2.6 * self.get_weapon_damage('mh', ap)

    def oh_killing_spree_damage(self, ap):
        return 2.6 * self.oh_penalty() * self.get_weapon_damage('oh', ap)

    def main_gauche_damage(self, ap):
        return 2.1 * self.oh_penalty() * self.get_weapon_damage('oh', ap) * (1 + (0.1 * self.traits.fortunes_strike))

    def pistol_shot_damage(self, ap):
        return 1.65 * ap

    def run_through_damage(self, ap, cp):
        return 1.42 * ap * cp * (1 + (0.04 * self.traits.fates_thirst))

    def saber_slash_damage(self, ap):
        return 3.02 * self.get_weapon_damage('mh', ap) * (1 + (0.15 * self.traits.cursed_edges))

    #subtlety
    #Ignore positional modifier for now
    def backstab_damage(self, ap):
        return 3.7 * self.get_weapon_damage('mh', ap) * (1 + (0.0333 * self.traits.the_quiet_knife))

    #has two ranks
    def eviscerate_damage(self, ap, cp):
        return 1.472 * cp * ap

    def gloomblade_damage(self, ap):
        return 5.25 * self.get_weapon_damage('mh', ap) * (1 + (0.0333 * self.traits.the_quiet_knife))

    def mh_goremaws_bite_damage(self, ap):
        return 10 * self.get_weapon_damage('mh', ap)

    def oh_goremaws_bite_damage(self, ap):
        return 10 * self.oh_penalty() * self.get_weapon_damage('oh', ap)

    #Nightblade doesn't actually scale with cps but passing cps for simplicity
    def nightblade_tick_damage(self, ap, cp):
        return 1.38 * ap * (1 + (0.05 * self.traits.demons_kiss))

    def shadowstrike_damage(self, ap):
        return 8.5 * self.get_weapon_damage('mh', ap) * (1 + (0.05 * self.traits.precision_strike))

    def mh_shadow_blades_damage(self, ap):
        return self.get_weapon_damage('mh', ap, is_normalized=False)

    def oh_shadow_blades_damage(self, ap):
        return self.oh_penalty() * self.get_weapon_damage('oh', ap, is_normalized=False)

    def second_shuriken_damage(self, ap):
        return 0.338 * ap

    def shuriken_storm_damage(self, ap):
        return 0.7215 * ap

    def shuriken_toss_damage(self, ap):
        return 1.2 * ap

    def soul_rip_damage(self, ap):
        return 1.5 * ap

    def shadow_nova_damage(self, ap):
        return 1.5 * ap

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
            'fan_of_knives':             self.fan_of_knives_damage,
            'from_the_shadows':          self.from_the_shadows_damage,
            'garrote_ticks':             self.garrote_tick_damage,
            'hemorrhage':                self.hemorrhage_damage,
            'mh_kingsbane':              self.mh_kingsbane_damage,
            'oh_kingsbane':              self.oh_kingsbane_damage,
            'kingsbane_ticks':           self.kingsbane_tick_damage,
            'mh_mutilate':               self.mh_mutilate_damage,
            'oh_mutilate':               self.oh_mutilate_damage,
            'poisoned_knife':            self.poisoned_knife_damage,
            'poison_bomb':               self.poison_bomb_damage,
            'rupture_ticks':             self.rupture_tick_damage,
            'wound_poison':              self.wound_poison_damage,
            'toxic_blade':               self.toxic_blade_damage,
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
            'gloomblade':                self.gloomblade_damage,
            'mh_goremaws_bite':          self.mh_goremaws_bite_damage,
            'oh_goremaws_bite':          self.oh_goremaws_bite_damage,
            'nightblade_ticks':          self.nightblade_tick_damage,
            'shadowstrike':              self.shadowstrike_damage,
            'mh_shadow_blades':          self.mh_shadow_blades_damage,
            'oh_shadow_blades':          self.oh_shadow_blades_damage,
            'second_shuriken':           self.second_shuriken_damage,
            'shuriken_storm':            self.shuriken_storm_damage,
            'shuriken_toss':             self.shuriken_toss_damage,
            'soul_rip':                  self.soul_rip_damage,
            'shadow_nova':               self.shadow_nova_damage,
        }
        return formulas[name]

    def get_spell_cost(self, ability, cost_mod=1.0):
        cost = self.ability_info[ability][0] * cost_mod
        if ability == 'shadowstrike':
            cost -= 0.25 * (5 * self.traits.energetic_stabbing)
            #Assume 5 yards away so 3 + 5/3
            if self.stats.gear_buffs.shadow_satyrs_walk:
                cost -= 4.67
        return cost

    def get_spell_cd(self, ability):
        cd = self.ability_cds[ability]
        if ability == 'adrenaline_rush':
            cd -= self.fortunes_boon_cdr[self.traits.fortunes_boon]
        elif ability == 'vendetta':
            cd -= self.master_assassin_cdr[self.traits.master_assassin]

        #Convergence of Fates Trinket
        cof = self.stats.procs.convergence_of_fates
        if cof and ability in ['vendetta', 'adrenaline_rush', 'shadow_blades']:
            #We want time t in sec when CD is ready. CD goes down by 1 every sec plus value * proc_chance.
            #That gives us: 0 = cd - t(1 + value * proc_chance) <=> t = cd / (1 + value * proc_chance)
            cd /= 1 + cof.value * cof.get_proc_rate(spec=self.spec)

        return cd

    def crit_rate(self, crit=None):
        # all rogues have 10% base crit
        # should be coded better?
        base_crit = .10
        base_crit += self.stats.get_crit_from_rating(crit)
        return base_crit + self.race.get_racial_crit(is_day=self.settings.is_day) - self.crit_reduction

    def add_special_procs_damage(self, current_stats, attacks_per_second, crit_rates, modifier_dict, damage_breakdown):
        ap = current_stats['ap'] + current_stats['agi'] * self.stat_multipliers['ap']

        # Nightblooming Frond
        frond = self.stats.procs.nightblooming_frond
        if frond:
            autoattacks_per_second = attacks_per_second['mh_autoattacks'] * self.dual_wield_mh_hit_chance()
            autoattacks_per_second += attacks_per_second['oh_autoattacks'] * self.dual_wield_oh_hit_chance()
            if 'shadow_blades' in attacks_per_second:
                autoattacks_per_second += attacks_per_second['shadow_blades'] * 2 #both hands

            # calculate stacks for each second and accumulate bonus damage per proc
            stack_list = []
            for second in range(1, frond.duration + 1):
                stack_list.append(min(second * autoattacks_per_second, frond.max_stacks))
            stack_damage = self.get_proc_damage_contribution(frond, 1, current_stats, ap, modifier_dict)
            proc_damage = 0
            for stack_count in stack_list:
                proc_damage += stack_count * stack_damage * autoattacks_per_second

            damage_breakdown[frond.proc_name] = proc_damage * frond.get_proc_rate(spec=self.spec) * 1.1307 #BLP

        # Tiny Oozeling in a Jar
        oozeling = self.stats.procs.tiny_oozeling_in_a_jar
        if oozeling:
            haste = self.get_haste_multiplier(current_stats)
            stacks_per_use = min(oozeling.icd * haste * 1.1307 * 3 / 60, 6) #3 rppm, capped at 6 stacks, 1.1307 bad luck protection
            damage_per_use = self.get_proc_damage_contribution(oozeling, stacks_per_use, current_stats, ap, modifier_dict)
            damage_breakdown[oozeling.proc_name] = damage_per_use / oozeling.icd

        # Potions: Potion of the Old War
        # Trinkets: Tirathon's Betrayal and Faulty Countermeasure
        for proc in [self.stats.procs.old_war_pot, self.stats.procs.old_war_prepot,
            self.stats.procs.tirathons_betrayal, self.stats.procs.faulty_countermeasure]:
            if proc:
                # all 20 RPPM with haste mod
                rppm = 20
                haste_mod = self.get_haste_multiplier(current_stats) if proc.haste_scales else 1
                procs_per_use = proc.duration * rppm * 1.1307 * haste_mod / 60
                damage_per_use = self.get_proc_damage_contribution(proc, procs_per_use, current_stats, ap, modifier_dict)
                if proc.proc_name in damage_breakdown:
                    damage_breakdown[proc.proc_name] += damage_per_use / proc.icd
                else:
                    damage_breakdown[proc.proc_name] = damage_per_use / proc.icd
