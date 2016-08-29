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

class ConvergenceErrorException(exceptions.InvalidInputException):
    # Return this if a convergence loop goes too long
    pass


class AldrianasRogueDamageCalculator(RogueDamageCalculator):
    ###########################################################################
    # Main DPS comparison function.  Calls the appropriate sub-function based
    # on talent tree.
    ###########################################################################

    def get_dps(self):
        super(AldrianasRogueDamageCalculator, self).get_dps()
        if self.spec == 'assassination':
            self.init_assassination()
            return 0
            #return self.assassination_dps_estimate()
        elif self.spec == 'outlaw':
            return self.outlaw_dps_estimate()
        elif self.spec == 'subtlety':
            return self.subtlety_dps_estimate()
        else:
            raise InputNotModeledException(_('You must specify a spec.'))

    def get_dps_breakdown(self):
        if self.spec == 'assassination':
            self.init_assassination() # why the special init?
            return self.assassination_dps_breakdown()
        elif self.spec == 'outlaw':
            return self.outlaw_dps_breakdown()
        elif self.spec == 'subtlety':
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

    #i don't know why this is overridden, but I disabled it to fix talent ranking
    #def get_talents_ranking(self, list=None):
    #    if list is None:
    #        list = [
    #            'nightstalker',
    #            'subterfuge',
    #            'shadow_focus',
    #            #'shuriken_toss',
    #            'marked_for_death',
    #            'anticipation',
    #            'lemon_zest',
    #            'death_from_above',
    #            'shadow_reflection',
    #        ]
    #    return super(AldrianasRogueDamageCalculator, self).get_talents_ranking(list)

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

    def get_crit_rates(self, stats):
        base_melee_crit_rate = self.crit_rate(crit=stats['crit'])
        crit_rates = {
            'mh_autoattacks': min(base_melee_crit_rate, self.dw_mh_hit_chance),
            'oh_autoattacks': min(base_melee_crit_rate, self.dw_oh_hit_chance),
        }

        for attack in ('rupture_ticks', 'shuriken_toss'):
            crit_rates[attack] = base_melee_crit_rate

        if self.spec == 'assassination':
            spec_attacks = self.assassination_damage_sources
        elif self.spec == 'outlaw':
            spec_attacks = self.outlaw_damage_sources
        elif self.spec == 'subtlety':
            spec_attacks = self.subtlety_damage_sources

        for attack in spec_attacks:
            #for handling odd crit rates
            if attack == 'mutilate' and self.traits.balanced_blades:
                crit_rates[attack] = base_melee_crit_rate + (0.02 * self.traits.balanced_blades)
            elif attack == 'rupture_ticks' and self.traits.serrated_edge:
                crit_rates[attack] = base_melee_crit_rate + (0.03333 * self.traits.serrated_edge)
            elif attack  in ('pistol_shot', 'blunderbuss') and self.traits.gunslinger:
                crit_rates[attack] = base_melee_crit_rate + (0.06 * self.traits.gunslinger)
            elif attack == 'eviscerate' and self.traits.gutripper:
                crit_rates[attack] = base_melee_crit_rate + (0.05 * self.traits.gutripper)
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
        if self.settings.feint_interval != 0:
            self.bonus_energy_regen -= self.get_spell_stats('feint')[0] / self.settings.feint_interval


        #only include if general multiplier applies to spec calculations
        self.true_haste_mod *= self.get_heroism_haste_multiplier()
        self.base_stats = {
            'agi': (self.stats.agi + self.buffs.buff_agi(race=self.race.epicurean) + self.race.racial_agi),
            'ap': (self.stats.ap),
            'crit': (self.stats.crit + self.buffs.buff_crit(race=self.race.epicurean)),
            'haste': (self.stats.haste + self.buffs.buff_haste(race=self.race.epicurean)),
            'mastery': (self.stats.mastery + self.buffs.buff_mast(race=self.race.epicurean)),
            'versatility': (self.stats.versatility + self.buffs.buff_versatility(race=self.race.epicurean)),
        }
        self.stat_multipliers = {
            'str': 1.,
            'agi': self.stats.gear_buffs.gear_specialization_multiplier(),
            'ap': 1,
            'crit': 1. + (0.02 * self.race.human_spirit),
            'haste': 1. + (0.02 * self.race.human_spirit),
            'mastery': 1. + (0.02 * self.race.human_spirit),
            'versatility': 1. + (0.02 * self.race.human_spirit),
        }

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

        self.base_strength = self.stats.str + self.race.racial_str
        self.base_intellect = self.stats.int + self.race.racial_int

        self.relentless_strikes_energy_return_per_cp = 5 #.20 * 25

        #should only include bloodlust if the spec can average it in, deal with this later
        self.base_speed_multiplier = 1.4
        if self.race.berserking:
            self.true_haste_mod *= (1 + .15 * 10. / (180 + self.settings.response_time))
        self.true_haste_mod *= 1 + self.race.get_racial_haste() #doesn't include Berserking
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

        #TODO Re-add multipliers here
        multiplier = 1
        '''if proc.stat == 'spell_damage':
            multiplier = self.get_modifiers(current_stats, damage_type='spell')
        elif proc.stat == 'physical_damage':
            multiplier = self.get_modifiers(current_stats, damage_type='physical')
        elif proc.stat == 'physical_dot':
            multiplier = self.get_modifiers(current_stats, damage_type='bleed')
        elif proc.stat == 'bleed_damage':
            multiplier = self.get_modifiers(current_stats, damage_type='bleed')
        else:
            return 0'''

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
            proc_value = total_swings*(average_ap/3.5) * (1+ self.settings.num_boss_adds)

        #.424*max(AP, SP)
        if proc is getattr(self.stats.procs, 'felmouth_frenzy'):
            proc_value = average_ap * 0.424 * 5

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
            for ability in ('mutilate', 'dispatch', 'backstab', 'pistol_shot', 'saber_slash', 'ambush', 'hemorrhage', 'mh_killing_spree', 'shuriken_toss'):
                if ability in attacks_per_second:
                    if proc.procs_off_crit_only():
                        triggers_per_second += attacks_per_second[ability] * crit_rates[ability]
                    else:
                        triggers_per_second += attacks_per_second[ability]
            for ability in ('envenom', 'eviscerate', 'run_through'):
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
        if self.spec == 'outlaw':
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

    def get_average_alacrity(self, attacks_per_second):
        stacks_per_second = 0.0
        for finisher in self.finisher_damage_sources:
            #Don't double count DfA
            if finisher in attacks_per_second and finisher != 'death_from_above_pulse':
                for cp in xrange(7):
                    stacks_per_second += 0.2 * cp * attacks_per_second[finisher][cp]
        stack_time = 20/stacks_per_second
        if stack_time > self.settings.duration:
            max_stacks = self.settings.duration * stacks_per_second
            return max_stacks/2
        else:
            max_time = self.settings.duration - stack_time
            return (max_time/self.settings.duration) * 20 + (stack_time/self.settings.duration) * 10

    def determine_stats(self, attack_counts_function):
        current_stats = {
            'str': self.base_strength,
            'agi': self.base_stats['agi'] * self.stat_multipliers['agi'],
            'ap': self.base_stats['ap'] * self.stat_multipliers['ap'],
            'crit': self.base_stats['crit'] * self.stat_multipliers['crit'],
            'haste': self.base_stats['haste'] * self.stat_multipliers['haste'],
            'mastery': self.base_stats['mastery'] * self.stat_multipliers['mastery'],
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

        if self.buffs.felmouth_food():
            self.stats.procs.set_proc('felmouth_frenzy')

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
            #check if... assassination:crit/haste, outlaw:mastery/haste, sub:haste/mastery
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
        # really only useful for outlaw calculations (restless blades calculations)
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

        self.spec_convergence_stats = ['haste', 'crit']

        # Assassasins's Resolve
        self.damage_modifier_cache = 1.17

        #update spec specific proc rates
        if getattr(self.stats.procs, 'legendary_capacitive_meta'):
            getattr(self.stats.procs, 'legendary_capacitive_meta').proc_rate_modifier = 1.789
        if getattr(self.stats.procs, 'fury_of_xuen'):
            getattr(self.stats.procs, 'fury_of_xuen').proc_rate_modifier = 1.55

        self.ability_cds['vanish'] = 120

        self.base_energy_regen = 10
        self.max_energy = 120.
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            self.max_energy += 30
        if self.talents.lemon_zest:
            self.base_energy_regen *= 1 + .05 * (1 + min(self.settings.num_boss_adds, 2))
            self.max_energy += 15
        if self.stats.gear_buffs.rogue_t18_4pc_lfr:
            self.max_energy += 20
        if self.race.expansive_mind:
            self.max_energy = round(self.max_energy * 1.05, 0)


        self.set_constants()
        self.stat_multipliers['mastery'] *= 1.05

        if getattr(self.stats.procs, 'bleeding_hollow_toxin_vessel'):
            spec_needs_converge = True
        self.envenom_crit_modifier = 0.0

        self.vendetta_duration = 20 #+ 10 * self.glyphs.vendetta
        self.vendetta_uptime = self.vendetta_duration / (self.get_spell_cd('vendetta') + self.settings.response_time + self.major_cd_delay)
        self.vendetta_multiplier = .3 #- .05 * self.glyphs.vendetta
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
        #multistrike_multiplier = .3 * 2 * (self.stats.get_multistrike_chance_from_rating(rating=current_stats['multistrike']) + self.buffs.multistrike_bonus())
        #multistrike_multiplier = min(.6, multistrike_multiplier)

        soul_cap_mod = 1.0
        if getattr(self.stats.procs, 'soul_capacitor'):
            soul_cap= getattr(self.stats.procs, 'soul_capacitor')
            self.set_rppm_uptime(soul_cap)
            soul_cap_mod = 1+(soul_cap.uptime * soul_cap.value['damage_mod']/10000.)

        infallible_trinket_mod = 1.0
        if self.settings.is_demon:
            if getattr(self.stats.procs, 'infallible_tracking_charm_mod'):
                ift = getattr(self.stats.procs, 'infallible_tracking_charm_mod')
                self.set_rppm_uptime(ift)
                infallible_trinket_mod = 1+(ift.uptime *0.10)


        maalus_mod = 1.0
        if getattr(self.stats.procs,'maalus'):
            maalus = getattr(self.stats.procs, 'maalus')
            maalus_val = maalus.value['damage_mod']/10000.
            maalus_mod = 1 + (15.0/120* maalus_val) #super hackish


        for key in damage_breakdown:
            damage_breakdown[key] *= maalus_mod
            #Fel Lash doesn't MS
            if key == 'Fel Lash':
                continue
            damage_breakdown[key] *= 1
            #mirror of the blademaster doesn't get any player buffs
            if key == 'Mirror of the Blademaster':
                continue
            if ('sr_' not in key):
                damage_breakdown[key] *= self.vendetta_mult
                damage_breakdown[key] *= soul_cap_mod
                damage_breakdown[key] *= infallible_trinket_mod
            elif 'sr_' in key:
                damage_breakdown[key] *= 1 + self.vendetta_multiplier
            if self.level == 100 and key in ('mutilate', 'dispatch', 'sr_mutilate', 'sr_mh_mutilate', 'sr_oh_mutilate', 'sr_dispatch'):
                damage_breakdown[key] *= self.emp_envenom_percentage
            if self.stats.gear_buffs.rogue_t18_2pc:
                if key == 'dispatch':
                    damage_breakdown[key]*= 1+(0.25 * (1+(self.stats.get_mastery_from_rating(rating=current_stats['mastery'])*self.assassination_mastery_conversion)))

        #add maalus burst
        if maalus_mod > 1.0:
            damage_breakdown['maalus'] = sum(damage_breakdown.values())*(maalus_mod-1.0) * (self.settings.num_boss_adds+1)

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
        avg_count = {'mutilate':0, 'hemorrhage':0}
        avg_breakdown = [0,0,0,0,0,0]
        new_count = copy(ability_count)

        if blindside_proc or execute:
            new_count['hemorrhage'] += 1 # these hemos are dispatch hacks

            n_chance = 1 - crit_rates['hemorrhage']
            c_chance = crit_rates['hemorrhage']
            if self.stats.gear_buffs.rogue_t18_4pc:
                n_value, n_proc, n_count, n_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+3, crit_rates, new_count, current_sizes, cp_limit=cp_limit, execute=execute)
                c_value, c_proc, c_count, c_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+4, crit_rates, new_count, current_sizes, cp_limit=cp_limit, execute=execute)
            else:
                n_value, n_proc, n_count, n_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+1, crit_rates, new_count, current_sizes, cp_limit=cp_limit, execute=execute)
                c_value, c_proc, c_count, c_breakdown = self.assassination_cp_distribution_for_finisher(current_cp+2, crit_rates, new_count, current_sizes, cp_limit=cp_limit, execute=execute)

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
        self.settings.time_in_execute_range = 1 #hack old settings
        attacks_per_second = {}
        additional_info = {}
        #can't rely on a cache, due to the Cold Blood perk
        crit_rates = self.get_crit_rates(current_stats)
        for key in crit_rates:
            if key in ('mutilate', 'garrote', 'hemorrhage'):
                crit_rates[key]+=self.envenom_crit_modifier
                crit_rates[key] = min(crit_rates[key], 1.0)

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod
        ability_cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_reduced_cost()

        energy_regen = self.base_energy_regen * haste_multiplier
        if self.stats.gear_buffs.rogue_t17_4pc_lfr:
            #http://www.wolframalpha.com/input/?i=1.1307+*+%281+-+e+**+%28-1+*+1.1+*+6%2F+60%29%29
            #https://twitter.com/Celestalon/status/525350819856535552
            energy_regen *= 1 + (.11778034322021550695 * .3) #11% uptime on 30% boost)
        if self.stats.gear_buffs.rogue_t18_4pc_lfr:
            energy_regen *= 1.05
        energy_regen += self.bonus_energy_regen
        if cpg == 'hemorrhage': # dispatch hack
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

        seal_fate_proc_rate = crit_rates['hemorrhage'] # just hacked in to get rid of dispatch errors
        if cpg == 'mutilate':
            seal_fate_proc_rate *= blindside_proc_rate
            seal_fate_proc_rate += 1 - (1 - crit_rates['mutilate']) ** 2

        mutilate_cps = 3 - (1 - crit_rates['mutilate']) ** 2 # 1 - (1 - crit_rates['mutilate']) ** 2 is the Seal Fate CP
        dispatch_cps = 1 + crit_rates['hemorrhage'] #hack get rid of dispatch errors
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
            ability_count = {'mutilate':0, 'hemorrhage':0} #hack to get rid of dispatch errors
            finisher_size_breakdown = [0,0,0,0,0,0]

            #This is incredibly verbose, but functional. It exhaustively calculates the potential finisher size outcomes using recursion.
            #avg_finisher_size - measures average finisher size
            #avg_bs_afterwards - likelyhood of finishing with a blindside proc active
            #avg_count - number of ability casts per finisher (dictionary of both Mutilate and Dispatch)
            #avg_breakdown - frequency of finisher sizes (should sum to 100% or 1)
            execute = False
            base_cp = 0
            min_finisher_size = self.settings.cycle.min_envenom_size_non_execute
            if cpg == 'hemorrhage': #hack to get rid of dispatch errors
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

        cpg_energy_cost = self.get_spell_cost(cpg, cost_mod=ability_cost_modifier)
        cpg_cost_reduction = 0
        if self.stats.gear_buffs.rogue_t17_2pc:
            cpg_cost_reduction = 8 * crit_rates['mutilate'] #4 per hand, double crit is 2 procs
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            cpg_cost_reduction = 6 * seal_fate_proc_rate
        cpg_energy_cost -= cpg_cost_reduction

        ##hardcode an opner for now
        #current_opener_name = 'garrote'
        ##if self.settings.opener_name == 'cpg':
        #current_opener_name = cpg

        #cp_generated = 0
        #if current_opener_name == 'envenom':
        #    opener_net_cost = self.get_spell_cost('envenom', cost_mod=ability_cost_modifier*(1-self.get_shadow_focus_multiplier()))
        #    energy_regen += opener_net_cost * self.total_openers_per_second
        #elif current_opener_name == cpg:
        #    opener_net_cost = self.get_spell_cost(current_opener_name, cost_mod=(1-self.get_shadow_focus_multiplier()))
        #    opener_net_cost += cpg_cost_reduction
        #    cp_generated = avg_cp_per_cpg
        #    #energy_regen += opener_net_cost * self.total_openers_per_second
        #    energy_regen += opener_net_cost * 1 #hack opener per sec calc
        #else:
        #    opener_net_cost = self.get_spell_cost(current_opener_name, cost_mod=self.get_shadow_focus_multiplier())
        #    #attacks_per_second[current_opener_name] = self.total_openers_per_second
        #    attacks_per_second[current_opener_name] = self.total_openers_per_second
        #    if current_opener_name == 'mutilate':
        #        attacks_per_second['hemorrhage'] += self.total_openers_per_second * blindside_proc_rate # more dispatch hacks
        #    if current_opener_name in ('mutilate', 'hemorrhage', 'cpg'): #another dispatch hack
        #        cp_generated = mutilate_cps + dispatch_cps * blindside_proc_rate
        #    elif current_opener_name == 'ambush':
        #        cp_generated = 2 + crit_rates['ambush']
        #    energy_regen -= opener_net_cost * self.total_openers_per_second
        #for i in xrange(1,6):
        #    attacks_per_second['envenom'][i] = self.total_openers_per_second * cp_generated / i * avg_size_breakdown[i]

        attacks_per_second['venomous_wounds'] = .5
        energy_regen_with_rupture = energy_regen + .5 * vw_energy_return

        avg_cycle_length = 4. * (1 + avg_finisher_size + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())

        energy_for_rupture = avg_cpgs_per_finisher * cpg_energy_cost + self.get_spell_cost('rupture', cost_mod=ability_cost_modifier)
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

        envenom_energy_cost = avg_cpgs_per_finisher * cpg_energy_cost + self.get_spell_cost('envenom', cost_mod=ability_cost_modifier)
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
        #if cpg == 'mutilate':
        #    attacks_per_second['hemorrhage'] += cpgs_per_second * blindside_proc_rate #another dispatch hack

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

        #if self.talents.shadow_reflection:
        #    sr_uptime = 8. / self.get_spell_cd('shadow_reflection')
        #    for ability in ('rupture_ticks', 'dispatch'):
        #        if type(attacks_per_second[ability]) in (tuple, list):
        #            attacks_per_second['sr_'+ability] = [0,0,0,0,0,0]
        #            for i in xrange(1, 6):
        #                attacks_per_second['sr_'+ability][i] = sr_uptime * attacks_per_second[ability][i]
        #        else:
        #            attacks_per_second['sr_'+ability] = sr_uptime * attacks_per_second[ability]
        #    envenom_per_sr = 1.5 * sum(attacks_per_second['envenom'])
        #    attacks_per_second['sr_envenom'] = [finisher_chance * envenom_per_sr / self.get_spell_cd('shadow_reflection') for finisher_chance in avg_size_breakdown]
        #    crit_rates['sr_envenom'] = 1./envenom_per_sr + (1-envenom_per_sr)/envenom_per_sr * crit_rates['envenom']
        #    if 'mutilate' in attacks_per_second:
        #        attacks_per_second['sr_mh_mutilate'] = 2 * sr_uptime * attacks_per_second['mutilate']
        #        attacks_per_second['sr_oh_mutilate'] = 2 * sr_uptime * attacks_per_second['mutilate']

        self.swing_reset_spacing = None #hack resets for now
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

        self.settings.dmg_poison = 'dp' #hack in deadly poison for now
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
        return self.assassination_attack_counts(current_stats, 'hemorrhage', self.settings.cycle.min_envenom_size_execute, crit_rates=crit_rates)

    ###########################################################################
    # Outlaw DPS functions
    ###########################################################################

    #Legion TODO:

    #Talents:
        #T3:Anticipation
        #T6:Marked for Death

    #Artifact:
        # 'curse_of_the_dreadblades',
        # 'hidden_blade', (ambush proc weirdness)
        # 'blurred_time',

    #Items:
        #Class hall set bonus
        #Tier bonus
        #Trinkets
        #Legendaries

    #Rotation details:

    def outlaw_dps_estimate(self):
        return sum(self.outlaw_dps_breakdown().values())

    def outlaw_dps_breakdown(self):
        if not self.spec == 'outlaw':
            raise InputNotModeledException(_('You must specify a outlaw cycle to match your outlaw spec.'))

        #outlaw specific constants
        self.outlaw_cd_delay = 0 #this is for DFA convergence, mostly

        self.damage_modifier_cache = 1 + (0.005 * self.traits.cursed_steel)

        self.ar_duration = 15
        self.ar_cd = self.get_spell_cd('adrenaline_rush')

        self.set_constants()

        #table of minicycle ability amounts
        #indexed by (min_spend_cps, deeper_strat, quick_draw, swordmaster, broadside, jollyroger)
        #values are (ss_per_min_cycle, ps_per_min_cycle, finisher_cp_list)
        #TODO: 60 element table is probably a bit much, should probably be condensed
        self.minicycle_table = {
            (4, True, True, False, True, True) : (0.92778015, 0.5566681, [0, 0, 0, 0, 0.46230870485305786, 0.40208783745765686, 0.13560345768928528]) ,
            (4, True, True, False, True, False) : (1.2831669, 0.44910839, [0, 0, 0, 0, 0.35908344388008118, 0.49529376626014709, 0.14562278985977173]) ,
            (4, True, True, False, False, True) : (1.3207548, 0.79245281, [0, 0, 0, 0, 0.37735849618911743, 0.62264150381088257, 0.0]) ,
            (4, True, True, False, False, False) : (1.7271835, 0.60451424, [0, 0, 0, 0, 0.57409226894378662, 0.42590776085853577, 0.0]) ,
            (4, True, False, True, True, True) : (1.7995313, 1.2596719, [0, 0, 0, 0, 0.19270744919776917, 0.39063876867294312, 0.41665378212928772]) ,
            (4, True, False, True, True, False) : (1.759297, 0.79168367, [0, 0, 0, 0, 0.13849352300167084, 0.56256377696990967, 0.29894271492958069]) ,
            (4, True, False, True, False, True) : (1.3918972, 0.97432804, [0, 0, 0, 0, 0.82430845499038696, 0.17569157481193542, 0.0]) ,
            (4, True, False, True, False, False) : (1.7689608, 0.79603237, [0, 0, 0, 0, 0.7987181544303894, 0.20128187537193298, 0.0]) ,
            (4, True, False, False, True, True) : (1.7663901, 1.059834, [0, 0, 0, 0, 0.17100141942501068, 0.45841407775878906, 0.37058448791503906]) ,
            (4, True, False, False, True, False) : (1.7791812, 0.62271339, [0, 0, 0, 0, 0.11556066572666168, 0.63698828220367432, 0.24745103716850281]) ,
            (4, True, False, False, False, True) : (1.5257645, 0.91545868, [0, 0, 0, 0, 0.80414772033691406, 0.19585229456424713, 0.0]) ,
            (4, True, False, False, False, False) : (1.9706308, 0.68972075, [0, 0, 0, 0, 0.81240963935852051, 0.1875903457403183, 0.0]) ,
            (4, False, True, False, True, True) : (0.90085906, 0.54051542, [0, 0, 0, 0, 0.46230870485305786, 0.53769129514694214, 0]) ,
            (4, False, True, False, True, False) : (1.2441286, 0.43544501, [0, 0, 0, 0, 0.35908344388008118, 0.64091658592224121, 0]) ,
            (4, False, True, False, False, True) : (1.3207548, 0.79245281, [0, 0, 0, 0, 0.37735849618911743, 0.62264150381088257, 0]) ,
            (4, False, True, False, False, False) : (1.7271835, 0.60451424, [0, 0, 0, 0, 0.57409226894378662, 0.42590776085853577, 0]) ,
            (4, False, False, True, True, True) : (1.6560036, 1.1592025, [0, 0, 0, 0, 0.19270744919776917, 0.80729258060455322, 0]) ,
            (4, False, False, True, True, False) : (1.6573817, 0.74582177, [0, 0, 0, 0, 0.13849352300167084, 0.86150646209716797, 0]) ,
            (4, False, False, True, False, True) : (1.3918972, 0.97432804, [0, 0, 0, 0, 0.82430845499038696, 0.17569157481193542, 0]) ,
            (4, False, False, True, False, False) : (1.7689608, 0.79603237, [0, 0, 0, 0, 0.7987181544303894, 0.20128187537193298, 0]) ,
            (4, False, False, False, True, True) : (1.640496, 0.98429757, [0, 0, 0, 0, 0.17100141942501068, 0.82899856567382812, 0]) ,
            (4, False, False, False, True, False) : (1.693392, 0.59268725, [0, 0, 0, 0, 0.11556066572666168, 0.88443934917449951, 0]) ,
            (4, False, False, False, False, True) : (1.5257645, 0.91545868, [0, 0, 0, 0, 0.80414772033691406, 0.19585229456424713, 0]) ,
            (4, False, False, False, False, False) : (1.9706308, 0.68972075, [0, 0, 0, 0, 0.81240963935852051, 0.1875903457403183, 0]) ,
            (5, True, True, False, True, True) : (1.5440897, 0.92645377, [0, 0, 0, 0, 0, 0.47792428731918335, 0.52207571268081665]) ,
            (5, True, True, False, True, False) : (1.6837471, 0.58931148, [0, 0, 0, 0, 0, 0.52392536401748657, 0.47607460618019104]) ,
            (5, True, True, False, False, True) : (1.509434, 0.90566039, [0, 0, 0, 0, 0, 0.71698111295700073, 0.28301885724067688]) ,
            (5, True, True, False, False, False) : (2.0673864, 0.72358519, [0, 0, 0, 0, 0, 0.70232254266738892, 0.29767745733261108]) ,
            (5, True, False, True, True, True) : (2.7676663, 1.9373665, [0, 0, 0, 0, 0, 0.32654938101768494, 0.67345058917999268]) ,
            (5, True, False, True, True, False) : (2.0575211, 0.92588449, [0, 0, 0, 0, 0, 0.53625214099884033, 0.46374788880348206]) ,
            (5, True, False, True, False, True) : (1.7693849, 1.2385694, [0, 0, 0, 0, 0, 0.69184529781341553, 0.30815470218658447]) ,
            (5, True, False, True, False, False) : (2.1994596, 0.98975676, [0, 0, 0, 0, 0, 0.7762836217880249, 0.22371639311313629]) ,
            (5, True, False, False, True, True) : (2.3502514, 1.4101509, [0, 0, 0, 0, 0, 0.41270622611045837, 0.58729374408721924]) ,
            (5, True, False, False, True, False) : (1.9709414, 0.68982947, [0, 0, 0, 0, 0, 0.62002801895141602, 0.37997198104858398]) ,
            (5, True, False, False, False, True) : (1.9163667, 1.14982, [0, 0, 0, 0, 0, 0.72999167442321777, 0.27000829577445984]) ,
            (5, True, False, False, False, False) : (2.4447069, 0.85564739, [0, 0, 0, 0, 0, 0.80499798059463501, 0.19500201940536499]) ,
            (5, False, True, False, True, True) : (1.475865, 0.88551903, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, True, False, True, False) : (1.6334157, 0.57169551, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, True, False, False, True) : (1.509434, 0.90566039, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, True, False, False, False) : (2.0673864, 0.72358519, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, False, True, True, True) : (2.5490196, 1.7843137, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, False, True, True, False) : (1.9435737, 0.87460816, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, False, True, False, True) : (1.7693849, 1.2385694, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, False, True, False, False) : (2.1994596, 0.98975676, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, False, False, True, True) : (2.1875, 1.3125, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, False, False, True, False) : (1.8803419, 0.65811968, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, False, False, False, True) : (1.9163667, 1.14982, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (5, False, False, False, False, False) : (2.4447069, 0.85564739, [0, 0, 0, 0, 0, 1.0, 0]) ,
            (6, True, True, False, True, True) : (2.7550187, 1.6530112, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, True, False, True, False) : (2.4767113, 0.86684889, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, True, False, False, True) : (1.8489302, 1.1093582, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, True, False, False, False) : (2.4813204, 0.86846215, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, False, True, True, True) : (1.8811882, 1.3168317, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, False, True, True, False) : (2.0423892, 0.91907513, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, False, True, False, True) : (2.1186955, 1.4830868, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, False, True, False, False) : (2.6321666, 1.1844751, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, False, False, True, True) : (1.9298246, 1.1578947, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, False, False, True, False) : (2.1415608, 0.74954629, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, False, False, False, True) : (2.2952538, 1.3771522, [0, 0, 0, 0, 0, 0, 1.0]) ,
            (6, True, False, False, False, False) : (2.9230175, 1.0230561, [0, 0, 0, 0, 0, 0, 1.0]) ,
        }

        stats, aps, crits, procs, additional_info = self.determine_stats(self.outlaw_attack_counts)
        damage_breakdown, additional_info  = self.compute_damage_from_aps(stats, aps, crits, procs, additional_info)

        bf_mod = .35
        if self.settings.cycle.blade_flurry:
            damage_breakdown['blade_flurry'] = 0
            for key in damage_breakdown:
                if key in self.blade_flurry_damage_sources:
                    damage_breakdown['blade_flurry'] += bf_mod * damage_breakdown[key] * self.settings.num_boss_adds

        infallible_trinket_mod = 1.0
        if self.settings.is_demon:
            if getattr(self.stats.procs, 'infallible_tracking_charm_mod'):
                ift = getattr(self.stats.procs, 'infallible_tracking_charm_mod')
                self.set_rppm_uptime(ift)
                infallible_trinket_mod = 1+(ift.uptime *0.10)

        for ability in damage_breakdown:
            damage_breakdown[ability] *= infallible_trinket_mod

        return damage_breakdown

    def outlaw_attack_counts(self, current_stats, crit_rates=None):
        attacks_per_second = {}
        additional_info = {}

        #Compute values that are true through all RtB variations
        self.base_energy_regen = 12.
        if self.talents.vigor:
            self.base_energy_regen *= 1.1
        if self.settings.cycle.blade_flurry:
            self.base_energy_regen *= .8 + (0.03333 * self.traits.blade_dancer)

        if crit_rates == None:
            crit_rates = self.get_crit_rates(current_stats)

        self.haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod

        combat_potency_proc_energy = 15 + (1 * self.traits.fortune_strikes)
        self.combat_potency_regen_per_oh = combat_potency_proc_energy * 3. * self.stats.oh.speed / 1.4  # the new "normalized" formula
        self.combat_potency_from_mg = combat_potency_proc_energy * 3.

        self.main_gauche_proc_rate = self.outlaw_mastery_conversion * self.stats.get_mastery_from_rating(current_stats['mastery'])
        cost_reducer = self.main_gauche_proc_rate * self.combat_potency_from_mg

        #compute MG lumped ability costs
        self.run_through_energy_cost = self.get_spell_cost('run_through') - (4 * self.traits.fatebringer) - cost_reducer
        self.between_the_eyes_energy_cost = self.get_spell_cost('between_the_eyes') - (4 * self.traits.fatebringer) - cost_reducer
        self.pistol_shot_energy_cost = self.get_spell_cost('run_through') - (4 * self.traits.fatebringer) - cost_reducer
        self.saber_slash_energy_cost = self.get_spell_cost('saber_slash') - cost_reducer
        self.death_from_above_energy_cost = max(0, self.get_spell_cost('death_from_above')  - (4 * self.traits.fatebringer) - cost_reducer * (1 + self.settings.num_boss_adds))
        if self.talents.slice_and_dice:
            self.slice_and_dice_cost = self.get_spell_cost('slice_and_dice') - (4 * self.traits.fatebringer)
        else:
            self.roll_the_bones_cost = self.get_spell_cost('roll_the_bones') - (4 * self.traits.fatebringer)
        if self.talents.ghostly_strike:
            self.ghostly_strike_cost = self.get_spell_cost('ghostly_strike') - cost_reducer

        self.white_swing_downtime = self.settings.response_time / self.get_spell_cd('vanish')
        #compute dps phases each non-rerolling rtb buff combo ar and not
        phases = {}
        ar_phases = {}

        keep_chance = 0.0
        keep_tb_uptime = 0.0
        keep_shark_uptime = 0.0
        keep_gm_uptime = 0.0
        maintainence_buff_duration = 6 * (1 + self.settings.finisher_threshold)
        if self.talents.slice_and_dice:
            aps_normal = self.outlaw_attack_counts_mincycle(current_stats, snd=True, duration=maintainence_buff_duration)
            aps_ar = self.outlaw_attack_counts_mincycle(current_stats, snd=True, ar=True, duration=self.ar_duration)
        else:
            for phase in self.settings.cycle.keep_list:
                jolly = 'jr' in phase
                melee = 'gm' in phase
                buried = 'bt' in phase
                broadsides = 'b' in phase
                true_bearing = 'tb' in phase
                shark = 's' in phase

                chance = self.rtb_probabilities[len(phase)]/self.rtb_buff_count[len(phase)]
                aps = self.outlaw_attack_counts_mincycle(current_stats, jolly=jolly, 
                        melee=melee, buried=buried, broadsides=broadsides, shark=shark, true_bearing=true_bearing,
                        duration=maintainence_buff_duration)
                aps_ar = self.outlaw_attack_counts_mincycle(current_stats,  ar=True, jolly=jolly, 
                        melee=melee, buried=buried, broadsides=broadsides, shark=shark, true_bearing=true_bearing,
                        duration=self.ar_duration)

                phases[phase] = (chance, aps)
                ar_phases[phase] = (chance, aps_ar)
                keep_chance += chance
                if melee:
                    keep_gm_uptime += chance
                if true_bearing:
                    keep_tb_uptime += chance
                if shark:
                    keep_shark_uptime += chance
            #merge ar and non-ar into single phases
            aps_normal = self.merge_attacks_per_second(phases, total_time=keep_chance)
            aps_ar = self.merge_attacks_per_second(ar_phases, total_time=keep_chance)
            #technically there is a convergence relationship here but ignoring it
            if self.talents.alacrity:
                alacrity_stacks = self.get_average_alacrity(aps_normal)
                alacrity_stacks_ar = self.get_average_alacrity(aps_ar)
            else:
                alacrity_stacks = 0
                alacrity_stacks_ar = 0
            #now compute the average time for each reroll
            phases = {}
            ar_phases = {}
            net_reroll_time = 0.0
            net_reroll_time_ar = 0.0
            reroll_tb_uptime = 0.0
            reroll_shark_uptime = 0.0
            reroll_gm_uptime = 0.0
            for phase in self.settings.cycle.reroll_list:
                jolly = 'jr' in phase
                melee = 'gm' in phase
                buried = 'bt' in phase
                broadsides = 'b' in phase
                true_bearing = 'tb' in phase
                shark = 's' in phase

                chance = self.rtb_probabilities[len(phase)]/self.rtb_buff_count[len(phase)]
                aps, reroll_time = self.outlaw_attack_counts_reroll(current_stats, jolly=jolly, 
                        melee=melee, buried=buried, broadsides=broadsides, alacrity_stacks=alacrity_stacks)
                aps_ar, reroll_time_ar = self.outlaw_attack_counts_reroll(current_stats,  ar=True, jolly=jolly, 
                        melee=melee, buried=buried, broadsides=broadsides, alacrity_stacks=alacrity_stacks_ar)
                phases[phase] = (chance * reroll_time, aps)
                ar_phases[phase] = (chance * reroll_time_ar, aps_ar)
                net_reroll_time += chance * reroll_time
                net_reroll_time_ar += chance * reroll_time_ar
                if true_bearing:
                    reroll_tb_uptime += chance * reroll_time
                if shark:
                    reroll_shark_uptime += chance * reroll_time
                if melee:
                    reroll_gm_uptime += chance * reroll_time

            reroll_tb_uptime *= 1./net_reroll_time
            reroll_shark_uptime *= 1./net_reroll_time
            reroll_gm_uptime *= 1./net_reroll_time

            aps_reroll = self.merge_attacks_per_second(phases, total_time=net_reroll_time)
            aps_reroll_ar = self.merge_attacks_per_second(phases, total_time=net_reroll_time_ar)
            #now combine the reroll and keep dicts
            rtb_keep_duration = 6 * (1+ self.settings.finisher_threshold)
            #will pandemic into rtb based on keep_chance
            rtb_keep_duration *= 1 + (0.3 * keep_chance)
            reroll_duration = net_reroll_time * len(self.settings.cycle.reroll_list)
            ar_reroll_duration = net_reroll_time_ar * len(self.settings.cycle.reroll_list)
            phases = {'keep': (rtb_keep_duration, aps_normal),
                      'reroll': (reroll_duration, aps_reroll)}
            aps_normal = self.merge_attacks_per_second(phases, rtb_keep_duration + reroll_duration)
            phases = {'keep': (rtb_keep_duration, aps_ar),
                      'reroll': (ar_reroll_duration, aps_reroll_ar)}
            aps_ar = self.merge_attacks_per_second(phases, rtb_keep_duration + ar_reroll_duration)

            keep_uptime = rtb_keep_duration/(rtb_keep_duration + reroll_duration)
            tb_uptime = (keep_uptime * keep_tb_uptime) + (1 - keep_uptime) * reroll_tb_uptime
            gm_uptime = (keep_uptime * keep_gm_uptime) + (1 - keep_uptime) * reroll_gm_uptime
            shark_uptime = (keep_uptime * keep_shark_uptime) + (1 - keep_uptime) * reroll_shark_uptime

        #determine ar uptime and merge the two distributions
        attacks_per_second = self.merge_attacks_per_second({'normal': (self.ar_cd - self.ar_duration, aps_normal),
            'ar': (self.ar_duration, aps_ar)}, total_time=self.ar_cd)
        ar_uptime = self.ar_duration / self.ar_cd
        tb_seconds_per_second = 0
        #if rtb loop on ar cooldown
        if not self.talents.slice_and_dice:
            old_ar_cd = self.ar_duration
            loop_counter = 0
            while (loop_counter < 20):
                cp_spend_per_second = 0
                for ability in attacks_per_second:
                    if ability in self.finisher_damage_sources:
                        for cp in xrange(7):
                            cp_spend_per_second += attacks_per_second[ability][cp] * cp
                tb_seconds_per_second = 2 * cp_spend_per_second * tb_uptime
                new_ar_cd = self.ar_cd/(1 + tb_seconds_per_second)
                #remerge the ars
                attacks_per_second = self.merge_attacks_per_second({'normal': (new_ar_cd - self.ar_duration, aps_normal),
                    'ar': (self.ar_duration, aps_ar)}, total_time=new_ar_cd)
                
                if old_ar_cd - new_ar_cd < 0.1:
                    break
                else:
                    old_ar_cd = new_ar_cd
            ar_uptime = self.ar_duration / new_ar_cd
        
        #add in cannonball and killing spree
        if self.talents.killing_spree:
            ksp_cd = self.get_spell_cd('killing_spree') / (1. + tb_seconds_per_second)
            #ksp is 7 hits per hand
            attacks_per_second['killing_spree'] = 7./ksp_cd
        if self.talents.cannonball_barrage:
            cannonball_barrage_cd = self.get_spell_cd('cannonball_barrage') / (1. + tb_seconds_per_second)
            attacks_per_second['cannonball_barrage'] = 1./cannonball_barrage_cd


        #figure swing timer and add mg
        attack_speed_multiplier = self.haste_multiplier * (1 + (0.9 * self.talents.slice_and_dice))
        attack_speed_multiplier *= (1 + (0.2 * ar_uptime))
        if not self.talents.slice_and_dice:
            attack_speed_multiplier *= (1 + (0.5 * gm_uptime))
        swing_timer = self.stats.mh.speed / attack_speed_multiplier
        attacks_per_second['mh_autoattacks'] = 1./swing_timer
        attacks_per_second['oh_autoattacks'] = 1./swing_timer
        attacks_per_second['main_gauche'] = self.main_gauche_proc_rate * attacks_per_second['mh_autoattacks'] * self.dual_wield_mh_hit_chance()
        #add in mg
        for ability in attacks_per_second:
            if ability in ['ambush', 'ghostly_strike', 'killing_spree', 'saber_slash']:
                attacks_per_second['main_gauche'] += self.main_gauche_proc_rate * attacks_per_second[ability]
            elif ability in ['death_from_above_pulse', 'death_from_above_strike','run_through',]:
                attacks_per_second['main_gauche'] += sum(attacks_per_second[ability]) * self.main_gauche_proc_rate

        if not self.talents.slice_and_dice:
            crit_mod = 1 + (0.25 * shark_uptime)
            for ability in crit_rates:
                if ability == 'between_the_eyes' and self.settings.cycle.between_the_eyes_policy == 'shark':
                    crit_rates[ability] += 0.25
                else:
                    crit_rates[ability] += crit_mod

        if self.traits.greed:
            attacks_per_second['greed'] = 0.35 * sum(attacks_per_second['run_through'])

        if self.traits.blunderbuss:
            attacks_per_second['blunderbuss'] = 0.33 * attacks_per_second['pistol_shot']
            attacks_per_second['pistol_shot'] -= attacks_per_second['blunderbuss']

        #print attacks_per_second
        return attacks_per_second, crit_rates, additional_info

    def outlaw_attack_counts_mincycle(self, current_stats, snd=False, ar=False,
        jolly=False, melee=False, buried=False, broadsides=False, duration=30,
        #probably don't actually need shark or tb here but simpler
        shark=False, true_bearing=True):
        maintainence_buff ='roll_the_bones'
        attack_speed_multiplier = self.haste_multiplier
        if melee:
            attack_speed_multiplier *= 1.5
        if snd:
            attack_speed_multiplier *= 1.9
            maintainence_buff = 'slice_and_dice'

        energy_regen = self.base_energy_regen * self.haste_multiplier
        if buried:
            energy_regen *= 1.25

        if ar:
            attack_speed_multiplier *= 1.2
            energy_regen *= 2.0

        gcd_size = 1.0 + self.settings.latency
        if ar:
            gcd_size -= .2

        #fetch minicycle value
        minicycle_key = (self.settings.finisher_threshold, bool(self.talents.deeper_strategem), bool(self.talents.quick_draw),
                         bool(self.talents.swordmaster), broadsides, jolly)
        ss_count, ps_count, finisher_list = self.minicycle_table[minicycle_key]

        # set up our initial budgets
        energy_budget = duration * energy_regen
        gcd_budget = duration/gcd_size

        #since artifacts we'll just compute a one handed swing timer
        if self.talents.death_from_above and not ar:
            dfa_cd = self.get_spell_cd('death_from_above') + self.settings.response_time - (10 * true_bearing)
            dfa_count = duration/dfa_cd
            dfa_lost_swings = self.lost_swings_from_swing_delay(1.3, self.mh.speed/attack_speed_multiplier)
            dfa_energy_lost = dfa_lost_swings * (self.main_gauche_proc_rate * self.combat_potency_from_mg + self.combat_potency_regen_per_oh)
            energy_budget -= dfa_energy_lost
        
        mg_cp_energy = self.get_mg_cp_regen_from_haste(attack_speed_multiplier) * (1 - self.white_swing_downtime)
        energy_budget += mg_cp_energy

        attacks_per_second = {}

        #consider the cost of building to max cps and using rtb
        energy_budget -= ss_count * self.saber_slash_energy_cost
        #don't account for ps energy becuase ps is free
        if snd:
            energy_budget -= self.slice_and_dice_cost
        else:
            energy_budget -= self.roll_the_bones_cost
        gcd_budget -= (ss_count + ps_count + 1)
        attacks_per_second['saber_slash'] = float(ss_count)/duration
        attacks_per_second['pistol_shot'] = float(ps_count)/duration

        attacks_per_second[maintainence_buff] = [0, 0, 0, 0, 0, 0, 0]
        for cp in xrange(7):
            attacks_per_second[maintainence_buff][cp] += finisher_list[cp]/duration

        if (shark and self.settings.cycle.between_the_eyes_policy == 'shark') or self.settings.cycle.between_the_eyes_policy == 'always':
            bte_count = duration/(20 + self.settings.response_time - (10 * true_bearing))
            attacks_per_second['between_the_eyes'] = [0, 0, 0, 0, 0, 0, 0]
            for cp in xrange(7):
                attacks_per_second['between_the_eyes'][cp] += float(finisher_list[cp] * bte_count)/duration
            attacks_per_second['pistol_shot'] += float(bte_count * ps_count)/duration
            attacks_per_second['saber_slash'] += float(bte_count * ss_count)/duration
            energy_budget -= (bte_count * ss_count) * self.saber_slash_energy_cost
            energy_budget -= bte_count * self.between_the_eyes_energy_cost
            gcd_budget -= bte_count * (ss_count + ps_count + 1)

        #consider DfA
        if self.talents.death_from_above and not ar:
            energy_budget -= ss_count * dfa_count * self.saber_slash_energy_cost
            energy_budget -= dfa_count * self.death_from_above_energy_cost
            attacks_per_second['saber_slash'] += float(ss_count * dfa_count)/duration
            attacks_per_second['pistol_shot'] += float(ps_count * dfa_count)/duration
            attacks_per_second['death_from_above_strike'] = [0, 0, 0, 0, 0, 0, 0]
            attacks_per_second['death_from_above_pulse'] = [0, 0, 0, 0, 0, 0, 0]
            for cp in xrange(7):
                attacks_per_second['death_from_above_strike'][cp] *= float(finisher_list[cp] * dfa_count)/duration
                attacks_per_second['death_from_above_pulse'][cp] *= float(finisher_list[cp] * dfa_count)/duration
            #DfA forces a 2 second GCD
            gcd_budget -= dfa_count * (ss_count + ps_count + 2)

        #consider ghostly strike
        if self.talents.ghostly_strike:
            gs_count = duration/15.
            gs_cps = gs_count * (1 + broadsides)
            gs_energy = self.ghostly_strike_cost * gs_count
            #TODO: use these ghostly strike cps
            energy_budget -= gs_energy
            gcd_budget -= gs_count
            attacks_per_second['ghostly_strike'] = float(gs_count)/duration

        #Burn the rest of our energy until you run out of energy or gcds
        gcds_per_minicycle = ss_count + ps_count + 1
        energy_per_minicycle = ss_count * self.saber_slash_energy_cost + self.run_through_energy_cost

        alacrity_stacks = 0
        loop_counter = 0
        while energy_budget > 0.1 and gcd_budget > 0.1:
            if loop_counter > 20:
                   raise ConvergenceErrorException(_('Mini-cycles failed to converge.'))

            loop_counter += 1
            minicycle_count = min(gcd_budget/gcds_per_minicycle, energy_budget/energy_per_minicycle)
            
            attacks_per_second['saber_slash'] += float(minicycle_count * ss_count)/duration
            attacks_per_second['pistol_shot'] += float(minicycle_count * ps_count)/duration
            attacks_per_second['run_through'] = [0, 0, 0, 0, 0, 0, 0]
            for cp in xrange(7):
                attacks_per_second['run_through'][cp] += float(minicycle_count * finisher_list[cp])/duration

            #Don't need to converge if we don't have alacrity
            if not self.talents.alacrity:
                break
            else:
                energy_budget -= minicycle_count * energy_per_minicycle
                gcd_budget -= minicycle_count * gcds_per_minicycle

                #ar doubles the effect of alacrity while up
                old_alacrity_regen = energy_regen * (1 + (alacrity_stacks *0.01)) * (1 + int(ar))
                new_alacrity_stacks = self.get_average_alacrity(attacks_per_second)
                new_alacrity_regen = energy_regen * (1 + (new_alacrity_stacks *0.01)) * (1 + int(ar))
                energy_budget += (new_alacrity_regen - old_alacrity_regen) * duration 
                #compute new CP/MG regen
                old_cp_mg = self.get_mg_cp_regen_from_haste(attack_speed_multiplier * 1 + (0.01 * alacrity_stacks))
                new_cp_mg = self.get_mg_cp_regen_from_haste(attack_speed_multiplier * 1 + (0.01 * new_alacrity_stacks))
                energy_budget += new_cp_mg - old_cp_mg
                alacrity_stacks = new_alacrity_stacks

        #skip white swings and mg procs because we can do those later
        return attacks_per_second

    def outlaw_attack_counts_reroll(self, current_stats, ar=False,
        jolly=False, melee=False, buried=False, broadsides=False, alacrity_stacks=0):
        #fetch minicycle value
        minicycle_key = (self.settings.finisher_threshold, bool(self.talents.deeper_strategem), bool(self.talents.quick_draw),
                         bool(self.talents.swordmaster), broadsides, jolly)
        ss_count, ps_count, finisher_list = self.minicycle_table[minicycle_key]
        reroll_energy_cost = (ss_count * self.saber_slash_energy_cost) + self.roll_the_bones_cost
        energy_regen = self.base_energy_regen * (self.haste_multiplier + 0.01 * alacrity_stacks)
        if buried:
            energy_regen *= 1.25
        attack_speed_multiplier = self.haste_multiplier + 0.01 * alacrity_stacks
        if melee:
            attack_speed_multiplier *= 1.5
        if ar:
            energy_regen *= 2.0
            attack_speed_multiplier *= 1.2

        mg_cp_energy = self.get_mg_cp_regen_from_haste(attack_speed_multiplier)
        total_regen = energy_regen + mg_cp_energy
        reroll_time = reroll_energy_cost / total_regen
        attacks_per_second = {}
        attacks_per_second['saber_slash'] = float(ss_count)/reroll_time
        attacks_per_second['pistol_shot'] = float(ps_count)/reroll_time
        attacks_per_second['roll_the_bones'] = [0, 0, 0, 0, 0, 0, 0]
        for cp in xrange(7):
            attacks_per_second['roll_the_bones'][cp] *= finisher_list[cp]/reroll_time
        return attacks_per_second, reroll_time


    #dict of (probability, aps) pairs
    def merge_attacks_per_second(self, aps_dicts, total_time=1.0):
        attacks_per_second = {}
        for key in aps_dicts:
            proportion, aps = aps_dicts[key]
            uptime = float(proportion)/total_time

            for ability in aps:
                if ability in attacks_per_second:
                    if isinstance(attacks_per_second[ability], list):
                        for cp in xrange(7):
                            attacks_per_second[ability][cp] += uptime * aps[ability][cp]
                    else:    
                        attacks_per_second[ability] += uptime * aps[ability]
                else:
                    if isinstance(aps[ability], list):
                        attacks_per_second[ability] = aps[ability]
                        for cp in xrange(7):
                            attacks_per_second[ability][cp] *= uptime
                    else:
                        attacks_per_second[ability] = uptime * aps[ability]
        return attacks_per_second

    def get_mg_cp_regen_from_haste(self, haste_multiplier):
        swing_per_second = (self.stats.mh.speed * self.dw_mh_hit_chance)/haste_multiplier
        mg_regen = self.main_gauche_proc_rate * self.combat_potency_from_mg * swing_per_second
        cp_regen = self.combat_potency_regen_per_oh * swing_per_second
        return mg_regen + cp_regen

    def get_max_energy(self):
        self.max_energy = 100
        if self.talents.vigor:
            self.max_energy += 50
        if self.race.expansive_mind:
            self.max_energy = round(self.max_energy * 1.05, 0)
        return self.max_energy

    ###########################################################################
    # Subtlety DPS functions
    ###########################################################################

    #Legion TODO:

    #Artifact:
        # 'flickering_shadows',

    #Items:
        #Class hall set bonus
        #Tier bonus
        #Trinkets
        #Legendaries

    #Rotation details:
        #Combo Point loss
        #Shuriken storm dances details
        #weaponmaster bonus cp gen

    def subtlety_dps_estimate(self):
        return sum(self.subtlety_dps_breakdown().values())

    def subtlety_dps_breakdown(self):
        if not self.settings.is_subtlety_rogue():
            raise InputNotModeledException(_('You must specify a subtlety cycle to match your subtlety spec.'))

        self.cp_builder = self.settings.cycle.cp_builder
        if self.cp_builder == 'shuriken_storm':
            self.dance_cp_builder = 'shuriken_storm'
        elif self.cp_builder == 'backstab':
            self.dance_cp_builder = 'shadowstrike'
        else:
            raise InputNotModeledException(_("{} is not a valid cp_builder").format(self.cp_builder))

        if self.cp_builder == 'backstab' and self.talents.gloomblade:
            self.cp_builder = 'gloomblade'

        self.max_spend_cps = 5
        if self.talents.deeper_strategem:
            self.max_spend_cps += 1
        self.max_store_cps = self.max_spend_cps
        if self.talents.anticipation:
            self.max_store_cps += 3

        self.set_constants()

        #symbols of death
        self.damage_modifier_cache = 1.2 * (1 +(0.005 * self.traits.legionblade))

        stats, aps, crits, procs, additional_info = self.determine_stats(self.subtlety_attack_counts)
        damage_breakdown, additional_info  = self.compute_damage_from_aps(stats, aps, crits, procs, additional_info)

        infallible_trinket_mod = 1.0
        if self.settings.is_demon:
            if getattr(self.stats.procs, 'infallible_tracking_charm_mod'):
                ift = getattr(self.stats.procs, 'infallible_tracking_charm_mod')
                self.set_rppm_uptime(ift)
                infallible_trinket_mod = 1+(ift.uptime *0.10)

        #nightstalker
        if self.talents.nightstalker:
            ns_full_multiplier = 0.12
            for key  in damage_breakdown:
                if key == 'shadowstrike':
                    damage_breakdown[key] *= ns_full_multiplier
                elif key == 'shuriken_storm':
                    damage_breakdown[key] *= 1 + (0.12 * self.stealth_shuriken_uptime)
                elif key == 'finality_nightblade_ticks':
                    damage_breakdown[key] *= 1 + (0.12 * self.dance_finality_nb_uptime)
                elif key == 'nightblade_ticks':
                    damage_breakdown[key] *= 1 + (0.12 * self.dance_nb_uptime)
                elif key in ('eviscerate', 'finality:eviscerate'):
                    damage_breakdown[key] *= 1 + (0.12 * self.stealth_evis_uptime)

        #master of subtlety
        if self.talents.master_of_subtlety:
            mos_full_multiplier = 1.1
            mos_uptime_multipler = 1. + (0.1 * self.mos_time)

            for key in damage_breakdown:
                if key == 'shadowstrike':
                    damage_breakdown[key] *= mos_full_multiplier
                elif key == 'shuriken_storm':
                    damage_breakdown[key] *= 1 + (0.1 * self.stealth_shuriken_uptime)
                elif key in ('eviscerate', 'finality:eviscerate'):
                    damage_breakdown[key] *= 1 + (0.1 * self.stealth_evis_uptime)
                else:
                    damage_breakdown[key] *= mos_uptime_multipler

        ds_multiplier = 1.0
        if self.talents.deeper_strategem:
            ds_multiplier = 1.1

        for key in damage_breakdown:
            damage_breakdown[key] *= infallible_trinket_mod
            if key == 'shuriken_storm':
                damage_breakdown[key] *= (1 + self.stealth_shuriken_uptime * 3)
            if key in self.finisher_damage_sources:
                damage_breakdown[key] *= ds_multiplier
            if key == 'backstab':
                damage_breakdown[key] *= 1 + (0.3 * self.settings.cycle.positional_uptime)

        #add AoE damage sources:
        if self.settings.num_boss_adds:    
            for key in damage_breakdown:
                if key == 'shuriken_toss':
                    damage_breakdown[key] *= 1 + self.settings.num_boss_adds
                elif key == 'second_shuriken':
                    damage_breakdown[key] *= 1 + self.settings.num_boss_adds
                elif key == 'shadow_nova':
                    damage_breakdown *= 1 + self.settings.num_boss_adds

        return damage_breakdown

    def subtlety_attack_counts(self, current_stats, crit_rates=None):
        attacks_per_second = {}
        additional_info = {}
        if crit_rates == None:
            crit_rates = self.get_crit_rates(current_stats)

        use_sod = False
        if self.settings.cycle.symbols_policy == 'always':
            use_sod = True

        #Set up initial energy budget
        base_energy_regen = 10.
        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod
        self.energy_regen = base_energy_regen * haste_multiplier
        if self.talents.vigor:
            self.energy_regen *= 1.1

        self.max_energy = 100.
        if self.talents.vigor:
            self.max_energy += 50
        self.energy_budget = self.settings.duration * self.energy_regen + self.max_energy

        #set initial dance budget
        self.dance_budget = 3 + self.settings.duration/60.

        shadow_blades_duration = 15. + (3.3333 * self.traits.soul_shadows)
        self.shadow_blades_uptime = shadow_blades_duration/self.get_spell_cd('shadow_blades')

        #swing timer
        white_swing_downtime = 0
        self.swing_reset_spacing = self.get_spell_cd('vanish')
        if self.swing_reset_spacing is not None:
            white_swing_downtime += .5 / self.swing_reset_spacing
        attacks_per_second['mh_autoattacks'] = haste_multiplier / self.stats.mh.speed * (1 - white_swing_downtime)
        attacks_per_second['oh_autoattacks'] = haste_multiplier / self.stats.oh.speed * (1 - white_swing_downtime)

        #Set up initial combo point budget
        mfd_cps = self.talents.marked_for_death * (self.settings.duration/60. * 5. * (1. + self.settings.marked_for_death_resets))
        self.cp_budget = mfd_cps


        #Enveloping Shadows generates 1 bonus cp per 6 seconds regardless of cps
        #2 net energy per 6 seconds from relentless strikes
        if self.talents.enveloping_shadows:
            self.cp_budget += self.settings.duration/6.
            self.energy_budget += (2./6) * self.settings.duration
            self.dance_budget += (0.5 * self.settings.duration)/60

        #setup timelines
        sod_duration = 35
        nightblade_duration = 6 + (2 * self.settings.finisher_threshold)
        finality_nightblade_duration = 6 + (2 * self.settings.finisher_threshold)

        #Add attacks that could occur during first pass to aps
        attacks_per_second[self.dance_cp_builder] = 0
        attacks_per_second['symbols_of_death'] = 0
        attacks_per_second['shadow_dance'] = 0
        attacks_per_second['vanish'] = 0
        

        #Leaving space for opener handling for the first cast
        sod_timeline = range(0, self.settings.duration, sod_duration)
        if self.traits.finality:
            finality_nb_timeline = range(0, self.settings.duration, finality_nightblade_duration + nightblade_duration)
            nightblade_timeline = range(nightblade_duration, self.settings.duration, finality_nightblade_duration + nightblade_duration)
        else:
            finality_nb_timeline = []
            nightblade_timeline = range(nightblade_duration, self.settings.duration, nightblade_duration)

        dance_finality_nb_uptime = 0.0
        dance_nb_uptime = 0.0
        for finisher in ['finality:nightblade', 'nightblade', 'eviscerate']:
            attacks_per_second[finisher] = [0, 0, 0, 0, 0, 0, 0]
            #Timeline match of ruptures, fill in rest with eviscerate
            if self.settings.cycle.dance_finishers_allowed:
                dance_count = 0
                if finisher == 'finality:nightblade' and self.traits.finality:
                    #Allow SoDs to be used on pandemic for match purposes
                    joint, sod_timeline, finality_nb_timeline = self.timeline_overlap(sod_timeline, finality_nb_timeline, -0.3 * sod_duration)
                    #if there is overlap compute a dance rotation for this combo
                    dance_count = len(joint)
                    dance_finality_nb_uptime = dance_count/len(finality_nb_timeline)
                elif finisher == 'nightblade':
                    joint, sod_timeline, nightblade_timeline = self.timeline_overlap(sod_timeline, nightblade_timeline, -0.3 * sod_duration)
                    dance_count = len(joint)
                    dance_nb_uptime = dance_count/len(nightblade_timeline)
                elif finisher == 'eviscerate':
                    dance_count = len(sod_timeline)
                    sod_timeline = []

            #Not using finishers during dance
            else:
                finisher=None
                dance_count = len(sod_timeline)
                sod_timeline = []

            if dance_count:
                net_energy, net_cps, spent_cps, attack_counts = self.get_dance_resources(use_sod=True, finisher=finisher)
                self.energy_budget += dance_count * net_energy
                self.cp_budget += dance_count * net_cps
                self.dance_budget += ((3. * spent_cps* dance_count)/60) - dance_count
                #merge attack counts into attacks_per_second
                self.rotation_merge(attacks_per_second, attack_counts, dance_count)

        #Add in ruptures not previously covered
        nightblade_count = len(nightblade_timeline)
        attacks_per_second['nightblade'][self.settings.finisher_threshold] += float(nightblade_count)/self.settings.duration
        self.cp_budget -= self.settings.finisher_threshold * nightblade_count
        self.energy_budget += (40 * (0.2 * self.settings.finisher_threshold) - self.get_spell_cost('nightblade')) * nightblade_count
        self.dance_budget += (3. * self.settings.finisher_threshold * nightblade_count)/60.

        finality_nightblade_count = len(finality_nb_timeline)
        attacks_per_second['finality:nightblade'][self.settings.finisher_threshold] += float(finality_nightblade_count)/self.settings.duration
        self.cp_budget -= self.settings.finisher_threshold * finality_nightblade_count
        self.energy_budget += (40 * (0.2 * self.settings.finisher_threshold) - self.get_spell_cost('finality:nightblade')) * finality_nightblade_count
        self.dance_budget += (3. * self.settings.finisher_threshold * finality_nightblade_count)/60.

        #Add in various cooldown abilities
        #This could be made better with timelining but for now simple time average will do
        if self.traits.goremaws_bite:
            goremaws_bite_cd = self.get_spell_cd('goremaws_bite') + self.settings.response_time
            attacks_per_second['goremaws_bite'] = 1./goremaws_bite_cd
            self.cp_budget += 3 * (self.settings.duration/goremaws_bite_cd)
            self.energy_budget += 30 * (self.settings.duration/goremaws_bite_cd)

        if self.talents.death_from_above:
            dfa_cd = self.get_spell_cd('death_from_above') + self.settings.response_time
            dfa_count = self.settings.duration/dfa_cd

            lost_swings_mh = self.lost_swings_from_swing_delay(1.3, self.stats.mh.speed / haste_multiplier)
            lost_swings_oh = self.lost_swings_from_swing_delay(1.3, self.stats.oh.speed / haste_multiplier)

            attacks_per_second['mh_autoattacks'] -= lost_swings_mh / dfa_cd
            attacks_per_second['oh_autoattacks'] -= lost_swings_oh / dfa_cd

            attacks_per_second['death_from_above_strike'] = [0, 0, 0, 0, 0, 0, 0]
            attacks_per_second['death_from_above_strike'][self.max_spend_cps] += 1./dfa_cd
            attacks_per_second['death_from_above_pulse'] = [0, 0, 0, 0, 0, 0, 0]
            attacks_per_second['death_from_above_pulse'][self.max_spend_cps] += 1./dfa_cd

            self.cp_budget -= self.max_spend_cps * dfa_count
            self.energy_budget += (40 * (0.2 * self.max_spend_cps) - self.get_spell_cost('death_from_above')) * dfa_count
            self.dance_budget += (3. * self.max_spend_cps * dfa_count)/60.

        #Need to handle shadow techniques now to account for swing timer loss
        attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dw_mh_hit_chance
        attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dw_oh_hit_chance

        shadow_techniques_cps_per_proc = 1 + (0.05 * self.traits.fortunes_bite)
        shadow_techniques_procs = self.settings.duration * (attacks_per_second['mh_autoattack_hits'] + attacks_per_second['oh_autoattack_hits']) / 4
        shadow_techniques_cps = shadow_techniques_procs * shadow_techniques_cps_per_proc
        self.cp_budget += shadow_techniques_cps

        #vanish handling
        vanish_count = self.settings.duration/self.get_spell_cd('vanish')
        #Treat subterfuge as a mini-dance
        if self.talents.subterfuge:
            net_energy, net_cps, spent_cps, attack_counts = self.get_dance_resources(use_sod=use_sod, finisher='eviscerate', vanish=True)
        else:
           net_energy, net_cps, spent_cps, attack_counts = self.get_dance_resources(use_sod=use_sod, finisher=None, vanish=True)
        self.energy_budget += vanish_count * net_energy
        self.cp_budget += vanish_count * net_cps
        self.dance_budget += ((3. * spent_cps* vanish_count)/60)
        self.rotation_merge(attacks_per_second, attack_counts, vanish_count)

        #Generate one final dance templates
        if self.settings.cycle.dance_finishers_allowed:
            net_energy, net_cps, spent_cps, attack_counts = self.get_dance_resources(use_sod=use_sod, finisher='eviscerate')
        else:
            net_energy, net_cps, spent_cps, attack_counts = self.get_dance_resources(use_sod=use_sod, finisher=None)

        #Now lets make sure all our budgets are positive
        cp_per_builder = 1 + self.shadow_blades_uptime
        if self.cp_builder == 'shuriken_storm':
            cp_per_builder += self.settings.num_boss_adds
        energy_per_cp = self.get_spell_cost(self.cp_builder) /(cp_per_builder)

        extra_evis = 0
        extra_builders = 0
        #Not enough dances, generate some more
        if self.dance_budget<0:
            cps_required = abs(self.dance_budget) * 20
            extra_evis += cps_required/self.settings.finisher_threshold
            self.energy_budget += self.net_evis_cost
            #just subtract the cps because we'll fix those next
            self.cp_budget -= cps_required
            self.dance_budget = 0
        #If we have too many dances just spend them now
        elif self.dance_budget > 0:
            #quick convergence loop
            loop_counter = 0
            while self.dance_budget > 0.0001:
                if loop_counter > 100:
                   raise ConvergenceErrorException(_('Dance fixup failed to converge.'))
                dance_count = abs(self.dance_budget)
                self.energy_budget += dance_count * net_energy
                self.cp_budget += dance_count * net_cps
                self.dance_budget += ((3. * spent_cps* dance_count)/60.) - dance_count
                #merge attack counts into attacks_per_second
                self.rotation_merge(attacks_per_second, attack_counts, dance_count)
                loop_counter += 1

        #if we don't have enough cps lets build some
        if self.cp_budget <0:
            #can add since we know cp_budget is negative
            self.energy_budget += self.cp_budget * energy_per_cp
            extra_builders += abs(self.cp_budget) / cp_per_builder
            print extra_builders, energy_per_cp
            self.cp_budget = 0

        if self.cp_builder == 'shuriken_storm':
            attacks_per_second['shuriken_storm-no-dance'] = extra_builders / self.settings.duration
        else:
            attacks_per_second[self.cp_builder] = extra_builders / self.settings.duration
        attacks_per_second['eviscerate'][self.settings.finisher_threshold] += extra_evis

        #Hopefully energy budget here isn't negative, if it is we're in trouble
        #Now we convert all the energy we have left into mini-cycles
        #Each mini-cycle contains enough 1 dance and generators+finishers for one dance
        cps_per_dance = 20
        finishers_per_minicycle = cps_per_dance/self.settings.finisher_threshold

        attack_counts_mini_cycle = attack_counts
        attack_counts_mini_cycle['eviscerate'] = [0, 0, 0, 0, 0, 0, 0]
        loop_counter = 0

        alacrity_stacks = 0
        while self.energy_budget > 0.1:
            #print self.energy_budget
            if loop_counter > 20:
                   raise ConvergenceErrorException(_('Mini-cycles failed to converge.'))
            loop_counter += 1
            cps_to_generate = max(cps_per_dance - self.cp_budget, 0)
            builders_per_minicycle = cps_to_generate / cp_per_builder
            mini_cycle_energy = 5 * finishers_per_minicycle - (cps_to_generate * energy_per_cp)
            #add in dance energy
            mini_cycle_energy += net_energy
            if cps_to_generate:
                mini_cycle_count = 0.9*float(self.energy_budget) / abs(mini_cycle_energy)
            else:
                mini_cycle_count = 1
            #mini_cycle_count = 1
            #build the minicycle attack_counts
            if self.cp_builder == 'shuriken_storm':
                attack_counts_mini_cycle['shuriken_storm-no-dance'] = builders_per_minicycle
            else:
                attack_counts_mini_cycle[self.cp_builder] = builders_per_minicycle
            attack_counts_mini_cycle['eviscerate'][self.settings.finisher_threshold] = finishers_per_minicycle
            self.rotation_merge(attacks_per_second, attack_counts_mini_cycle, mini_cycle_count)
            self.energy_budget += mini_cycle_energy * mini_cycle_count
            self.cp_budget += net_cps - 20 + cps_to_generate
            #Update energy budget with alacrity and haste procs
            if self.talents.alacrity:
                old_alacrity_regen = self.energy_regen * (1 + (alacrity_stacks *0.01))
                new_alacrity_stacks = self.get_average_alacrity(attacks_per_second)
                new_alacrity_regen = self.energy_regen * (1 + (new_alacrity_stacks *0.01))
                self.energy_budget += (new_alacrity_regen - old_alacrity_regen) * self.settings.duration
                alacrity_stacks = new_alacrity_stacks

        #Now fixup attacks_per_second
        #convert nightblade casts into nightblade ticks
        for ability in ('finality:nightblade', 'nightblade'):
            if ability in attacks_per_second:
                tick_name = ability + '_ticks'
                attacks_per_second[tick_name] = [0, 0, 0, 0, 0, 0, 0]
                for cp in xrange(7):
                    attacks_per_second[tick_name][cp] = (3 + cp) * attacks_per_second[ability][cp]
                del attacks_per_second[ability]

        #convert some white swings into shadowblades
        #since weapon speeds are now fixed just handle a single shadowblades
        attacks_per_second['shadow_blades'] = self.shadow_blades_uptime * attacks_per_second['mh_autoattacks']
        attacks_per_second['mh_autoattacks'] -= attacks_per_second['shadow_blades']
        attacks_per_second['oh_autoattacks'] -= attacks_per_second['shadow_blades']

        if self.traits.akarris_soul:
            attacks_per_second['soul_rip'] = attacks_per_second['shadowstrike']
        if self.traits.shadow_nova:
            attacks_per_second['shadow_nova'] = attacks_per_second['symbols_of_death'] + attacks_per_second['vanish']

        self.stealth_shuriken_uptime = 0.
        if self.cp_builder == 'shuriken_storm':
            self.stealth_shuriken_uptime = attacks_per_second['shuriken_storm'] / (attacks_per_second['shuriken_storm'] + attacks_per_second['shuriken_storm-no-dance'])
            attacks_per_second['shuriken_storm'] = attacks_per_second['shuriken_storm'] + attacks_per_second['shuriken_storm-no-dance']
            del attacks_per_second['shuriken_storm-no-dance']

        #Full additive assumption for now
        if self.talents.master_of_subtlety:
            stealth_time = 9. * attacks_per_second['shadow_dance'] + 6 * attacks_per_second['vanish']
            if self.talents.subterfuge:
                 stealth_time = 11. * attacks_per_second['shadow_dance'] + 9 * attacks_per_second['vanish']
            self.mos_time =  float(stealth_time)/self.settings.duration

        if self.talents.nightstalker:
            self.dance_finality_nb_uptime = dance_finality_nb_uptime
            self.dance_nb_uptime = dance_nb_uptime

        for ability in attacks_per_second.keys():
            if not attacks_per_second[ability]:
                del attacks_per_second[ability]
            elif isinstance(attacks_per_second[ability], list) and not any(attacks_per_second[ability]):
                del attacks_per_second[ability]

        #determine how many evis used during dance
        if self.settings.cycle.dance_finishers_allowed:
            stealth_evis = attacks_per_second['shadow_dance']
            if self.talents.subterfuge:
                stealth_evis += attacks_per_second['vanish']
        else:
            stealth_evis = 0
        self.stealth_evis_uptime = stealth_evis/sum(attacks_per_second['eviscerate'])

        #convert half of evis to finality
        if self.traits.finality:
            attacks_per_second['finality:eviscerate'] = [0, 0, 0, 0, 0, 0, 0]
            for cp in xrange(7):
                attacks_per_second['finality:eviscerate'][cp] = attacks_per_second['eviscerate'][cp] * 0.5
                attacks_per_second['eviscerate'][cp] *= 0.5

        if self.traits.second_shuriken and 'shuriken_toss' in attacks_per_second:
            attacks_per_second['second_shuriken'] = 0.1 * attacks_per_second['shuriken_toss']
        #print attacks_per_second

        #add SoD auto crits
        if 'shadowstrike' in attacks_per_second:
            sod_shadowstrikes = attacks_per_second['symbols_of_death']/attacks_per_second['shadowstrike']
            crit_rates['shadowstrike'] = crit_rates['shadowstrike'] * (1. - sod_shadowstrikes) + sod_shadowstrikes

        if self.talents.weaponmaster:
            for ability in attacks_per_second:
                if isinstance(attacks_per_second[ability], list):
                    for cp in xrange(7):
                        attacks_per_second[ability][cp] *= 1.06
                else:
                    attacks_per_second[ability] *=1.06

        return attacks_per_second, crit_rates, additional_info

    #Computes the net energy and combo points from a shadow dance rotation
    #Returns net_energy, net_cps, spent_cps, dict of attack counts
    def get_dance_resources(self, use_sod=False, finisher=None, vanish=False):
        net_energy = 0
        net_cps = 0
        spent_cps = 0

        attack_counts = {}

        if self.talents.master_of_shadows:
            net_energy += 30

        cost_mod = 1.0
        if self.talents.shadow_focus:
            cost_mod = 0.7

        if use_sod:
            net_energy -= self.get_spell_cost('symbols_of_death', cost_mod=cost_mod)
            attack_counts['symbols_of_death'] = 1

        dance_gcds = 3
        if self.talents.subterfuge:
            if vanish:
                dance_gcds += 1
            else:
                dance_gcds += 2
        elif vanish:
            dance_gcds = 1

        max_dance_energy = dance_gcds * self.energy_regen + self.max_energy

        if finisher:
            net_energy += 40 * (0.2 * self.settings.finisher_threshold) - self.get_spell_cost(finisher)
            dance_gcds -= 1
            net_cps -= self.settings.finisher_threshold
            attack_counts[finisher] = [0, 0, 0, 0, 0, 0, 0]
            attack_counts[finisher][self.settings.finisher_threshold] += 1
            spent_cps += self.settings.finisher_threshold
        #fill remaining gcds with shadowstrikes
        cp_builder = self.dance_cp_builder
        cp_builder_cost = float(self.get_spell_cost(cp_builder, cost_mod=cost_mod))
        builder_count = min(dance_gcds, (net_energy+max_dance_energy)/cp_builder_cost)
        if vanish:
            attack_counts[cp_builder] = builder_count
            attack_counts['vanish'] = 1
        else:
            attack_counts[cp_builder] = builder_count
            attack_counts['shadow_dance'] = 1

        net_energy -= attack_counts[cp_builder] * cp_builder_cost
        if cp_builder == 'shadowstrike':
            net_cps += attack_counts['shadowstrike'] * (1 + self.talents.premeditation) + self.shadow_blades_uptime
        elif cp_builder == 'shuriken_storm':
            net_cps += min(1 + self.settings.num_boss_adds, self.max_store_cps) + self.shadow_blades_uptime

        return net_energy, net_cps, spent_cps, attack_counts

    #Performs fuzzy matching, with specified delta on two lists.
    #Returns 3 lists, match, and a and b with matches removed
    #Only works for negative deltas for now.
    def timeline_overlap(self, timeline_a, timeline_b, match_delta):
        match_list = []
        #index of matches for removal
        no_match_a = []
        for a in xrange(len(timeline_a)):
            match = False
            for b in xrange(len(timeline_b)):
                #early termination for impossible matches
                if timeline_b[b] > timeline_a[a]:
                    break
                if timeline_b[b] > timeline_a[a] + match_delta and timeline_b[b] < timeline_a[a]:
                    match_list.append(timeline_b[b])
                    match = True
            if not match:
                no_match_a.append(timeline_a[a])

        return match_list, no_match_a, [x for x in timeline_b if x not in match_list]

    #Takes in the full attacks per second dict and a raw attack counts dict
    #adds attack countes into the rotation at global scope
    def rotation_merge (self, attacks_per_second, attack_counts, count):
        rotations_per_second = float(count)/self.settings.duration
        for ability in attack_counts:
            if ability in self.finisher_damage_sources:
                for cp in xrange(7):
                    attacks_per_second[ability][cp] += rotations_per_second *  attack_counts[ability][cp]
            else:
                attacks_per_second[ability] += rotations_per_second * attack_counts[ability]
