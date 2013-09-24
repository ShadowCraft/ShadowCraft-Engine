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
                'tricks_of_the_trade',
                'adrenaline_rush'
            ]
        return super(AldrianasRogueDamageCalculator, self).get_glyphs_ranking(list)

    def get_talents_ranking(self, list=None):
        if list is None:
            list = [
                'nightstalker',
                'marked_for_death',
                'shadow_focus',
                'anticipation',
                'subterfuge',
                'shuriken_toss'
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
        base_melee_crit_rate = self.melee_crit_rate(agi=stats['agi'], crit=stats['crit'])
        crit_rates = {
            'mh_autoattacks': min(base_melee_crit_rate, self.dw_mh_hit_chance - self.GLANCE_RATE),
            'oh_autoattacks': min(base_melee_crit_rate, self.dw_oh_hit_chance - self.GLANCE_RATE),
            'emh_autoattacks':min(base_melee_crit_rate, self.dw_mh_hit_chance - self.GLANCE_RATE),
            'eoh_autoattacks':min(base_melee_crit_rate, self.dw_oh_hit_chance - self.GLANCE_RATE),
        }
        for attack in ('mh_shadow_blade', 'oh_shadow_blade', 'rupture_ticks', 'shuriken_toss'):
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
            poisons = tuple(['wound_poison'])

        openers = tuple([self.settings.opener_name])

        for attack in spec_attacks + poisons + openers:
            if attack is None:
                pass
            crit_rates[attack] = base_melee_crit_rate

        for attack, crit_rate in crit_rates.items():
            if crit_rate > 1:
                crit_rates[attack] = 1

        return crit_rates

    def get_snd_length(self, size):
        duration = 6 + 6 * (size + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())
        return duration

    def set_constants(self):
        # General setup that we'll use in all 3 cycles.
        self.load_from_advanced_parameters()
        self.bonus_energy_regen = 0
        if self.settings.tricks_on_cooldown:
            self.bonus_energy_regen -= self.get_spell_stats('tricks_of_the_trade')[0] / (30 + self.settings.response_time)
        if self.settings.shiv_interval != 0:
            self.bonus_energy_regen -= self.get_spell_stats('shiv')[0] / self.settings.shiv_interval
        if self.race.arcane_torrent:
            self.bonus_energy_regen += 15. / (120 + self.settings.response_time)
        if self.settings.feint_interval != 0:
            self.bonus_energy_regen -= self.get_spell_stats('feint')[0] / self.settings.feint_interval
            
        self.set_openers()
        
        # thoks tail tip
        # TODO verify if the numbers are correct
        # VERIFY: ingame it looks like that the crit multiplier is more around 8% instead of 7% for 553 ilvl
        # maybe 3.5% crit multiplier is rounded to 4 and then doubled through the 200% crit damage...
        # VERIFY: tooltip of the item only shows multiplier for haste and mastery
        self.amplify_crit_damage = 0.
        self.amplify_stats = 1.
        prefixes = ('heroic_war_','heroic_','war_','','flex_','lfr_')
        for prefix in prefixes:
            proc = getattr(self.stats.procs, ''.join((prefix, 'thoks_tail_tip')))
            if proc and proc.scaling:
                item_level = proc.scaling['item_level']
                if proc.scaling['quality'] == 'epic':
                    item_level += proc.upgrade_level * 4
                elif proc.scaling['quality'] == 'blue':
                    item_level += proc.upgrade_level * 8
                scale_value = self.tools.get_random_prop_point(item_level, proc.scaling['quality'])
                self.amplify_crit_damage = 0.0008850000 * scale_value / 100
                amp_stats = round(0.0017700000 * scale_value)
                self.amplify_stats += amp_stats / 100
                break
        
        self.true_haste_mod *= self.get_heroism_haste_multiplier()
        self.base_stats = {
            'agi': (self.stats.agi + self.buffs.buff_agi() + self.race.racial_agi) * self.stats.agi_mod,
            'ap': (self.stats.ap + 2 * self.level - 30) * self.stats.ap_mod,
            'crit': (self.stats.crit) * self.stats.crit_mod,
            'haste': (self.stats.haste) * self.stats.haste_mod,
            'mastery': (self.stats.mastery + self.buffs.buff_mast()) * self.stats.mastery_mod,
        }
        
        for boost in self.race.get_racial_stat_boosts():
            if boost['stat'] in self.base_stats:
                self.base_stats[boost['stat']] += boost['value'] * boost['duration'] * 1.0 / (boost['cooldown'] + self.settings.response_time)

        if getattr(self.stats.gear_buffs, 'synapse_springs'):
            self.stats.gear_buffs.activated_boosts['synapse_springs']['stat'] = 'agi'
        for proc in self.stats.procs.get_all_procs_for_stat('highest'):
            if 'agi' in proc.stats:
                proc.stat = 'agi'

        for stat in self.base_stats:
            for boost in self.stats.gear_buffs.get_all_activated_boosts_for_stat(stat):
                if 'scaling' in boost and 'upgrade_level' in boost:
                    item_level = boost['scaling']['item_level']
                    if boost['scaling']['quality'] == 'epic':
                        item_level += boost['upgrade_level'] * 4
                    elif boost['scaling']['quality'] == 'blue':
                        item_level += boost['upgrade_level'] * 8
                    boost['value'] = round(boost['scaling']['factor'] * self.tools.get_random_prop_point(item_level, boost['scaling']['quality']))
                if boost['cooldown'] is not None:
                    self.base_stats[stat] += (boost['value'] * boost['duration']) * 1.0 / (boost['cooldown'] + self.settings.response_time)
                else:
                    self.base_stats[stat] += (boost['value'] * boost['duration']) * 1.0 / self.settings.duration

        self.agi_multiplier = self.buffs.stat_multiplier() * self.stats.gear_buffs.leather_specialization_multiplier()
        if self.settings.is_subtlety_rogue():
            self.agi_multiplier *= 1.30
        if 'agi_mod' in self.settings.adv_params:
            self.agi_multiplier *= self.settings.adv_params['agi_mod']

        self.base_strength = self.stats.str + self.buffs.buff_str() + self.race.racial_str
        self.base_strength *= self.buffs.stat_multiplier()

        self.relentless_strikes_energy_return_per_cp = .20 * 25

        self.base_speed_multiplier = 1.4 * self.buffs.melee_haste_multiplier()
        if self.race.berserking:
            self.true_haste_mod *= (1 + .2 * 10. / (180 + self.settings.response_time))
        if self.race.time_is_money:
            self.base_speed_multiplier *= 1.01

        self.dw_mh_hit_chance = self.dual_wield_mh_hit_chance()
        self.dw_oh_hit_chance = self.dual_wield_oh_hit_chance()
        #NOT to be used for energy costs, nor GCD calculations 
        self.strike_hit_chance = self.one_hand_melee_hit_chance()
        #this is to account for possibly getting multiple dodge/parry/miss in a row (see: geometric series calculus :: miss_chance / (1-miss_chance))
        self.geometric_strike_chance = 1 - (1-self.strike_hit_chance)/self.strike_hit_chance #Only use where calculating GCDs and energy costs
        self.off_hand_strike_hit_chance = self.off_hand_melee_hit_chance()
        self.poison_hit_chance = self.melee_spells_hit_chance()
        self.cast_spell_hit_chance = self.spell_hit_chance() # this is not for poisons
        
        if 'heroic_matrix_restabilizer' in proc_data.allowed_procs:
            if self.stats.procs.heroic_matrix_restabilizer or self.stats.procs.matrix_restabilizer:
                self.set_matrix_restabilizer_stat(self.base_stats)
        if self.stats.procs.heroic_rune_of_re_origination or self.stats.procs.heroic_thunder_rune_of_re_origination:
            self.set_re_origination_stat(self.base_stats)
        if self.stats.procs.thunder_rune_of_re_origination or self.stats.procs.rune_of_re_origination or self.stats.procs.lfr_rune_of_re_origination:
            self.set_re_origination_stat(self.base_stats)
    
    def load_from_advanced_parameters(self):
        self.stats.agi += self.get_adv_param('agi_bonus', 0) #agi
        self.stats.agi_mod = self.get_adv_param('agi_mod', 1., min_bound=.1, max_bound=3.)
        self.stats.ap += self.get_adv_param('ap_bonus', 0) #ap
        self.stats.ap_mod = self.get_adv_param('ap_mod', 1., min_bound=.1, max_bound=3.)
        self.stats.crit += self.get_adv_param('crit_bonus', 0) #crit rating
        self.stats.crit_mod = self.get_adv_param('crit_mod', 1., min_bound=.1, max_bound=3.)
        self.stats.haste += self.get_adv_param('haste_bonus', 0) #haste rating
        self.stats.haste_mod = self.get_adv_param('haste_mod', 1., min_bound=.1, max_bound=3.)
        self.stats.mastery += self.get_adv_param('mastery_bonus', 0) #mastery rating
        self.stats.mastery_mod = self.get_adv_param('mastery_mod', 1., min_bound=.1, max_bound=3.)
        self.stats.hit += self.get_adv_param('hit_bonus', 0) #hit rating
        self.stats.hit_mod = self.get_adv_param('hit_mod', 1., min_bound=.1, max_bound=3.)
        self.stats.exp += self.get_adv_param('exp_bonus', 0) #exp rating
        self.stats.exp_mod = self.get_adv_param('exp_mod', 1., min_bound=.1, max_bound=3.)
        
        self.true_haste_mod = self.get_adv_param('haste_buff', 1., min_bound=.1, max_bound=3.)
        self.damage_mod = self.get_adv_param('damage_mod', 1., min_bound=.1, max_bound=3.)
        
        self.major_cd_delay = self.get_adv_param('major_cd_delay', 0, min_bound=0, max_bound=600)
        self.hit_chance_bonus = self.get_adv_param('hit_chance_bonus', 0, min_bound=0, max_bound=1.0)
        self.settings.feint_interval = self.get_adv_param('feint_interval', self.settings.feint_interval, min_bound=0, max_bound=600)
        
        self.get_version_number = self.get_adv_param('print_version', False, ignore_bounds=True)
    
    def get_stat_mod(self, stat):
        if stat == 'ap':
            return self.stats.ap_mod
        if stat == 'crit':
            return self.stats.crit_mod
        if stat == 'haste':
            return self.stats.haste_mod
        if stat == 'mastery':
            return self.stats.mastery_mod
        return 1.
    
    def get_adv_param(self, type, default_val, min_bound=-10000, max_bound=10000, ignore_bounds=False):
        if type in self.settings.adv_params and not ignore_bounds:
            return max(   min(float(self.settings.adv_params[type]), max_bound), min_bound   )
        elif type in self.settings.adv_params:
            return self.settings.adv_params[type]
        else:
            return default_val
        raise exceptions.InvalidInputException(_('Improperly defined parameter type: '+type))
    
    def get_proc_damage_contribution(self, proc, proc_count, current_stats, average_ap, damage_breakdown):
        if proc.stat == 'spell_damage':
            multiplier = self.raid_settings_modifiers('spell')
            crit_multiplier = self.crit_damage_modifiers()
            crit_rate = self.spell_crit_rate(crit=current_stats['crit'])
            hit_chance = self.cast_spell_hit_chance
        elif proc.stat == 'physical_damage':
            multiplier = self.raid_settings_modifiers('physical')
            crit_multiplier = self.crit_damage_modifiers()
            crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
            hit_chance = self.strike_hit_chance
        elif proc.stat == 'melee_spell_damage':
            multiplier = self.raid_settings_modifiers('spell')
            crit_multiplier = self.crit_damage_modifiers()
            crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
            hit_chance = self.strike_hit_chance
        else:
            return 0, 0

        if proc.can_crit == False:
            crit_rate = 0

        proc_value = proc.value
        # Vial of Shadows scales with AP.
        if 'heroic_vial_of_shadows' in proc_data.allowed_procs:
            vial_of_shadows_modifiers = {
                'heroic_vial_of_shadows': 1.016,
                'vial_of_shadows': .9,
                'lfr_vial_of_shadows': .797
                }
            for i in vial_of_shadows_modifiers:
                if proc is getattr(self.stats.procs, i):
                    proc_value += vial_of_shadows_modifiers[i] * average_ap
        #280+75% AP
        if proc is getattr(self.stats.procs, 'legendary_capacitive_meta'):
            crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
            hit_chance = self.strike_hit_chance
            proc_value = average_ap * .75 + 280
        
        if proc is getattr(self.stats.procs, 'fury_of_xuen'):
            crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
            hit_chance = self.strike_hit_chance
            proc_value = (average_ap * .20 + 1) * 10 * (1 + min(4., self.settings.num_boss_adds))

        average_hit = proc_value * multiplier * hit_chance
        average_damage = average_hit * (1 + crit_rate * (crit_multiplier - 1)) * proc_count
        crit_contribution = average_hit * crit_multiplier * crit_rate * proc_count
        return average_damage, crit_contribution

    def append_damage_on_use(self, average_ap, current_stats, damage_breakdown):
        on_use_damage_list = []
        for i in ('spell_damage', 'physical_damage', 'melee_spell_damage'):
            on_use_damage_list += self.stats.gear_buffs.get_all_activated_boosts_for_stat(i)
        if self.race.rocket_barrage:
            rocket_barrage_dict = {'stat': 'spell_damage', 'cooldown': 120, 'name': 'Rocket Barrage'}
            rocket_barrage_dict['value'] = self.race.calculate_rocket_barrage(average_ap, 0, 0)
            on_use_damage_list.append(rocket_barrage_dict)

        for item in on_use_damage_list:
            if item['stat'] == 'physical_damage':
                modifier = self.raid_settings_modifiers('physical')
                crit_multiplier = self.crit_damage_modifiers()
                crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
                hit_chance = self.strike_hit_chance
            elif item['stat'] == 'spell_damage':
                modifier = self.raid_settings_modifiers('spell')
                crit_multiplier = self.crit_damage_modifiers()
                crit_rate = self.spell_crit_rate(crit=current_stats['crit'])
                hit_chance = self.cast_spell_hit_chance
            elif item['stat'] == 'melee_spell_damage':
                modifier = self.raid_settings_modifiers('spell')
                crit_multiplier = self.crit_damage_modifiers()
                crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
                hit_chance = self.strike_hit_chance
            average_hit = item['value'] * modifier
            frequency = 1. / (item['cooldown'] + self.settings.response_time)
            average_dps = average_hit * (1 + crit_rate * (crit_multiplier - 1)) * frequency * hit_chance
            crit_contribution = average_hit * crit_multiplier * crit_rate * frequency * hit_chance

            damage_breakdown[item['name']] = average_dps, crit_contribution

    def set_matrix_restabilizer_stat(self, base_stats):
        base_stats_for_matrix_restabilizer = {}
        for key in self.base_stats:
            if key in ('haste', 'mastery', 'crit'):
                base_stats_for_matrix_restabilizer[key] = self.base_stats[key]
        sorted_list = base_stats_for_matrix_restabilizer.keys()
        sorted_list.sort(cmp=lambda b, a: cmp(base_stats_for_matrix_restabilizer[a], base_stats_for_matrix_restabilizer[b]))

        if self.stats.procs.heroic_matrix_restabilizer:
            self.stats.procs.heroic_matrix_restabilizer.stat = sorted_list[0]
        if self.stats.procs.matrix_restabilizer:
            self.stats.procs.matrix_restabilizer.stat = sorted_list[0]
    
    def set_re_origination_stat(self, base_stats):
        #http://blue.mmo-champion.com/topic/254470-ptr-class-and-set-bonus-issues-part-iii/#post953
        max_stat = ('stat', 0)
        total_stats = 0
        # doesnt include the mastery raid buff
        base_stats['mastery'] -= self.buffs.buff_mast() * self.stats.mastery_mod * self.amplify_stats
        for key in base_stats:
            if key in ('haste', 'mastery', 'crit'):
                if (base_stats[key] > max_stat[1]):
                    max_stat = (key, base_stats[key])
        for key in base_stats:
            if key in ('haste', 'mastery', 'crit') and key != max_stat[0]:
                total_stats += base_stats[key]
                
        
        buff_cache = []
        for key in ('haste', 'mastery', 'crit'):
            if key != max_stat[0]:
                buff_cache.append( (key, -1. * base_stats[key]) )
            else:
                buff_cache.append( (key, (total_stats) * 2) )

        # (extremely sloppy)
        #set buff amounts
        if self.stats.procs.heroic_thunder_rune_of_re_origination:
            self.stats.procs.heroic_thunder_rune_of_re_origination.buffs = buff_cache
            self.stats.procs.heroic_thunder_rune_of_re_origination.set_rune_of_reorigination_rppm()
        if self.stats.procs.heroic_rune_of_re_origination:
            self.stats.procs.heroic_rune_of_re_origination.buffs = buff_cache
            self.stats.procs.heroic_rune_of_re_origination.set_rune_of_reorigination_rppm()
        if self.stats.procs.thunder_rune_of_re_origination:
            self.stats.procs.thunder_rune_of_re_origination.buffs = buff_cache
            self.stats.procs.thunder_rune_of_re_origination.set_rune_of_reorigination_rppm()
        if self.stats.procs.rune_of_re_origination:
            self.stats.procs.rune_of_re_origination.buffs = buff_cache
            self.stats.procs.rune_of_re_origination.set_rune_of_reorigination_rppm()
        if self.stats.procs.lfr_rune_of_re_origination:
            self.stats.procs.lfr_rune_of_re_origination.buffs = buff_cache
            self.stats.procs.lfr_rune_of_re_origination.set_rune_of_reorigination_rppm()

    def set_openers(self):
        if self.settings.is_subtlety_rogue():
            self.settings.use_opener = 'always' #Overrides setting. Using Ambush + Vanish on CD is critical.
            self.settings.opener_name = 'ambush'
        # Sets the swing_reset_spacing and total_openers_per_second variables.
        opener_cd = [10, 20][self.settings.opener_name == 'garrote']
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
        if self.settings.opener_name in cycle_abilities and not self.talents.shadow_focus:
            return 0
        elif self.settings.opener_name not in cycle_abilities and self.talents.shadow_focus:
            energy_per_opener = self.get_net_energy_cost(self.settings.opener_name)
            return -1 * self.get_shadow_focus_multiplier() * energy_per_opener * self.total_openers_per_second
        else:
            energy_per_opener = self.get_net_energy_cost(self.settings.opener_name)
            return [-1, 1][self.talents.shadow_focus] * self.get_shadow_focus_multiplier() * energy_per_opener * self.total_openers_per_second

    def get_t12_2p_damage(self, damage_breakdown):
        crit_damage = 0
        for key in damage_breakdown:
            if key in ('mutilate', 'hemorrhage', 'dispatch', 'backstab', 'sinister_strike', 'revealing_strike', 'main_gauche', 'ambush', 'killing_spree', 'envenom', 'eviscerate', 'autoattack'):
                average_damage, crit_contribution = damage_breakdown[key]
                crit_damage += crit_contribution
        for key in ('mut_munch', 'ksp_munch'):
            if key in damage_breakdown:
                average_damage, crit_contribution = damage_breakdown[key]
                crit_damage -= crit_contribution
                del damage_breakdown[key]

        return crit_damage * self.stats.gear_buffs.rogue_t12_2pc_damage_bonus(), 0

    def get_damage_breakdown(self, current_stats, attacks_per_second, crit_rates, damage_procs):
        average_ap = current_stats['ap'] + 2 * current_stats['agi'] + current_stats['str']
        average_ap *= self.buffs.attack_power_multiplier()
        if self.settings.is_combat_rogue():
            average_ap *= self.passive_vitality_ap

        damage_breakdown = {}
                
        if 'mh_autoattacks' in attacks_per_second:
            # Assumes mh and oh attacks are both active at the same time. As they should always be.
            #
            # Friends don't let friends raid without gear.
            (mh_base_damage, mh_crit_damage) = self.mh_damage(average_ap)
            mh_hit_rate = self.dw_mh_hit_chance - self.GLANCE_RATE - crit_rates['mh_autoattacks']
            average_mh_hit = self.GLANCE_RATE * self.GLANCE_MULTIPLIER * mh_base_damage + mh_hit_rate * mh_base_damage + crit_rates['mh_autoattacks'] * mh_crit_damage
            crit_mh_hit = crit_rates['mh_autoattacks'] * mh_crit_damage
            mh_dps_tuple = average_mh_hit * attacks_per_second['mh_autoattacks'], crit_mh_hit * attacks_per_second['mh_autoattacks']
            
            (oh_base_damage, oh_crit_damage) = self.oh_damage(average_ap)
            oh_hit_rate = self.dw_oh_hit_chance - self.GLANCE_RATE - crit_rates['oh_autoattacks']
            average_oh_hit = self.GLANCE_RATE * self.GLANCE_MULTIPLIER * oh_base_damage + oh_hit_rate * oh_base_damage + crit_rates['oh_autoattacks'] * oh_crit_damage
            crit_oh_hit = crit_rates['oh_autoattacks'] * oh_crit_damage
            oh_dps_tuple = average_oh_hit * attacks_per_second['oh_autoattacks'], crit_oh_hit * attacks_per_second['oh_autoattacks']
            
            if self.settings.merge_damage:
                damage_breakdown['autoattack'] = mh_dps_tuple[0] + oh_dps_tuple[0], mh_dps_tuple[1] + oh_dps_tuple[1]
            else:
                damage_breakdown['mh_autoattack'] = mh_dps_tuple[0], mh_dps_tuple[1]
                damage_breakdown['oh_autoattack'] = oh_dps_tuple[0], oh_dps_tuple[1]
                
            if 'eoh_autoattacks' in attacks_per_second:
                (eoh_base_damage, eoh_crit_damage) = self.eoh_damage(average_ap)
                eoh_hit_rate = self.dw_oh_hit_chance - self.GLANCE_RATE - crit_rates['eoh_autoattacks']
                average_eoh_hit = self.GLANCE_RATE * self.GLANCE_MULTIPLIER * eoh_base_damage + eoh_hit_rate * eoh_base_damage + crit_rates['eoh_autoattacks'] * eoh_crit_damage
                crit_eoh_hit = crit_rates['eoh_autoattacks'] * eoh_crit_damage
                eoh_dps_tuple = average_eoh_hit * attacks_per_second['eoh_autoattacks'], crit_eoh_hit * attacks_per_second['eoh_autoattacks']
                
                if self.settings.merge_damage:
                    damage_breakdown['autoattack'] = damage_breakdown['autoattack'][0] + eoh_dps_tuple[0], damage_breakdown['autoattack'][1] + eoh_dps_tuple[1]
                else:
                    damage_breakdown['eoh_autoattack'] = eoh_dps_tuple[0], eoh_dps_tuple[1]

        for key in attacks_per_second.keys():
            if not attacks_per_second[key]:
                del attacks_per_second[key]
        
        if 'mutilate' in attacks_per_second:
            mh_dmg = self.mh_mutilate_damage(average_ap)
            oh_dmg = self.oh_mutilate_damage(average_ap)
            mh_mutilate_dps = self.get_dps_contribution(mh_dmg, crit_rates['mutilate'], attacks_per_second['mutilate'])
            oh_mutilate_dps = self.get_dps_contribution(oh_dmg, crit_rates['mutilate'], attacks_per_second['mutilate'])
            if self.settings.merge_damage:
                damage_breakdown['mutilate'] = mh_mutilate_dps[0] + oh_mutilate_dps[0], mh_mutilate_dps[1] + oh_mutilate_dps[1]
            else:
                damage_breakdown['mh_mutilate'] = mh_mutilate_dps[0], mh_mutilate_dps[1]
                damage_breakdown['oh_mutilate'] = oh_mutilate_dps[0], oh_mutilate_dps[1]
            #if self.stats.gear_buffs.rogue_t12_2pc:
            #    p_double_crit = crit_rates['mutilate'] ** 2
            #    munch_per_sec = attacks_per_second['mutilate'] * p_double_crit
            #    damage_breakdown['mut_munch'] = 0, munch_per_sec * mh_dmg[1]

        for strike in ('hemorrhage', 'backstab', 'sinister_strike', 'revealing_strike', 'main_gauche', 'ambush', 'dispatch', 'shuriken_toss'):
            if strike in attacks_per_second:
                dps = self.get_dps_contribution(self.get_formula(strike)(average_ap), crit_rates[strike], attacks_per_second[strike])
                if strike in ('sinister_strike', 'backstab'):
                    dps = tuple([i * self.stats.gear_buffs.rogue_t14_2pc_damage_bonus(strike) for i in dps])
                damage_breakdown[strike] = dps

        if 'mh_shadow_blade' in attacks_per_second:
            mh_dps = self.get_dps_contribution(self.get_formula('mh_shadow_blade')(average_ap), crit_rates['mh_shadow_blade'], attacks_per_second['mh_shadow_blade'])
            oh_dps = self.get_dps_contribution(self.get_formula('oh_shadow_blade')(average_ap), crit_rates['oh_shadow_blade'], attacks_per_second['oh_shadow_blade'])
            if self.settings.merge_damage:
                damage_breakdown['shadow_blades'] = mh_dps[0] + oh_dps[0], mh_dps[1] + oh_dps[1]
            else:
                damage_breakdown['mh_shadow_blades'] = mh_dps[0], mh_dps[1]
                damage_breakdown['oh_shadow_blades'] = oh_dps[0], oh_dps[1]

        for poison in ('venomous_wounds', 'deadly_poison', 'wound_poison', 'deadly_instant_poison'):
            if poison in attacks_per_second:
                damage = self.get_dps_contribution(self.get_formula(poison)(average_ap, mastery=current_stats['mastery']), crit_rates[poison], attacks_per_second[poison])
                if poison == 'venomous_wounds':
                    damage = tuple([i * self.stats.gear_buffs.rogue_t14_2pc_damage_bonus('venomous_wounds') for i in damage])
                damage_breakdown[poison] = damage

        if 'mh_killing_spree' in attacks_per_second:
            mh_dmg = self.mh_killing_spree_damage(average_ap)
            if self.settings.cycle.weapon_swap:
                oh_dmg = self.oh_killing_spree_damage_swap(average_ap)
            else:
                oh_dmg = self.oh_killing_spree_damage(average_ap)
            mh_killing_spree_dps = self.get_dps_contribution(mh_dmg, crit_rates['killing_spree'], attacks_per_second['mh_killing_spree'])
            oh_killing_spree_dps = self.get_dps_contribution(oh_dmg, crit_rates['killing_spree'], attacks_per_second['oh_killing_spree'])
            if self.settings.merge_damage:
                damage_breakdown['killing_spree'] = mh_killing_spree_dps[0] + oh_killing_spree_dps[0], mh_killing_spree_dps[1] + oh_killing_spree_dps[1]
            else:
                damage_breakdown['mh_killing_spree'] = mh_killing_spree_dps[0], mh_killing_spree_dps[1]
                damage_breakdown['oh_killing_spree'] = oh_killing_spree_dps[0], oh_killing_spree_dps[1]
            #if self.stats.gear_buffs.rogue_t12_2pc:
            #    p_double_crit = crit_rates['killing_spree'] ** 2
            #    munch_per_sec = attacks_per_second['mh_killing_spree'] * p_double_crit
            #    damage_breakdown['ksp_munch'] = 0, munch_per_sec * mh_dmg[1]
                
        finisher_per_second = {'envenom': 0, 'eviscerate': 0, 'rupture_ticks':0}
        if 'rupture_ticks' in attacks_per_second:
            average_dps = crit_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.get_dps_contribution(self.rupture_tick_damage(average_ap, i), crit_rates['rupture_ticks'], attacks_per_second['rupture_ticks'][i])
                average_dps += dps_tuple[0]
                crit_dps += dps_tuple[1]
                finisher_per_second['rupture_ticks'] += attacks_per_second['rupture_ticks'][i]
            damage_breakdown['rupture'] = average_dps, crit_dps

        if 'garrote_ticks' in attacks_per_second:
            damage_breakdown['garrote'] = self.get_dps_contribution(self.garrote_tick_damage(average_ap), crit_rates['garrote'], attacks_per_second['garrote_ticks'])
            
        if 'envenom' in attacks_per_second:
            average_dps = crit_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.get_dps_contribution(self.envenom_damage(average_ap, i, current_stats['mastery']), crit_rates['envenom'], attacks_per_second['envenom'][i])
                average_dps += dps_tuple[0]
                crit_dps += dps_tuple[1]
                finisher_per_second['envenom'] += attacks_per_second['envenom'][i]
            damage_breakdown['envenom'] = average_dps, crit_dps

        if 'eviscerate' in attacks_per_second:
            average_dps = crit_dps = 0
            for i in xrange(1, 6):
                dps_tuple = self.get_dps_contribution(self.eviscerate_damage(average_ap, i), crit_rates['eviscerate'], attacks_per_second['eviscerate'][i])
                average_dps += dps_tuple[0]
                crit_dps += dps_tuple[1]
                finisher_per_second['eviscerate'] += attacks_per_second['eviscerate'][i]
            damage_breakdown['eviscerate'] = average_dps, crit_dps
            
        if 'hemorrhage_ticks' in attacks_per_second:
            dps_from_hit_hemo = self.get_dps_contribution(self.hemorrhage_tick_damage(average_ap, from_crit_hemo=False), crit_rates['hemorrhage'], attacks_per_second['hemorrhage_ticks'] * (1 - crit_rates['hemorrhage']))
            dps_from_crit_hemo = self.get_dps_contribution(self.hemorrhage_tick_damage(average_ap, from_crit_hemo=True), crit_rates['hemorrhage'], attacks_per_second['hemorrhage_ticks'] * crit_rates['hemorrhage'])
            damage_breakdown['hemorrhage_dot'] = dps_from_hit_hemo[0] + dps_from_crit_hemo[0], dps_from_hit_hemo[1] + dps_from_crit_hemo[1]
            
        # multistrike
        prefixes = ('heroic_war_','heroic_','war_','','flex_','lfr_')
        for prefix in prefixes:
            proc = getattr(self.stats.procs, ''.join((prefix, 'haromms_talisman')))
            if proc and proc.scaling:
                item_level = proc.scaling['item_level']
                if proc.scaling['quality'] == 'epic':
                    item_level += proc.upgrade_level * 4
                elif proc.scaling['quality'] == 'blue':
                    item_level += proc.upgrade_level * 8
                proc_chance = 0.0353999995 / 1000 * self.tools.get_random_prop_point(item_level, proc.scaling['quality'])
                dmg_multistrike = 0.
                for attack in damage_breakdown:
                    if attack not in ('deadly_instant_poison'):
                        dmg_multistrike += damage_breakdown[attack][0] / 3. * proc_chance
                damage_breakdown['multistrike'] = (dmg_multistrike,0.)
                break
            
        # cleave
        for prefix in prefixes:
            proc = getattr(self.stats.procs, ''.join((prefix, 'sigil_of_rampage')))
            if proc and proc.scaling:
                item_level = proc.scaling['item_level']
                if proc.scaling['quality'] == 'epic':
                    item_level += proc.upgrade_level * 4
                elif proc.scaling['quality'] == 'blue':
                    item_level += proc.upgrade_level * 8
                proc_chance = 0.0785999969 / 10000 * self.tools.get_random_prop_point(item_level, proc.scaling['quality'])
                dmg_cleave = 0.
                for attack in damage_breakdown:
                    if attack not in ('deadly_instant_poison','multistrike'):
                        # does not do damage to your primary target, only adds
                        dmg_cleave += damage_breakdown[attack][0] * proc_chance * min(5., self.settings.num_boss_adds)
                damage_breakdown['cleave'] = (dmg_cleave,0.)
                break

        if self.settings.use_stormlash:
            stormlash_mod_table = {'mh_autoattack_hits': .4 * (self.stats.mh.speed / 2.6),
                     'oh_autoattack_hits': .2 * (self.stats.oh.speed / 2.6), 
                     'mh_shadow_blade': .4 * (self.stats.mh.speed / 2.6), 
                     'oh_shadow_blade': .2 * (self.stats.oh.speed / 2.6), 
                     'sinister_strike': .5}
            if self.settings.use_stormlash == 'True':
                self.settings.use_stormlash = 1
            average_dps = crit_dps = 0
            uptime = int(self.settings.use_stormlash) * 10. / (5 * 60)
            for value in attacks_per_second:
                if value in self.all_attacks:
                    damage_mod = 1.
                    if value in stormlash_mod_table:
                        damage_mod = stormlash_mod_table[value]
                    if value in ('envenom', 'eviscerate', 'rupture_ticks'):
                        damage_tuple = self.get_dps_contribution(self.stormlash_totem_damage(average_ap, mod=damage_mod), self.spell_crit_rate(), finisher_per_second[value])
                    else:
                        damage_tuple = self.get_dps_contribution(self.stormlash_totem_damage(average_ap, mod=damage_mod), self.spell_crit_rate(), attacks_per_second[value])
                    average_dps += uptime * damage_tuple[0] * self.cast_spell_hit_chance
                    crit_dps += uptime * damage_tuple[1] * self.cast_spell_hit_chance
            damage_breakdown['stormlash'] = average_dps, crit_dps
        
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
            
        if self.damage_mod != 1:
            for key in damage_breakdown:
                damage_breakdown[key] *= self.damage_mod
        
        self.add_exported_data(damage_breakdown)

        return damage_breakdown
    
    def add_exported_data(self, damage_breakdown):
        #used explicitly to highjack data outputs to export additional data.
        if self.get_version_number:
            damage_breakdown['version_' + self.GENERAL_VERSION_NUMBER] = [.0, 0]
        
    def get_net_energy_cost(self, ability):
        stats = self.get_spell_stats(ability)
        hit_chance = (1, self.geometric_strike_chance)[stats[1] == 'strike']
        return stats[0] * (.8 + .2 / hit_chance)

    def get_activated_uptime(self, duration, cooldown, use_response_time=True):
        response_time = [0, self.settings.response_time][use_response_time]
        return 1. * duration / (cooldown + response_time)

    def get_shadow_blades_duration(self):
        if self.level < 87:
            return 0
        return 12 + self.stats.gear_buffs.rogue_t14_4pc_extra_time(is_combat=self.settings.is_combat_rogue())

    def get_shadow_blades_uptime(self, cooldown=None):
        # 'cooldown' used as an overide for combat cycles
        duration = self.get_shadow_blades_duration()
        return self.get_activated_uptime(duration, (cooldown, self.get_spell_cd('shadow_blades'))[cooldown is None])

    def update_with_shadow_blades(self, attacks_per_second, shadow_blades_uptime):
        mh_sb_swings_per_second = attacks_per_second['mh_autoattacks'] * shadow_blades_uptime
        oh_sb_swings_per_second = attacks_per_second['oh_autoattacks'] * shadow_blades_uptime
        attacks_per_second['mh_shadow_blade'] = mh_sb_swings_per_second * self.strike_hit_chance
        attacks_per_second['oh_shadow_blade'] = oh_sb_swings_per_second * self.strike_hit_chance
        
    def update_with_autoattack_passives(self, attacks_per_second, *args, **kwargs):
        # Appends the keys passed in args to attacks_per_second. This includes
        # autoattack, autoattack_hits, shadow_blades, main_gauche and poisons.
        # If no args passed, it'll attempt to append all of them.
        if not args or 'swings' in args or 'mh_autoattack' not in attacks_per_second or 'oh_autoattack' not in attacks_per_second:
            attacks_per_second['mh_autoattacks'] = kwargs['attack_speed_multiplier'] / self.stats.mh.speed
            attacks_per_second['oh_autoattacks'] = kwargs['attack_speed_multiplier'] / self.stats.oh.speed
        if (not args or 'shadow_blades' in args):
            if 'shadow_blades_uptime' not in kwargs:
                kwargs['shadow_blades_uptime'] = self.get_shadow_blades_uptime()
            self.update_with_shadow_blades(attacks_per_second, kwargs['shadow_blades_uptime'])
        if self.swing_reset_spacing is not None:
            attacks_per_second['mh_autoattacks'] *= (1 - max((1 - .5 * self.stats.mh.speed / kwargs['attack_speed_multiplier']), 0) / self.swing_reset_spacing)
            attacks_per_second['oh_autoattacks'] *= (1 - max((1 - .5 * self.stats.oh.speed / kwargs['attack_speed_multiplier']), 0) / self.swing_reset_spacing)
        if (not args or 'shadow_blades' in args):
            attacks_per_second['mh_autoattacks'] -= attacks_per_second['mh_shadow_blade'] / self.strike_hit_chance
            attacks_per_second['oh_autoattacks'] -= attacks_per_second['oh_shadow_blade'] / self.strike_hit_chance
        if not args or 'autoattack_hits' in args:
            attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dw_mh_hit_chance
            attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dw_oh_hit_chance
        if not args or 'poisons' in args:
            self.get_poison_counts(attacks_per_second)

    def get_mh_procs_per_second(self, proc, attacks_per_second, crit_rates):
        if proc.is_real_ppm():
            return proc.proc_rate(haste=self.buffs.spell_haste_multiplier() * self.true_haste_mod * self.stats.get_haste_multiplier_from_rating(self.base_stats['haste']))
        triggers_per_second = 0
        if proc.procs_off_auto_attacks():
            if proc.procs_off_crit_only():
                if 'mh_autoattacks' in attacks_per_second:
                    triggers_per_second += attacks_per_second['mh_autoattacks'] * crit_rates['mh_autoattacks']
            else:
                if 'mh_autoattack_hits' in attacks_per_second:
                    triggers_per_second += attacks_per_second['mh_autoattack_hits']
        if proc.procs_off_strikes():
            for ability in ('mutilate', 'dispatch', 'backstab', 'revealing_strike', 'sinister_strike', 'ambush', 'hemorrhage', 'mh_killing_spree', 'main_gauche', 'mh_shadow_blade', 'shuriken_toss'):
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
        return triggers_per_second * proc.proc_rate(self.stats.mh.speed)

    def get_oh_procs_per_second(self, proc, attacks_per_second, crit_rates):
        if proc.is_real_ppm() and not proc.scaling:
            return proc.proc_rate(haste=self.buffs.spell_haste_multiplier() * self.true_haste_mod * self.stats.get_haste_multiplier_from_rating(self.base_stats['haste']))
        elif proc.is_real_ppm():
            return 0
        triggers_per_second = 0
        if proc.procs_off_auto_attacks():
            if proc.procs_off_crit_only():
                if 'oh_autoattacks' in attacks_per_second:
                    triggers_per_second += attacks_per_second['oh_autoattacks'] * crit_rates['oh_autoattacks']
                if 'eoh_autoattacks' in attacks_per_second:
                    triggers_per_second += attacks_per_second['eoh_autoattacks'] * crit_rates['eoh_autoattacks']
            else:
                if 'oh_autoattack_hits' in attacks_per_second:
                    triggers_per_second += attacks_per_second['oh_autoattack_hits']
                if 'eoh_autoattack_hits' in attacks_per_second:
                    triggers_per_second += attacks_per_second['eoh_autoattack_hits']
        if proc.procs_off_strikes():
            for ability in ('mutilate', 'oh_killing_spree', 'oh_shadow_blade'):
                if ability in attacks_per_second:
                    if proc.procs_off_crit_only():
                        triggers_per_second += attacks_per_second[ability] * crit_rates[ability]
                    else:
                        triggers_per_second += attacks_per_second[ability]
        return triggers_per_second * proc.proc_rate(self.stats.oh.speed)

    def get_other_procs_per_second(self, proc, attacks_per_second, crit_rates):
        if proc.is_real_ppm() and not proc.scaling:
            return proc.proc_rate()
        elif proc.is_real_ppm():
            return 0
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
            return triggers_per_second * proc.proc_rate()

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

    def set_uptime(self, proc, attacks_per_second, crit_rates):
        if proc.is_real_ppm():
            #http://iam.yellingontheinternet.com/2013/04/12/theorycraft-201-advanced-rppm/
            haste = 1.
            if proc.haste_scales:
                haste *= self.stats.get_haste_multiplier_from_rating(self.base_stats['haste']) * self.buffs.spell_haste_multiplier() * self.true_haste_mod
            #The 1.1307 is a value that increases the proc rate due to bad luck prevention. It /should/ be constant among all rppm proc styles
            if not proc.icd:
                if proc.max_stacks <= 1:
                    proc.uptime = 1.1307 * (1 - math.e ** (-1 * haste * proc.rppm_proc_rate() * proc.duration / 60))
                else:
                    lambd = haste * proc.rppm_proc_rate() * proc.duration / 60
                    e_lambda = math.e ** lambd
                    e_minus_lambda = math.e ** (-1 * lambd)
                    proc.uptime = 1.1307 * (e_lambda - 1) * (1 - ((1 - e_minus_lambda) ** proc.max_stacks))
            else:
                mean_proc_time = 60. / (haste * proc.rppm_proc_rate()) + proc.icd - min(proc.icd, 10)
                proc.uptime = 1.1307 * proc.duration / mean_proc_time
        else:
            procs_per_second = self.get_procs_per_second(proc, attacks_per_second, crit_rates)

            if proc.icd:
                proc.uptime = proc.duration / (proc.icd + 1. / procs_per_second)
            else:
                if procs_per_second >= 1:
                    self.set_uptime_for_ramping_proc(proc, procs_per_second)
                else:
                # See http://elitistjerks.com/f31/t20747-advanced_rogue_mechanics_discussion/#post621369
                # for the derivation of this formula.
                    q = 1 - procs_per_second
                    Q = q ** proc.duration
                    if Q < .0001:
                        self.set_uptime_for_ramping_proc(proc, procs_per_second)
                    else:
                        P = 1 - Q
                        proc.uptime = P * (1 - P ** proc.max_stacks) / Q

    def update_with_damaging_proc(self, proc, attacks_per_second, crit_rates):
        if proc.is_real_ppm():
            #http://us.battle.net/wow/en/forum/topic/8197741003?page=4#79
            haste = 1.
            if proc.haste_scales:
                haste *= self.buffs.spell_haste_multiplier() * self.true_haste_mod * self.stats.get_haste_multiplier_from_rating(self.base_stats['haste'])
            #The 1.1307 is a value that increases the proc rate due to bad luck prevention. It /should/ be constant among all rppm proc styles
            #print proc.rppm_proc_rate()
            if not proc.icd:
                frequency = haste * 1.1307 * proc.rppm_proc_rate() / 60
            else:
                mean_proc_time = 60. / (haste * proc.rppm_proc_rate()) + proc.icd - min(proc.icd, 10)
                if proc.max_stacks > 1: # just correct if you only do damage on max_stacks, e.g. legendary_capacitive_meta
                    mean_proc_time *= proc.max_stacks
                frequency = 1.1307 / mean_proc_time
        else:
            if proc.icd:
                frequency = 1. / (proc.icd + 0.5 / self.get_procs_per_second(proc, attacks_per_second, crit_rates))
            else:
                frequency = self.get_procs_per_second(proc, attacks_per_second, crit_rates)

        attacks_per_second.setdefault(proc.proc_name, 0)
        if proc.stat == 'spell_damage':
            attacks_per_second[proc.proc_name] += frequency * self.cast_spell_hit_chance
        elif proc.stat == 'physical_damage':
            attacks_per_second[proc.proc_name] += frequency * self.strike_hit_chance
        elif proc.stat == 'melee_spell_damage':
            attacks_per_second[proc.proc_name] += frequency * self.strike_hit_chance

    """
    def get_weapon_damage_bonus(self):
        # Unheeded Warning does not proc as weapon damage anymore. I'll leave
        # this here in case they implement anything alike.
        bonus = 0
        if self.stats.procs.unheeded_warning:
            proc = self.stats.procs.unheeded_warning
            bonus += proc.value * proc.uptime

        return bonus
    """

    def update_crit_rates_for_4pc_t11(self, attacks_per_second, crit_rates):
        t11_4pc_bonus = self.stats.procs.rogue_t11_4pc
        if t11_4pc_bonus:
            direct_damage_finisher = ''
            for key in ('envenom', 'eviscerate'):
                if key in attacks_per_second and sum(attacks_per_second[key]) != 0:
                    if direct_damage_finisher:
                        raise InputNotModeledException(_('Unable to model the 4pc T11 set bonus in a cycle that uses both eviscerate and envenom'))
                    direct_damage_finisher = key

            if direct_damage_finisher:
                procs_per_second = self.get_procs_per_second(t11_4pc_bonus, attacks_per_second, crit_rates)
                finisher_spacing = min(1 / sum(attacks_per_second[direct_damage_finisher]), t11_4pc_bonus.duration)
                p = 1 - (1 - procs_per_second) ** finisher_spacing
                crit_rates[direct_damage_finisher] = p + (1 - p) * crit_rates[direct_damage_finisher]

    def get_4pc_t12_multiplier(self):
        if self.settings.tricks_on_cooldown:
            tricks_uptime = 30. / (30 + self.settings.response_time)
            return 1 + self.stats.gear_buffs.rogue_t12_4pc_stat_bonus() * tricks_uptime / 3
        else:
            return 1.

    def get_rogue_t13_legendary_combat_multiplier(self):
        # This only deals with the SS/RvS damage increase.
        if self.stats.gear_buffs.rogue_t13_legendary or self.stats.procs.jaws_of_retribution or self.stats.procs.maw_of_oblivion or self.stats.procs.fangs_of_the_father:
            return 1.45
        else:
            return 1.
    
    def get_shadow_focus_multiplier(self):
        if self.talents.shadow_focus:
            return (1 - .75)
        return 1.

    def setup_unique_procs(self):
        # We need to set these behaviours before calling any other method.
        # The stage 3 will very likely need a different set of behaviours
        # once we figure the whole thing.
        for proc in ('jaws_of_retribution', 'maw_of_oblivion', 'fangs_of_the_father'):
            if getattr(self.stats.procs, proc):
                if self.settings.is_assassination_rogue():
                    spec = 'assassination'
                elif self.settings.is_combat_rogue():
                    spec = 'combat'
                elif self.settings.is_subtlety_rogue():
                    spec = 'subtlety'
                getattr(self.stats.procs, proc).behaviour_toggle = spec
        
        
        if getattr(self.stats.procs, 'legendary_capacitive_meta'):
            if self.settings.is_assassination_rogue():
                spec = 'assassination'
            elif self.settings.is_combat_rogue():
                spec = 'combat'
            elif self.settings.is_subtlety_rogue():
                spec = 'subtlety'
            getattr(self.stats.procs, 'legendary_capacitive_meta').behaviour_toggle = spec

        if getattr(self.stats.procs, 'fury_of_xuen'):
            if self.settings.is_assassination_rogue():
                spec = 'assassination'
            elif self.settings.is_combat_rogue():
                spec = 'combat'
            elif self.settings.is_subtlety_rogue():
                spec = 'subtlety'
            getattr(self.stats.procs, 'fury_of_xuen').behaviour_toggle = spec

        # Tie Nokaled to the MH (equipping it in the OH, as a rogue, is unlikely)
        if 'nokaled_the_elements_of_death' in proc_data.allowed_procs:
            for i in ('', 'heroic_', 'lfr_'):
                proc = getattr(self.stats.procs, ''.join((i, 'nokaled_the_elements_of_death')))
                if proc:
                    setattr(proc, 'mh_only', True)

    def get_poison_counts(self, attacks_per_second):
        # Builds a phony 'poison' proc object to count triggers through the proc
        # methods. Removes first poison hit.
        poison = procs.Proc(**proc_data.allowed_procs['rogue_poison'])
        mh_hits_per_second = self.get_mh_procs_per_second(poison, attacks_per_second, None)
        oh_hits_per_second = self.get_oh_procs_per_second(poison, attacks_per_second, None)
        total_hits_per_second = mh_hits_per_second + oh_hits_per_second
        if self.settings.dmg_poison == 'dp':
            poison_base_proc_rate = .3
        elif self.settings.dmg_poison == 'wp':
            poison_base_proc_rate = .3

        if self.settings.is_assassination_rogue():
            poison_base_proc_rate += .2
            poison_envenom_proc_rate = poison_base_proc_rate + .15
            envenom_uptime = min(sum([(1 / self.geometric_strike_chance + cps + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp()) * attacks_per_second['envenom'][cps] for cps in xrange(1, 6)]), 1)
            avg_poison_proc_rate = poison_base_proc_rate * (1 - envenom_uptime) + poison_envenom_proc_rate * envenom_uptime
        else:
            avg_poison_proc_rate = poison_base_proc_rate

        if self.settings.dmg_poison == 'dp':
            poison_procs = avg_poison_proc_rate * total_hits_per_second - 1 / self.settings.duration
            attacks_per_second['deadly_instant_poison'] = poison_procs * self.poison_hit_chance
            attacks_per_second['deadly_poison'] = 1. / 3 * (1 - total_hits_per_second / self.settings.duration)
        elif self.settings.dmg_poison == 'wp':
            attacks_per_second['wound_poison'] = total_hits_per_second * avg_poison_proc_rate * self.poison_hit_chance

    def get_self_healing(self, dps_breakdown=None):
        # TODO: Needs better implementation, should be usable for now
        if dps_breakdown is None:
            dps_breakdown = self.get_dps_breakdown()
        healing_breakdown = {
            #'leeching': 0,
            'recuperate': 0, #if we ever allow recup weaving
            #'shiv_effect': 0 #if we ever allow shiv weaving (only with lp)
        }
        healing_sum = 0
        if self.settings.utl_poison == 'lp':
            if self.settings.shiv_interval > 0:
                healing_breakdown['shiv_effect'] = .05 * self.stats.get_max_health() * (1./self.settings.shiv_interval)
            healing_breakdown['leeching'] = 0
            for key in dps_breakdown:
                if key in self.melee_attacks:
                    healing_breakdown['leeching'] += dps_breakdown[key]*.1
        for entry in healing_breakdown:
            healing_sum += healing_breakdown[entry]
        return healing_sum, healing_breakdown
    
    def determine_stats(self, attack_counts_function):
        current_stats = {
            'str': self.base_strength,
            'agi': self.base_stats['agi'] * self.agi_multiplier * self.stats.agi_mod,
            'ap': self.base_stats['ap'] * self.stats.ap_mod,
            'crit': self.base_stats['crit'] * self.stats.crit_mod,
            'haste': self.base_stats['haste'] * self.stats.haste_mod * self.amplify_stats,
            'mastery': self.base_stats['mastery'] * self.stats.mastery_mod * self.amplify_stats
        }
        self.current_variables = {}

        active_procs = []
        damage_procs = []
        weapon_damage_procs = []

        self.setup_unique_procs()

        for proc_info in self.stats.procs.get_all_procs_for_stat():
            if (proc_info.stat in current_stats or proc_info.stat == 'multi') and not proc_info.is_ppm():
                active_procs.append(proc_info)
            elif proc_info.stat in ('spell_damage', 'physical_damage', 'melee_spell_damage'):
                damage_procs.append(proc_info)
            elif proc_info.stat == 'extra_weapon_damage':
                weapon_damage_procs.append(proc_info)

        for proc in active_procs:
            if proc.scaling is not None:
                item_level = proc.scaling['item_level']
                if proc.scaling['quality'] == 'epic':
                    item_level += proc.upgrade_level * 4
                elif proc.scaling['quality'] == 'blue':
                    item_level += proc.upgrade_level * 8
                proc.value = round(proc.scaling['factor'] * self.tools.get_random_prop_point(item_level, proc.scaling['quality']))

        windsong_enchants = []
        weapon_enchants = set([])
        for hand, enchant in [(x, y) for x in ('mh', 'oh') for y in ('windsong', 'dancing_steel', 'elemental_force')]:
            proc = getattr(getattr(self.stats, hand), enchant)
            if proc:
                setattr(proc, '_'.join((hand, 'only')), True)
                if (proc.stat in current_stats or proc.stat == 'multi'):
                    active_procs.append(proc)
                elif enchant in ('avalanche', 'elemental_force'):
                    damage_procs.append(proc)
                elif enchant == 'windsong':
                    windsong_enchants.append(proc)
                elif proc.stat == 'highest' and 'agi' in proc.stats:
                    proc.stat = 'agi'
                    active_procs.append(proc)

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

        attacks_per_second, crit_rates = attack_counts_function(current_stats)

        for _loop in range(20):
            current_stats = {
                'str': self.base_strength,
                'agi': self.base_stats['agi'] * self.agi_multiplier * self.stats.agi_mod,
                'ap': self.base_stats['ap'] * self.stats.ap_mod,
                'crit': self.base_stats['crit'] * self.stats.crit_mod,
                'haste': self.base_stats['haste'] * self.stats.haste_mod * self.amplify_stats,
                'mastery': self.base_stats['mastery'] * self.stats.mastery_mod * self.amplify_stats
            }

            for proc in damage_procs:
                if not proc.icd:
                    self.update_with_damaging_proc(proc, attacks_per_second, crit_rates)

            for proc in active_procs:
                if not proc.icd:
                    self.set_uptime(proc, attacks_per_second, crit_rates)
                    if proc.stat == 'multi':
                        for e in proc.buffs:
                            current_stats[ e[0] ] += proc.uptime * e[1] * self.get_stat_mod(e[0])
                    else:
                        current_stats[proc.stat] += proc.uptime * proc.value * self.get_stat_mod(proc.stat)

            if windsong_enchants:
                proc = windsong_enchants[0]
                stats = proc.stats
                effective_ppm_multiplier = len(windsong_enchants) * 1.0 / len(stats)
                proc.ppm *= effective_ppm_multiplier
                self.set_uptime(proc, attacks_per_second, crit_rates)
                proc.ppm /= effective_ppm_multiplier
                for stat in stats:
                    current_stats[stat] += proc.uptime * proc.value * self.get_stat_mod(stat)
            
            old_attacks_per_second = attacks_per_second
            attacks_per_second, crit_rates = attack_counts_function(current_stats)

            if self.are_close_enough(old_attacks_per_second, attacks_per_second):
                break
            
        for proc in active_procs:
            if proc.icd:
                self.set_uptime(proc, attacks_per_second, crit_rates)
                if proc.stat == 'multi':
                    for e in proc.buffs:
                        if proc.stat == 'agi':
                            current_stats[ e[0] ] += proc.uptime * e[1] * self.agi_multiplier
                        else:
                            current_stats[ e[0] ] += proc.uptime * e[1] * self.get_stat_mod(e[0])
                else:
                    if proc.stat == 'agi':
                        current_stats[proc.stat] += proc.uptime * proc.value * self.agi_multiplier
                    else:
                        current_stats[proc.stat] += proc.uptime * proc.value * self.get_stat_mod(proc.stat)

        attacks_per_second, crit_rates = attack_counts_function(current_stats)

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
            current_stats['mastery'] += res * self.stats.mastery_mod * self.amplify_stats

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
    
    def average_damage_breakdowns(self, aps_dict, denom=180):
        final_breakdown = {}
        #key: phase name
        #number: place in tuple... tuple = (phase_length, dps_breakdown)
        #entry: DPS skill_name
        #denom: total duration (to divide phase duration by it)
        for key in aps_dict:
            for entry in aps_dict[key][1]:
                if entry in final_breakdown:
                    final_breakdown[entry] += aps_dict[key][1][entry] * (aps_dict[key][0]/denom)
                else:
                    final_breakdown[entry] = aps_dict[key][1][entry] * (aps_dict[key][0]/denom)
        return final_breakdown

    # This relies on set_uptime being called for the proc in compute_damage before any of the actual computation stuff is invoked.
    def unheeded_warning_bonus(self):
        proc = self.stats.procs.unheeded_warning
        if not proc:
            return 0        
        return proc.value * proc.uptime
        
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

        self.set_constants()

        self.base_energy_regen = 10
        self.max_energy = 120.
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            self.max_energy += 30

        self.vendetta_duration = 20 + 10 * self.glyphs.vendetta
        self.vendetta_uptime = self.vendetta_duration / (self.get_spell_cd('vendetta') + self.settings.response_time + self.major_cd_delay)
        vendetta_multiplier = .3 - .05 * self.glyphs.vendetta
        self.vendetta_mult = 1 + vendetta_multiplier * self.vendetta_uptime

        shadow_blades_duration = self.get_shadow_blades_duration()
        vendetta_shadow_blades_overlap = min(shadow_blades_duration, self.vendetta_duration)
        vendetta_uptime_during_shadow_blades = .5 * vendetta_shadow_blades_overlap / shadow_blades_duration
        self.shadow_blades_vendetta_mult = 1 + vendetta_multiplier * vendetta_uptime_during_shadow_blades

        shadow_blades_spacing = self.get_spell_cd('shadow_blades') + self.settings.response_time + self.major_cd_delay
        autoattack_duration = shadow_blades_spacing - shadow_blades_duration
        autoattack_vendetta_overlap = shadow_blades_spacing * self.vendetta_uptime - shadow_blades_duration * vendetta_uptime_during_shadow_blades
        self.autoattack_vendetta_mult = 1 + vendetta_multiplier * autoattack_vendetta_overlap / autoattack_duration

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
            if key == 'shadow_blades':
                damage_breakdown[key] *= self.shadow_blades_vendetta_mult
            elif key == 'autoattack':
                damage_breakdown[key] *= self.autoattack_vendetta_mult
            elif key != 'Elemental Force':
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

    def assassination_attack_counts(self, current_stats, cpg, finisher_size):
        attacks_per_second = {}
        crit_rates = self.get_crit_rates(current_stats)

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod
        ability_cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_reduced_cost()

        energy_regen = self.base_energy_regen * haste_multiplier
        energy_regen += self.bonus_energy_regen
        if cpg == 'dispatch':
            energy_regen += (self.max_energy - 10) / (self.settings.duration * self.settings.time_in_execute_range)

        vw_energy_return = 10
        vw_proc_chance = .75
        vw_energy_per_bleed_tick = vw_energy_return * vw_proc_chance

        blindside_proc_rate = [0, .3][cpg == 'mutilate']
        blindside_proc_rate *= self.strike_hit_chance
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

        shadow_blades_uptime = self.get_shadow_blades_uptime()

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
            cpg_energy_cost -= 6 * seal_fate_proc_rate * self.strike_hit_chance

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
            for blindside, shadow_blades in [(x, y) for x in (True, False) for y in (True, False)]:
                # blindside uptime as the amount of connecting cpgs that get 'turned' into dipatches
                if blindside and shadow_blades:
                    uptime = shadow_blades_uptime * dispatch_as_cpg_chance
                    cp_per_cpg = self.get_cp_per_cpg(1, dsp_seal_fate_proc_rate, 1)
                    current_finisher_size = finisher_size
                elif blindside and not shadow_blades:
                    uptime = dispatch_as_cpg_chance - shadow_blades_uptime * dispatch_as_cpg_chance
                    cp_per_cpg = self.get_cp_per_cpg(1, dsp_seal_fate_proc_rate)
                    current_finisher_size = finisher_size + 1
                elif not blindside and shadow_blades:
                    uptime = shadow_blades_uptime - shadow_blades_uptime * dispatch_as_cpg_chance
                    cp_per_cpg = self.get_cp_per_cpg(base_cp_per_cpg, mut_seal_fate_proc_rate, 1)
                    current_finisher_size = finisher_size - 1
                elif not blindside and not shadow_blades:
                    uptime = 1 - shadow_blades_uptime - dispatch_as_cpg_chance + shadow_blades_uptime * dispatch_as_cpg_chance
                    cp_per_cpg = self.get_cp_per_cpg(base_cp_per_cpg, mut_seal_fate_proc_rate)
                    current_finisher_size = finisher_size
                dists = self.get_cp_distribution_for_cycle(cp_per_cpg, current_finisher_size)
                uptime_and_dists_tuples.append((uptime, dists))
        else:
            for shadow_blades in (True, False):
                if shadow_blades:
                    uptime = shadow_blades_uptime
                    cp_per_cpg = self.get_cp_per_cpg(base_cp_per_cpg, seal_fate_proc_rate, 1)
                    current_finisher_size = finisher_size - 1
                elif not shadow_blades:
                    uptime = 1 - shadow_blades_uptime
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
        avg_wait_to_strike_connect = 1 / self.geometric_strike_chance - 1
        avg_gap = 0 + .5 * (avg_wait_to_strike_connect + .5 * self.settings.response_time)
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

        energy_for_rupture = cpg_per_rupture * cpg_energy_cost + self.get_spell_stats('rupture',  hit_chance=self.geometric_strike_chance, cost_mod=ability_cost_modifier)[0]
        energy_for_rupture -= avg_rupture_size * self.relentless_strikes_energy_return_per_cp
        energy_for_envenoms = energy_per_cycle - energy_for_rupture

        envenom_energy_cost = cpg_per_finisher * cpg_energy_cost + self.get_spell_stats('envenom',  hit_chance=self.geometric_strike_chance, cost_mod=ability_cost_modifier)[0]
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
            attacks_per_second['venomous_wounds'] += total_rupture_ticks_per_second * vw_proc_chance * self.poison_hit_chance
        else:
            attacks_per_second['venomous_wounds'] = total_rupture_ticks_per_second * vw_proc_chance * self.poison_hit_chance

        if 'garrote' in attacks_per_second:
            attacks_per_second['garrote_ticks'] = 6 * attacks_per_second['garrote']
        for opener, cps in [('ambush', 2), ('garrote', 1)]:
            if opener in attacks_per_second:
                if opener == 'ambush':
                    cps += crit_rates[opener]
                extra_finishers_per_second = attacks_per_second[opener] * cps / 5
                attacks_per_second['envenom'][5] += extra_finishers_per_second

        self.update_with_autoattack_passives(attacks_per_second,
                shadow_blades_uptime=shadow_blades_uptime,
                attack_speed_multiplier=attack_speed_multiplier)

        return attacks_per_second, crit_rates
    
    def assassination_attack_counts_anticipation(self, current_stats, cpg, finisher_size):
        attacks_per_second = {}
        crit_rates = self.get_crit_rates(current_stats)

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod
        ability_cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_reduced_cost()

        energy_regen = self.base_energy_regen * haste_multiplier
        energy_regen += self.bonus_energy_regen

        vw_energy_return = 10
        vw_proc_chance = .75
        vw_energy_per_bleed_tick = vw_energy_return * vw_proc_chance

        blindside_proc_rate = [0, .3 * self.strike_hit_chance][cpg == 'mutilate']
        dispatch_as_cpg_chance = blindside_proc_rate / (1 + blindside_proc_rate)

        opener_net_cost = self.get_spell_stats(self.settings.opener_name, cost_mod=ability_cost_modifier*self.get_shadow_focus_multiplier(), hit_chance=self.strike_hit_chance)[0]
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

        shadow_blades_uptime = self.get_shadow_blades_uptime()
        blindside_cost = 0
        mutilate_cost = self.get_spell_stats('mutilate', cost_mod=ability_cost_modifier, hit_chance=self.geometric_strike_chance)[0]
        
        if cpg == 'mutilate':
            cpg_energy_cost = blindside_cost + mutilate_cost
        else:
            cpg_energy_cost = self.get_spell_stats('dispatch', cost_mod=ability_cost_modifier, hit_chance=self.geometric_strike_chance)[0]
        mutilate_cps = 3 - (1 - crit_rates['mutilate']) ** 2 # 1 - (1 - crit_rates['mutilate']) ** 2 is the Seal Fate CP
        dispatch_cps = 1 + crit_rates['dispatch']
        if cpg == 'mutilate':
            avg_cp_per_cpg = mutilate_cps + dispatch_cps * blindside_proc_rate + shadow_blades_uptime * (1+blindside_proc_rate)
        else:
            avg_cp_per_cpg = dispatch_cps + shadow_blades_uptime
        seal_fate_proc_rate = crit_rates['dispatch']
        if cpg == 'mutilate':
            seal_fate_proc_rate *= blindside_proc_rate
            seal_fate_proc_rate += 1 - (1 - crit_rates['mutilate']) ** 2
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            cpg_energy_cost -= 6 * seal_fate_proc_rate * self.strike_hit_chance
            
        cp_per_finisher = 5
        avg_rupture_length = 4. * (6 + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp()) # 1+5 since all 5CP ruptures
        avg_wait_to_strike_connect = 1 / self.geometric_strike_chance - 1
        avg_gap = 0 + .5 * (avg_wait_to_strike_connect + .5 * self.settings.response_time)
        avg_cycle_length = avg_gap + avg_rupture_length
        attacks_per_second['rupture'] = 1 / avg_cycle_length
        rupture_ticks_per_second = 2 * (6 + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp()) / avg_cycle_length # 1+5 since all 5CP ruptures
        attacks_per_second['rupture_ticks'] = [0, 0, 0, 0, 0, rupture_ticks_per_second]
        
        energy_regen_with_rupture = energy_regen + attacks_per_second['rupture_ticks'][5] * vw_energy_per_bleed_tick
        energy_per_cycle = avg_rupture_length * energy_regen_with_rupture + avg_gap * energy_regen
        cpg_per_finisher = cp_per_finisher / avg_cp_per_cpg
        
        energy_for_rupture = cpg_per_finisher * cpg_energy_cost + self.get_spell_stats('rupture',  hit_chance=self.geometric_strike_chance, cost_mod=ability_cost_modifier)[0]
        energy_for_rupture -= cp_per_finisher * self.relentless_strikes_energy_return_per_cp
        energy_for_envenoms = energy_per_cycle - energy_for_rupture

        envenom_energy_cost = cpg_per_finisher * cpg_energy_cost + self.get_spell_stats('envenom',  hit_chance=self.geometric_strike_chance, cost_mod=ability_cost_modifier)[0]
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
            attacks_per_second['venomous_wounds'] += rupture_ticks_per_second * vw_proc_chance * self.poison_hit_chance
        else:
            attacks_per_second['venomous_wounds'] = rupture_ticks_per_second * vw_proc_chance * self.poison_hit_chance

        if 'garrote' in attacks_per_second:
            attacks_per_second['garrote_ticks'] = 6 * attacks_per_second['garrote']
        for opener, cps in [('ambush', 2), ('garrote', 1)]:
            if opener in attacks_per_second:
                if opener == 'ambush':
                    cps += crit_rates[opener]
                attacks_per_second['envenom'][5] += attacks_per_second[opener] * cps / 5
        attacks_per_second['envenom'][5] += 1. / 180
        
        self.update_with_autoattack_passives(attacks_per_second,
                shadow_blades_uptime=shadow_blades_uptime,
                attack_speed_multiplier=attack_speed_multiplier)
        
        #print attacks_per_second
        return attacks_per_second, crit_rates

    def assassination_attack_counts_non_execute(self, current_stats):
        if self.talents.anticipation:
            return self.assassination_attack_counts_anticipation(current_stats, 'mutilate', self.settings.cycle.min_envenom_size_non_execute)
        return self.assassination_attack_counts(current_stats, 'mutilate', self.settings.cycle.min_envenom_size_non_execute)

    def assassination_attack_counts_execute(self, current_stats):
        if self.talents.anticipation:
            return self.assassination_attack_counts_anticipation(current_stats, 'dispatch', self.settings.cycle.min_envenom_size_non_execute)
        return self.assassination_attack_counts(current_stats, 'dispatch', self.settings.cycle.min_envenom_size_execute)

    ###########################################################################
    # Combat DPS functions
    ###########################################################################

    def combat_dps_estimate(self):
        return sum(self.combat_dps_breakdown().values())

    def combat_dps_breakdown(self):
        if not self.settings.is_combat_rogue():
            raise InputNotModeledException(_('You must specify a combat cycle to match your combat spec.'))

        self.set_constants()

        self.max_bandits_guile_buff = 1.3

        self.ks_cd = 120
        self.max_energy = 100.
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            self.max_energy += 30
            
        ar_duration = 15
        sb_dur = self.get_shadow_blades_duration()
        restless_blades_reduction = 2
        self.ksp_buff = 0.5
        self.revealing_strike_multiplier = 1.35
        self.extra_cp_chance = .2 # Assume all casts during RvS
        self.rvs_duration = 24
        self.combat_phase_buffer = 3.5 #rough accounting for KS+RB delay
        
        cds = {'ar':self.get_spell_cd('adrenaline_rush')}
        
        phases = {}
        #Could definitely be cleaner, but it works for now
        if self.settings.cycle.stack_cds:
            #Phase 1: AR (AND) SB
            stats, aps, crits, procs = self.determine_stats(self.combat_attack_counts_both)
            #                (phase_length,
            #                 damage_breakdown)
            phases['both'] = (min(ar_duration, self.get_shadow_blades_duration()),
                              self.update_with_bandits_guile(self.compute_damage_from_aps(stats, aps, crits, procs)) )
        
            for e in cds:
                cds[e] -= phases['both'][0] / self.rb_cd_modifier(aps)
        
            #Phase 2: AR (xor) SB, if possible
            phase_length = abs(ar_duration - self.get_shadow_blades_duration()) #length of time with either just AR or SB up
            phases['buffer'] = (0, {})
            if ar_duration > self.get_shadow_blades_duration():
                stats, aps, crits, procs = self.determine_stats(self.combat_attack_counts_ar)
                phases['buffer'] = (abs(ar_duration - self.get_shadow_blades_duration()),
                                    self.update_with_bandits_guile(self.compute_damage_from_aps(stats, aps, crits, procs)) )
            elif ar_duration < self.get_shadow_blades_duration():
                stats, aps, crits, procs = self.determine_stats(self.combat_attack_counts_sb)
                phases['buffer'] = (abs(ar_duration - self.get_shadow_blades_duration()),
                                    self.update_with_bandits_guile(self.compute_damage_from_aps(stats, aps, crits, procs)) )
            for e in cds:
                cds[e] -= phases['buffer'][0] / self.rb_cd_modifier(aps)
            
            #Phase 3: (not) AR (nor) SB
            self.tmp_phase_length = cds['ar'] #This is to approximate the value of a full energy bar to be used when not during AR or SB
            stats, aps, crits, procs = self.determine_stats(self.combat_attack_counts_none)
            phases['none'] = (self.rb_actual_cds(aps, cds)['ar'] + self.settings.response_time + self.major_cd_delay + self.combat_phase_buffer,
                              self.update_with_bandits_guile(self.compute_damage_from_aps(stats, aps, crits, procs)) )
            
            total_duration = phases['none'][0] + phases['buffer'][0] + phases['both'][0]
        else:
            #AR phase
            stats, aps, crits, procs = self.determine_stats(self.combat_attack_counts_ar)
            phases['ar'] = (ar_duration,
                            self.update_with_bandits_guile(self.compute_damage_from_aps(stats, aps, crits, procs)) )
            for e in cds:
                cds[e] -= ar_duration / self.rb_cd_modifier(aps)
            
            #SB phase
            stats, aps, crits, procs = self.determine_stats(self.combat_attack_counts_sb)
            phases['sb'] = (self.get_shadow_blades_duration(),
                            self.update_with_bandits_guile(self.compute_damage_from_aps(stats, aps, crits, procs)) )
            for e in cds:
                cds[e] -= self.get_shadow_blades_duration() / self.rb_cd_modifier(aps)
            
            #none
            self.tmp_phase_length = cds['ar'] #This is to approximate the value of a full energy bar to be used when not during AR or SB
            stats, aps, crits, procs = self.determine_stats(self.combat_attack_counts_none)
            phases['none'] = (self.rb_actual_cds(aps, cds)['ar'] + self.settings.response_time + self.major_cd_delay + self.combat_phase_buffer,
                              self.update_with_bandits_guile(self.compute_damage_from_aps(stats, aps, crits, procs)) )
            
            total_duration = phases['ar'][0] + phases['sb'][0] + phases['none'][0] 
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
            elif key in ('sinister_strike', 'revealing_strike', 'shadow_blades', 'mh_shadow_blades', 'oh_shadow_blades'):
                damage_breakdown[key] *= self.bandits_guile_multiplier
            elif key in ('eviscerate', 'rupture'):
                damage_breakdown[key] *= self.bandits_guile_multiplier * self.revealing_strike_multiplier
            elif key in ('autoattack', 'deadly_poison', 'main_gauche', 'mh_autoattack', 'oh_autoattack'):
                damage_breakdown[key] *= self.bandits_guile_multiplier #* self.ksp_multiplier
            else:
                damage_breakdown[key] *= self.bandits_guile_multiplier #* self.ksp_multiplier
                
        return damage_breakdown
    
    def combat_attack_counts(self, current_stats, ar=False, sb=False):
        attacks_per_second = {}
        #base_energy_regen needs to be reset here.
        self.base_energy_regen = 12.
        if self.settings.cycle.blade_flurry:
            self.base_energy_regen *= .8

        crit_rates = self.get_crit_rates(current_stats)

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste']) * self.true_haste_mod

        self.attack_speed_increase = self.base_speed_multiplier * haste_multiplier

        main_gauche_proc_rate = self.combat_mastery_conversion * self.stats.get_mastery_from_rating(current_stats['mastery']) * self.strike_hit_chance

        combat_potency_regen_per_oh = 15 * .2 * self.stats.oh.speed / 1.4  # the new "normalized" formula
        combat_potency_from_mg = 15 * .2
        FINISHER_SIZE = 5
        ruthlessness_value = 1 # 1CP gained at 20% chance per CP spent (5CP spent means 1 is always added)
        
        if ar:
            self.attack_speed_increase *= 1.2
            self.base_energy_regen *= 2.0
        gcd_size = 1.0 + self.settings.latency
        if ar: #AR glyph is baseline
            gcd_size -= .2
        if sb and self.stats.gear_buffs.rogue_t15_4pc:
            gcd_size -= .3
        cp_per_cpg = 1.
        if sb:
            cp_per_cpg += 1
            
        # Combine energy cost scalers to reduce function calls (ie, 40% reduced energy cost). Assume multiplicative.
        cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_modifier(is_sb=sb)
        # Turn the cost of the ability into the net loss of energy by reducing it by the energy gained from MG
        cost_reducer = main_gauche_proc_rate * combat_potency_from_mg
        
        #get_spell_stats(self, ability, hit_chance=1.0, cost_mod=1.0)
        rupture_energy_cost = self.get_spell_stats('rupture', hit_chance=self.geometric_strike_chance, cost_mod=cost_modifier)[0]
        eviscerate_energy_cost =  self.get_spell_stats('eviscerate', hit_chance=self.geometric_strike_chance, cost_mod=cost_modifier)[0]
        eviscerate_energy_cost -= cost_reducer
        revealing_strike_energy_cost =  self.get_spell_stats('revealing_strike', hit_chance=self.geometric_strike_chance, cost_mod=cost_modifier)[0]
        revealing_strike_energy_cost -= cost_reducer
        sinister_strike_energy_cost =  self.get_spell_stats('sinister_strike', hit_chance=self.geometric_strike_chance, cost_mod=cost_modifier)[0]
        sinister_strike_energy_cost -= cost_reducer
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            sinister_strike_energy_cost -= 15 * self.extra_cp_chance
        
        ## Base CPs and Attacks
        #Autoattacks and SB swings
        if sb:
            attacks_per_second['mh_shadow_blade'] = self.attack_speed_increase / self.stats.mh.speed
            attacks_per_second['oh_shadow_blade'] = self.attack_speed_increase / self.stats.oh.speed
            attacks_per_second['main_gauche'] = attacks_per_second['mh_shadow_blade'] * main_gauche_proc_rate
            combat_potency_regen = attacks_per_second['oh_shadow_blade'] * combat_potency_regen_per_oh
        else:
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
        if self.settings.cycle.weapon_swap and not (ar or sb):
            combat_potency_regen *= 1. - 1. / (self.tmp_phase_length + self.combat_phase_buffer + self.major_cd_delay)
        
        #Base energy
        bonus_energy_from_openers = self.get_bonus_energy_from_openers('sinister_strike', 'revealing_strike')
        combat_potency_regen += combat_potency_from_mg * attacks_per_second['main_gauche']
        if self.settings.opener_name in ('ambush', 'garrote'):
            attacks_per_second[self.settings.opener_name] = self.total_openers_per_second
            attacks_per_second['main_gauche'] += self.total_openers_per_second * main_gauche_proc_rate
        energy_regen = self.base_energy_regen * haste_multiplier + self.bonus_energy_regen + combat_potency_regen + bonus_energy_from_openers
        #Rough idea to factor in a full energy bar
        if not ar and not sb:
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
            if sb:
                ss_per_finisher = 2
        cp_per_finisher = FINISHER_SIZE
        energy_cost_per_cp = ss_per_finisher * sinister_strike_energy_cost
        total_eviscerate_cost = energy_cost_per_cp + eviscerate_energy_cost - cp_per_finisher * self.relentless_strikes_energy_return_per_cp
        total_rupture_cost = energy_cost_per_cp + rupture_energy_cost - cp_per_finisher * self.relentless_strikes_energy_return_per_cp

        ss_per_snd = ss_per_finisher
        snd_size = FINISHER_SIZE
        snd_base_cost = 25
        snd_cost = ss_per_snd * sinister_strike_energy_cost + snd_base_cost - snd_size * self.relentless_strikes_energy_return_per_cp
        snd_duration = self.get_snd_length(snd_size)
        energy_spent_on_snd = snd_cost / snd_duration
        
        #Base Actions
        #marked for death CD
        marked_for_death_cd = self.get_spell_cd('marked_for_death') + (total_rupture_cost - .5 * total_eviscerate_cost) / (2 * energy_regen) + self.settings.response_time
        if self.talents.marked_for_death:
            energy_regen -= 10. / marked_for_death_cd
        energy_regen -= revealing_strike_energy_cost / rvs_interval
        if self.settings.cycle.use_rupture:
            avg_rupture_gap = (total_rupture_cost - .5 * total_eviscerate_cost) / energy_regen
            avg_rupture_duration = 4 * (1 + cp_per_finisher + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())
            attacks_per_second['rupture'] = 1 / (avg_rupture_duration + avg_rupture_gap)
        else:
            attacks_per_second['rupture'] = 0
        energy_spent_on_rupture = total_rupture_cost * attacks_per_second['rupture']
        
        #Base CPGs
        attacks_per_second['sinister_strike_base'] = ss_per_snd / snd_duration + attacks_per_second['rupture'] * ss_per_finisher
        attacks_per_second['revealing_strike'] = 1. / rvs_interval
        extra_finishers_per_second = attacks_per_second['revealing_strike'] / (5/cp_per_cpg)
        #Scaling CPGs
        free_gcd = 1./gcd_size
        free_gcd -= 1./snd_duration + (attacks_per_second['sinister_strike_base'] + attacks_per_second['revealing_strike'] + attacks_per_second['rupture'] + extra_finishers_per_second) / self.geometric_strike_chance
        if self.talents.marked_for_death:
            free_gcd -= (1. / marked_for_death_cd) / self.geometric_strike_chance
        energy_available_for_evis = energy_regen - energy_spent_on_snd - energy_spent_on_rupture
        total_evis_per_second = energy_available_for_evis / total_eviscerate_cost
        evisc_actions_per_second = (total_evis_per_second * ss_per_finisher + total_evis_per_second) / self.geometric_strike_chance
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
        
        #self.current_variables['cp_spent_on_damage_finishers_per_second'] = (attacks_per_second['rupture'] + total_evis_per_second) * cp_per_finisher
        ticks_per_rupture = 2 * (1 + 5 + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())
        attacks_per_second['rupture_ticks'] = [0, 0, 0, 0, 0, ticks_per_rupture * attacks_per_second['rupture']]
        #for i in xrange(1, 6):
            #ticks_per_rupture = 2 * (1 + i + self.stats.gear_buffs.rogue_t15_2pc_bonus_cp())
            ##attacks_per_second['rupture_ticks'][i] = ticks_per_rupture * attacks_per_second['rupture'] * finisher_size_breakdown[i]
            #attacks_per_second['rupture_ticks'][i] = ticks_per_rupture * attacks_per_second['rupture'] * [0,0,0,0,0,1][i]

        if 'garrote' in attacks_per_second:
            attacks_per_second['garrote_ticks'] = 6 * attacks_per_second['garrote']
        
        self.current_variables['cpgs_per_second'] = attacks_per_second['sinister_strike'] + attacks_per_second['revealing_strike']
        time_at_level = 4 / self.current_variables['cpgs_per_second']
        cycle_duration = 3 * time_at_level + 15
        avg_stacks = (3 * time_at_level + 45) / cycle_duration #45 is the duration (15s) multiplied by the stack power (30% BG)
        self.bandits_guile_multiplier = 1 + .1 * avg_stacks
        
        if not sb and not ar:
            final_ks_cd = self.rb_actual_cd(attacks_per_second, self.tmp_phase_length) + self.combat_phase_buffer + self.major_cd_delay
            if not self.settings.cycle.ksp_immediately:
                final_ks_cd += (3 * time_at_level)/2 * (3 * time_at_level)/cycle_duration
            attacks_per_second['mh_killing_spree'] = 7 * self.strike_hit_chance / (final_ks_cd + self.settings.response_time)
            attacks_per_second['oh_killing_spree'] = 7 * self.off_hand_strike_hit_chance / (final_ks_cd + self.settings.response_time)
            attacks_per_second['main_gauche'] += attacks_per_second['mh_killing_spree'] * main_gauche_proc_rate
            
            if not (ar or sb) and self.settings.cycle.weapon_swap:
                attacks_per_second['eoh_autoattacks'] = math.floor(3. * self.attack_speed_increase / self.stats.eoh.speed) / final_ks_cd
                attacks_per_second['eoh_autoattack_hits'] = attacks_per_second['eoh_autoattacks'] * self.dw_oh_hit_chance
                attacks_per_second['mh_autoattack_hits'] *= 1. - (1. / final_ks_cd)
                attacks_per_second['oh_autoattack_hits'] *= 1. - (3.5 / final_ks_cd)
                attacks_per_second['mh_autoattacks'] *= 1. - (1. / final_ks_cd)
                attacks_per_second['oh_autoattacks'] *= 1. - (3.5 / final_ks_cd)
        
        if (ar or sb) and not self.settings.cycle.stack_cds:
            approx_time_to_empty = 100 / sinister_strike_energy_cost
            approx_time_to_empty += (energy_regen * approx_time_to_empty) / sinister_strike_energy_cost
            if approx_time_to_empty > self.combat_phase_buffer:
                self.combat_phase_buffer = approx_time_to_empty
        
        self.get_poison_counts(attacks_per_second)
        
        #print attacks_per_second
        return attacks_per_second, crit_rates
    
    def rb_actual_cds(self, attacks_per_second, base_cds, avg_rb_effect=10):
        final_cds = {}
        # If it's best to always use 5CP finishers as combat now, it should continue to be so, this is simpler and faster
        offensive_finisher_rate = attacks_per_second['eviscerate'][5]
        if 'rupture' in attacks_per_second:
            offensive_finisher_rate += attacks_per_second['rupture']
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
        if 'rupture' in attacks_per_second:
            offensive_finisher_rate += attacks_per_second['rupture']
        #should never happen, catch error just in case
        if offensive_finisher_rate != 0:
            final_cds = base_cd * (1 - avg_rb_effect / (1. / offensive_finisher_rate + avg_rb_effect))
        return final_cds
    
    def rb_cd_modifier(self, attacks_per_second, avg_rb_effect=10):
        # If it's best to always use 5CP finishers as combat now, it should continue to be so, this is simpler and faster
        offensive_finisher_rate = attacks_per_second['eviscerate'][5]
        if 'rupture' in attacks_per_second:
            offensive_finisher_rate += attacks_per_second['rupture']
        if offensive_finisher_rate != 0:
            #should never happen, catch error just in case
            return (1 - avg_rb_effect / (1. / offensive_finisher_rate + avg_rb_effect))
        else:
            return 1.
    
    def combat_attack_counts_ar(self, current_stats):
        return self.combat_attack_counts(current_stats, ar=True)

    def combat_attack_counts_sb(self, current_stats):
        return self.combat_attack_counts(current_stats, sb=True)
    
    def combat_attack_counts_both(self, current_stats):
        return self.combat_attack_counts(current_stats, ar=True, sb=True)
    
    def combat_attack_counts_none(self, current_stats):
        return self.combat_attack_counts(current_stats)

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

        self.set_constants()
        
        self.base_energy_regen = 10.
        self.max_energy = 100.
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            self.max_energy += 30
        self.shd_duration = 8
        self.shd_cd = self.get_spell_cd('shadow_dance') + self.settings.response_time + self.major_cd_delay

        cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_reduced_cost()
        if self.settings.cycle.sub_sb_timing == 'shd':
            shd_ambush_cost_modifier = self.stats.gear_buffs.rogue_t15_4pc_modifier()
            backstab_cost_mod = self.stats.gear_buffs.rogue_t15_4pc_reduced_cost((self.get_shadow_blades_duration() - self.shd_duration) / self.get_spell_cd('shadow_blades'))
        else:
            shd_ambush_cost_modifier = 1.
            backstab_cost_mod = cost_modifier / ((self.shd_cd - self.shd_duration) / self.shd_cd)
        self.base_eviscerate_cost = self.get_spell_stats('eviscerate', hit_chance=self.geometric_strike_chance, cost_mod=cost_modifier)[0]
        self.base_rupture_cost = self.get_spell_stats('rupture', hit_chance=self.geometric_strike_chance, cost_mod=cost_modifier)[0]
        self.base_hemo_cost = self.get_spell_stats('hemorrhage', hit_chance=self.geometric_strike_chance, cost_mod=cost_modifier)[0]
        self.base_st_cost = self.get_spell_stats('shuriken_toss', hit_chance=self.geometric_strike_chance, cost_mod=cost_modifier)[0]
        self.base_backstab_energy_cost = self.get_spell_stats('backstab', hit_chance=self.geometric_strike_chance, cost_mod=backstab_cost_mod)[0]
        self.sd_ambush_cost = self.get_spell_stats('ambush', hit_chance=self.strike_hit_chance, cost_mod=shd_ambush_cost_modifier)[0] - 20
        self.normal_ambush_cost = self.get_spell_stats('ambush', hit_chance=self.strike_hit_chance)[0]
            
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
                # Hemo dot and 2pc_t12 derive from physical attacks too.
                # Testing needed for physical damage procs.
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

    def subtlety_attack_counts(self, current_stats):
        attacks_per_second = {}
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
        sb_uptime = self.get_shadow_blades_uptime()
        hat_triggers_per_second = self.settings.cycle.raid_crits_per_second
        hat_cp_per_second = 1. / (2 + 1. / hat_triggers_per_second)
        er_energy = 8. / 2 #8 energy every 2 seconds
        fw_duration = 10. #17.5s
        attacks_per_second['eviscerate'] = [0,0,0,0,0,0]
        attacks_per_second['rupture_ticks'] = [0,0,0,0,0,0]
        attacks_per_second['ambush'] = self.total_openers_per_second
        attacks_per_second['backstab'] = 0
        attacks_per_second['hemorrhage'] = 0
        cp_per_ambush = 2
        cp_per_shd_ambush = cp_per_ambush
        cp_per_cpg = 1
        rupture_cd = 24
        snd_cd = 36
        shadow_blades_cd = self.get_spell_cd('shadow_blades')
        base_cp_per_second = hat_cp_per_second + self.total_openers_per_second * 2
        if self.stats.gear_buffs.rogue_t15_2pc:
            rupture_cd += 4
            snd_cd += 6
        cpg_denom = shadow_blades_cd - (shadow_blades_cd/self.shd_cd * self.shd_duration)
        cpg_denom -= (1 + 3 * self.talents.subterfuge * [1, 2][self.glyphs.vanish]) * shadow_blades_cd/self.get_spell_cd('vanish')
        if self.race.shadowmeld:
            cpg_denom -= shadow_blades_cd / (self.get_spell_cd('shadowmeld') + self.settings.response_time)
        if self.settings.cycle.sub_sb_timing == 'shd':
            cp_per_shd_ambush += 1. / 3
            cp_per_cpg += (self.get_shadow_blades_duration() - self.shd_duration) / cpg_denom
        else:
            cp_per_cpg += self.get_shadow_blades_duration() / cpg_denom
                
        #passive energy regen
        energy_regen = self.base_energy_regen * haste_multiplier + self.bonus_energy_regen + self.max_energy / self.settings.duration + er_energy
        energy_regen += self.get_bonus_energy_from_openers('ambush')
        if self.stats.gear_buffs.rogue_t16_2pc_bonus():
            energy_regen += 2 * hat_cp_per_second * self.strike_hit_chance
        
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
        shd_energy = (self.max_energy - 10) + energy_regen * self.shd_duration #lasts 8s, assume we pool to ~10 energy below max
        
        #swing timer
        attacks_per_second['mh_autoattacks'] = attack_speed_multiplier / self.stats.mh.speed
        attacks_per_second['oh_autoattacks'] = attack_speed_multiplier / self.stats.oh.speed
        #shadow blades
        attacks_per_second['mh_shadow_blade'] = attacks_per_second['mh_autoattacks'] * self.strike_hit_chance * sb_uptime
        attacks_per_second['oh_shadow_blade'] = attacks_per_second['oh_autoattacks'] * self.strike_hit_chance * sb_uptime
        attacks_per_second['mh_autoattacks'] *= (1 - sb_uptime)
        attacks_per_second['oh_autoattacks'] *= (1 - sb_uptime)
        #swing resets
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
            attacks_per_second['ambush'] += shadowmeld_ambushes
            energy_regen -= self.normal_ambush_cost * shadowmeld_ambushes
            base_cp_per_second += shadowmeld_ambushes * 2
           
        #base CPs, CPGs, and finishers 
        if self.settings.cycle.use_hemorrhage != 'always' and self.settings.cycle.use_hemorrhage != 'never':
            hemo_per_second = 1. / float(self.settings.cycle.use_hemorrhage)
            energy_regen -= hemo_per_second
            base_cp_per_second += hemo_per_second + sb_uptime
            attacks_per_second['hemorrhage'] += hemo_per_second
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
        shd_cycles_per_shd = shd_energy / shd_cycle_size # We would calculate GCD capping right after this if needed
        attacks_per_second['ambush'] += (5. / cp_per_shd_ambush) * shd_cycles_per_shd / self.shd_cd
        attacks_per_second['eviscerate'][5] += shd_cycles_per_shd / self.shd_cd
        energy_regen -= shd_energy / self.shd_cd
        #calculate percentage of ambushes with FW
        ambush_no_fw = shadowmeld_ambushes + 1. / self.shd_cd + self.total_openers_per_second
        self.ambush_no_fw_rate = ambush_no_fw / attacks_per_second['ambush']
        #calculate percentage of backstabs with FW
        self.backstab_fw_rate = fw_duration / self.shd_cd + fw_duration / self.get_spell_cd('shadowmeld') + fw_duration / self.get_spell_cd('vanish')
        self.backstab_fw_rate = self.backstab_fw_rate / ((self.shd_cd - 8.) / self.shd_cd) #accounts for the fact that backstab isn't evenly distributed
        #calculate FW uptime overall
        self.find_weakness_uptime = (fw_duration + 7.5) / self.shd_cd + fw_duration / self.get_spell_cd('shadowmeld') + fw_duration / self.get_spell_cd('vanish')
        #calculate percentage of autoattack time with FW
        if self.settings.cycle.sub_sb_timing == 'other':
            self.autoattack_fw_rate = (self.find_weakness_uptime * 180) / (180 - self.get_shadow_blades_duration())
        else:
            self.autoattack_fw_rate = (self.find_weakness_uptime * 180 - self.get_shadow_blades_duration()) / 180
        
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
            self.find_weakness_uptime += fw_duration / t16_cycle_length * ((self.shd_cd - 8.) / self.shd_cd)
        
        #Hemo ticks
        if 'hemorrhage' in attacks_per_second and self.settings.cycle.use_hemorrhage != 'never':
            if self.settings.cycle.use_hemorrhage == 'always':
                hemo_gap = 1 / attacks_per_second['hemorrhage']
            else:
                hemo_gap = float(self.settings.cycle.use_hemorrhage)
            ticks_per_second = min(1. / 3, 8. / hemo_gap)
            attacks_per_second['hemorrhage_ticks'] = ticks_per_second
        
        self.get_poison_counts(attacks_per_second)
                
        return attacks_per_second, crit_rates
