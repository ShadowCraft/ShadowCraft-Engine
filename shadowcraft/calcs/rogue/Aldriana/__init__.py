#import copy
import gettext
import __builtin__
import math
from operator import add
from copy import copy

__builtin__._ = gettext.gettext

from shadowcraft.calcs.rogue import RogueDamageCalculator
from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data


class InputNotModeledException(exceptions.InvalidInputException):
    # I'll return these when inputs don't make sense to the model.
    pass


class AldrianasRogueDamageCalculator(RogueDamageCalculator):
    ###########################################################################
    # Main DPS comparison function.  Calls the appropriate sub-function based
    # on talent tree.
    ###########################################################################

    def get_dps(self):
        super(AldrianasRogueDamageCalculator, self).get_dps()
        if self.settings.is_assassination_rogue():
            self.init_assassination()
            return self.assassination_dps_estimate()
        elif self.settings.is_combat_rogue():
            return self.combat_dps_estimate()
        elif self.settings.is_subtlety_rogue():
            return self.subtlety_dps_estimate()
        else:
            raise InputNotModeledException(_('You must specify a spec.'))

    def get_dps_breakdown(self):
        if self.settings.is_assassination_rogue():
            self.init_assassination()
            return self.assassination_dps_breakdown()
        elif self.settings.is_combat_rogue():
            return self.combat_dps_breakdown()
        elif self.settings.is_subtlety_rogue():
            return self.subtlety_dps_breakdown()
        else:
            raise InputNotModeledException(_('You must specify a spec.'))

    ###########################################################################
    # General object manipulation functions that we'll use multiple places.
    ###########################################################################

    PRECISION_REQUIRED = 10 ** -7

    def are_close_enough(self, old_dist, new_dist, precision=PRECISION_REQUIRED):
        for item in new_dist:
            if item not in old_dist:
                return False
            elif not hasattr(new_dist[item], '__iter__'):
                if abs(new_dist[item] - old_dist[item]) > precision:
                    return False
            else:
                for index in range(len(new_dist[item])):
                    if abs(new_dist[item][index] - old_dist[item][index]) > precision:
                        return False
        return True
    
    ###########################################################################
    # Overrides: these make the ep methods default to glyphs/talents or weapon
    # setups that we are really modeling.
    ###########################################################################

    def get_glyphs_ranking(self, list=None):
        if list is None:
            list = [
                'vendetta',
                'energy',
                'disappearance',
            ]
        return super(AldrianasRogueDamageCalculator, self).get_glyphs_ranking(list)

    def get_talents_ranking(self, list=None):
        if list is None:
            list = [
                'nightstalker',
                'subterfuge',
                'shadow_focus',
                #'shuriken_toss',
                'marked_for_death',
                'anticipation',
                'lemon_zest',
                'death_from_above',
                'shadow_reflection',
            ]
        return super(AldrianasRogueDamageCalculator, self).get_talents_ranking(list)

    def get_oh_weapon_modifier(self, setups=None):
        if setups is None:
            setups = [
                (None, {'hand':'oh', 'type':'one-hander', 'speed':2.6}),
                (None, {'hand':'oh', 'type':'dagger', 'speed':1.8})
            ]
        return super(AldrianasRogueDamageCalculator, self).get_oh_weapon_modifier(setups)

    ###########################################################################
    # General modeling functions for pulling information useful across all
    # models.
    ###########################################################################

    def heroism_uptime_per_fight(self):
        if not self.buffs.short_term_haste_buff:
            return 0

        total_uptime = 0
        remaining_duration = self.settings.duration
        while remaining_duration > 0:
            total_uptime += min(remaining_duration, 40)
            remaining_duration -= 600

        return total_uptime * 1.0 / self.settings.duration

    def get_heroism_haste_multiplier(self):
        # Just average-casing for now.  Should fix that at some point.
        return 1 + .3 * self.heroism_uptime_per_fight()

    def get_cp_distribution_for_cycle(self, cp_distribution_per_move, target_cp_quantity):
        avg_cp_per_cpg = sum([key * cp_distribution_per_move[key] for key in cp_distribution_per_move])
        
        time_spent_at_cp = [0, 0, 0, 0, 0, 0]
        cur_min_cp = 0
        cur_dist = {(0, 0): 1}
        while cur_min_cp < target_cp_quantity:
            cur_min_cp += 1

            new_dist = {}
            for (cps, moves), prob in cur_dist.items():
                if cps >= cur_min_cp:
                    if (cps, moves) in new_dist:
                        new_dist[(cps, moves)] += prob
                    else:
                        new_dist[(cps, moves)] = prob
                else:
                    for (move_cp, move_prob) in cp_distribution_per_move.items():
                        total_cps = cps + move_cp
                        if total_cps > 5:
                            total_cps = 5
                        dist_entry = (total_cps, moves + 1)
                        time_spent_at_cp[total_cps] += move_prob * prob
                        if dist_entry in new_dist:
                            new_dist[dist_entry] += move_prob * prob
                        else:
                            new_dist[dist_entry] = move_prob * prob
            cur_dist = new_dist

        for (cps, moves), prob in cur_dist.items():
            time_spent_at_cp[cps] += prob

        total_weight = sum(time_spent_at_cp)
        for i in xrange(6):
            time_spent_at_cp[i] /= total_weight

        return cur_dist, time_spent_at_cp, avg_cp_per_cpg

    def get_cp_per_cpg(self, base_cp_per_cpg=1, *probs):
        # Computes the combined probabilites of getting an additional cp from
        # each of the items in probs.
        cp_per_cpg = {base_cp_per_cpg: 1}
        for prob in probs:
            if prob == 0:
                continue
            new_cp_per_cpg = {}
            for cp in cp_per_cpg:
                new_cp_per_cpg.setdefault(cp, 0)
                new_cp_per_cpg.setdefault(cp + 1, 0)
                new_cp_per_cpg[cp] += cp_per_cpg[cp] * (1 - prob)
                new_cp_per_cpg[cp + 1] += cp_per_cpg[cp] * prob
            cp_per_cpg = new_cp_per_cpg
        return cp_per_cpg

    def get_crit_rates(self, stats):
        base_melee_crit_rate = self.crit_rate(crit=stats['crit'])
        crit_rates = {
            'mh_autoattacks': min(base_melee_crit_rate, self.dw_mh_hit_chance),
            'oh_autoattacks': min(base_melee_crit_rate, self.dw_oh_hit_chance),
        }
        for attack in ('rupture_ticks', 'shuriken_toss'):
            crit_rates[attack] = base_melee_crit_rate

        if self.settings.is_assassination_rogue():
            spec_attacks = ('mutilate', 'dispatch', 'envenom', 'venomous_wounds')
        elif self.settings.is_combat_rogue():
            spec_attacks = ('main_gauche', 'sinister_strike', 'revealing_strike', 'eviscerate', 'killing_spree', 'oh_killing_spree', 'mh_killing_spree')
        elif self.settings.is_subtlety_rogue():
            spec_attacks = ('eviscerate', 'backstab', 'ambush', 'hemorrhage')

        if self.settings.dmg_poison == 'dp':
            poisons = ('deadly_instant_poison', 'deadly_poison')
        elif self.settings.dmg_poison == 'wp':
            poisons = ('wound_poison', )
        elif self.settings.dmg_poison == 'sp':
            poisons = ('swift_poison', )

        talent_attacks = ()
        if self.talents.death_from_above:
            talent_attacks = ('death_from_above', 'death_from_above_strike', 'death_from_above_pulse')

        openers = tuple([self.settings.opener_name])

        for attack in spec_attacks + poisons + openers + talent_attacks:
            #for handling odd crit rates
            if attack in ('eviscerate', 'envenom') and self.stats.gear_buffs.rogue_t15_4pc:
                crit_rates[attack] = base_melee_crit_rate + .2
            else:
                crit_rates[attack] = base_melee_crit_rate

        for attack, crit_rate in crit_rates.items():
            if crit_rate > 1:
                crit_rates[attack] = 1

        return crit_rates

    def set_constants(self):
        # General setup that we'll use in all 3 cycles.
        self.load_from_advanced_parameters()
        self.bonus_energy_regen = 0
        self.spec_needs_converge = False
        #racials
        if self.race.arcane_torrent:
            self.bonus_energy_regen += 15. / (120 + self.settings.response_time)
        #auxiliary rotational effects
        if self.settings.shiv_interval != 0:
            self.bonus_energy_regen -= self.get_spell_stats('shiv')[0] / self.settings.shiv_interval
        if self.settings.feint_interval != 0:
            self.bonus_energy_regen -= self.get_spell_stats('feint')[0] / self.settings.feint_interval
            
        self.set_openers()
        
        #only include if general multiplier applies to spec calculations 
        self.true_haste_mod *= self.get_heroism_haste_multiplier()
        self.base_stats = {
            'agi': (self.stats.agi + self.buffs.buff_agi(race=self.race.epicurean) + self.race.racial_agi),
            'ap': (self.stats.ap),
            'crit': (self.stats.crit + self.buffs.buff_crit(race=self.race.epicurean)),
            'haste': (self.stats.haste + self.buffs.buff_haste(race=self.race.epicurean)),
            'mastery': (self.stats.mastery + self.buffs.buff_mast(race=self.race.epicurean)),
            'readiness': (self.stats.readiness + self.buffs.buff_readiness(race=self.race.epicurean)),
            'multistrike': (self.stats.multistrike + self.buffs.buff_multistrike(race=self.race.epicurean)),
            'versatility': (self.stats.versatility + self.buffs.buff_versatility(race=self.race.epicurean)),
        }
        self.stat_multipliers = {
            'str': 1.,
            'agi': self.buffs.stat_multiplier() * self.stats.gear_buffs.gear_specialization_multiplier(),
            'ap': self.buffs.attack_power_multiplier(),
            'crit': 1.,
            'haste': 1.,
            'mastery': 1.,
            'readiness': 1.,
            'multistrike': 1.,
            'versatility': 1.,
        }
        
        if self.race.human_spirit:
            self.base_stats['versatility'] += self.race.versatility_bonuses[self.level]
                
        for boost in self.race.get_racial_stat_boosts():
            if boost['stat'] in self.base_stats:
                self.base_stats[boost['stat']] += boost['value'] * boost['duration'] * 1.0 / (boost['cooldown'] + self.settings.response_time)
        
        if self.stats.procs.virmens_bite:
            getattr(self.stats.procs, 'virmens_bite').icd = self.settings.duration
        if self.stats.procs.virmens_bite_prepot:
            getattr(self.stats.procs, 'virmens_bite_prepot').icd = self.settings.duration
        if self.stats.procs.draenic_agi_pot:
            getattr(self.stats.procs, 'draenic_agi_pot').icd = self.settings.duration
        if self.stats.procs.draenic_agi_prepot:
            getattr(self.stats.procs, 'draenic_agi_prepot').icd = self.settings.duration

        self.base_strength = self.stats.str + self.buffs.buff_str() + self.race.racial_str
        self.base_strength *= self.buffs.stat_multiplier()
        self.base_intellect = self.stats.int + self.race.racial_int
        self.base_intellect *= self.buffs.stat_multiplier()

        self.relentless_strikes_energy_return_per_cp = 5 #.20 * 25
        
        #should only include bloodlust if the spec can average it in, deal with this later
        self.base_speed_multiplier = 1.4
        if self.race.berserking:
            self.true_haste_mod *= (1 + .15 * 10. / (180 + self.settings.response_time))
        self.true_haste_mod *= 1 + self.race.get_racial_haste() #doesn't include Berserking
        self.true_haste_mod *= self.buffs.haste_multiplier()
        if self.stats.gear_buffs.rogue_t14_4pc:
            self.true_haste_mod *= 1.05
                    
        #hit chances
        self.dw_mh_hit_chance = self.dual_wield_mh_hit_chance()
        self.dw_oh_hit_chance = self.dual_wield_oh_hit_chance()
    
    def load_from_advanced_parameters(self):
        self.true_haste_mod = self.get_adv_param('haste_buff', 1., min_bound=.1, max_bound=3.)
        
        self.major_cd_delay = self.get_adv_param('major_cd_delay', 0, min_bound=0, max_bound=600)
        self.settings.feint_interval = self.get_adv_param('feint_interval', self.settings.feint_interval, min_bound=0, max_bound=600)
        
        self.settings.is_day = self.get_adv_param('is_day', self.settings.is_day, ignore_bounds=True)
        self.get_version_number = self.get_adv_param('print_version', False, ignore_bounds=True)
    
    def get_proc_damage_contribution(self, proc, proc_count, current_stats, average_ap, damage_breakdown):
        crit_multiplier = self.crit_damage_modifiers()
        crit_rate = self.crit_rate(crit=current_stats['crit'])
        
        if proc.stat == 'spell_damage':
            multiplier = self.get_modifiers(current_stats, damage_type='spell')
        elif proc.stat == 'physical_damage':
            multiplier = self.get_modifiers(current_stats, damage_type='physical')
        elif proc.stat == 'physical_dot':
            multiplier = self.get_modifiers(current_stats, damage_type='bleed')
        elif proc.stat == 'bleed_damage':
            multiplier = self.get_modifiers(current_stats, damage_type='bleed')
        else:
            return 0

        if proc.can_crit == False:
            crit_rate = 0

        proc_value = proc.value
        #280+75% AP
        if proc is getattr(self.stats.procs, 'legendary_capacitive_meta'):
            crit_rate = self.crit_rate(crit=current_stats['crit'])
            proc_value = average_ap * 1.5 + 50
        
        if proc is getattr(self.stats.procs, 'fury_of_xuen'):
            crit_rate = self.crit_rate(crit=current_stats['crit'])
            proc_value = (average_ap * .40 + 1) * 10 * (1 + min(4., self.settings.num_boss_adds))

        if proc is getattr(self.stats.procs, 'mirror_of_the_blademaster'):
            crit_rate = self.crit_rate(crit=current_stats['crit'])
            # Each mirror produces 10 swings scaling with haste
            # There are 4 mirrors, 2 spawn in front of the get and are parryable
            # Each mirror swings a weapon with weapon damage based on 100% of AP
            haste_mult = self.stats.get_haste_multiplier_from_rating(current_stats['haste'])
            swings_per_mirror = 20.0/(2.0/haste_mult)
            total_swings = 2*swings_per_mirror + 2*(1.0-self.base_parry_chance)*swings_per_mirror
            proc_value = total_swings*(average_ap/3.5)

        average_hit = proc_value * multiplier
        average_damage = average_hit * (1 + crit_rate * (crit_multiplier - 1)) * proc_count
        #print proc.proc_name, average_hit, multiplier
        
        if proc.stat == 'physical_dot':
            average_damage *= proc.uptime / proc_count
        
        return average_damage

    def set_openers(self):
        # Sets the swing_reset_spacing and total_openers_per_second variables.
        opener_cd = [10, 20][self.settings.opener_name == 'garrote']
        if self.settings.is_subtlety_rogue():
            opener_cd = 30
        if self.settings.use_opener == 'always':
            opener_spacing = (self.get_spell_cd('vanish') + self.settings.response_time)
            total_openers_per_second = (1. + math.floor((self.settings.duration - opener_cd) / opener_spacing)) / self.settings.duration
        elif self.settings.use_opener == 'opener':
            total_openers_per_second = 1. / self.settings.duration
            opener_spacing = None
        else:
            total_openers_per_second = 0
            opener_spacing = None
        
        self.total_openers_per_second = total_openers_per_second
        self.swing_reset_spacing = opener_spacing

    def get_bonus_energy_from_openers(self, *cycle_abilities):
        if self.settings.opener_name not in cycle_abilities:
            # if not a normal rotational ability, it should cost the player energy
            return -1 * self.get_net_energy_cost(self.settings.opener_name) * self.get_shadow_focus_multiplier() * self.total_openers_per_second
        elif not self.talents.shadow_focus:
            # or a rotational ability and without SF then
            return 0
        else:
            # else, it's a rotational ability and we have SF, so we should add energy
            # this lets us save computational time in the aps methods
            return self.get_net_energy_cost(self.settings.opener_name) * (1 - self.get_shadow_focus_multiplier()) * self.total_openers_per_second
    
    def get_net_energy_cost(self, ability):
        return self.get_spell_stats(ability)[0]

    def get_mh_procs_per_second(self, proc, attacks_per_second, crit_rates):
        triggers_per_second = 0
        if proc.procs_off_auto_attacks():
            if proc.procs_off_crit_only():
                if 'mh_autoattacks' in attacks_per_second:
                    triggers_per_second += attacks_per_second['mh_autoattacks'] * crit_rates['mh_autoattacks']
            else:
                if 'mh_autoattack_hits' in attacks_per_second:
                    triggers_per_second += attacks_per_second['mh_autoattack_hits']
        if proc.procs_off_strikes():
            for ability in ('mutilate', 'dispatch', 'backstab', 'revealing_strike', 'sinister_strike', 'ambush', 'hemorrhage', 'mh_killing_spree', 'shuriken_toss'):
                if ability in attacks_per_second:
                    if proc.procs_off_crit_only():
                        triggers_per_second += attacks_per_second[ability] * crit_rates[ability]
                    else:
                        triggers_per_second += attacks_per_second[ability]
            for ability in ('envenom', 'eviscerate'):
                if ability in attacks_per_second:
                    if proc.procs_off_crit_only():
                        triggers_per_second += sum(attacks_per_second[ability]) * crit_rates[ability]
                    else:
                        triggers_per_second += sum(attacks_per_second[ability])
        if proc.procs_off_apply_debuff() and not proc.procs_off_crit_only():
            if 'rupture' in attacks_per_second:
                triggers_per_second += attacks_per_second['rupture']
            if 'garrote' in attacks_per_second:
                triggers_per_second += attacks_per_second['garrote']
            if 'hemorrhage_ticks' in attacks_per_second:
                triggers_per_second += attacks_per_second['hemorrhage']
        return triggers_per_second * proc.get_proc_rate(self.stats.mh.speed)

    def get_oh_procs_per_second(self, proc, attacks_per_second, crit_rates):
        triggers_per_second = 0
        if proc.procs_off_auto_attacks():
            if proc.procs_off_crit_only():
                if 'oh_autoattacks' in attacks_per_second:
                    triggers_per_second += attacks_per_second['oh_autoattacks'] * crit_rates['oh_autoattacks']
            else:
                if 'oh_autoattack_hits' in attacks_per_second:
                    triggers_per_second += attacks_per_second['oh_autoattack_hits']
        if proc.procs_off_strikes():
            for ability in ('mutilate', 'oh_killing_spree'):
                if ability in attacks_per_second:
                    if proc.procs_off_crit_only():
                        triggers_per_second += attacks_per_second[ability] * crit_rates[ability]
                    else:
                        triggers_per_second += attacks_per_second[ability]
        return triggers_per_second * proc.get_proc_rate(self.stats.oh.speed)

    def get_other_procs_per_second(self, proc, attacks_per_second, crit_rates):
        triggers_per_second = 0
        if proc.procs_off_harmful_spells():
            for ability in ('deadly_instant_poison', 'wound_poison', 'venomous_wounds'):
                if ability in attacks_per_second:
                    if proc.procs_off_crit_only():
                        triggers_per_second += attacks_per_second[ability] * crit_rates[ability]
                    else:
                        triggers_per_second += attacks_per_second[ability]
        if proc.procs_off_periodic_spell_damage():
            if 'deadly_poison' in attacks_per_second:
                if proc.procs_off_crit_only():
                    triggers_per_second += attacks_per_second['deadly_poison'] * crit_rates['deadly_poison']
                else:
                    triggers_per_second += attacks_per_second['deadly_poison']
        if proc.procs_off_bleeds():
            if 'rupture_ticks' in attacks_per_second:
                if proc.procs_off_crit_only():
                    triggers_per_second += sum(attacks_per_second['rupture_ticks']) * crit_rates['rupture']
                else:
                    triggers_per_second += sum(attacks_per_second['rupture_ticks'])
            if 'garrote_ticks' in attacks_per_second:
                if proc.procs_off_crit_only():
                    triggers_per_second += attacks_per_second['garrote_ticks'] * crit_rates['garrote']
                else:
                    triggers_per_second += attacks_per_second['garrote_ticks']
            if 'hemorrhage_ticks' in attacks_per_second and not proc.procs_off_crit_only():
                triggers_per_second += attacks_per_second['hemorrhage_ticks']
        if proc.is_ppm():
            if triggers_per_second == 0:
                return 0
            else:
                raise InputNotModeledException(_('PPMs that also proc off spells are not yet modeled.'))
        else:
            return triggers_per_second * proc.get_proc_rate()

    def get_procs_per_second(self, proc, attacks_per_second, crit_rates):
        # TODO: Include damaging proc hits in figuring out how often everything else procs.
        if getattr(proc, 'mh_only', False):
            procs_per_second = self.get_mh_procs_per_second(proc, attacks_per_second, crit_rates)
        elif getattr(proc, 'oh_only', False):
            procs_per_second = self.get_oh_procs_per_second(proc, attacks_per_second, crit_rates)
        else:
            procs_per_second = self.get_mh_procs_per_second(proc, attacks_per_second, crit_rates)
            procs_per_second += self.get_oh_procs_per_second(proc, attacks_per_second, crit_rates)
            procs_per_second += self.get_other_procs_per_second(proc, attacks_per_second, crit_rates)
        return procs_per_second
    
    def lost_swings_from_swing_delay(self, delay, swing_timer):
        # delay = swing delay = s (see: graphs)
        # swing timer = x (see: graphs)
        delay_remainder = delay % .5        #m
        num_sum = min(swing_timer, delay)   #n
        
        #TODO: Wiki Documentation explaining swing delay calculations
        #OLD SWING DELAY METHODS: delay//swing_timer + (delay%swing_timer)/swing_timer
        #                       : delay/swing_timer
        #                       : OH is the same value but 1 lower
            
        t0 = max(min( delay_remainder/swing_timer*1.5, 1.5 ),                  0)
        t1 = max(min( num_sum - delay_remainder,        .5 )/swing_timer,      0)
        t2 = max(min( num_sum - delay_remainder - .5,   .5 )/swing_timer * .5, 0)
        
        #print "total delay: ", t0, t1, t2, (t0+t1+t2)
        return (t0+t1+t2)/swing_timer
    
    def set_uptime_for_ramping_proc(self, proc, procs_per_second):
        time_for_one_stack = 1 / procs_per_second
        if time_for_one_stack * proc.max_stacks > self.settings.duration:
            max_stacks_reached = self.settings.duration * procs_per_second
            proc.uptime = max_stacks_reached / 2
        else:
            missing_stacks = proc.max_stacks * (proc.max_stacks + 1) / 2
            stack_time_lost = missing_stacks * time_for_one_stack
            proc.uptime = proc.max_stacks - stack_time_lost / self.settings.duration

    def update_with_damaging_proc(self, proc, attacks_per_second, crit_rates):
        if proc.is_real_ppm():
            #http://us.battle.net/wow/en/forum/topic/8197741003?page=4#79
            haste = 1.
            if proc.haste_scales:
                haste *= self.true_haste_mod * self.stats.get_haste_multiplier_from_rating(self.base_stats['haste'])
            if proc.att_spd_scales:
                haste *= 1.4
            #The 1.1307 is a value that increases the proc rate due to bad luck prevention. It /should/ be constant among all rppm proc styles
            if not proc.icd:
                frequency = haste * 1.1307 * proc.get_rppm_proc_rate() / 60
            else:
                mean_proc_time = 60. / (haste * proc.get_rppm_proc_rate()) + proc.icd - min(proc.icd, 10)
                if proc.max_stacks > 1: # just correct if you only do damage on max_stacks, e.g. legendary_capacitive_meta
                    mean_proc_time *= proc.max_stacks
                frequency = 1.1307 / mean_proc_time
        else:
            if proc.icd:
                frequency = 1. / (proc.icd + 0.5 / self.get_procs_per_second(proc, attacks_per_second, crit_rates))
            else:
                frequency = self.get_procs_per_second(proc, attacks_per_second, crit_rates)
        
        if proc.proc_name in attacks_per_second:
            attacks_per_second[proc.proc_name] += frequency
        else:
            attacks_per_second[proc.proc_name] = frequency

    def get_shadow_focus_multiplier(self):
        if self.talents.shadow_focus:
            return (1 - .75)
        return 1.

    def setup_unique_procs(self, current_stats, average_ap):
        if self.stats.procs.rocket_barrage:
            getattr(self.stats.procs, 'rocket_barrage').value = 0.42900 * self.base_intellect + .5 * average_ap + 1 + self.level * 2 #need to update
        if self.stats.procs.touch_of_the_grave:
            getattr(self.stats.procs, 'touch_of_the_grave').value = 8 * self.tools.get_constant_scaling_point(self.level) # +/- 15% spread

    def get_poison_counts(self, attacks_per_second, current_stats):
        # Builds a phony 'poison' proc object to count triggers through the proc
        # methods.
        poison = procs.Proc(**proc_data.allowed_procs['rogue_poison'])
        mh_hits_per_second = self.get_mh_procs_per_second(poison, attacks_per_second, None)
        oh_hits_per_second = self.get_oh_procs_per_second(poison, attacks_per_second, None)
        total_hits_per_second = mh_hits_per_second + oh_hits_per_second
        if poison:
            poison_base_proc_rate = .3
        else:
            return
        proc_multiplier = 1
        if self.settings.is_combat_rogue():
            if self.settings.cycle.blade_flurry:
                ms_value = 1 + min(2 * (self.stats.get_multistrike_chance_from_rating(rating=current_stats['multistrike']) + self.buffs.multistrike_bonus()), 2)
                proc_multiplier += min(self.settings.num_boss_adds, [4, 999][self.level==100]) * ms_value

        if self.settings.is_assassination_rogue():
            poison_base_proc_rate += .2
            poison_envenom_proc_rate = poison_base_proc_rate + .3
            aps_envenom = attacks_per_second['envenom']
            if self.talents.death_from_above: 
                aps_envenom = map(add, attacks_per_second['death_from_above_strike'], attacks_per_second['envenom'])
            envenom_uptime = min(sum([(1 + cps + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp()) * aps_envenom[cps] for cps in xrange(1, 6)]), 1)
            avg_poison_proc_rate = poison_base_proc_rate * (1 - envenom_uptime) + poison_envenom_proc_rate * envenom_uptime
        else:
            avg_poison_proc_rate = poison_base_proc_rate
        
        if self.settings.dmg_poison == 'sp':
            poison_procs = avg_poison_proc_rate * total_hits_per_second * proc_multiplier - 1 / self.settings.duration
            attacks_per_second['swift_poison'] = poison_procs
        elif self.settings.dmg_poison == 'dp':
            poison_procs = avg_poison_proc_rate * total_hits_per_second * proc_multiplier - 1 / self.settings.duration
            attacks_per_second['deadly_instant_poison'] = poison_procs
            attacks_per_second['deadly_poison'] = 1. / 3  * proc_multiplier
        elif self.settings.dmg_poison == 'wp':
            attacks_per_second['wound_poison'] = total_hits_per_second * avg_poison_proc_rate

    def determine_stats(self, attack_counts_function):
        current_stats = {
            'str': self.base_strength,
            'agi': self.base_stats['agi'] * self.stat_multipliers['agi'],
            'ap': self.base_stats['ap'] * self.stat_multipliers['ap'],
            'crit': self.base_stats['crit'] * self.stat_multipliers['crit'],
            'haste': self.base_stats['haste'] * self.stat_multipliers['haste'],
            'mastery': self.base_stats['mastery'] * self.stat_multipliers['mastery'],
            'readiness': self.base_stats['readiness'] * self.stat_multipliers['readiness'],
            'multistrike': self.base_stats['multistrike'] * self.stat_multipliers['multistrike'],
            'versatility': self.base_stats['versatility'] * self.stat_multipliers['versatility'],
        }
        self.current_variables = {}
        
        #arrys to store different types of procs
        active_procs_rppm_stat_mods = []
        active_procs_rppm = []
        active_procs_icd = []
        active_procs_no_icd = []
        damage_procs = []
        weapon_damage_procs = []
        
        shatt_hand = 0
        for hand in ('mh', 'oh'):
            if getattr(getattr(self.stats, hand), 'mark_of_the_shattered_hand'):
                self.stats.procs.set_proc('mark_of_the_shattered_hand_dot') #this enables the proc if it's not active, doesn't duplicate
                shatt_hand += 1
        if shatt_hand > 0:
            if shatt_hand > 1:
                getattr(self.stats.procs, 'mark_of_the_shattered_hand_dot').proc_rate = 5
            else:
                getattr(self.stats.procs, 'mark_of_the_shattered_hand_dot').proc_rate = 2.5
            self.set_rppm_uptime(getattr(self.stats.procs, 'mark_of_the_shattered_hand_dot'))
        if not shatt_hand:
            self.stats.procs.del_proc('mark_of_the_shattered_hand_dot')
        
        #sort the procs into groups
        for proc in self.stats.procs.get_all_procs_for_stat():
            if (proc.stat == 'stats'):
                if proc.is_real_ppm():
                    active_procs_rppm.append(proc)
                else:
                    if proc.icd:
                        active_procs_icd.append(proc)
                    else:
                        active_procs_no_icd.append(proc)
            elif proc.stat == 'stats_modifier':
                active_procs_rppm_stat_mods.append(proc)
            elif proc.stat in ('spell_damage', 'physical_damage', 'physical_dot'):
                damage_procs.append(proc)
            elif proc.stat == 'extra_weapon_damage':
                weapon_damage_procs.append(proc)
        
        #calculate weapon procs
        weapon_enchants = set([])
        for hand, enchant in [(x, y) for x in ('mh', 'oh') for y in ('dancing_steel', 'mark_of_the_frostwolf',
                                                                     'mark_of_the_shattered_hand', 'mark_of_the_thunderlord',
                                                                     'mark_of_the_bleeding_hollow', 'mark_of_warsong')]:
            proc = getattr(getattr(self.stats, hand), enchant)
            if proc:
                setattr(proc, '_'.join((hand, 'only')), True)
                if (proc.stat in current_stats or proc.stat == 'stats'):
                    if proc.is_real_ppm():
                        active_procs_rppm.append(proc)
                    else:
                        if proc.icd:
                            active_procs_icd.append(proc)
                        else:
                            active_procs_no_icd.append(proc)
                elif enchant in ('mark_of_the_shattered_hand', ):
                    damage_procs.append(proc)
        
        static_proc_stats = {
            'str': 0,
            'agi': 0,
            'ap': 0,
            'crit': 0,
            'haste': 0,
            'mastery': 0,
            'readiness': 0,
            'multistrike': 0,
            'versatility': 0,
        }
        
        for proc in active_procs_rppm_stat_mods:
            self.set_rppm_uptime(proc)
            for e in proc.value:
                self.stat_multipliers[e] *= 1 + proc.uptime * proc.value[e]
                current_stats[e] *= 1 + proc.uptime * proc.value[e]

        for proc in active_procs_rppm:
            if proc.stat == 'stats':
                self.set_rppm_uptime(proc)
                for e in proc.value:
                    static_proc_stats[ e ] += proc.uptime * proc.value[e] * self.stat_multipliers[e]
        
        for k in static_proc_stats:
            current_stats[k] +=  static_proc_stats[ k ]
        
        attacks_per_second, crit_rates, additional_info = attack_counts_function(current_stats)
        recalculate_crit = False
        
        #check need to converge
        need_converge = False
        convergence_stats = False
        if len(active_procs_no_icd) > 0:
            need_converge = True
        while (need_converge or self.spec_needs_converge):
            current_stats = {
                'str': self.base_strength,
                'agi': self.base_stats['agi'] * self.stat_multipliers['agi'],
                'ap': self.base_stats['ap'] * self.stat_multipliers['ap'],
                'crit': self.base_stats['crit'] * self.stat_multipliers['crit'],
                'haste': self.base_stats['haste'] * self.stat_multipliers['haste'],
                'mastery': self.base_stats['mastery'] * self.stat_multipliers['mastery'],
                'readiness': self.base_stats['readiness'] * self.stat_multipliers['readiness'],
                'multistrike': self.base_stats['multistrike'] * self.stat_multipliers['multistrike'],
                'versatility': self.base_stats['versatility'] * self.stat_multipliers['versatility'],
            }
            for k in static_proc_stats:
                current_stats[k] +=  static_proc_stats[k]
                
            for proc in active_procs_no_icd:
                self.set_uptime(proc, attacks_per_second, crit_rates)
                for e in proc.value:
                    if e in self.spec_convergence_stats:
                        convergence_stats = True
                    if e == 'crit':
                        recalculate_crit = True
                    current_stats[ e ] += proc.uptime * proc.value[e] * self.stat_multipliers[e]
            
            #only have to converge with specific procs
            #check if... assassination:crit/haste, combat:mastery/haste, sub:haste/mastery
            if not convergence_stats and not self.spec_needs_converge:
                break
            
            old_attacks_per_second = attacks_per_second
            if recalculate_crit:
                crit_rates = None
                recalculate_crit = False
            attacks_per_second, crit_rates, additional_info = attack_counts_function(current_stats, crit_rates=crit_rates)
            
            if self.are_close_enough(old_attacks_per_second, attacks_per_second):
                break
            
        for proc in active_procs_icd:
            self.set_uptime(proc, attacks_per_second, crit_rates)
            for e in proc.value:
                if e == 'crit':
                    recalculate_crit = True
                current_stats[ e ] += proc.uptime * proc.value[e] * self.stat_multipliers[e]
        
        #if no new stats are added, skip this step
        if len(active_procs_icd) > 0 or self.spec_needs_converge:
            if recalculate_crit:
                crit_rates = None
            attacks_per_second, crit_rates, additional_info = attack_counts_function(current_stats, crit_rates=crit_rates)

        # the t16 4pc do not need to be in the main loop because mastery for assa is just increased damage
        # and has no impact on the cycle
        if self.stats.gear_buffs.rogue_t16_4pc_bonus() and self.settings.is_assassination_rogue():
            #20 stacks of 250 mastery, lasts 5 seconds
            mas_per_stack = 38.
            max_stacks = 20.
            buff_duration = 5.
            extra_duration = buff_duration - self.settings.response_time
            ability_aps = 0
            mutilate_aps = 0
            for key in ('mutilate', 'dispatch', 'envenom'):
                if key in attacks_per_second:
                    if key in ('envenom'):
                        ability_aps += sum(attacks_per_second[key])
                    elif key == 'mutilate':
                        ability_aps += attacks_per_second[key]
                        mutilate_aps += attacks_per_second[key]
                    else:
                        ability_aps += attacks_per_second[key]
            attack_spacing = 1 / ability_aps
            # mutilate gives 2 stacks, so it needs to be included
            avg_stacks_per_attack = 1 + mutilate_aps / ability_aps
            res = 0.
            if attack_spacing < 5:
                time_to_max = max_stacks * attack_spacing / avg_stacks_per_attack
                time_at_max = max(0., self.vendetta_duration - time_to_max)
                max_stacks_able_to_reach = min(self.vendetta_duration / attack_spacing, max_stacks)
                avg_stacks = max_stacks_able_to_reach / 2
                avg = time_to_max * avg_stacks + time_at_max * max_stacks + extra_duration * max_stacks_able_to_reach
                res = avg * mas_per_stack / self.get_spell_cd('vendetta')
            else:
                uptime = buff_duration / attack_spacing
                res = self.vendetta_duration * uptime * mas_per_stack * avg_stacks_per_attack / self.get_spell_cd('vendetta')
            current_stats['mastery'] += res
        
        #some procs need specific prep, think RoRO/VoS
        self.setup_unique_procs(current_stats, current_stats['agi']+current_stats['ap'])
        
        for proc in damage_procs:
            self.update_with_damaging_proc(proc, attacks_per_second, crit_rates)
        
        for proc in weapon_damage_procs:
            self.set_uptime(proc, attacks_per_second, crit_rates)
        return current_stats, attacks_per_second, crit_rates, damage_procs, additional_info
    
    def compute_damage_from_aps(self, current_stats, attacks_per_second, crit_rates, damage_procs, additional_info):
        # this method exists solely to let us use cached values you would get from determine stats
        # really only useful for combat calculations (restless blades calculations)
        damage_breakdown, additional_info = self.get_damage_breakdown(current_stats, attacks_per_second, crit_rates, damage_procs, additional_info)
        return damage_breakdown, additional_info
    
    def compute_damage(self, attack_counts_function):
        current_stats, attacks_per_second, crit_rates, damage_procs, additional_info = self.determine_stats(attack_counts_function)
        damage_breakdown, additional_info = self.get_damage_breakdown(current_stats, attacks_per_second, crit_rates, damage_procs, additional_info)
        #damage_breakdown, additional_info = self.get_damage_breakdown(self.determine_stats(attack_counts_function))
        return damage_breakdown, additional_info
        
    ###########################################################################
    # Assassination DPS functions
    ###########################################################################

    def init_assassination(self):
        # Call this before calling any of the assassination_dps functions
        # directly.  If you're just calling get_dps, you can ignore this as it
        # happens automatically; however, if you're going to pull a damage
        # breakdown or other sub-result, make sure to call this, as it
        # initializes many values that are needed to perform the calculations.

        if not self.settings.is_assassination_rogue():
            raise InputNotModeledException(_('You must specify an assassination cycle to match your assassination spec.'))
        if self.stats.mh.type != 'dagger' or self.stats.oh.type != 'dagger':
            raise InputNotModeledException(_('Assassination modeling requires daggers in both hands'))
        
        #set readiness coefficient
        self.readiness_spec_conversion = self.assassination_readiness_conversion
        self.spec_convergence_stats = ['haste', 'crit', 'readiness']
        
        # Assassasins's Resolve
        self.damage_modifier_cache = 1.17
        
        #update spec specific proc rates
        if getattr(self.stats.procs, 'legendary_capacitive_meta'):
            getattr(self.stats.procs, 'legendary_capacitive_meta').proc_rate_modifier = 1.789
        if getattr(self.stats.procs, 'fury_of_xuen'):
            getattr(self.stats.procs, 'fury_of_xuen').proc_rate_modifier = 1.55
            
        #spec specific glyph behaviour
        if self.glyphs.disappearance:
            self.ability_cds['vanish'] = 60
        else:
            self.ability_cds['vanish'] = 120
        
        self.base_energy_regen = 10
        self.max_energy = 120.
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            self.max_energy += 30
        if self.talents.lemon_zest:
            self.base_energy_regen *= 1 + .05 * (1 + min(self.settings.num_boss_adds, 2))
            self.max_energy += 15
        if self.glyphs.energy:
            self.max_energy += 20
        if self.race.expansive_mind:
            self.max_energy = round(self.max_energy * 1.05, 0)
            
        self.set_constants()
        self.stat_multipliers['mastery'] *= 1.05

        if getattr(self.stats.procs, 'bleeding_hollow_toxin_vessel'):
            spec_needs_converge = True
        self.envenom_crit_modifier = 0.0

        self.vendetta_duration = 20 + 10 * self.glyphs.vendetta
        self.vendetta_uptime = self.vendetta_duration / (self.get_spell_cd('vendetta') + self.settings.response_time + self.major_cd_delay)
        self.vendetta_multiplier = .3 - .05 * self.glyphs.vendetta
        self.vendetta_mult = 1 + self.vendetta_multiplier * self.vendetta_uptime

    def assassination_dps_estimate(self):
        non_execute_dps = self.assassination_dps_estimate_non_execute() * (1 - self.settings.time_in_execute_range)
        execute_dps = self.assassination_dps_estimate_execute() * self.settings.time_in_execute_range
        return non_execute_dps + execute_dps

    def assassination_dps_estimate_execute(self):
        return sum(self.assassination_dps_breakdown_execute().values())

    def assassination_dps_estimate_non_execute(self):
        return sum(self.assassination_dps_breakdown_non_execute().values())

    def assassination_dps_breakdown(self):
        non_execute_dps_breakdown = self.assassination_dps_breakdown_non_execute()
        execute_dps_breakdown = self.assassination_dps_breakdown_execute()

        non_execute_weight = 1 - self.settings.time_in_execute_range
        execute_weight = self.settings.time_in_execute_range

        dps_breakdown = {}
        for source, quantity in non_execute_dps_breakdown.items():
            dps_breakdown[source] = quantity * non_execute_weight

        for source, quantity in execute_dps_breakdown.items():
            if source in dps_breakdown:
                dps_breakdown[source] += quantity * execute_weight
            else:
                dps_breakdown[source] = quantity * execute_weight
                
        return dps_breakdown

    def update_assassination_breakdown_with_modifiers(self, damage_breakdown, current_stats):
        #calculate multistrike here for Sub and Assassination, really cheap to calculate
        #turns out the 2 chance system yields a very basic linear pattern, the damage modifier is 30% of the multistrike %!
        multistrike_multiplier = .3 * 2 * (self.stats.get_multistrike_chance_from_rating(rating=current_stats['multistrike']) + self.buffs.multistrike_bonus())
        multistrike_multiplier = min(.6, multistrike_multiplier)
        
        soul_cap_mod = 1.0
        if getattr(self.stats.procs, 'soul_capacitor'):
            soul_cap= getattr(self.stats.procs, 'soul_capacitor')
            self.set_rppm_uptime(soul_cap)
            soul_cap_mod = 1+(soul_cap.uptime * soul_cap.value['damage_mod']/10000)

        for key in damage_breakdown:
            damage_breakdown[key] *= 1 + multistrike_multiplier
            if ('sr_' not in key):
                damage_breakdown[key] *= self.vendetta_mult
                damage_breakdown[key] *= soul_cap_mod
            elif 'sr_' in key:
                damage_breakdown[key] *= 1 + self.vendetta_multiplier
            if self.level == 100 and key in ('mutilate', 'dispatch', 'sr_mutilate', 'sr_mh_mutilate', 'sr_oh_mutilate', 'sr_dispatch'):
                damage_breakdown[key] *= self.emp_envenom_percentage
            if self.stats.gear_buffs.rogue_t18_2pc: 
                if key == 'dispatch':
                    damage_breakdown[key]*= 1+(0.25 * (1+(self.stats.get_mastery_from_rating(rating=current_stats['mastery'])*self.assassination_mastery_conversion)))

    def assassination_dps_breakdown_non_execute(self):
        #damage_breakdown, additional_info = self.compute_damage(self.assassination_attack_counts_non_execute)
        current_stats, attacks_per_second, crit_rates, damage_procs, additional_info = self.determine_stats(self.assassination_attack_counts_non_execute)
        damage_breakdown, additional_info = self.get_damage_breakdown(current_stats, attacks_per_second, crit_rates, damage_procs, additional_info)
        
        self.update_assassination_breakdown_with_modifiers(damage_breakdown, current_stats)
        return damage_breakdown

    def assassination_dps_breakdown_execute(self):
        #damage_breakdown, additional_info = self.compute_damage(self.assassination_attack_counts_execute)
        current_stats, attacks_per_second, crit_rates, damage_procs, additional_info = self.determine_stats(self.assassination_attack_counts_execute)
        damage_breakdown, additional_info = self.get_damage_breakdown(current_stats, attacks_per_second, crit_rates, damage_procs, additional_info)
        
        self.update_assassination_breakdown_with_modifiers(damage_breakdown, current_stats)
        return damage_breakdown
    
    def assassination_cp_distribution_for_finisher(self, current_cp, crit_rates, ability_count, size_breakdown, cp_limit=4, blindside_proc=0, execute=False):
        current_sizes = copy(size_breakdown)
        if (current_cp >= cp_limit and not blindside_proc and not execute) or current_cp >= 5:
            final_cp = min(current_cp, 5)
            current_sizes[final_cp] += 1
            return final_cp, blindside_proc, ability_count, current_sizes
        avg_count = {'mutilate':0, 'dispatch':0}
        avg_breakdown = [0,0,0,0,0,0]
        new_count = copy(ability_count)
        
        if blindside_proc or execute:
            new_count['dispatch'] += 1
            
            n_chance = 1 - crit_rates['dispatch']
            n_value, n_proc, n_count, n_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+1, crit_rates, new_count, current_sizes, cp_limit=cp_limit, execute=execute)
            if self.stats.gear_buffs.rogue_t18_4pc:
                n_value, n_proc, n_count, n_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+3, crit_rates, new_count, current_sizes, cp_limit=cp_limit, execute=execute)
            c_chance = crit_rates['dispatch']
            c_value, c_proc, c_count, c_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+2, crit_rates, new_count, current_sizes, cp_limit=cp_limit, execute=execute)
            if self.stats.gear_buffs.rogue_t18_4pc:
                c_value, c_proc, c_count, c_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+4, crit_rates, new_count, current_sizes, cp_limit=cp_limit, execute=execute)
            
            avg_cp = n_chance*n_value + c_chance*c_value
            avg_bs_afterwards = n_chance*n_proc + c_chance*c_proc
            for key in new_count:
                avg_count[key] = n_chance*n_count[key] + c_chance*c_count[key]
            for i in xrange(1, 6):
                avg_breakdown[i] = n_chance*n_breakdown[i] + c_chance*c_breakdown[i]
            return avg_cp, avg_bs_afterwards, avg_count, avg_breakdown
        else:
            bs_proc_rate = .3
            new_count['mutilate'] += 1
            
            n_chance = ((1 - crit_rates['mutilate']) ** 2)  * (1-bs_proc_rate)
            n_value, n_proc, n_count, n_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+2, crit_rates, new_count, current_sizes, cp_limit=cp_limit)
            n_bs_chance = ((1 - crit_rates['mutilate']) ** 2)  * bs_proc_rate
            n_bs_value, n_bs_proc, n_bs_count, n_bs_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+2, crit_rates, new_count, current_sizes, cp_limit=cp_limit, blindside_proc=1.)
            
            c_chance = (1 - (1 - crit_rates['mutilate']) ** 2)  * (1-bs_proc_rate)
            c_value, c_proc, c_count, c_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+3, crit_rates, new_count, current_sizes, cp_limit=cp_limit)
            c_bs_chance = (1 - (1 - crit_rates['mutilate']) ** 2)  * bs_proc_rate
            c_bs_value, c_bs_proc, c_bs_count, c_bs_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+3, crit_rates, new_count, current_sizes, cp_limit=cp_limit, blindside_proc=1.)
            
            avg_cp = n_chance*n_value + n_bs_chance*n_bs_value + c_chance*c_value + c_bs_chance*c_bs_value
            avg_bs_afterwards = n_chance*n_proc + n_bs_chance*n_bs_proc + c_chance*c_proc + c_bs_chance*c_bs_proc
            for key in new_count:
                avg_count[key] = n_chance*n_count[key] + n_bs_chance*n_bs_count[key] + c_chance*c_count[key] + c_bs_chance*c_bs_count[key]
            for i in xrange(1, 6):
                avg_breakdown[i] = n_chance*n_breakdown[i] + n_bs_chance*n_bs_breakdown[i] + c_chance*c_breakdown[i] + c_bs_chance*c_bs_breakdown[i]
            return avg_cp, avg_bs_afterwards, avg_count, avg_breakdown
    
    def assassination_attack_counts(self, current_stats, cpg, finisher_size, crit_rates=None):
        attacks_per_second = {}
        additional_info = {}
        #can't rely on a cache, due to the Cold Blood perk
        crit_rates = self.get_crit_rates(current_stats)
        for key in crit_rates:
            if key in ('mutilate', 'dispatch'):
                crit_rates[key]+=self.envenom_crit_modifier
                crit_rates[key] = min(crit_rates[key], 1.0)

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod
        ability_cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_reduced_cost()
        
        energy_regen = self.base_energy_regen * haste_multiplier
        if self.stats.gear_buffs.rogue_t17_4pc_lfr:
            #http://www.wolframalpha.com/input/?i=1.1307+*+%281+-+e+**+%28-1+*+1.1+*+6%2F+60%29%29
            #https://twitter.com/Celestalon/status/525350819856535552
            energy_regen *= 1 + (.11778034322021550695 * .3) #11% uptime on 30% boost)
        energy_regen += self.bonus_energy_regen
        if cpg == 'dispatch':
            #this is for the effects of pooling going into execute phase
            energy_regen += (self.max_energy - 10) / (self.settings.duration * self.settings.time_in_execute_range)

        vw_energy_return = 10
        vw_energy_per_bleed_tick = vw_energy_return
        
        blindside_proc_rate = [0, .3][cpg == 'mutilate']
        attacks_per_second['envenom'] = [0,0,0,0,0,0]
        attacks_per_second['dispatch'] = 0
        
        if self.talents.marked_for_death:
            energy_regen -= 10. / self.get_spell_cd('marked_for_death') # 35-25
        
        attack_speed_multiplier = self.base_speed_multiplier * haste_multiplier
        self.attack_speed_increase = attack_speed_multiplier
        
        seal_fate_proc_rate = crit_rates['dispatch']
        if cpg == 'mutilate':
            seal_fate_proc_rate *= blindside_proc_rate
            seal_fate_proc_rate += 1 - (1 - crit_rates['mutilate']) ** 2
        
        mutilate_cps = 3 - (1 - crit_rates['mutilate']) ** 2 # 1 - (1 - crit_rates['mutilate']) ** 2 is the Seal Fate CP
        dispatch_cps = 1 + crit_rates['dispatch']
        if self.stats.gear_buffs.rogue_t18_4pc:
            dispatch_cps += 2
        
        if self.talents.anticipation:
            avg_finisher_size = 5
            avg_size_breakdown = [0,0,0,0,0,1.] #this is for determining the % likelyhood of sizes, not frequency of the sizes
            cp_needed_per_finisher = 5
            if self.stats.gear_buffs.rogue_t17_4pc:
                cp_needed_per_finisher -= 1
            
            if cpg == 'mutilate':
                avg_cp_per_cpg = mutilate_cps + dispatch_cps * blindside_proc_rate
            else:
                avg_cp_per_cpg = dispatch_cps
            
            avg_cpgs_per_finisher = cp_needed_per_finisher / avg_cp_per_cpg
        else:
            ability_count = {'mutilate':0, 'dispatch':0}
            finisher_size_breakdown = [0,0,0,0,0,0]
            
            #This is incredibly verbose, but functional. It exhaustively calculates the potential finisher size outcomes using recursion.
            #avg_finisher_size - measures average finisher size
            #avg_bs_afterwards - likelyhood of finishing with a blindside proc active
            #avg_count - number of ability casts per finisher (dictionary of both Mutilate and Dispatch)
            #avg_breakdown - frequency of finisher sizes (should sum to 100% or 1)
            execute = False
            base_cp = 0
            min_finisher_size = self.settings.cycle.min_envenom_size_non_execute
            if cpg == 'dispatch':
                min_finisher_size = self.settings.cycle.min_envenom_size_execute
                execute = True
            if self.stats.gear_buffs.rogue_t17_4pc:
                base_cp = 1
            avg_finisher_size, avg_bs, avg_count, avg_size_breakdown  = self.assassination_cp_distribution_for_finisher(base_cp, crit_rates,
                                                                        ability_count, finisher_size_breakdown, cp_limit=min_finisher_size, execute=execute)
            if avg_bs > 0:
                mut_start_chance = 1/(1+avg_bs)
                bs_start_chance = 1 - mut_start_chance
                extra_tuple = self.assassination_cp_distribution_for_finisher(base_cp, crit_rates, ability_count, finisher_size_breakdown, cp_limit=4, blindside_proc=1)
                
                avg_finisher_size = avg_finisher_size*mut_start_chance + extra_tuple[0]*bs_start_chance
                for key in ability_count:
                    avg_count[key] = avg_count[key]*mut_start_chance + extra_tuple[2][key]*bs_start_chance
                for i in xrange(1,6):
                    avg_size_breakdown[i] = avg_size_breakdown[i]*mut_start_chance + extra_tuple[3][i]*bs_start_chance
            
            avg_cpgs_per_finisher = avg_count[cpg]
            avg_cp_per_cpg = avg_finisher_size / avg_cpgs_per_finisher
        
        cpg_energy_cost = self.get_spell_stats(cpg, cost_mod=ability_cost_modifier)[0]
        cpg_cost_reduction = 0
        if self.stats.gear_buffs.rogue_t17_2pc:
            cpg_cost_reduction = 14 * crit_rates['mutilate'] #7 per hand, double crit is 2 procs
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            cpg_cost_reduction = 6 * seal_fate_proc_rate
        cpg_energy_cost -= cpg_cost_reduction
            
        current_opener_name = self.settings.opener_name
        if self.settings.opener_name == 'cpg':
            current_opener_name = cpg
            
        cp_generated = 0
        if current_opener_name == 'envenom':
            opener_net_cost = self.get_spell_stats('envenom', cost_mod=ability_cost_modifier*(1-self.get_shadow_focus_multiplier()))[0]
            energy_regen += opener_net_cost * self.total_openers_per_second
        elif current_opener_name == cpg:
            opener_net_cost = self.get_spell_stats(current_opener_name, cost_mod=(1-self.get_shadow_focus_multiplier()))[0]
            opener_net_cost += cpg_cost_reduction
            cp_generated = avg_cp_per_cpg
            energy_regen += opener_net_cost * self.total_openers_per_second
        else:
            opener_net_cost = self.get_spell_stats(current_opener_name, cost_mod=self.get_shadow_focus_multiplier())[0]
            attacks_per_second[current_opener_name] = self.total_openers_per_second
            if current_opener_name == 'mutilate':
                attacks_per_second['dispatch'] += self.total_openers_per_second * blindside_proc_rate
            if current_opener_name in ('mutilate', 'dispatch', 'cpg'):
                cp_generated = mutilate_cps + dispatch_cps * blindside_proc_rate
            elif current_opener_name == 'ambush':
                cp_generated = 2 + crit_rates['ambush']
            energy_regen -= opener_net_cost * self.total_openers_per_second
        for i in xrange(1,6):
            attacks_per_second['envenom'][i] = self.total_openers_per_second * cp_generated / i * avg_size_breakdown[i]
        
        attacks_per_second['venomous_wounds'] = .5
        energy_regen_with_rupture = energy_regen + .5 * vw_energy_return
        
        avg_cycle_length = 4. * (1 + avg_finisher_size + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())
            
        energy_for_rupture = avg_cpgs_per_finisher * cpg_energy_cost + self.get_spell_stats('rupture', cost_mod=ability_cost_modifier)[0]
        energy_for_rupture -= avg_finisher_size * self.relentless_strikes_energy_return_per_cp
        
        attacks_per_second['rupture'] = 1. / avg_cycle_length
        energy_per_cycle = avg_cycle_length * energy_regen_with_rupture
        
        energy_for_dfa = 0        
        if self.talents.death_from_above:
            dfa_cd = self.get_spell_cd('death_from_above') + self.settings.response_time
            dfa_cd += energy_for_rupture / (4 * energy_regen_with_rupture)
            dfa_interval = 1./dfa_cd
            energy_for_dfa = avg_cpgs_per_finisher * cpg_energy_cost + self.get_spell_stats('death_from_above', cost_mod=ability_cost_modifier)[0]
            energy_for_dfa -= avg_finisher_size * self.relentless_strikes_energy_return_per_cp

            attacks_per_second['death_from_above'] = dfa_interval
            attacks_per_second['death_from_above_strike'] = [finisher_chance * dfa_interval for finisher_chance in avg_size_breakdown]
            attacks_per_second['death_from_above_pulse'] = [finisher_chance * dfa_interval * self.settings.num_boss_adds for finisher_chance in avg_size_breakdown]

            #Normalize DfA energy intervals to rupture intervals
            energy_for_dfa *= (avg_cycle_length)/(1./dfa_interval)
        
        energy_for_envenoms = energy_per_cycle - energy_for_rupture - energy_for_dfa

        envenom_energy_cost = avg_cpgs_per_finisher * cpg_energy_cost + self.get_spell_stats('envenom', cost_mod=ability_cost_modifier)[0]
        envenom_energy_cost -= avg_finisher_size * self.relentless_strikes_energy_return_per_cp
        envenoms_per_cycle = energy_for_envenoms / envenom_energy_cost

        envenoms_per_second = envenoms_per_cycle / avg_cycle_length
        finishers_per_second = envenoms_per_second + attacks_per_second['rupture']
        if self.talents.death_from_above:
            finishers_per_second += attacks_per_second['death_from_above']
        cpgs_per_second = avg_cpgs_per_finisher * finishers_per_second
        if cpg in attacks_per_second:
            attacks_per_second[cpg] += cpgs_per_second
        else:
            attacks_per_second[cpg] = cpgs_per_second
        if cpg == 'mutilate':
            attacks_per_second['dispatch'] += cpgs_per_second * blindside_proc_rate
        
        attacks_per_second['rupture_ticks'] = [0,0,0,0,0,.5]
        if self.talents.anticipation:
            attacks_per_second['envenom'][5] += envenoms_per_second
        else:
            for i in xrange(1,6):
                attacks_per_second['envenom'][i] = envenoms_per_second * avg_size_breakdown[i]
            #attacks_per_second['envenom'] = [finisher_chance * envenoms_per_second for finisher_chance in avg_size_breakdown]
            for i in xrange(1, 6):
                ticks_per_rupture = 2 * (1 + i + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())
                attacks_per_second['rupture_ticks'][i] = ticks_per_rupture * attacks_per_second['rupture'] * avg_size_breakdown[i]
                
        if self.talents.marked_for_death:
            attacks_per_second['envenom'][5] += 1. / self.get_spell_cd('marked_for_death')
        
        if 'garrote' in attacks_per_second:
            attacks_per_second['garrote_ticks'] = 6 * attacks_per_second['garrote']
        attacks_per_second['envenom'][5] += 1. / 180
        
        if self.level == 100:
            finisher_per_second = sum(attacks_per_second['envenom']) + attacks_per_second['rupture']
            if self.talents.death_from_above:
                finisher_per_second += sum(attacks_per_second['death_from_above_strike'])
            self.emp_envenom_percentage = 1 + .3 * (1 - attacks_per_second['rupture']/finisher_per_second)
            crit_mod = 0
            if getattr(self.stats.procs, 'bleeding_hollow_toxin_vessel'):
                #may need a better model for envenom uptime at high cp gen
                crit_mod = round(getattr(self.stats.procs, 'bleeding_hollow_toxin_vessel').value['ability_mod'])/10000
                self.envenom_crit_modifier = crit_mod * (1 - attacks_per_second['rupture']/finisher_per_second)
        
        if self.talents.shadow_reflection:
            sr_uptime = 8. / self.get_spell_cd('shadow_reflection')
            for ability in ('rupture_ticks', 'dispatch'):
                if type(attacks_per_second[ability]) in (tuple, list):
                    attacks_per_second['sr_'+ability] = [0,0,0,0,0,0]
                    for i in xrange(1, 6):
                        attacks_per_second['sr_'+ability][i] = sr_uptime * attacks_per_second[ability][i]
                else:
                    attacks_per_second['sr_'+ability] = sr_uptime * attacks_per_second[ability]
            envenom_per_sr = 1.5 * sum(attacks_per_second['envenom'])
            attacks_per_second['sr_envenom'] = [finisher_chance * envenom_per_sr / self.get_spell_cd('shadow_reflection') for finisher_chance in avg_size_breakdown]
            crit_rates['sr_envenom'] = 1./envenom_per_sr + (1-envenom_per_sr)/envenom_per_sr * crit_rates['envenom']
            if 'mutilate' in attacks_per_second:
                attacks_per_second['sr_mh_mutilate'] = 2 * sr_uptime * attacks_per_second['mutilate']
                attacks_per_second['sr_oh_mutilate'] = 2 * sr_uptime * attacks_per_second['mutilate']
        
        white_swing_downtime = 0
        if self.swing_reset_spacing is not None:
            white_swing_downtime += .5 / self.swing_reset_spacing
        attacks_per_second['mh_autoattacks'] = self.attack_speed_increase / self.stats.mh.speed * (1 - white_swing_downtime)
        attacks_per_second['oh_autoattacks'] = self.attack_speed_increase / self.stats.oh.speed * (1 - white_swing_downtime)
        
        if self.talents.death_from_above:
            lost_swings_mh = self.lost_swings_from_swing_delay(1.3, self.stats.mh.speed / self.attack_speed_increase)
            lost_swings_oh = self.lost_swings_from_swing_delay(1.3, self.stats.oh.speed / self.attack_speed_increase)
            
            attacks_per_second['mh_autoattacks'] -= lost_swings_mh / dfa_cd
            attacks_per_second['oh_autoattacks'] -= lost_swings_oh / dfa_cd
        
        attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dw_mh_hit_chance
        attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dw_oh_hit_chance
        
        self.get_poison_counts(attacks_per_second, current_stats)
        
        if self.level == 100:
            #this is to update the crit rate for envenom due to the 'crit on Vendetta cast' perk, unlikely to ever be another ability
            crit_uptime = (1./(self.get_spell_cd('vendetta') + self.settings.response_time + self.major_cd_delay)) / sum(attacks_per_second['envenom'])
            #this takes the difference between normal and guaranteed crits (1 - crit_rate), and multiplies it by the "uptime" across all envenoms
            #it's then added back to the original crit rate
            crit_rates['envenom'] += crit_uptime * (1 - crit_rates['envenom'])

        return attacks_per_second, crit_rates, additional_info
    
    def assassination_attack_counts_non_execute(self, current_stats, crit_rates=None):
        return self.assassination_attack_counts(current_stats, 'mutilate', self.settings.cycle.min_envenom_size_non_execute, crit_rates=crit_rates)

    def assassination_attack_counts_execute(self, current_stats, crit_rates=None):
        return self.assassination_attack_counts(current_stats, 'dispatch', self.settings.cycle.min_envenom_size_execute, crit_rates=crit_rates)

    ###########################################################################
    # Combat DPS functions
    ###########################################################################

    def combat_dps_estimate(self):
        return sum(self.combat_dps_breakdown().values())

    def combat_dps_breakdown(self):
        if not self.settings.is_combat_rogue():
            raise InputNotModeledException(_('You must specify a combat cycle to match your combat spec.'))
        
        #set readiness coefficient
        self.readiness_spec_conversion = self.combat_readiness_conversion
        self.spec_convergence_stats = ['haste', 'mastery', 'readiness']
        
        #spec specific glyph behaviour
        if self.glyphs.disappearance:
            self.ability_cds['vanish'] = 60
        else:
            self.ability_cds['vanish'] = 120
        
        #update spec specific proc rates
        if getattr(self.stats.procs, 'legendary_capacitive_meta'):
            getattr(self.stats.procs, 'legendary_capacitive_meta').proc_rate_modifier = 1.136
        if getattr(self.stats.procs, 'fury_of_xuen'):
            getattr(self.stats.procs, 'fury_of_xuen').proc_rate_modifier = 1.15

        #combat specific constants
        self.max_bandits_guile_buff = 1.3
        self.combat_cd_delay = 0 #this is for DFA convergence, mostly
        if self.level == 100:
            self.max_bandits_guile_buff += .2
            self.dw_miss_penalty = 0
            self.recalculate_hit_constants()
        self.max_energy = 100.
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            self.max_energy += 30
        if self.talents.lemon_zest:
            self.max_energy += 15
        if self.glyphs.energy:
            self.max_energy += 20
        if self.race.expansive_mind:
            self.max_energy = round(self.max_energy * 1.05, 0)
        self.ar_duration = 15
        # recurance relation of 0.16*x until convergence
        # https://www.wolframalpha.com/input/?i=15%2Bsum%28x%3D1+to+inf%29+of+15*.16%5Ex
        if self.stats.gear_buffs.rogue_t18_2pc:
            self.ar_duration = 17.8571
        self.revealing_strike_multiplier = 1.35
        self.extra_cp_chance = .25 # Assume all casts during RvS
        if self.stats.gear_buffs.rogue_t17_2pc:
            self.extra_cp_chance += 0.2
        self.rvs_duration = 24
        if self.settings.dmg_poison == 'dp' and self.level == 100:
            self.settings.dmg_poison = 'sp'
        
        self.set_constants()
        self.stat_multipliers['haste'] *= 1.05
        self.stat_multipliers['ap'] *= 1.50
        
        if self.talents.death_from_above:
            self.spec_needs_converge = True
        
        cds = {'ar':self.get_spell_cd('adrenaline_rush'),
               'ks':self.get_spell_cd('killing_spree')}
        
        # actual damage calculations here
        phases = {}
        #AR phase
        stats, aps, crits, procs, additional_info = self.determine_stats(self.combat_attack_counts_ar)
        ar_tuple = self.compute_damage_from_aps(stats, aps, crits, procs, additional_info)
        phases['ar'] = (self.ar_duration, self.update_with_bandits_guile(ar_tuple[0], ar_tuple[1]))
        for e in cds:
            cds[e] -= self.ar_duration / self.rb_cd_modifier(aps)
            
        #none
        self.tmp_ks_cd = cds['ks']
        self.tmp_phase_length = cds['ar'] #This is to approximate the value of a full energy bar to be used when not during AR or SB
        stats, aps, crits, procs, additional_info = self.determine_stats(self.combat_attack_counts_none)
        none_tuple = self.compute_damage_from_aps(stats, aps, crits, procs, additional_info)
        phases['none'] = (self.rb_actual_cds(aps, cds)['ar'] + self.settings.response_time + self.major_cd_delay,
                            self.update_with_bandits_guile(none_tuple[0], none_tuple[1]) )

        if self.stats.gear_buffs.rogue_t18_4pc:
            for key in phases['ar'][1]:
                    phases['ar'][1][key] *=1.15
            for key in phases['none'][1]:
                #15% damage boost with 16% uptime
                phases['none'][1][key] *= 1.024


        total_duration = phases['ar'][0] + phases['none'][0]
        #average it together
        damage_breakdown = self.average_damage_breakdowns(phases, denom = total_duration)
        
        bf_mod = .35
        bf_max_targets = 4
        if self.level == 100:
            bf_max_targets = 999 #this is the "no more target cap" limit, screw extra if statements
        if self.settings.cycle.blade_flurry:
            damage_breakdown['blade_flurry'] = 0
            for key in damage_breakdown:
                if key in self.melee_attacks:
                    damage_breakdown['blade_flurry'] += bf_mod * damage_breakdown[key] * min(self.settings.num_boss_adds, bf_max_targets)

        evis_multiplier = 1
        if getattr(self.stats.procs, 'bleeding_hollow_toxin_vessel'):
            evis_multiplier = 1+round(getattr(self.stats.procs, 'bleeding_hollow_toxin_vessel').value['ability_mod']*1.31132259)/10000


        soul_cap_mod = 1.0
        if getattr(self.stats.procs, 'soul_capacitor'):
            soul_cap= getattr(self.stats.procs, 'soul_capacitor')
            self.set_rppm_uptime(soul_cap)
            soul_cap_mod = 1+(soul_cap.uptime * soul_cap.value['damage_mod']/10000)

        #combat gets it's own MS calculation due to BF mechanics
        #calculate multistrike here, really cheap to calculate
        #turns out the 2 chance system yields a very basic linear pattern, the damage modifier is 30% of the multistrike %!
        multistrike_multiplier = .3 * 2 * (self.stats.get_multistrike_chance_from_rating(rating=stats['multistrike']) + self.buffs.multistrike_bonus())
        multistrike_multiplier = min(.6, multistrike_multiplier)
        for ability in damage_breakdown:
            if 'sr_' not in ability:
                damage_breakdown[ability] *= soul_cap_mod
            damage_breakdown[ability] *= (1 + multistrike_multiplier)
            if ability == 'eviscerate':
                damage_breakdown[ability] *= evis_multiplier

        return damage_breakdown
    
    def update_with_bandits_guile(self, damage_breakdown, additional_info):
        for key in damage_breakdown:
            if key in ('killing_spree', 'mh_killing_spree', 'oh_killing_spree'):
                if self.settings.cycle.ksp_immediately:
                    damage_breakdown[key] *= self.bandits_guile_multiplier
                else:
                    damage_breakdown[key] *= self.max_bandits_guile_buff
                if self.stats.gear_buffs.rogue_t16_4pc_bonus():
                    #http://elitistjerks.com/f78/t132793-5_4_changes_discussion/p2/#post2301780
                    #http://www.wolframalpha.com/input/?i=%28sum+of+1.5*1.1%5Ex+from+x%3D1+to+7%29+%2F+%281.5*7%29
                    # No need to use anything other than a constant. Yay for convenience!
                    damage_breakdown[key] *= 1.49084
            elif key in ('sinister_strike', 'revealing_strike'):
                damage_breakdown[key] *= self.bandits_guile_multiplier
            elif key in ('eviscerate', ):
                damage_breakdown[key] *= self.bandits_guile_multiplier * self.revealing_strike_multiplier
            else:
                damage_breakdown[key] *= self.bandits_guile_multiplier #* self.ksp_multiplier
                
        return damage_breakdown
    
    def combat_cpg_per_finisher(self, current_cp, ability_count):
        if current_cp >= 5:
            return ability_count
        new_count = copy(ability_count)
        new_count += 1
        
        normal = self.combat_cpg_per_finisher(current_cp+1, new_count)
        rvs_proc = self.combat_cpg_per_finisher(current_cp+2, new_count)
        
        return (1 - self.extra_cp_chance)*normal + self.extra_cp_chance*rvs_proc
    
    def combat_attack_counts(self, current_stats, ar=False, crit_rates=None):
        attacks_per_second = {}
        additional_info = {}
        # base_energy_regen needs to be reset here due to determine_stats method
        self.base_energy_regen = 12.
        if self.settings.cycle.blade_flurry:
            self.base_energy_regen *= .8

        if crit_rates == None:
            crit_rates = self.get_crit_rates(current_stats)

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod

        self.attack_speed_increase = self.base_speed_multiplier * haste_multiplier

        main_gauche_proc_rate = self.combat_mastery_conversion * self.stats.get_mastery_from_rating(current_stats['mastery'])

        combat_potency_regen_per_oh = 15 * .2 * self.stats.oh.speed / 1.4  # the new "normalized" formula
        combat_potency_from_mg = 15 * .2
        FINISHER_SIZE = 5
        ruthlessness_value = 1 # 1CP gained at 20% chance per CP spent (5CP spent means 1 is always added)
        
        if ar:
            self.attack_speed_increase *= 1.2
            self.base_energy_regen *= 2.0
        if self.talents.lemon_zest:
            self.base_energy_regen *= 1 + .05 * (1 + min(self.settings.num_boss_adds, 2))
        gcd_size = 1.0 + self.settings.latency
        if ar:
            gcd_size -= .2
        cp_per_cpg = 1.
        dfa_cd = self.get_spell_cd('death_from_above') + self.settings.response_time
        
        if self.stats.gear_buffs.rogue_t18_2pc and not ar:
            self.attack_speed_increase *= 1 + (0.16 *0.2)
            self.base_energy_regen *= 1.16
            gcd_size -= (0.16 * 0.2)
                  
        # Combine energy cost scalers to reduce function calls (ie, 40% reduced energy cost). Assume multiplicative.
        cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_modifier()
        # Turn the cost of the ability into the net loss of energy by reducing it by the energy gained from MG
        cost_reducer = main_gauche_proc_rate * combat_potency_from_mg
        
        eviscerate_energy_cost =  self.get_spell_stats('eviscerate', cost_mod=cost_modifier)[0]
        eviscerate_energy_cost -= cost_reducer
        eviscerate_energy_cost -= FINISHER_SIZE * self.relentless_strikes_energy_return_per_cp
        revealing_strike_energy_cost =  self.get_spell_stats('revealing_strike', cost_mod=cost_modifier)[0]
        revealing_strike_energy_cost -= cost_reducer
        sinister_strike_energy_cost =  self.get_spell_stats('sinister_strike', cost_mod=cost_modifier)[0]
        sinister_strike_energy_cost -= cost_reducer
        death_from_above_energy_cost = self.get_spell_stats('death_from_above', cost_mod=cost_modifier)[0]
        death_from_above_energy_cost -= cost_reducer * (2 + self.settings.num_boss_adds)
        #need to reduce the cost of DFA by the strike's MG proc ...
        #but also the MG procs from the AOE which hits the main target plus each additional add (strike + aoe)
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            sinister_strike_energy_cost -= 15 * self.extra_cp_chance
        
        ## Base CPs and Attacks
        #Autoattacks
        white_swing_downtime = 0
        if self.swing_reset_spacing is not None and not ar:
            white_swing_downtime += self.settings.response_time / self.swing_reset_spacing #from vanish
        swing_timer_mh = self.stats.mh.speed / self.attack_speed_increase
        swing_timer_mh = self.stats.oh.speed / self.attack_speed_increase
        
        attacks_per_second['mh_autoattacks'] = self.attack_speed_increase / self.stats.mh.speed * (1 - white_swing_downtime)
        attacks_per_second['oh_autoattacks'] = self.attack_speed_increase / self.stats.oh.speed * (1 - white_swing_downtime)
        #swing delays should be handled here
        if self.talents.death_from_above and not ar:
            lost_swings_mh = self.lost_swings_from_swing_delay(1.3, self.stats.mh.speed / self.attack_speed_increase)
            lost_swings_oh = self.lost_swings_from_swing_delay(1.3, self.stats.oh.speed / self.attack_speed_increase)
            
            attacks_per_second['mh_autoattacks'] -= lost_swings_mh / dfa_cd
            attacks_per_second['oh_autoattacks'] -= lost_swings_oh / dfa_cd
        
        attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dw_mh_hit_chance
        attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dw_oh_hit_chance
        attacks_per_second['main_gauche'] = attacks_per_second['mh_autoattack_hits'] * main_gauche_proc_rate
        combat_potency_regen = attacks_per_second['oh_autoattack_hits'] * combat_potency_regen_per_oh
        
        #Base energy
        bonus_energy_from_openers = self.get_bonus_energy_from_openers('sinister_strike', 'revealing_strike')
        if self.settings.opener_name in ('ambush', 'garrote'):
            attacks_per_second[self.settings.opener_name] = self.total_openers_per_second
            attacks_per_second['main_gauche'] += self.total_openers_per_second * main_gauche_proc_rate
        if self.talents.death_from_above and not ar:
            attacks_per_second['main_gauche'] += (1 + self.settings.num_boss_adds) * main_gauche_proc_rate / dfa_cd
        combat_potency_regen += combat_potency_from_mg * attacks_per_second['main_gauche']
        energy_regen = self.base_energy_regen * haste_multiplier
        if self.stats.gear_buffs.rogue_t17_4pc_lfr:
            #http://www.wolframalpha.com/input/?i=1.1307+*+%281+-+e+**+%28-1+*+1.1+*+6%2F+60%29%29
            #https://twitter.com/Celestalon/status/525350819856535552
            energy_regen *= 1 + (.11778034322021550695 * .3) #11% uptime on 30% boost)
        energy_regen += self.bonus_energy_regen + combat_potency_regen + bonus_energy_from_openers
        #Rough idea to factor in a full energy bar
        if not ar:
            energy_regen += self.max_energy / self.settings.duration
        
        #Base actions
        rvs_interval = self.rvs_duration
        if self.settings.cycle.revealing_strike_pooling:
            min_energy_while_pooling = energy_regen * gcd_size
            max_energy_while_pooling = self.max_energy - 20
            rvs_interval += (max_energy_while_pooling - min_energy_while_pooling) / energy_regen
        
        #Minicycle sizes and cpg_per_finisher stats
        if self.talents.anticipation:
            ss_per_finisher = (FINISHER_SIZE - ruthlessness_value) / (cp_per_cpg + self.extra_cp_chance)
        else:
            ss_per_finisher = self.combat_cpg_per_finisher(1, 0)
        cp_per_finisher = FINISHER_SIZE
        energy_cost_for_cpgs = ss_per_finisher * sinister_strike_energy_cost
        total_eviscerate_cost = energy_cost_for_cpgs + eviscerate_energy_cost

        ss_per_snd = ss_per_finisher
        snd_size = FINISHER_SIZE
        snd_base_cost = 25
        snd_cost = ss_per_snd * sinister_strike_energy_cost + snd_base_cost - snd_size * self.relentless_strikes_energy_return_per_cp
        snd_duration = 6 + 6 * (snd_size + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())
        energy_spent_on_snd = snd_cost / snd_duration
        
        #Base Actions
        #marked for death CD
        self.combat_cd_delay = (.5 * total_eviscerate_cost) / (2 * energy_regen)
        marked_for_death_cd = self.get_spell_cd('marked_for_death') + self.combat_cd_delay + self.settings.response_time
        if self.talents.marked_for_death:
            energy_regen -= 10. / marked_for_death_cd
        energy_regen -= revealing_strike_energy_cost / rvs_interval
    
        energy_for_dfa = 0        
        if self.talents.death_from_above and not ar:
            #dfa_gap probably should be handled more accurately especially in the non-anticipation case
            dfa_interval = 1./(dfa_cd)
            energy_for_dfa = energy_cost_for_cpgs + death_from_above_energy_cost
            energy_for_dfa -= cp_per_finisher * self.relentless_strikes_energy_return_per_cp          
            energy_for_dfa *= dfa_interval

            attacks_per_second['death_from_above'] = dfa_interval
            attacks_per_second['death_from_above_strike'] = [0, 0, 0, 0, 0, dfa_interval]
            attacks_per_second['death_from_above_pulse'] = [0, 0, 0, 0, 0, dfa_interval * (self.settings.num_boss_adds+1)]

        #Base CPGs
        attacks_per_second['sinister_strike_base'] = ss_per_snd / snd_duration
        if self.talents.death_from_above and not ar:
            attacks_per_second['sinister_strike_base'] += ss_per_finisher / (1/dfa_interval)

        attacks_per_second['revealing_strike'] = 1. / rvs_interval
        extra_finishers_per_second = attacks_per_second['revealing_strike'] / 5.
        #Scaling CPGs
        free_gcd = 1./gcd_size
        free_gcd -= 1./snd_duration + (attacks_per_second['sinister_strike_base'] + attacks_per_second['revealing_strike'] + extra_finishers_per_second)
        if self.talents.marked_for_death:
            free_gcd -= (1. / marked_for_death_cd)
        #2 seconds is an approximation of GCD loss while in air        
        if self.talents.death_from_above and not ar:
            free_gcd -= dfa_interval * (2. / gcd_size) #wowhead claims a 2s GCD
        energy_available_for_evis = energy_regen - energy_spent_on_snd - energy_for_dfa
        total_evis_per_second = energy_available_for_evis / total_eviscerate_cost
        evisc_actions_per_second = (total_evis_per_second * ss_per_finisher + total_evis_per_second)
        if self.stats.gear_buffs.rogue_t17_4pc:
            #http://www.wolframalpha.com/input/?i=sum+of+.2%5Ex+from+x%3D1+to+inf
            #This increases the frequency of Eviscerates by 25% for every Evisc cast
            evisc_actions_per_second += total_evis_per_second * .25
        attacks_per_second['sinister_strike'] = total_evis_per_second * ss_per_finisher
        # If GCD capped
        if evisc_actions_per_second > free_gcd:
            gcd_cap_mod = evisc_actions_per_second / free_gcd
            attacks_per_second['sinister_strike'] = attacks_per_second['sinister_strike'] / gcd_cap_mod
            total_evis_per_second = total_evis_per_second / gcd_cap_mod
        # Reintroduce flat gcds
        attacks_per_second['sinister_strike'] += attacks_per_second['sinister_strike_base']
        attacks_per_second['main_gauche'] += (attacks_per_second['sinister_strike'] + attacks_per_second['revealing_strike'] +
                                              total_evis_per_second) * main_gauche_proc_rate
        if self.talents.death_from_above and not ar:
            attacks_per_second['main_gauche'] += attacks_per_second['death_from_above_strike'][5] * main_gauche_proc_rate
        
        #attacks_per_second['eviscerate'] = [finisher_chance * total_evis_per_second for finisher_chance in finisher_size_breakdown]
        attacks_per_second['eviscerate'] = [0,0,0,0,0,total_evis_per_second]
        for opener, cps in [('ambush', 2), ('garrote', 1)]:
            if opener in attacks_per_second:
                extra_finishers_per_second += attacks_per_second[opener] * cps / 5
        attacks_per_second['eviscerate'][5] += extra_finishers_per_second
        if self.talents.marked_for_death:
            attacks_per_second['eviscerate'][5] += 1. / marked_for_death_cd
        if self.stats.gear_buffs.rogue_t17_4pc:
            attacks_per_second['eviscerate'][5] *= 1.25
        
        #self.current_variables['cp_spent_on_damage_finishers_per_second'] = (total_evis_per_second) * cp_per_finisher
        if 'garrote' in attacks_per_second:
            attacks_per_second['garrote_ticks'] = 6 * attacks_per_second['garrote']
        
        time_at_level = 4 / attacks_per_second['sinister_strike']
        cycle_duration = 3 * time_at_level + 15
        if self.level == 100:
            self.bandits_guile_multiplier = 1 + (0*time_at_level + .1*time_at_level + .2*time_at_level + .5 * 15) / cycle_duration
        else:
            avg_stacks = (3 * time_at_level + 45) / cycle_duration #45 is the duration (15s) multiplied by the stack power (30% BG)
            self.bandits_guile_multiplier = 1 + .1 * avg_stacks
        
        if not ar:
            ks_duration = 3
            if self.stats.gear_buffs.rogue_pvp_wod_4pc:
                ks_duration += 1
            final_ks_cd = self.rb_actual_cd(attacks_per_second, self.tmp_ks_cd) + self.major_cd_delay + self.ar_duration/2.
            if not self.settings.cycle.ksp_immediately:
                final_ks_cd += (3 * time_at_level)/2 * (3 * time_at_level)/cycle_duration
            attacks_per_second['mh_killing_spree'] = (1 + 2*ks_duration) / (final_ks_cd + self.settings.response_time)
            attacks_per_second['oh_killing_spree'] = (1 + 2*ks_duration) / (final_ks_cd + self.settings.response_time)
            attacks_per_second['main_gauche'] += attacks_per_second['mh_killing_spree'] * main_gauche_proc_rate
        
        if self.talents.shadow_reflection:
            sr_uptime = 8. / self.get_spell_cd('shadow_reflection')
            lst = ('sinister_strike', 'eviscerate', 'revealing_strike')
            if not ar:
                lst += ('mh_killing_spree', 'oh_killing_spree')
            for ability in lst:
                if type(attacks_per_second[ability]) in (tuple, list):
                    attacks_per_second['sr_'+ability] = [0,0,0,0,0,0]
                    for i in xrange(1, 6):
                        attacks_per_second['sr_'+ability][i] = sr_uptime * attacks_per_second[ability][i]
                else:
                    attacks_per_second['sr_'+ability] = sr_uptime * attacks_per_second[ability]
        
        self.get_poison_counts(attacks_per_second, current_stats)
        
        #print attacks_per_second   
        return attacks_per_second, crit_rates, additional_info
    
    def rb_actual_cds(self, attacks_per_second, base_cds, avg_rb_effect=10):
        final_cds = {}
        # If it's best to always use 5CP finishers as combat now, it should continue to be so, this is simpler and faster
        for cd_name in base_cds:
            final_cds[cd_name] = base_cds[cd_name] * self.rb_cd_modifier(attacks_per_second)
        return final_cds
    
    def rb_actual_cd(self, attacks_per_second, base_cd, avg_rb_effect=10):
        # If it's best to always use 5CP finishers as combat now, it should continue to be so, this is simpler and faster
        return base_cd * self.rb_cd_modifier(attacks_per_second)
    
    def rb_cd_modifier(self, attacks_per_second, avg_rb_effect=10):
        # If it's best to always use 5CP finishers as combat now, it should continue to be so, this is simpler and faster
        offensive_finisher_rate = attacks_per_second['eviscerate'][5]
        if 'death_from_above' in attacks_per_second:
            offensive_finisher_rate += attacks_per_second['death_from_above']
        return (1./avg_rb_effect) / (offensive_finisher_rate + (1./avg_rb_effect))
    
    def combat_attack_counts_ar(self, current_stats, crit_rates=None):
        return self.combat_attack_counts(current_stats, ar=True, crit_rates=crit_rates)

    def combat_attack_counts_none(self, current_stats, crit_rates=None):
        return self.combat_attack_counts(current_stats, crit_rates=crit_rates)

    ###########################################################################
    # Subtlety DPS functions
    ###########################################################################

    def subtlety_dps_estimate(self):
        return sum(self.subtlety_dps_breakdown().values())

    def subtlety_dps_breakdown(self):
        if not self.settings.is_subtlety_rogue():
            raise InputNotModeledException(_('You must specify a subtlety cycle to match your subtlety spec.'))

        if self.stats.mh.type != 'dagger' and self.settings.cycle.use_hemorrhage != 'always':
            raise InputNotModeledException(_('Subtlety modeling requires a MH dagger if Hemorrhage is not the main combo point builder'))

        if self.settings.cycle.use_hemorrhage not in ('always', 'never', 'uptime'):
            if float(self.settings.cycle.use_hemorrhage) <= 0:
                raise InputNotModeledException(_('Hemorrhage usage must be set to always, never or a positive number'))
            if float(self.settings.cycle.use_hemorrhage) > self.settings.duration:
                raise InputNotModeledException(_('Interval between Hemorrhages cannot be higher than the fight duration'))
            
        #set readiness coefficient
        self.readiness_spec_conversion = self.subtlety_readiness_conversion
        self.spec_convergence_stats = ['haste', 'multistrike']
        
        #overrides setting, using Ambush + Vanish on CD is critical
        self.settings.use_opener = 'always'
        self.settings.opener_name = 'ambush'
        # Sanguinary Vein
        self.damage_modifier_cache = 1.25
        
        self.sc_trigger_rate = 0
        mos_value = .1

        self.vanish_cd_modifier = 1.0

        # leveling perks
        if self.level == 100:
            mos_value += .05
            self.ability_cds['vanish'] = 90

        #update spec specific proc rates
        if getattr(self.stats.procs, 'legendary_capacitive_meta'):
            getattr(self.stats.procs, 'legendary_capacitive_meta').proc_rate_modifier = 1.114
        
        self.set_constants()
        self.stat_multipliers['multistrike'] *= 1.05
        self.stat_multipliers['agi'] *= 1.15
        #sinister calling requires convergence to calculate (for now?)
        self.spec_needs_converge = True

        self.settings.cycle.raid_crits_per_second = self.get_adv_param('hat_triggers_per_second', self.settings.cycle.raid_crits_per_second, min_bound=0, max_bound=600)
        self.settings.cycle.clip_fw = self.get_adv_param('clip_fw', self.settings.cycle.clip_fw, ignore_bounds=True)
        
        self.vanish_rate = 1. / (self.get_spell_cd('vanish') + self.settings.response_time) + 1. / (self.get_spell_cd('preparation') + self.settings.response_time * 3) #vanish CD + Prep CD
        mos_multiplier = 1. + mos_value * (6 + 3 * self.talents.subterfuge * [1, 2][self.glyphs.vanish]) * self.vanish_rate
        
        stats, aps, crits, procs, additional_info = self.determine_stats(self.subtlety_attack_counts)
        damage_breakdown, additional_info  = self.compute_damage_from_aps(stats, aps, crits, procs, additional_info)

        armor_value = self.target_armor()
        find_weakness_damage_boost = 1. / self.max_level_armor_multiplier()
        find_weakness_multiplier = 1 + (find_weakness_damage_boost - 1) * additional_info['fw_uptime']
        

        trinket_multiplier = 1
        if getattr(self.stats.procs, 'bleeding_hollow_toxin_vessel'):
            trinket_multiplier = 1+round(getattr(self.stats.procs, 'bleeding_hollow_toxin_vessel').value['ability_mod']*1.38590017)/10000

        #calculate multistrike here for Sub and Assassination, really cheap to calculate
        #turns out the 2 chance system yields a very basic linear pattern, the damage modifier is 30% of the multistrike %!
        multistrike_multiplier = .3 * 2 * (self.stats.get_multistrike_chance_from_rating(rating=stats['multistrike']) + self.buffs.multistrike_bonus())
        multistrike_multiplier = min(.6, multistrike_multiplier)
        
        soul_cap_mod = 1.0
        if getattr(self.stats.procs, 'soul_capacitor'):
            soul_cap= getattr(self.stats.procs, 'soul_capacitor')
            self.set_rppm_uptime(soul_cap)
            soul_cap_mod = 1+(soul_cap.uptime * soul_cap.value['damage_mod']/10000)

        vanish_damage_mod = 1.0
        if self.stats.gear_buffs.rogue_t18_2pc:
            vanish_damage_buff_uptime = 10/self.get_spell_cd('vanish')
            vanish_damage_mod += vanish_damage_buff_uptime * 0.3

        for key in damage_breakdown:
            damage_breakdown[key] *= vanish_damage_mod
            if key in ('eviscerate', 'hemorrhage', 'shuriken_toss', 'hemorrhage_dot', 'autoattack'): #'burning_wounds'
                damage_breakdown[key] *= find_weakness_multiplier
            if key == 'ambush':
                #damage_breakdown[key] *= find_weakness_multiplier
                damage_breakdown[key] *= 1 + ((1 - additional_info['ambush_no_fw_rate']) * (find_weakness_damage_boost - 1))
            if key == 'backstab':
                #damage_breakdown[key] *= find_weakness_multiplier
                damage_breakdown[key] *= 1 + additional_info['backstab_fw_rate'] * (find_weakness_damage_boost - 1)
            if key in ('rupture', 'sr_rupture', 'rupture_sc'):
                damage_breakdown[key] *= 1.3
            if key is not 'rupture_sc':
                damage_breakdown[key] *= (1 + multistrike_multiplier)
            if key in ('ambush', 'garrote'):
                damage_breakdown[key] *=trinket_multiplier
            if "sr_" not in key:
                damage_breakdown[key] *= soul_cap_mod
            damage_breakdown[key] *= mos_multiplier
        
        #discard the loose rupture component to clean up the breakdown
        if 'rupture_sc' in damage_breakdown and self.settings.merge_damage:
            damage_breakdown['rupture'] += damage_breakdown['rupture_sc']
            del damage_breakdown['rupture_sc']
        
        return damage_breakdown

    def subtlety_attack_counts(self, current_stats, crit_rates=None):
        attacks_per_second = {}
        additional_info = {}
        if crit_rates == None:
            crit_rates = self.get_crit_rates(current_stats)
        
        self.ability_cds['vanish'] = 90 * self.vanish_cd_modifier

        base_energy_regen = 10.
        max_energy = 100.
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            max_energy += 30
        if self.talents.lemon_zest:
            base_energy_regen *= 1 + .05 * (1 + min(self.settings.num_boss_adds, 2))
            max_energy += 15
        if self.glyphs.energy:
            max_energy += 20
        if self.race.expansive_mind:
            max_energy = round(max_energy * 1.05, 0)
        shd_duration = 8
        if self.level == 100:
            shd_duration += 2
        shd_cd = self.get_spell_cd('shadow_dance') + self.settings.response_time + self.major_cd_delay
            
        cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_reduced_cost()
        shd_ambush_cost_modifier = 1.
        backstab_cost_mod = cost_modifier
        base_eviscerate_cost = self.get_spell_stats('eviscerate', cost_mod=cost_modifier)[0]
        base_rupture_cost = self.get_spell_stats('rupture', cost_mod=cost_modifier)[0]
        base_hemo_cost = self.get_spell_stats('hemorrhage', cost_mod=cost_modifier)[0]
        base_backstab_energy_cost = self.get_spell_stats('backstab', cost_mod=backstab_cost_mod)[0]
        sd_ambush_cost = self.get_spell_stats('ambush', cost_mod=shd_ambush_cost_modifier)[0] - 20
        normal_ambush_cost = self.get_spell_stats('ambush')[0]
        if self.talents.death_from_above:
            self.dfa_cost = self.get_spell_stats('death_from_above', cost_mod=cost_modifier)[0]
        
        #haste and attack speed
        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod
        mastery_snd_speed = 1 + .4 * (1 + self.subtlety_mastery_conversion * self.stats.get_mastery_from_rating(current_stats['mastery']))
        attack_speed_multiplier = self.base_speed_multiplier * haste_multiplier * mastery_snd_speed / 1.4
        
        cpg_name = 'backstab'
        if self.settings.cycle.use_hemorrhage == 'always':
            cpg_name = 'hemorrhage'
        
        #constant and base values
        hat_triggers_per_second = self.settings.cycle.raid_crits_per_second
        hat_cp_per_second = 1. / (2 + 1. / hat_triggers_per_second)
        er_energy = 8. / 2 #8 energy every 2 seconds, assumed full SnD uptime
        fw_duration = 10. #17.5s
        if self.settings.cycle.clip_fw:
            fw_duration -= .5
        attacks_per_second['eviscerate'] = [0,0,0,0,0,0]
        attacks_per_second['rupture_ticks'] = [0,0,0,0,0,0]
        attacks_per_second['ambush'] = self.total_openers_per_second
        attacks_per_second['backstab'] = 0
        attacks_per_second['hemorrhage'] = 0
        cp_per_ambush = 2
        vanish_bonus_stealth = 0 + 3 * self.talents.subterfuge * [1, 2][self.glyphs.vanish]
        rupture_ticks_per_cast = 12.
        rupture_cd = 24.
        hemo_cd = 24.
        snd_cd = 36.
        base_cp_per_second = hat_cp_per_second * (shd_cd-8.)/shd_cd + self.total_openers_per_second * 2
        if self.stats.gear_buffs.rogue_t18_2pc:
            base_cp_per_second += 5 / self.get_spell_cd('vanish')
        if self.stats.gear_buffs.rogue_t15_2pc:
            rupture_ticks_per_cast += 2
            rupture_cd += 4
            snd_cd += 6
        
        #sinister calling mechanic
        sc_scaler = .5 / (.5 + self.sc_trigger_rate)
        rupture_cd *= sc_scaler
        hemo_cd *= sc_scaler
        
        #passive energy regen
        energy_regen = base_energy_regen * haste_multiplier
        if self.stats.gear_buffs.rogue_t17_4pc_lfr:
            #http://www.wolframalpha.com/input/?i=1.1307+*+%281+-+e+**+%28-1+*+1.1+*+6%2F+60%29%29
            #https://twitter.com/Celestalon/status/525350819856535552
            energy_regen *= 1 + (.11778034322021550695 * .3) #11% uptime on 30% boost)
        energy_regen += self.bonus_energy_regen + max_energy / self.settings.duration + er_energy
        energy_regen += self.get_bonus_energy_from_openers()
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            energy_regen += 2 * hat_cp_per_second
        if self.stats.gear_buffs.rogue_t17_2pc:
            energy_regen += 60. / shd_cd
        if self.stats.gear_buffs.rogue_t17_4pc:
            energy_regen -= (base_eviscerate_cost - 25) / shd_cd
        
        #deal with extra subterfuge ambushes
        if self.talents.subterfuge:
            attacks_per_second['ambush'] += (1. / self.get_spell_cd('vanish')) * [1., 2.][self.glyphs.vanish]
            energy_regen -= (normal_ambush_cost / self.get_spell_cd('vanish')) * [1., 2.][self.glyphs.vanish]
            base_cp_per_second += (2. / self.get_spell_cd('vanish')) * [1., 2.][self.glyphs.vanish]
        
        ##calculations dependent on energy regen
        cpg_costs_for_cycle = base_backstab_energy_cost * 5
        if self.settings.cycle.use_hemorrhage == 'always':
            cpg_costs_for_cycle = base_hemo_cost * 5
        typical_cycle_size = cpg_costs_for_cycle + (base_eviscerate_cost - 25)
        
        #swing timer
        white_swing_downtime = 0
        if self.swing_reset_spacing is not None:
            white_swing_downtime += .5 / self.swing_reset_spacing
        attacks_per_second['mh_autoattacks'] = attack_speed_multiplier / self.stats.mh.speed * (1 - white_swing_downtime)
        attacks_per_second['oh_autoattacks'] = attack_speed_multiplier / self.stats.oh.speed * (1 - white_swing_downtime)
        if self.talents.death_from_above:
            dfa_cd = self.get_spell_cd('death_from_above') + self.settings.response_time
            
            lost_swings_mh = self.lost_swings_from_swing_delay(1.3, self.stats.mh.speed / attack_speed_multiplier)
            lost_swings_oh = self.lost_swings_from_swing_delay(1.3, self.stats.oh.speed / attack_speed_multiplier)
            
            attacks_per_second['mh_autoattacks'] -= lost_swings_mh / dfa_cd
            attacks_per_second['oh_autoattacks'] -= lost_swings_oh / dfa_cd
        
        attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dw_mh_hit_chance
        attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dw_oh_hit_chance
        
        ##start consuming energy
        #base energy reductions
        marked_for_death_cd = self.get_spell_cd('marked_for_death') + (.5 * typical_cycle_size / energy_regen) + self.settings.response_time
        if self.talents.marked_for_death:
            energy_regen -= (base_eviscerate_cost - 25) / marked_for_death_cd
            attacks_per_second['eviscerate'][5] += 1. / marked_for_death_cd
        shadowmeld_ambushes = 0.
        if self.race.shadowmeld:
            shadowmeld_ambushes = 1. / (self.get_spell_cd('shadowmeld') + self.settings.response_time)
            shadowmeld_ambushes *= ((self.settings.duration - fw_duration * 3 - 8) / self.settings.duration)
            attacks_per_second['ambush'] += shadowmeld_ambushes
            energy_regen -= normal_ambush_cost * shadowmeld_ambushes
            base_cp_per_second += shadowmeld_ambushes * 2
           
        #base CPs, CPGs, and finishers 
        if self.settings.cycle.use_hemorrhage != 'always' and self.settings.cycle.use_hemorrhage != 'never':
            if self.settings.cycle.use_hemorrhage == 'uptime':
                hemo_per_second = 1. / hemo_cd
            else:
                hemo_per_second = 1. / float(self.settings.cycle.use_hemorrhage)
            energy_regen -= hemo_per_second * base_hemo_cost
            base_cp_per_second += hemo_per_second
            attacks_per_second['hemorrhage'] += hemo_per_second
        #premed
        base_cp_per_second += 2. / self.settings.duration #start of the fight
        base_cp_per_second += 2. / shd_cd * (self.settings.duration-25.)/self.settings.duration
        base_cp_per_second += 2. / self.get_spell_cd('vanish') * (self.settings.duration-50.)/self.settings.duration
        #rupture
        attacks_per_second['rupture'] = 1. / rupture_cd
        attacks_per_second['rupture_ticks'][5] = rupture_ticks_per_cast / rupture_cd
        #attacks_per_second['rupture_ticks_sc'] = [0,0,0,0,0, (1 - sc_scaler) * rupture_ticks_per_cast / rupture_cd]
        base_cp_per_second -= 5. / rupture_cd
        energy_regen -= (base_rupture_cost - 25) / rupture_cd
        #no need to add slice and dice to attacks per second
        base_cp_per_second -= 5. / snd_cd
        
        energy_for_dfa = 0        
        if self.talents.death_from_above:
            #dfa_gap probably should be handled more accurately especially in the non-anticipation case
            dfa_interval = 1./(dfa_cd)
            energy_for_dfa = typical_cycle_size + self.dfa_cost - base_eviscerate_cost

            attacks_per_second['death_from_above'] = dfa_interval
            attacks_per_second['death_from_above_strike'] = [0, 0, 0, 0, 0, dfa_interval]
            attacks_per_second['death_from_above_pulse'] = [0, 0, 0, 0, 0, dfa_interval * (self.settings.num_boss_adds+1)]
            attacks_per_second[cpg_name] += dfa_interval * 5
            energy_regen -= energy_for_dfa / dfa_cd
        
        base_cp_per_second += self.vanish_rate * 2
        #if we've consumed more CP's than we have for base functionality, lets generate some more CPs
        if base_cp_per_second < 0:
            cpg_per_second = math.fabs(base_cp_per_second)
            base_cp_per_second += cpg_per_second
            attacks_per_second[cpg_name] += cpg_per_second
            if cpg_name == 'backstab':
                energy_regen -= base_backstab_energy_cost * cpg_per_second
            elif cpg_name == 'hemorrhage':
                energy_regen -= base_hemo_cost * cpg_per_second
        extra_evisc = base_cp_per_second / 5
        energy_regen -= (base_eviscerate_cost - 25) * extra_evisc
        attacks_per_second['eviscerate'][5] += extra_evisc
        if energy_regen < 0:
            raise InputNotModeledException(_('Catastrophic failure: cycle not sustainable.'))
        
        #calculate shd ambush cycles
        shd_energy = (max_energy - self.get_adv_param('max_pool_reduct', 10, min_bound=0, max_bound=50)) + energy_regen * shd_duration #lasts 8s, assume we pool to ~10 energy below max
        shd_cycle_cost = 2 * sd_ambush_cost + (base_eviscerate_cost - 25)
        shd_eviscerates = min(shd_energy / shd_cycle_cost, 8./3) #8/3 is the max GCDs
        shd_ambushes = shd_eviscerates * 2
        attacks_per_second['ambush'] += (shd_ambushes / shd_cd) * ((self.settings.duration - fw_duration) / self.settings.duration)
        attacks_per_second['eviscerate'][5] += (shd_eviscerates / shd_cd) * ((self.settings.duration - fw_duration) / self.settings.duration)
        energy_regen -= (shd_cycle_cost * shd_eviscerates) / shd_cd * ((self.settings.duration - fw_duration) / self.settings.duration)
        
        #calculate percentage of ambushes with FW
        ambush_no_fw = shadowmeld_ambushes + 1. / shd_cd - 1. / self.settings.duration
        if not self.settings.cycle.clip_fw:
            ambush_no_fw += self.total_openers_per_second + 1. / self.settings.duration
        additional_info['ambush_no_fw_rate'] = ambush_no_fw / attacks_per_second['ambush']
        #calculate percentage of backstabs with FW
        additional_info['backstab_fw_rate'] = (fw_duration - 1) / self.settings.duration #start of fight
        additional_info['backstab_fw_rate'] += (fw_duration - 1) / shd_cd * (1. - fw_duration / self.settings.duration)
        additional_info['backstab_fw_rate'] += (fw_duration + vanish_bonus_stealth - 1) / self.get_spell_cd('vanish') * ((self.settings.duration - fw_duration * 2 - 8) / self.settings.duration)
        if self.race.shadowmeld:
            additional_info['backstab_fw_rate'] += (fw_duration - 1) / self.get_spell_cd('shadowmeld') * ((self.settings.duration - fw_duration * 3 - 8) / self.settings.duration)
        #accounts for the fact that backstab isn't evenly distributed
        additional_info['backstab_fw_rate'] = additional_info['backstab_fw_rate'] / ((shd_cd - 8.) / shd_cd)
        #calculate FW uptime overall
        additional_info['fw_uptime'] = fw_duration / self.settings.duration #start of fight
        additional_info['fw_uptime'] += (fw_duration + 7.5) / shd_cd * ((self.settings.duration - fw_duration) / self.settings.duration)
        additional_info['fw_uptime'] += (fw_duration + vanish_bonus_stealth) / self.get_spell_cd('vanish') * ((self.settings.duration - fw_duration * 2 - 8) / self.settings.duration)
        if self.race.shadowmeld:
            additional_info['fw_uptime'] += fw_duration / self.get_spell_cd('shadowmeld') * ((self.settings.duration - fw_duration * 3 - 8) / self.settings.duration)
        #allocate the remaining energy
        filler_cycles_per_second = energy_regen / typical_cycle_size
        attacks_per_second[cpg_name] += filler_cycles_per_second * 5
        attacks_per_second['eviscerate'][5] += filler_cycles_per_second
        if self.stats.gear_buffs.rogue_t17_4pc:
            attacks_per_second['eviscerate'][5] += 1. / shd_cd
        
        #Hemo ticks
        if 'hemorrhage' in attacks_per_second and self.settings.cycle.use_hemorrhage != 'never':
            if self.settings.cycle.use_hemorrhage == 'always':
                hemo_gap = 1 / attacks_per_second['hemorrhage']
            else:
                hemo_gap = hemo_cd
            ticks_per_second = min(1. / (3 * sc_scaler), 8. / hemo_gap)
            attacks_per_second['hemorrhage_ticks'] = ticks_per_second
        
        sc_ms_chance = min(2 * (self.stats.get_multistrike_chance_from_rating(rating=current_stats['multistrike']) + self.buffs.multistrike_bonus()), 2)
        #this is a cache for convergence
        self.sc_trigger_rate = attacks_per_second['ambush'] * sc_ms_chance
        if 'backstab' in attacks_per_second:
            self.sc_trigger_rate += attacks_per_second['backstab'] * sc_ms_chance
        self.sc_trigger_rate = min(self.sc_trigger_rate, 2)
        
        if self.talents.shadow_reflection:
            sr_cd = self.get_spell_cd('shadow_reflection')
            attacks_per_second['sr_eviscerate'] = [0,0,0,0,0, shd_eviscerates / sr_cd]
            attacks_per_second['sr_rupture_ticks'] = [0,0,0,0,0, 12. / sr_cd]
            attacks_per_second['sr_ambush'] = shd_ambushes / sr_cd
        
        self.get_poison_counts(attacks_per_second, current_stats)
        
        if self.stats.gear_buffs.rogue_t18_4pc:
            finishers_per_second = sum(attacks_per_second['eviscerate']) + attacks_per_second['rupture']
            avg_cdr = 5 #assume all 5cp finishers
            self.vanish_cd_modifier = (1./avg_cdr) / (finishers_per_second + (1./avg_cdr))

        return attacks_per_second, crit_rates, additional_info
