import copy
import gettext
import __builtin__
import math

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
            #self.init_assassination()
            return self.assassination_dps_estimate()
        elif self.settings.is_combat_rogue():
            return self.combat_dps_estimate()
        elif self.settings.is_subtlety_rogue():
            return self.subtlety_dps_estimate()
        else:
            raise InputNotModeledException(_('You must specify a spec.'))

    def get_dps_breakdown(self):
        if self.settings.is_assassination_rogue():
            #self.init_assassination()
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

    def get_dps_contribution(self, damage_tuple, crit_rate, frequency):
        (base_damage, crit_damage) = damage_tuple
        average_hit = base_damage * (1 - crit_rate) + crit_damage * crit_rate
        crit_contribution = crit_damage * crit_rate
        return average_hit * frequency, crit_contribution * frequency

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
                #'death_from_above',
                #'shadow_reflection',
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
        if self.talents.anticipation:
            # TODO: The combat model is not yet updated to figure the distribution
            dist = {(5, 5 / avg_cp_per_cpg): 1}
            time_spent_at_cp = [0, 0, 0, 0, 0, 1]
            return dist, time_spent_at_cp, avg_cp_per_cpg

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
        base_melee_crit_rate = self.melee_crit_rate(crit=stats['crit'])
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
        elif self.settings.dmg_poison == 'ip':
            poisons = ('instant_poison', )

        openers = tuple([self.settings.opener_name])

        for attack in spec_attacks + poisons + openers:
            if attack is None:
                pass
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
        self.human_racial_stats = []
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
            'agi': (self.stats.agi + self.buffs.buff_agi() + self.race.racial_agi),
            'ap': (self.stats.ap + 2 * self.level - 30),
            'crit': (self.stats.crit),
            'haste': (self.stats.haste),
            'mastery': (self.stats.mastery + self.buffs.buff_mast()),
            'readiness': (self.stats.readiness),
            'multistrike': (self.stats.multistrike),
        }
        
        for boost in self.race.get_racial_stat_boosts():
            if boost['stat'] in self.base_stats:
                self.base_stats[boost['stat']] += boost['value'] * boost['duration'] * 1.0 / (boost['cooldown'] + self.settings.response_time)

        self.agi_multiplier = self.buffs.stat_multiplier() * self.stats.gear_buffs.leather_specialization_multiplier()
        if self.settings.is_subtlety_rogue():
            self.agi_multiplier *= 1.30

        self.base_strength = self.stats.str + self.buffs.buff_str() + self.race.racial_str
        self.base_strength *= self.buffs.stat_multiplier()

        self.relentless_strikes_energy_return_per_cp = 5 #.20 * 25
        
        #should only include bloodlust if the spec can average it in, deal with this later
        self.base_speed_multiplier = 1.4 * self.buffs.haste_multiplier()
        if self.race.berserking:
            self.true_haste_mod *= (1 + .15 * 10. / (180 + self.settings.response_time))
        if self.race.time_is_money:
            self.true_haste_mod *= 1.01
        if self.race.touch_of_elune and not self.settings.is_day:
            self.true_haste_mod *= 1.01
        if self.race.nimble_fingers:
            self.true_haste_mod *= 1.01
            
        #hit chances
        if self.settings.is_combat_rogue():
            self.dw_miss_penalty = 0 #for level 100
            self.recalculate_hit_constants()
        self.dw_mh_hit_chance = self.dual_wield_mh_hit_chance()
        self.dw_oh_hit_chance = self.dual_wield_oh_hit_chance()
    
    def load_from_advanced_parameters(self):
        self.true_haste_mod = self.get_adv_param('haste_buff', 1., min_bound=.1, max_bound=3.)
        
        self.major_cd_delay = self.get_adv_param('major_cd_delay', 0, min_bound=0, max_bound=600)
        self.settings.feint_interval = self.get_adv_param('feint_interval', self.settings.feint_interval, min_bound=0, max_bound=600)
        
        self.settings.is_day = self.get_adv_param('is_day', self.settings.is_day, ignore_bounds=True)
        self.get_version_number = self.get_adv_param('print_version', False, ignore_bounds=True)
        
    def get_stat_mod(self, stat):
        if stat == 'agi':
            return self.agi_multiplier
        return 1
    
    def get_proc_damage_contribution(self, proc, proc_count, current_stats, average_ap, damage_breakdown):
        if proc.stat == 'spell_damage':
            multiplier = self.raid_settings_modifiers('spell')
            crit_multiplier = self.crit_damage_modifiers()
            crit_rate = self.spell_crit_rate(crit=current_stats['crit'])
        elif proc.stat == 'physical_damage':
            multiplier = self.raid_settings_modifiers('physical')
            crit_multiplier = self.crit_damage_modifiers()
            crit_rate = self.melee_crit_rate(crit=current_stats['crit'])
        elif proc.stat == 'melee_spell_damage':
            multiplier = self.raid_settings_modifiers('spell')
            crit_multiplier = self.crit_damage_modifiers()
            crit_rate = self.melee_crit_rate(crit=current_stats['crit'])
        else:
            return 0, 0

        if proc.can_crit == False:
            crit_rate = 0

        proc_value = proc.value
        #280+75% AP
        if proc is getattr(self.stats.procs, 'legendary_capacitive_meta'):
            crit_rate = self.melee_crit_rate(crit=current_stats['crit'])
            proc_value = average_ap * .75 + 280
        
        if proc is getattr(self.stats.procs, 'fury_of_xuen'):
            crit_rate = self.melee_crit_rate(crit=current_stats['crit'])
            proc_value = (average_ap * .20 + 1) * 10 * (1 + min(4., self.settings.num_boss_adds))

        average_hit = proc_value * multiplier
        average_damage = average_hit * (1 + crit_rate * (crit_multiplier - 1)) * proc_count
        crit_contribution = average_hit * crit_multiplier * crit_rate * proc_count
        return average_damage, crit_contribution

    def append_damage_on_use(self, average_ap, current_stats, damage_breakdown):
        on_use_damage_list = []
        if self.race.rocket_barrage:
            rocket_barrage_dict = {'stat': 'spell_damage', 'cooldown': 120, 'name': 'Rocket Barrage'}
            rocket_barrage_dict['value'] = self.race.calculate_rocket_barrage(average_ap, 0, 0)
            on_use_damage_list.append(rocket_barrage_dict)

        for item in on_use_damage_list:
            if item['stat'] == 'physical_damage':
                modifier = self.raid_settings_modifiers('physical')
                crit_multiplier = self.crit_damage_modifiers()
                crit_rate = self.melee_crit_rate(crit=current_stats['crit'])
            elif item['stat'] == 'spell_damage':
                modifier = self.raid_settings_modifiers('spell')
                crit_multiplier = self.crit_damage_modifiers()
                crit_rate = self.spell_crit_rate(crit=current_stats['crit'])
            elif item['stat'] == 'melee_spell_damage':
                modifier = self.raid_settings_modifiers('spell')
                crit_multiplier = self.crit_damage_modifiers()
                crit_rate = self.melee_crit_rate(crit=current_stats['crit'])
            average_hit = item['value'] * modifier
            frequency = 1. / (item['cooldown'] + self.settings.response_time)
            average_dps = average_hit * (1 + crit_rate * (crit_multiplier - 1)) * frequency
            crit_contribution = average_hit * crit_multiplier * crit_rate * frequency

            damage_breakdown[item['name']] = average_dps, crit_contribution

    def set_openers(self):
        # Sets the swing_reset_spacing and total_openers_per_second variables.
        opener_cd = [10, 20][self.settings.opener_name == 'garrote']
        if self.settings.is_subtlety_rogue():
            self.settings.use_opener = 'always' #Overrides setting. Using Ambush + Vanish on CD is critical.
            self.settings.opener_name = 'ambush'
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

    def get_activated_uptime_DEPRECATED(self, duration, cooldown, use_response_time=True):
        response_time = [0, self.settings.response_time][use_response_time]
        return 1. * duration / (cooldown + response_time)

    def update_with_autoattack_passives(self, attacks_per_second, *args, **kwargs):
        # Appends the keys passed in args to attacks_per_second. This includes
        # autoattack, autoattack_hits, main_gauche and poisons.
        # If no args passed, it'll attempt to append all of them.
        if not args or 'swings' in args or 'mh_autoattack' not in attacks_per_second or 'oh_autoattack' not in attacks_per_second:
            attacks_per_second['mh_autoattacks'] = kwargs['attack_speed_multiplier'] / self.stats.mh.speed
            attacks_per_second['oh_autoattacks'] = kwargs['attack_speed_multiplier'] / self.stats.oh.speed
        if self.swing_reset_spacing is not None:
            attacks_per_second['mh_autoattacks'] *= (1 - max((1 - .5 * self.stats.mh.speed / kwargs['attack_speed_multiplier']), 0) / self.swing_reset_spacing)
            attacks_per_second['oh_autoattacks'] *= (1 - max((1 - .5 * self.stats.oh.speed / kwargs['attack_speed_multiplier']), 0) / self.swing_reset_spacing)
        if not args or 'autoattack_hits' in args:
            attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dw_mh_hit_chance
            attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dw_oh_hit_chance
        if not args or 'poisons' in args:
            self.get_poison_counts(attacks_per_second)

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
            for ability in ('mutilate', 'dispatch', 'backstab', 'revealing_strike', 'sinister_strike', 'ambush', 'hemorrhage', 'mh_killing_spree', 'main_gauche', 'shuriken_toss'):
                if ability == 'main_gauche' and not proc.procs_off_procced_strikes():
                    pass
                elif ability in attacks_per_second:
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
                haste *= self.buffs.haste_multiplier() * self.true_haste_mod * self.stats.get_haste_multiplier_from_rating(self.base_stats['haste'])
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

        attacks_per_second[proc.proc_name] = frequency

    def get_shadow_focus_multiplier(self):
        if self.talents.shadow_focus:
            return (1 - .75)
        return 1.

    def setup_unique_procs(self):
        self.setup_unique_procs_for_class()
        #modelling specific proc setup would go here
        #example, RoRO, Matrix Restabilizer, etc.

    def get_poison_counts(self, attacks_per_second):
        # Builds a phony 'poison' proc object to count triggers through the proc
        # methods.
        poison = procs.Proc(**proc_data.allowed_procs['rogue_poison'])
        mh_hits_per_second = self.get_mh_procs_per_second(poison, attacks_per_second, None)
        oh_hits_per_second = self.get_oh_procs_per_second(poison, attacks_per_second, None)
        total_hits_per_second = mh_hits_per_second + oh_hits_per_second
        if poison:
            poison_base_proc_rate = .3
        else:
            poison_base_proc_rate = 0

        if self.settings.is_assassination_rogue() and poison:
            poison_base_proc_rate += .2
            poison_envenom_proc_rate = poison_base_proc_rate + .15
            poison_envenom_proc_rate += .15 #for level 100
            envenom_uptime = min(sum([(1 + cps + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp()) * attacks_per_second['envenom'][cps] for cps in xrange(1, 6)]), 1)
            avg_poison_proc_rate = poison_base_proc_rate * (1 - envenom_uptime) + poison_envenom_proc_rate * envenom_uptime
        else:
            avg_poison_proc_rate = poison_base_proc_rate
        
        #for level 100
        if self.settings.dmg_poison == 'ip':
            poison_procs = avg_poison_proc_rate * total_hits_per_second - 1 / self.settings.duration
            attacks_per_second['instant_poison'] = poison_procs
        elif self.settings.dmg_poison == 'dp':
            poison_procs = avg_poison_proc_rate * total_hits_per_second - 1 / self.settings.duration
            attacks_per_second['deadly_instant_poison'] = poison_procs
            attacks_per_second['deadly_poison'] = 1. / 3
        elif self.settings.dmg_poison == 'wp':
            attacks_per_second['wound_poison'] = total_hits_per_second * avg_poison_proc_rate

    def determine_stats(self, attack_counts_function):
        current_stats = {
            'str': self.base_strength,
            'agi': self.base_stats['agi'] * self.agi_multiplier,
            'ap': self.base_stats['ap'],
            'crit': self.base_stats['crit'],
            'haste': self.base_stats['haste'],
            'mastery': self.base_stats['mastery'],
            'readiness': self.base_stats['readiness'],
            'multistrike': self.base_stats['multistrike'],
        }
        self.current_variables = {}
        
        #arrys to store different types of procs
        active_procs_rppm = []
        active_procs_icd = []
        active_procs_no_icd = []
        damage_procs = []
        weapon_damage_procs = []
        
        #some procs need specific prep, think RoRO/VoS
        self.setup_unique_procs()
        
        #set 'highest' procs to agi
        for proc in self.stats.procs.get_all_procs_for_stat('highest'):
            if 'agi' in proc.value:
                proc.stat = 'stats'
                for e in proc.value:
                    if proc.value[e] is not 'agi':
                        proc.value[e] = 0
        
        #sort the procs into groups
        for proc in self.stats.procs.get_all_procs_for_stat():
            if (proc.stat == 'stats') and not proc.is_ppm():
                if proc.is_real_ppm():
                    active_procs_rppm.append(proc)
                else:
                    if proc.icd:
                        active_procs_icd.append(proc)
                    else:
                        active_procs_no_icd.append(proc)
            elif proc.stat in ('spell_damage', 'physical_damage', 'melee_spell_damage'):
                damage_procs.append(proc)
            elif proc.stat == 'extra_weapon_damage':
                weapon_damage_procs.append(proc)
                
        #update proc values in each proc "folder"
        #for dict in (active_procs_rppm, active_procs_icd, active_procs_no_icd):
            #for proc in dict:
                #establish proc value for proc level
                #for e in proc.value:
                    #proc.value[e] = round(proc.scaling * self.tools.get_random_prop_point(proc.item_level))
        
        #calculate weapon procs
        weapon_enchants = set([])
        for hand, enchant in [(x, y) for x in ('mh', 'oh') for y in ('dancing_steel', 'elemental_force')]:
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
                elif enchant in ('avalanche', 'elemental_force'):
                    damage_procs.append(proc)
                elif proc.stat == 'highest' and 'agi' in proc.value:
                    proc.stat = 'stats'
                    #need to make sure all 'highest' procs are restrained to a single stat
                    for s in proc.value:
                        if s != 'agi':
                            proc.value[s] = 0
                    if proc.is_real_ppm():
                        active_procs_rppm.append(proc)
                    else:
                        if proc.icd:
                            active_procs_icd.append(proc)
                        else:
                            active_procs_no_icd.append(proc)

                if enchant not in weapon_enchants and enchant in ('hurricane', 'avalanche'):
                    weapon_enchants.add(enchant)
                    spell_component = copy.copy(proc)
                    delattr(spell_component, '_'.join((hand, 'only')))
                    spell_component.behaviour_toggle = 'spell'
                    if enchant == 'hurricane':
                        # This would heavily overestimate Hurricane by ignoring the refresh mechanic.
                        # active_procs.append(spell_component)
                        pass
                    elif enchant == 'avalanche':
                        damage_procs.append(spell_component)
        
        static_proc_stats = {
            'str': 0,
            'agi': 0,
            'ap': 0,
            'crit': 0,
            'haste': 0,
            'mastery': 0,
            'readiness': 0,
            'multistrike': 0,
        }
        
        #human racial stats, we can sneak it in static proc stats to keep code cleaner
        #should probably rely on self.race object for data instead of hardcoded value here
        for e in self.human_racial_stats:
            static_proc_stats[e] += 30 #placeholder
        
        for proc in active_procs_rppm:
            self.set_rppm_uptime(proc)
            for e in proc.value:
                static_proc_stats[ e ] += proc.uptime * proc.value[e] * self.get_stat_mod(e)
        
        for k in static_proc_stats:
            current_stats[k] +=  static_proc_stats[ k ]
                        
        attacks_per_second, crit_rates = attack_counts_function(current_stats)
        recalculate_crit = False
        
        #check need to converge
        need_converge = False
        if len(active_procs_no_icd) > 0:
            need_converge = True
        #only have to converge with specific procs, try to simplify later
        #check if... assassination:agi/crit/haste, combat:mastery/haste, sub:haste
        #while True:
            #stuff()
            #if not condition():
                #break
        while need_converge or self.spec_needs_converge:
            current_stats = {
                'str': self.base_strength,
                'agi': self.base_stats['agi'] * self.agi_multiplier,
                'ap': self.base_stats['ap'],
                'crit': self.base_stats['crit'],
                'haste': self.base_stats['haste'],
                'mastery': self.base_stats['mastery'],
                'readiness': self.base_stats['readiness'],
                'multistrike': self.base_stats['multistrike'],
            }
            for k in static_proc_stats:
                current_stats[k] +=  static_proc_stats[k]
                
            for proc in active_procs_no_icd:
                self.set_uptime(proc, attacks_per_second, crit_rates)
                for e in proc.value:
                    if e in ('agi', 'crit'):
                        recalculate_crit = True
                    current_stats[ e ] += proc.uptime * proc.value[e] * self.get_stat_mod(e)
                
            old_attacks_per_second = attacks_per_second
            if recalculate_crit:
                attacks_per_second, crit_rates = attack_counts_function(current_stats)
            else:
                attacks_per_second, crit_rates = attack_counts_function(current_stats, crit_rates=crit_rates)
            recalculate_crit = False
            
            if self.are_close_enough(old_attacks_per_second, attacks_per_second):
                break
            
        for proc in active_procs_icd:
            self.set_uptime(proc, attacks_per_second, crit_rates)
            for e in proc.value:
                if e in ('agi', 'crit'):
                    recalculate_crit = True
                current_stats[ e ] += proc.uptime * proc.value[e] * self.get_stat_mod(e)
        
        #if no new stats are added, skip this step
        if len(active_procs_icd) > 0:
            if recalculate_crit:
                attacks_per_second, crit_rates = attack_counts_function(current_stats)
            else:
                attacks_per_second, crit_rates = attack_counts_function(current_stats, crit_rates=crit_rates)

        # the t16 4pc do not need to be in the main loop because mastery for assa is just increased damage
        # and has no impact on the cycle
        if self.stats.gear_buffs.rogue_t16_4pc_bonus() and self.settings.is_assassination_rogue():
            #20 stacks of 250 mastery, lasts 5 seconds
            mas_per_stack = 250.
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

        for proc in damage_procs:
            self.update_with_damaging_proc(proc, attacks_per_second, crit_rates)

        for proc in weapon_damage_procs:
            self.set_uptime(proc, attacks_per_second, crit_rates)
                        
        return current_stats, attacks_per_second, crit_rates, damage_procs
    
    def compute_damage_from_aps(self, current_stats, attacks_per_second, crit_rates, damage_procs):
        damage_breakdown = self.get_damage_breakdown(current_stats, attacks_per_second, crit_rates, damage_procs)

        # Discard the crit component.
        for key in damage_breakdown:
            damage_breakdown[key] = damage_breakdown[key][0]

        return damage_breakdown
    
    def compute_damage(self, attack_counts_function):
        # TODO: Crit cap
        #
        # TODO: Hit/Exp procs
        
        current_stats, attacks_per_second, crit_rates, damage_procs = self.determine_stats(attack_counts_function)

        damage_breakdown = self.get_damage_breakdown(current_stats, attacks_per_second, crit_rates, damage_procs)

        # Discard the crit component.
        for key in damage_breakdown:
            damage_breakdown[key] = damage_breakdown[key][0]

        return damage_breakdown
        
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
        self.human_racial_stats = ['mastery', 'crit']
        
        self.set_constants()
        
        self.base_energy_regen = 10
        if self.talents.lemon_zest:
            self.base_energy_regen *= 1 + .05 * self.settings.num_boss_adds
        self.max_energy = 120.
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            self.max_energy += 30
        if self.talents.lemon_zest:
            self.max_energy += 15

        self.vendetta_duration = 20 + 10 * self.glyphs.vendetta
        self.vendetta_uptime = self.vendetta_duration / (self.get_spell_cd('vendetta') + self.settings.response_time + self.major_cd_delay)
        vendetta_multiplier = .3 - .05 * self.glyphs.vendetta
        self.vendetta_mult = 1 + vendetta_multiplier * self.vendetta_uptime

    def assassination_dps_estimate(self):
        non_execute_dps = self.assassination_dps_estimate_non_execute() * (1 - self.settings.time_in_execute_range)
        execute_dps = self.assassination_dps_estimate_execute() * self.settings.time_in_execute_range
        return non_execute_dps + execute_dps

    def assassination_dps_estimate_execute(self):
        return sum(self.assassination_dps_breakdown_execute().values())

    def assassination_dps_estimate_non_execute(self):
        return sum(self.assassination_dps_breakdown_non_execute().values())

    def assassination_dps_breakdown(self):
        self.init_assassination()
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

    def update_damage_breakdown_for_vendetta(self, damage_breakdown):
        for key in damage_breakdown:
            if key != 'Elemental Force':
                damage_breakdown[key] *= self.vendetta_mult

    def assassination_dps_breakdown_non_execute(self):
        self.init_assassination()
        damage_breakdown = self.compute_damage(self.assassination_attack_counts_non_execute)
        self.update_damage_breakdown_for_vendetta(damage_breakdown)
        return damage_breakdown

    def assassination_dps_breakdown_execute(self):
        self.init_assassination()
        damage_breakdown = self.compute_damage(self.assassination_attack_counts_execute)
        self.update_damage_breakdown_for_vendetta(damage_breakdown)
        return damage_breakdown

    def assassination_attack_counts(self, current_stats, cpg, finisher_size, crit_rates=None):
        attacks_per_second = {}
        if crit_rates == None:
            crit_rates = self.get_crit_rates(current_stats)

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod
        ability_cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_reduced_cost()

        energy_regen = self.base_energy_regen * haste_multiplier
        energy_regen += self.bonus_energy_regen
        if cpg == 'dispatch':
            energy_regen += (self.max_energy - 10) / (self.settings.duration * self.settings.time_in_execute_range)

        vw_energy_return = 10
        #vw_proc_chance = .75
        vw_proc_chance = 1.0 #for level 100
        vw_energy_per_bleed_tick = vw_energy_return * vw_proc_chance

        blindside_proc_rate = [0, .3][cpg == 'mutilate']
        dispatch_as_cpg_chance = blindside_proc_rate / (1 + blindside_proc_rate)

        opener_net_cost = self.get_net_energy_cost(self.settings.opener_name)
        opener_net_cost *= self.get_shadow_focus_multiplier()
        opener_net_cost *= ability_cost_modifier

        if self.settings.opener_name == 'garrote':
            energy_regen += vw_energy_return * vw_proc_chance / self.settings.duration # Only the first tick at the start of the fight
            attacks_per_second['venomous_wounds'] = vw_proc_chance / self.settings.duration

        energy_regen -= opener_net_cost * self.total_openers_per_second
        if self.talents.marked_for_death:
            energy_regen -= 10. / self.get_spell_cd('marked_for_death') # 35-25

        attacks_per_second[self.settings.opener_name] = self.total_openers_per_second

        energy_regen_with_rupture = energy_regen + 0.5 * vw_energy_per_bleed_tick

        attack_speed_multiplier = self.base_speed_multiplier * haste_multiplier
        self.attack_speed_increase = attack_speed_multiplier

        cpg_energy_cost = self.get_net_energy_cost(cpg)
        cpg_energy_cost *= self.stats.gear_buffs.rogue_t15_4pc_reduced_cost()

        if cpg == 'mutilate':
            cpg_energy_cost = cpg_energy_cost * (1 - dispatch_as_cpg_chance) + 0 * dispatch_as_cpg_chance  # blindside costs nothing
            mut_seal_fate_proc_rate = 1 - (1 - crit_rates['mutilate']) ** 2
            dsp_seal_fate_proc_rate = crit_rates['dispatch']
            seal_fate_proc_rate = mut_seal_fate_proc_rate * (1 - dispatch_as_cpg_chance) + dsp_seal_fate_proc_rate * dispatch_as_cpg_chance
            base_cp_per_cpg = 1
            mutilate_extra_cp_chance = 1 - dispatch_as_cpg_chance # in non execute the ratio of mutilate attacks is (1 - dispatch_as_cpg_chance)
        else:
            seal_fate_proc_rate = crit_rates['dispatch']
            base_cp_per_cpg = 1
            mutilate_extra_cp_chance = 0 # never using mutilate, so no extra cp chance
        
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            cpg_energy_cost -= 6 * seal_fate_proc_rate

        # This should be handled by the cp_distribution method or something
        # alike. For now, let's have each sub-distribution computed here.
        # If we find out a different set of finisher sizes can output a
        # higher dps, perhaps we'll need to let that be configurable by the
        # user.
        cp_distribution = {}
        rupture_sizes = [0, 0, 0, 0, 0, 0]
        avg_cp_per_cpg = 0
        uptime_and_dists_tuples = []
        if cpg == 'mutilate':
            for blindside in (True, False):
                # blindside uptime as the amount of connecting cpgs that get 'turned' into dipatches
                if blindside:
                    uptime = dispatch_as_cpg_chance
                    cp_per_cpg = self.get_cp_per_cpg(1, dsp_seal_fate_proc_rate)
                    current_finisher_size = finisher_size + 1
                elif not blindside:
                    uptime = 1 - dispatch_as_cpg_chance
                    cp_per_cpg = self.get_cp_per_cpg(base_cp_per_cpg, mut_seal_fate_proc_rate)
                    current_finisher_size = finisher_size
                dists = self.get_cp_distribution_for_cycle(cp_per_cpg, current_finisher_size)
                uptime_and_dists_tuples.append((uptime, dists))
        else:
            uptime = 1
            cp_per_cpg = self.get_cp_per_cpg(base_cp_per_cpg, seal_fate_proc_rate)
            current_finisher_size = finisher_size
            
            dists = self.get_cp_distribution_for_cycle(cp_per_cpg, current_finisher_size)
            uptime_and_dists_tuples.append((uptime, dists))

        for uptime, dists in uptime_and_dists_tuples:
            for i in dists[0]:
                cp_distribution.setdefault(i, 0)
                cp_distribution[i] += dists[0][i] * uptime
            rupture_sizes = [i + j * uptime for i, j in zip(rupture_sizes, dists[1])]
            avg_cp_per_cpg += dists[2] * uptime

        avg_rupture_size = sum([i * rupture_sizes[i] for i in xrange(6)])
        avg_rupture_length = 4. * (1 + avg_rupture_size + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())
        avg_gap = 0 + .5 * (.5 * self.settings.response_time)
        avg_cycle_length = avg_gap + avg_rupture_length
        energy_per_cycle = avg_rupture_length * energy_regen_with_rupture + avg_gap * energy_regen

        cpg_per_rupture = avg_rupture_size / avg_cp_per_cpg

        cpg_per_finisher = 0
        cp_per_finisher = 0
        envenom_size_breakdown = [0, 0, 0, 0, 0, 0]
        for (cps, cpgs), probability in cp_distribution.items():
            cpg_per_finisher += cpgs * probability
            cp_per_finisher += cps * probability
            envenom_size_breakdown[cps] += probability

        attacks_per_second['rupture'] = 1 / avg_cycle_length

        energy_for_rupture = cpg_per_rupture * cpg_energy_cost + self.get_spell_stats('rupture', cost_mod=ability_cost_modifier)[0]
        energy_for_rupture -= avg_rupture_size * self.relentless_strikes_energy_return_per_cp
        energy_for_envenoms = energy_per_cycle - energy_for_rupture

        envenom_energy_cost = cpg_per_finisher * cpg_energy_cost + self.get_spell_stats('envenom', cost_mod=ability_cost_modifier)[0]
        envenom_energy_cost -= cp_per_finisher * self.relentless_strikes_energy_return_per_cp
        envenoms_per_cycle = energy_for_envenoms / envenom_energy_cost

        envenoms_per_second = envenoms_per_cycle / avg_cycle_length
        cpgs_per_second = envenoms_per_second * cpg_per_finisher + attacks_per_second['rupture'] * cpg_per_rupture
        if cpg in attacks_per_second:
            attacks_per_second[cpg] += cpgs_per_second
        else:
            attacks_per_second[cpg] = cpgs_per_second
        if cpg == 'mutilate':
            attacks_per_second['mutilate'] *= 1 - dispatch_as_cpg_chance
            attacks_per_second['dispatch'] = cpgs_per_second * dispatch_as_cpg_chance
        if self.settings.opener_name == 'mutilate':
            attacks_per_second['mutilate'] += self.total_openers_per_second
            attacks_per_second['dispatch'] += self.total_openers_per_second * blindside_proc_rate

        attacks_per_second['envenom'] = [finisher_chance * envenoms_per_second for finisher_chance in envenom_size_breakdown]
        if self.talents.marked_for_death:
            attacks_per_second['envenom'][5] += 1. / self.get_spell_cd('marked_for_death')

        attacks_per_second['rupture_ticks'] = [0, 0, 0, 0, 0, 0]
        for i in xrange(1, 6):
            ticks_per_rupture = 2 * (1 + i + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())
            attacks_per_second['rupture_ticks'][i] = ticks_per_rupture * attacks_per_second['rupture'] * rupture_sizes[i]

        total_rupture_ticks_per_second = sum(attacks_per_second['rupture_ticks'])
        if 'venomous_wounds' in attacks_per_second:
            attacks_per_second['venomous_wounds'] += total_rupture_ticks_per_second * vw_proc_chance
        else:
            attacks_per_second['venomous_wounds'] = total_rupture_ticks_per_second * vw_proc_chance

        if 'garrote' in attacks_per_second:
            attacks_per_second['garrote_ticks'] = 6 * attacks_per_second['garrote']
        for opener, cps in [('ambush', 2), ('garrote', 1)]:
            if opener in attacks_per_second:
                if opener == 'ambush':
                    cps += crit_rates[opener]
                extra_finishers_per_second = attacks_per_second[opener] * cps / 5
                attacks_per_second['envenom'][5] += extra_finishers_per_second

        self.update_with_autoattack_passives(attacks_per_second,
                attack_speed_multiplier=attack_speed_multiplier)

        return attacks_per_second, crit_rates
    
    def assassination_attack_counts_anticipation(self, current_stats, cpg, crit_rates=None):
        attacks_per_second = {}
        if crit_rates == None:
            crit_rates = self.get_crit_rates(current_stats)

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod
        ability_cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_reduced_cost()

        energy_regen = self.base_energy_regen * haste_multiplier
        energy_regen += self.bonus_energy_regen

        vw_energy_return = 10
        #vw_proc_chance = .75
        vw_proc_chance = 1.0 #for level 100
        vw_energy_per_bleed_tick = vw_energy_return * vw_proc_chance

        blindside_proc_rate = [0, .3][cpg == 'mutilate']
        dispatch_as_cpg_chance = blindside_proc_rate / (1 + blindside_proc_rate)

        opener_net_cost = self.get_spell_stats(self.settings.opener_name, cost_mod=ability_cost_modifier*self.get_shadow_focus_multiplier())[0]
        if self.settings.opener_name == 'envenom':
            opener_net_cost = 0
        
        if self.settings.opener_name == 'garrote':
            # Only the first tick at the start of the fight. Not precise but better than nothing.
            energy_regen += vw_energy_return * vw_proc_chance / self.settings.duration
            attacks_per_second['venomous_wounds'] = vw_proc_chance / self.settings.duration
            
        energy_regen -= opener_net_cost * self.total_openers_per_second
        if cpg == 'dispatch':
            energy_regen += (self.max_energy - 10) / (self.settings.duration * self.settings.time_in_execute_range)

        attacks_per_second[self.settings.opener_name] = self.total_openers_per_second

        attack_speed_multiplier = self.base_speed_multiplier * haste_multiplier
        self.attack_speed_increase = attack_speed_multiplier

        blindside_cost = 0
        mutilate_cost = self.get_spell_stats('mutilate', cost_mod=ability_cost_modifier)[0]
        
        if cpg == 'mutilate':
            cpg_energy_cost = blindside_cost + mutilate_cost
        else:
            cpg_energy_cost = self.get_spell_stats('dispatch', cost_mod=ability_cost_modifier)[0]
        mutilate_cps = 3 - (1 - crit_rates['mutilate']) ** 2 # 1 - (1 - crit_rates['mutilate']) ** 2 is the Seal Fate CP
        dispatch_cps = 1 + crit_rates['dispatch']
        if cpg == 'mutilate':
            avg_cp_per_cpg = mutilate_cps + dispatch_cps * blindside_proc_rate
        else:
            avg_cp_per_cpg = dispatch_cps
        seal_fate_proc_rate = crit_rates['dispatch']
        if cpg == 'mutilate':
            seal_fate_proc_rate *= blindside_proc_rate
            seal_fate_proc_rate += 1 - (1 - crit_rates['mutilate']) ** 2
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            cpg_energy_cost -= 6 * seal_fate_proc_rate
            
        cp_per_finisher = 5
        avg_rupture_length = 4. * (6 + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp()) # 1+5 since all 5CP ruptures
        avg_gap = 0 + .5 * (.5 * self.settings.response_time)
        avg_cycle_length = avg_gap + avg_rupture_length
        attacks_per_second['rupture'] = 1 / avg_cycle_length
        rupture_ticks_per_second = 2 * (6 + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp()) / avg_cycle_length # 1+5 since all 5CP ruptures
        attacks_per_second['rupture_ticks'] = [0, 0, 0, 0, 0, rupture_ticks_per_second]
        
        energy_regen_with_rupture = energy_regen + attacks_per_second['rupture_ticks'][5] * vw_energy_per_bleed_tick
        energy_per_cycle = avg_rupture_length * energy_regen_with_rupture + avg_gap * energy_regen
        cpg_per_finisher = cp_per_finisher / avg_cp_per_cpg
        
        energy_for_rupture = cpg_per_finisher * cpg_energy_cost + self.get_spell_stats('rupture', cost_mod=ability_cost_modifier)[0]
        energy_for_rupture -= cp_per_finisher * self.relentless_strikes_energy_return_per_cp
        energy_for_envenoms = energy_per_cycle - energy_for_rupture

        envenom_energy_cost = cpg_per_finisher * cpg_energy_cost + self.get_spell_stats('envenom', cost_mod=ability_cost_modifier)[0]
        envenom_energy_cost -= cp_per_finisher * self.relentless_strikes_energy_return_per_cp
        envenoms_per_cycle = energy_for_envenoms / envenom_energy_cost

        envenoms_per_second = envenoms_per_cycle / avg_cycle_length
        cpgs_per_second = envenoms_per_second * cpg_per_finisher + attacks_per_second['rupture'] * cpg_per_finisher
        if cpg in attacks_per_second:
            attacks_per_second[cpg] += cpgs_per_second
        else:
            attacks_per_second[cpg] = cpgs_per_second
        if cpg == 'mutilate':
            if 'dispatch' in attacks_per_second:
                attacks_per_second['dispatch'] += cpgs_per_second * blindside_proc_rate
            else:
                attacks_per_second['dispatch'] = cpgs_per_second * blindside_proc_rate
        if self.settings.opener_name == 'mutilate' and cpg == 'dispatch':
            attacks_per_second['mutilate'] += self.total_openers_per_second
            attacks_per_second['dispatch'] += self.total_openers_per_second * blindside_proc_rate

        #attacks_per_second['envenom'] = [finisher_chance * envenoms_per_second for finisher_chance in envenom_size_breakdown]
        attacks_per_second['envenom'] = [0, 0, 0, 0, 0, envenoms_per_second]

        if 'venomous_wounds' in attacks_per_second:
            attacks_per_second['venomous_wounds'] += rupture_ticks_per_second * vw_proc_chance
        else:
            attacks_per_second['venomous_wounds'] = rupture_ticks_per_second * vw_proc_chance

        if 'garrote' in attacks_per_second:
            attacks_per_second['garrote_ticks'] = 6 * attacks_per_second['garrote']
        for opener, cps in [('ambush', 2), ('garrote', 1)]:
            if opener in attacks_per_second:
                if opener == 'ambush':
                    cps += crit_rates[opener]
                attacks_per_second['envenom'][5] += attacks_per_second[opener] * cps / 5
        attacks_per_second['envenom'][5] += 1. / 180
        
        self.update_with_autoattack_passives(attacks_per_second,
                attack_speed_multiplier=attack_speed_multiplier)
        
        #print attacks_per_second
        return attacks_per_second, crit_rates

    def assassination_attack_counts_non_execute(self, current_stats, crit_rates=None):
        if self.talents.anticipation:
            return self.assassination_attack_counts_anticipation(current_stats, 'mutilate')
        return self.assassination_attack_counts(current_stats, 'mutilate', self.settings.cycle.min_envenom_size_non_execute, crit_rates=crit_rates)

    def assassination_attack_counts_execute(self, current_stats, crit_rates=None):
        if self.talents.anticipation:
            return self.assassination_attack_counts_anticipation(current_stats, 'dispatch')
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
        self.human_racial_stats = ['haste', 'readiness']
        
        self.set_constants()
        
        #combat specific constants
        self.max_bandits_guile_buff = 1.3
        self.max_bandits_guile_buff += .2 #for level 100
        self.max_energy = 100.
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            self.max_energy += 30
        if self.talents.lemon_zest:
            self.max_energy += 15
        if self.glyphs.energy:
            self.max_energy += 20
        ar_duration = 15
        self.ksp_buff = 0.5
        self.revealing_strike_multiplier = 1.35
        self.extra_cp_chance = .2 # Assume all casts during RvS
        self.rvs_duration = 24
        if self.settings.dmg_poison == 'dp':
            self.settings.dmg_poison = 'ip'
        
        cds = {'ar':self.get_spell_cd('adrenaline_rush')}
        
        # actual damage calculations here
        phases = {}
        #AR phase
        stats, aps, crits, procs = self.determine_stats(self.combat_attack_counts_ar)
        phases['ar'] = (ar_duration,
                        self.update_with_bandits_guile(self.compute_damage_from_aps(stats, aps, crits, procs)) )
        for e in cds:
            cds[e] -= ar_duration / self.rb_cd_modifier(aps)
            
        #none
        self.tmp_phase_length = cds['ar'] #This is to approximate the value of a full energy bar to be used when not during AR or SB
        stats, aps, crits, procs = self.determine_stats(self.combat_attack_counts_none)
        phases['none'] = (self.rb_actual_cds(aps, cds)['ar'] + self.settings.response_time + self.major_cd_delay,
                            self.update_with_bandits_guile(self.compute_damage_from_aps(stats, aps, crits, procs)) )
            
        total_duration = phases['ar'][0] + phases['none'][0] 
        #average it together
        damage_breakdown = self.average_damage_breakdowns(phases, denom = total_duration)
        
        bf_mod = .40
        bf_max_targets = 4
        if self.settings.cycle.blade_flurry:
            damage_breakdown['blade_flurry'] = 0
            for key in damage_breakdown:
                if key in self.melee_attacks:
                    damage_breakdown['blade_flurry'] += bf_mod * damage_breakdown[key] * min(self.settings.num_boss_adds, bf_max_targets)
        
        return damage_breakdown
    
    def update_with_bandits_guile(self, damage_breakdown):
        for key in damage_breakdown:
            if key in ('killing_spree', 'mh_killing_spree', 'oh_killing_spree'):
                if self.settings.cycle.ksp_immediately:
                    damage_breakdown[key] *= self.bandits_guile_multiplier * (1. + self.ksp_buff)
                else:
                    damage_breakdown[key] *= self.max_bandits_guile_buff * (1. + self.ksp_buff)
                if self.stats.gear_buffs.rogue_t16_4pc_bonus():
                    #http://elitistjerks.com/f78/t132793-5_4_changes_discussion/p2/#post2301780
                    #http://www.wolframalpha.com/input/?i=%28sum+of+1.5*1.1%5Ex+from+x%3D1+to+7%29+%2F+%281.5*7%29
                    # No need to use anything other than a constant. Yay for convenience!
                    damage_breakdown[key] *= 1.49084
            elif key in ('sinister_strike', 'revealing_strike'):
                damage_breakdown[key] *= self.bandits_guile_multiplier
                if key == 'sinister_strike':
                    damage_breakdown[key] *= 1.2 #for level 100
            elif key in ('eviscerate', ):
                damage_breakdown[key] *= self.bandits_guile_multiplier * self.revealing_strike_multiplier * 1.2 #1.2 is for level 100
            elif key in ('autoattack', 'deadly_poison', 'main_gauche', 'mh_autoattack', 'oh_autoattack'):
                damage_breakdown[key] *= self.bandits_guile_multiplier #* self.ksp_multiplier
            else:
                damage_breakdown[key] *= self.bandits_guile_multiplier #* self.ksp_multiplier
                
        return damage_breakdown
    
    def combat_attack_counts(self, current_stats, ar=False, crit_rates=None):
        attacks_per_second = {}
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
            self.base_energy_regen *= 1 + .05 * self.settings.num_boss_adds
        gcd_size = 1.0 + self.settings.latency
        if ar:
            gcd_size -= .4 #GCD reduction changed to .4 from .1 for level 100
        cp_per_cpg = 1.
            
        # Combine energy cost scalers to reduce function calls (ie, 40% reduced energy cost). Assume multiplicative.
        cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_modifier()
        # Turn the cost of the ability into the net loss of energy by reducing it by the energy gained from MG
        cost_reducer = main_gauche_proc_rate * combat_potency_from_mg
        
        #get_spell_stats(self, ability, hit_chance=1.0, cost_mod=1.0)
        eviscerate_energy_cost =  self.get_spell_stats('eviscerate', cost_mod=cost_modifier)[0]
        eviscerate_energy_cost -= cost_reducer
        revealing_strike_energy_cost =  self.get_spell_stats('revealing_strike', cost_mod=cost_modifier)[0]
        revealing_strike_energy_cost -= cost_reducer
        sinister_strike_energy_cost =  self.get_spell_stats('sinister_strike', cost_mod=cost_modifier)[0]
        sinister_strike_energy_cost -= cost_reducer
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            sinister_strike_energy_cost -= 15 * self.extra_cp_chance
        
        ## Base CPs and Attacks
        #Autoattacks
        attacks_per_second['mh_autoattacks'] = self.attack_speed_increase / self.stats.mh.speed
        attacks_per_second['oh_autoattacks'] = self.attack_speed_increase / self.stats.oh.speed
        if not ar:
            if self.swing_reset_spacing is not None:
                attacks_per_second['mh_autoattacks'] *= (1 - max((1 - .5 * self.stats.mh.speed / self.attack_speed_increase), 0) / self.swing_reset_spacing)
                attacks_per_second['oh_autoattacks'] *= (1 - max((1 - .5 * self.stats.oh.speed / self.attack_speed_increase), 0) / self.swing_reset_spacing)
        attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dw_mh_hit_chance
        attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dw_oh_hit_chance
        attacks_per_second['main_gauche'] = attacks_per_second['mh_autoattack_hits'] * main_gauche_proc_rate
        combat_potency_regen = attacks_per_second['oh_autoattack_hits'] * combat_potency_regen_per_oh
        
        #Base energy
        bonus_energy_from_openers = self.get_bonus_energy_from_openers('sinister_strike', 'revealing_strike')
        combat_potency_regen += combat_potency_from_mg * attacks_per_second['main_gauche']
        if self.settings.opener_name in ('ambush', 'garrote'):
            attacks_per_second[self.settings.opener_name] = self.total_openers_per_second
            attacks_per_second['main_gauche'] += self.total_openers_per_second * main_gauche_proc_rate
        energy_regen = self.base_energy_regen * haste_multiplier + self.bonus_energy_regen + combat_potency_regen + bonus_energy_from_openers
        #Rough idea to factor in a full energy bar
        if not ar:
            energy_regen += self.max_energy / self.settings.duration
        
        #Base actions
        rvs_interval = self.rvs_duration
        if self.settings.cycle.revealing_strike_pooling and not ar:
            min_energy_while_pooling = energy_regen * gcd_size
            max_energy_while_pooling = 80.
            average_pooling = max(0, (max_energy_while_pooling - min_energy_while_pooling)) / 2
            rvs_interval += average_pooling / energy_regen
        
        #Minicycle sizes and cpg_per_finisher stats
        if self.talents.anticipation:
            ss_per_finisher = (FINISHER_SIZE - ruthlessness_value) / (cp_per_cpg + self.extra_cp_chance)
        else:
            #cp_per_ss = self.get_cp_per_cpg(1, self.extra_cp_chance)
            ss_per_finisher = 3.742
        cp_per_finisher = FINISHER_SIZE
        energy_cost_per_cp = ss_per_finisher * sinister_strike_energy_cost
        total_eviscerate_cost = energy_cost_per_cp + eviscerate_energy_cost - cp_per_finisher * self.relentless_strikes_energy_return_per_cp

        ss_per_snd = ss_per_finisher
        snd_size = FINISHER_SIZE
        snd_base_cost = 25
        snd_cost = ss_per_snd * sinister_strike_energy_cost + snd_base_cost - snd_size * self.relentless_strikes_energy_return_per_cp
        snd_duration = 6 + 6 * (snd_size + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())
        energy_spent_on_snd = snd_cost / snd_duration
        
        #Base Actions
        #marked for death CD
        marked_for_death_cd = self.get_spell_cd('marked_for_death') + (.5 * total_eviscerate_cost) / (2 * energy_regen) + self.settings.response_time
        if self.talents.marked_for_death:
            energy_regen -= 10. / marked_for_death_cd
        energy_regen -= revealing_strike_energy_cost / rvs_interval
        
        #Base CPGs
        attacks_per_second['sinister_strike_base'] = ss_per_snd / snd_duration
        attacks_per_second['revealing_strike'] = 1. / rvs_interval
        extra_finishers_per_second = attacks_per_second['revealing_strike'] / (5/cp_per_cpg)
        #Scaling CPGs
        free_gcd = 1./gcd_size
        free_gcd -= 1./snd_duration + (attacks_per_second['sinister_strike_base'] + attacks_per_second['revealing_strike'] + extra_finishers_per_second)
        if self.talents.marked_for_death:
            free_gcd -= (1. / marked_for_death_cd)
        energy_available_for_evis = energy_regen - energy_spent_on_snd
        total_evis_per_second = energy_available_for_evis / total_eviscerate_cost
        evisc_actions_per_second = (total_evis_per_second * ss_per_finisher + total_evis_per_second)
        attacks_per_second['sinister_strike'] = total_evis_per_second * ss_per_finisher
        # If GCD capped
        if evisc_actions_per_second > free_gcd:
            gcd_cap_mod = evisc_actions_per_second / free_gcd
            wasted_energy = (attacks_per_second['sinister_strike'] - attacks_per_second['sinister_strike'] / gcd_cap_mod) / sinister_strike_energy_cost
            attacks_per_second['sinister_strike'] = attacks_per_second['sinister_strike'] / gcd_cap_mod
            wasted_energy = (total_evis_per_second - total_evis_per_second / gcd_cap_mod) / eviscerate_energy_cost
            total_evis_per_second = total_evis_per_second / gcd_cap_mod
        # Reintroduce flat gcds
        attacks_per_second['sinister_strike'] += attacks_per_second['sinister_strike_base']
        attacks_per_second['main_gauche'] += (attacks_per_second['sinister_strike'] + attacks_per_second['revealing_strike'] + total_evis_per_second) * main_gauche_proc_rate
        
        #attacks_per_second['eviscerate'] = [finisher_chance * total_evis_per_second for finisher_chance in finisher_size_breakdown]
        attacks_per_second['eviscerate'] = [0,0,0,0,0,total_evis_per_second]
        for opener, cps in [('ambush', 2), ('garrote', 1)]:
            if opener in attacks_per_second:
                extra_finishers_per_second += attacks_per_second[opener] * cps / 5
        attacks_per_second['eviscerate'][5] += extra_finishers_per_second
        if self.talents.marked_for_death:
            attacks_per_second['eviscerate'][5] += 1. / marked_for_death_cd
        
        #self.current_variables['cp_spent_on_damage_finishers_per_second'] = (total_evis_per_second) * cp_per_finisher
        if 'garrote' in attacks_per_second:
            attacks_per_second['garrote_ticks'] = 6 * attacks_per_second['garrote']
        
        time_at_level = 4 / attacks_per_second['sinister_strike']
        cycle_duration = 3 * time_at_level + 15
        #avg_stacks = (3 * time_at_level + 45) / cycle_duration #45 is the duration (15s) multiplied by the stack power (30% BG)
        #self.bandits_guile_multiplier = 1 + .1 * avg_stacks
        #split up for clarity at the moment, needs to be simplified closer to launch
        self.bandits_guile_multiplier = 1 + (0*time_at_level + .1*time_at_level + .2*time_at_level + .5 * 15) / cycle_duration #for level 100
        
        if not ar:
            final_ks_cd = self.rb_actual_cd(attacks_per_second, self.tmp_phase_length) + self.major_cd_delay
            if not self.settings.cycle.ksp_immediately:
                final_ks_cd += (3 * time_at_level)/2 * (3 * time_at_level)/cycle_duration
            attacks_per_second['mh_killing_spree'] = 7 / (final_ks_cd + self.settings.response_time)
            attacks_per_second['oh_killing_spree'] = 7 / (final_ks_cd + self.settings.response_time)
            attacks_per_second['main_gauche'] += attacks_per_second['mh_killing_spree'] * main_gauche_proc_rate
        
        if ar and not self.settings.cycle.stack_cds:
            approx_time_to_empty = 100 / sinister_strike_energy_cost
            approx_time_to_empty += (energy_regen * approx_time_to_empty) / sinister_strike_energy_cost
        
        self.get_poison_counts(attacks_per_second)
        
        #print attacks_per_second
        return attacks_per_second, crit_rates
    
    def rb_actual_cds(self, attacks_per_second, base_cds, avg_rb_effect=10):
        final_cds = {}
        # If it's best to always use 5CP finishers as combat now, it should continue to be so, this is simpler and faster
        offensive_finisher_rate = attacks_per_second['eviscerate'][5]
        #should never happen, catch error just in case
        if offensive_finisher_rate != 0:
            for cd_name in base_cds:
                final_cds[cd_name] = base_cds[cd_name] * (1 - avg_rb_effect / (1. / offensive_finisher_rate + avg_rb_effect))
        else:
            final_cds[cd_name] = base_cds[cd_name]
        return final_cds
    def rb_actual_cd(self, attacks_per_second, base_cd, avg_rb_effect=10):
        final_cd = base_cd
        # If it's best to always use 5CP finishers as combat now, it should continue to be so, this is simpler and faster
        offensive_finisher_rate = attacks_per_second['eviscerate'][5]
        #should never happen, catch error just in case
        if offensive_finisher_rate != 0:
            return base_cd * (1 - avg_rb_effect / (1. / offensive_finisher_rate + avg_rb_effect))
        return base_cd
    def rb_cd_modifier(self, attacks_per_second, avg_rb_effect=10):
        # If it's best to always use 5CP finishers as combat now, it should continue to be so, this is simpler and faster
        offensive_finisher_rate = attacks_per_second['eviscerate'][5]
        if offensive_finisher_rate != 0:
            #should never happen, catch divide-by-zero error just in case
            return (1 - avg_rb_effect / (1. / offensive_finisher_rate + avg_rb_effect))
        else:
            return 1.
    
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

        if self.settings.cycle.use_hemorrhage not in ('always', 'never'):
            if float(self.settings.cycle.use_hemorrhage) <= 0:
                raise InputNotModeledException(_('Hemorrhage usage must be set to always, never or a positive number'))
            if float(self.settings.cycle.use_hemorrhage) > self.settings.duration:
                raise InputNotModeledException(_('Interval between Hemorrhages cannot be higher than the fight duration'))
            
        #set readiness coefficient
        self.readiness_spec_conversion = self.subtlety_readiness_conversion
        self.human_racial_stats = ['haste', 'readiness']
        
        self.set_constants()
        
        self.base_energy_regen = 10.
        self.max_energy = 100.
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            self.max_energy += 30
        if self.talents.lemon_zest:
            self.base_energy_regen *= 1 + .05 * self.settings.num_boss_adds
            self.max_energy += 15
        self.shd_duration = 8 + 2 # 2s more for level 100
        self.shd_cd = self.get_spell_cd('shadow_dance') + self.settings.response_time + self.major_cd_delay
        self.settings.cycle.raid_crits_per_second = self.get_adv_param('hat_triggers_per_second', self.settings.cycle.raid_crits_per_second, min_bound=0, max_bound=600)

        cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_reduced_cost()
        shd_ambush_cost_modifier = 1.
        backstab_cost_mod = cost_modifier / ((self.shd_cd - self.shd_duration) / self.shd_cd)
        self.base_eviscerate_cost = self.get_spell_stats('eviscerate', cost_mod=cost_modifier)[0]
        self.base_rupture_cost = self.get_spell_stats('rupture', cost_mod=cost_modifier)[0]
        self.base_hemo_cost = self.get_spell_stats('hemorrhage', cost_mod=cost_modifier)[0]
        self.base_st_cost = self.get_spell_stats('shuriken_toss', cost_mod=cost_modifier)[0]
        self.base_backstab_energy_cost = self.get_spell_stats('backstab', cost_mod=backstab_cost_mod)[0]
        self.sd_ambush_cost = self.get_spell_stats('ambush', cost_mod=shd_ambush_cost_modifier)[0] - 20
        self.normal_ambush_cost = self.get_spell_stats('ambush')[0]
            
        mos_value = .1
        self.vanish_rate = 1. / (self.get_spell_cd('vanish') + self.settings.response_time) + 1. / (self.get_spell_cd('preparation') + self.settings.response_time * 3) #vanish CD + Prep CD
        mos_multiplier = 1. + mos_value * (6 + 3 * self.talents.subterfuge * [1, 2][self.glyphs.vanish]) * self.vanish_rate

        damage_breakdown = self.compute_damage(self.subtlety_attack_counts)

        armor_value = self.target_armor()
        if self.settings.is_pvp:
            armor_reduction = .5
        else:
            armor_reduction = 0 #100% armor ignore now
        find_weakness_damage_boost = self.armor_mitigation_multiplier(armor_reduction * armor_value) / self.armor_mitigation_multiplier(armor_value)
        find_weakness_multiplier = 1 + (find_weakness_damage_boost - 1) * self.find_weakness_uptime

        for key in damage_breakdown:
            if key in ('eviscerate', 'hemorrhage', 'shuriken_toss') or key in ('hemorrhage_dot'): #'burning_wounds'
                damage_breakdown[key] *= find_weakness_multiplier
            if key == 'autoattack':
                damage_breakdown[key] *=  1 + self.autoattack_fw_rate * (find_weakness_damage_boost - 1)
            if key == 'ambush':
                damage_breakdown[key] *= 1 + ((1 - self.ambush_no_fw_rate) * (find_weakness_damage_boost - 1))
            if key == 'backstab':
                damage_breakdown[key] *= 1 + self.backstab_fw_rate * (find_weakness_damage_boost - 1)
            if key == 'rupture':
                damage_breakdown[key] *= 1.5
            damage_breakdown[key] *= mos_multiplier
        
        return damage_breakdown

    def subtlety_attack_counts(self, current_stats, crit_rates=None):
        attacks_per_second = {}
        if crit_rates == None:
            crit_rates = self.get_crit_rates(current_stats)
        
        #haste and attack speed
        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod
        mastery_snd_speed = 1 + .4 * (1 + self.subtlety_mastery_conversion * self.stats.get_mastery_from_rating(current_stats['mastery']))
        attack_speed_multiplier = self.base_speed_multiplier * haste_multiplier * mastery_snd_speed / 1.4
        self.attack_speed_increase = attack_speed_multiplier
        
        cpg_name = 'backstab'
        if self.settings.cycle.use_hemorrhage == 'always':
            cpg_name = 'hemorrhage'
        
        #constant and base values
        hat_triggers_per_second = self.settings.cycle.raid_crits_per_second
        hat_cp_per_second = 1. / (2 + 1. / hat_triggers_per_second)
        er_energy = 8. / 2 #8 energy every 2 seconds, assumed full SnD uptime
        fw_duration = 10. #17.5s
        attacks_per_second['eviscerate'] = [0,0,0,0,0,0]
        attacks_per_second['rupture_ticks'] = [0,0,0,0,0,0]
        attacks_per_second['ambush'] = self.total_openers_per_second
        attacks_per_second['backstab'] = 0
        attacks_per_second['hemorrhage'] = 0
        cp_per_ambush = 2
        cp_per_shd_ambush = cp_per_ambush
        cp_per_cpg = 1
        vanish_bonus_stealth = 0 + 3 * self.talents.subterfuge * [1, 2][self.glyphs.vanish]
        rupture_cd = 24
        snd_cd = 36
        base_cp_per_second = hat_cp_per_second * (self.shd_cd-8.)/self.shd_cd + self.total_openers_per_second * 2
        if self.stats.gear_buffs.rogue_t15_2pc:
            rupture_cd += 4
            snd_cd += 6
        cpg_denom = self.shd_duration
        cpg_denom -= (1 + vanish_bonus_stealth)
        if self.race.shadowmeld:
            cpg_denom -= (self.get_spell_cd('shadowmeld') + self.settings.response_time)
        
        #passive energy regen
        energy_regen = self.base_energy_regen * haste_multiplier + self.bonus_energy_regen + self.max_energy / self.settings.duration + er_energy
        energy_regen += self.get_bonus_energy_from_openers()
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            energy_regen += 2 * hat_cp_per_second
        
        ##calculations dependent on energy regen
        typical_cycle_size = self.base_backstab_energy_cost * 5 / cp_per_cpg + (self.base_eviscerate_cost - 25) #net eviscerate cost
        if self.settings.cycle.use_hemorrhage == 'always':
            typical_cycle_size = self.base_hemo_cost * 5 / cp_per_cpg + (self.base_eviscerate_cost - 25) #net eviscerate cost
        
        t16_cycle_size = typical_cycle_size * (1./.04) / 5 - 10 # 60-(35*2) = -10, handles the energy shifted from 2 backstabs to an ambush
        t16_cycle_length = t16_cycle_size / energy_regen
        typical_cycle_per_t16_cycle = t16_cycle_size / typical_cycle_size
        shd_cycle_size = self.sd_ambush_cost * (5. / cp_per_shd_ambush) + (self.base_eviscerate_cost - 25) #(40 energy per ambush) * (2.5 ambushes till 5CP) + 10 energy for the finisher
        shd_cycle_gcds = 3
        #calc energy for Shadow Dance
        shd_energy = (self.max_energy - self.get_adv_param('max_pool_reduct', 10, min_bound=0, max_bound=50)) + energy_regen * self.shd_duration #lasts 8s, assume we pool to ~10 energy below max
        
        #swing timer
        attacks_per_second['mh_autoattacks'] = attack_speed_multiplier / self.stats.mh.speed
        attacks_per_second['oh_autoattacks'] = attack_speed_multiplier / self.stats.oh.speed
        attacks_per_second['mh_autoattacks'] *= 1 - (1. / self.get_spell_cd('shadowmeld') + 1. / self.get_spell_cd('vanish'))
        attacks_per_second['oh_autoattacks'] *= 1 - (1. / self.get_spell_cd('shadowmeld') + 1. / self.get_spell_cd('vanish'))
        attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dw_mh_hit_chance
        attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dw_oh_hit_chance
        
        
        ##start consuming energy
        #base energy reductions
        marked_for_death_cd = self.get_spell_cd('marked_for_death') + (.5 * typical_cycle_size / energy_regen) + self.settings.response_time
        if self.talents.marked_for_death:
            energy_regen -= (self.base_eviscerate_cost - 25) / marked_for_death_cd
            attacks_per_second['eviscerate'][5] += 1. / marked_for_death_cd
        shadowmeld_ambushes = 0.
        if self.race.shadowmeld:
            shadowmeld_ambushes = 1. / (self.get_spell_cd('shadowmeld') + self.settings.response_time)
            shadowmeld_ambushes *= ((self.settings.duration - fw_duration * 3 - 8) / self.settings.duration)
            attacks_per_second['ambush'] += shadowmeld_ambushes
            energy_regen -= self.normal_ambush_cost * shadowmeld_ambushes
            base_cp_per_second += shadowmeld_ambushes * 2
           
        #base CPs, CPGs, and finishers 
        if self.settings.cycle.use_hemorrhage != 'always' and self.settings.cycle.use_hemorrhage != 'never':
            hemo_per_second = 1. / float(self.settings.cycle.use_hemorrhage)
            energy_regen -= hemo_per_second
            base_cp_per_second += hemo_per_second
            attacks_per_second['hemorrhage'] += hemo_per_second
        #premed
        base_cp_per_second += 2. / self.settings.duration #start of the fight
        base_cp_per_second += 2. / self.shd_cd * (self.settings.duration-25.)/self.settings.duration
        base_cp_per_second += 2. / self.get_spell_cd('vanish') * (self.settings.duration-50.)/self.settings.duration
        #rupture
        attacks_per_second['rupture'] = 1. / rupture_cd
        attacks_per_second['rupture_ticks'][5] = .5
        base_cp_per_second -= 5. / rupture_cd
        energy_regen -= self.base_rupture_cost - 25
        #no need to add slice and dice to attacks per second
        base_cp_per_second -= 5. / snd_cd
        
        base_cp_per_second += self.vanish_rate * 2
        if self.stats.gear_buffs.rogue_t16_4pc:
            base_cp_per_second += 1. / t16_cycle_length
        #if we've consumed more CP's than we have for base functionality, lets generate some more CPs
        if base_cp_per_second < 0:
            if cpg_name == 'backstab':
                cpg_per_second = math.fabs(base_cp_per_second) * self.base_backstab_energy_cost
            elif cpg_name == 'hemorrhage':
                cpg_per_second = math.fabs(base_cp_per_second) * self.base_hemo_cost
            base_cp_per_second += cpg_per_second
            attacks_per_second[cpg_name] += cpg_per_second
        attacks_per_second['eviscerate'][5] += base_cp_per_second / 5
        
        #calculate shd ambush cycles
        tmp_cp = 0
        max_gcds = 8
        tmp_gcd = 0
        energy_count = 0
        shd_ambushes = 0
        shd_eviscerates = 0
        while (energy_count + 40) < shd_energy and tmp_gcd < max_gcds:
            if tmp_cp < 4:
                energy_count += self.sd_ambush_cost
                tmp_cp += 2
                shd_ambushes += 1. / self.shd_cd
            else:
                energy_count += (self.base_eviscerate_cost - 25)
                tmp_cp = 0
                shd_eviscerates += 1. / self.shd_cd
            tmp_gcd += 1
        attacks_per_second['ambush'] += shd_ambushes * ((self.settings.duration - fw_duration) / self.settings.duration)
        attacks_per_second['eviscerate'][5] += shd_eviscerates * ((self.settings.duration - fw_duration) / self.settings.duration)
        energy_regen -= energy_count / self.shd_cd * ((self.settings.duration - fw_duration) / self.settings.duration)
        #calculate percentage of ambushes with FW
        ambush_no_fw = shadowmeld_ambushes + 1. / self.shd_cd + self.total_openers_per_second
        self.ambush_no_fw_rate = ambush_no_fw / attacks_per_second['ambush']
        #calculate percentage of backstabs with FW
        self.backstab_fw_rate = (fw_duration - 1) / self.settings.duration #start of fight
        self.backstab_fw_rate += (fw_duration - 1) / self.shd_cd * ((self.settings.duration - fw_duration) / self.settings.duration)
        self.backstab_fw_rate += (fw_duration + vanish_bonus_stealth - 1) / self.get_spell_cd('vanish') * ((self.settings.duration - fw_duration * 2 - 8) / self.settings.duration)
        if self.race.shadowmeld:
            self.backstab_fw_rate += (fw_duration - 1) / self.get_spell_cd('shadowmeld') * ((self.settings.duration - fw_duration * 3 - 8) / self.settings.duration)
        self.backstab_fw_rate = self.backstab_fw_rate / ((self.shd_cd - 8.) / self.shd_cd) #accounts for the fact that backstab isn't evenly distributed
        #calculate FW uptime overall
        self.find_weakness_uptime = fw_duration / self.settings.duration #start of fight
        self.find_weakness_uptime += (fw_duration + 7.5) / self.shd_cd * ((self.settings.duration - fw_duration) / self.settings.duration)
        self.find_weakness_uptime += (fw_duration + vanish_bonus_stealth) / self.get_spell_cd('vanish') * ((self.settings.duration - fw_duration * 2 - 8) / self.settings.duration)
        if self.race.shadowmeld:
            self.find_weakness_uptime += fw_duration / self.get_spell_cd('shadowmeld') * ((self.settings.duration - fw_duration * 3 - 8) / self.settings.duration)
        #calculate percentage of autoattack time with FW
        self.autoattack_fw_rate = self.find_weakness_uptime
        #allocate the remaining energy
        if self.stats.gear_buffs.rogue_t16_4pc and self.settings.cycle.use_hemorrhage != 'always':
            filler_cycles_per_second = energy_regen / t16_cycle_size
            attacks_per_second[cpg_name] += typical_cycle_per_t16_cycle * filler_cycles_per_second * 5 - 2. / t16_cycle_length
            attacks_per_second['ambush'] += 1. / t16_cycle_length
            attacks_per_second['eviscerate'][5] += typical_cycle_per_t16_cycle * filler_cycles_per_second
        else:
            filler_cycles_per_second = energy_regen / typical_cycle_size
            attacks_per_second[cpg_name] += filler_cycles_per_second * 5
            attacks_per_second['eviscerate'][5] += filler_cycles_per_second
        
        #t16 4pc
        if cpg_name == 'backstab' and self.stats.gear_buffs.rogue_t16_4pc:
            self.find_weakness_uptime += fw_duration / t16_cycle_length * (1-self.find_weakness_uptime)
        
        #Hemo ticks
        if 'hemorrhage' in attacks_per_second and self.settings.cycle.use_hemorrhage != 'never':
            if self.settings.cycle.use_hemorrhage == 'always':
                hemo_gap = 1 / attacks_per_second['hemorrhage']
            else:
                hemo_gap = float(self.settings.cycle.use_hemorrhage)
            ticks_per_second = min(1. / 3, 8. / hemo_gap)
            attacks_per_second['hemorrhage_ticks'] = ticks_per_second
        
        self.get_poison_counts(attacks_per_second)
        
        #print attacks_per_second
        
        return attacks_per_second, crit_rates
