from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import zip
from builtins import str
from builtins import object
import gettext
import builtins
import math
import os
import subprocess

_ = gettext.gettext

from shadowcraft.core import exceptions
from shadowcraft.objects import class_data
from shadowcraft.objects import talents
from shadowcraft.objects import artifact
from shadowcraft.objects import procs
from shadowcraft.objects.procs import InvalidProcException

class DamageCalculator(object):
    # This method holds the general interface for a damage calculator - the
    # sorts of parameters and calculated values that will be need by many (or
    # most) classes if they implement a damage calculator using this framework.
    # Not saying that will happen, but I want to leave my options open.
    # Any calculations that are specific to a particular class should go in
    # calcs.<class>.<Class>DamageCalculator instead - for an example, see
    # calcs.rogue.RogueDamageCalculator

    # Override this in your class specfic subclass to list appropriate stats
    # possible values are agi, str, spi, int, haste, crit, mastery
    default_ep_stats = []
    # normalize_ep_stat is the stat with value 1 EP, override in your subclass
    normalize_ep_stat = None

    def __init__(self, stats, talents, traits, buffs, race, spec, settings=None, level=110, target_level=None, char_class='rogue'):
        self.WOW_BUILD_TARGET = '7.3.0' # should reflect the game patch being targetted
        self.SHADOWCRAFT_BUILD = self.get_version_string()
        self.tools = class_data.Util()
        self.stats = stats
        self.talents = talents
        self.traits = traits
        self.buffs = buffs
        self.race = race
        self.char_class = char_class
        self.spec = spec
        self.settings = settings
        self.target_level = target_level if target_level else level+3 #assumes 3 levels higher if not explicit

        #racials
        if self.race.race_name == 'undead':
            self.stats.procs.set_proc('touch_of_the_grave')
        if self.race.race_name == 'goblin':
            self.stats.procs.set_proc('rocket_barrage')

        self.level_difference = max(self.target_level - level, 0)
        self.base_one_hand_miss_rate = 0
        self.base_parry_chance = .01 * self.level_difference
        self.base_dodge_chance = 0

        self.dw_miss_penalty = .19
        self._set_constants_for_class()
        self.level = level

        self.recalculate_hit_constants()
        self.base_block_chance = .03 + .015 * self.level_difference

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'level':
            self._set_constants_for_level()

    def __getattr__(self, name):
        # Any status we haven't assigned a value to, we don't have.
        if name == 'calculating_ep':
            return False
        object.__getattribute__(self, name)

    def _set_constants_for_level(self):
        self.buffs.level = self.level
        self.stats.level = self.level
        self.race.level = self.level
        self.stats.gear_buffs.level = self.level
        # calculate and cache the level-dependent armor mitigation parameter
        self.attacker_k_value = self.tools.get_k_value(self.level)
        # target level dependent constants
        self.target_base_armor = self.tools.get_base_armor(self.target_level)

        #Crit suppression removed in Legion
        #Source: http://blue.mmo-champion.com/topic/409203-theorycrafting-questions/#post274
        self.crit_reduction = 0

    def _set_constants_for_class(self):
        # These factors are class-specific. Generaly those go in the class module,
        # unless it's basic stuff like combat ratings or base stats that we can
        # datamine for all classes/specs at once.
        self.game_class = self.talents.game_class

    def get_version_string(self):
        try:
            thisdir = os.path.dirname(os.path.abspath(__file__))
            build = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], cwd=thisdir).strip()
            commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=thisdir).strip()
            if build.isdigit() and commit:
                return '{0} ({1})'.format(build, commit)
        except:
            pass
        return 'UNKNOWN'

    def recalculate_hit_constants(self):
        self.base_dw_miss_rate = self.base_one_hand_miss_rate + self.dw_miss_penalty

    def get_adv_param(self, type, default_val, min_bound=-10000, max_bound=10000, ignore_bounds=False):
        if type in self.settings.adv_params and not ignore_bounds:
            return max(   min(float(self.settings.adv_params[type]), max_bound), min_bound   )
        elif type in self.settings.adv_params:
            return self.settings.adv_params[type]
        else:
            return default_val
        raise exceptions.InvalidInputException(_('Improperly defined parameter type: '+type))

    def add_exported_data(self, damage_breakdown):
        #used explicitly to highjack data outputs to export additional data.
        if self.get_version_number:
            damage_breakdown['version_' + self.WOW_BUILD_TARGET + '_' + self.SHADOWCRAFT_BUILD] = [.0, 0]

    def set_rppm_uptime(self, proc):
        #http://iam.yellingontheinternet.com/2013/04/12/theorycraft-201-advanced-rppm/
        haste = 1.
        if proc.haste_scales:
            haste *= self.stats.get_haste_multiplier_from_rating(self.base_stats['haste'] * self.stat_multipliers['haste']) * self.true_haste_mod
        if proc.att_spd_scales:
            haste *= 1.4
        #The 1.1307 is a value that increases the proc rate due to bad luck prevention. It /should/ be constant among all rppm proc styles
        if not proc.icd:
            if proc.max_stacks <= 1:
                proc.uptime = 1.1307 * (1 - math.e ** (-1 * haste * proc.get_rppm_proc_rate(spec=self.spec) * proc.duration / 60))
            else:
                lambd = haste * proc.get_rppm_proc_rate(spec=self.spec) * proc.duration / 60
                e_lambda = math.e ** lambd
                e_minus_lambda = math.e ** (-1 * lambd)
                proc.uptime = 1.1307 * (e_lambda - 1) * (1 - ((1 - e_minus_lambda) ** proc.max_stacks))
        else:
            mean_proc_time = 60 / (haste * proc.get_rppm_proc_rate(spec=self.spec)) + proc.icd - min(proc.icd, 10)
            proc.uptime = 1.1307 * proc.duration / mean_proc_time

    def set_uptime(self, proc, attacks_per_second, crit_rates):
        if proc.is_real_ppm():
            self.set_rppm_uptime(proc)
        else:
            procs_per_second = self.get_procs_per_second(proc, attacks_per_second, crit_rates)

            if proc.icd:
                proc.uptime = proc.duration / (proc.icd + 1 / procs_per_second)
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

    def average_damage_breakdowns(self, aps_dict, denom=180):
        final_breakdown = {}
        #key: phase name
        #number: place in tuple... tuple = (phase_length, dps_breakdown)
        #entry: DPS skill_name
        #denom: total duration (to divide phase duration by it)
        for key in aps_dict:
            for entry in aps_dict[key][1]:
                if entry in final_breakdown:
                    final_breakdown[entry] += aps_dict[key][1][entry] * (aps_dict[key][0] / denom)
                else:
                    final_breakdown[entry] = aps_dict[key][1][entry] * (aps_dict[key][0] / denom)
        return final_breakdown

    def ep_helper(self, stat):
        setattr(self.stats, stat, getattr(self.stats, stat) + 1.)
        dps = self.get_dps()
        setattr(self.stats, stat, getattr(self.stats, stat) - 1.)
        return dps

    def get_ep(self, ep_stats=None, normalize_ep_stat=None, baseline_dps=None):
        if not normalize_ep_stat:
            normalize_ep_stat = self.get_adv_param('normalize_stat', self.settings.default_ep_stat, ignore_bounds=True)
        if not ep_stats:
            ep_stats = self.default_ep_stats

        if baseline_dps == None:
            baseline_dps = self.get_dps()

        if normalize_ep_stat == 'dps':
            normalize_dps_difference = 1.
        else:
            normalize_dps = self.ep_helper(normalize_ep_stat)
            normalize_dps_difference = normalize_dps - baseline_dps
        if normalize_dps_difference == 0:
            normalize_dps_difference = 1

        ep_values = {}
        for stat in ep_stats:
            ep_values[stat] = 1.0
            if normalize_ep_stat != stat:
                dps = self.ep_helper(stat)
                ep_values[stat] = abs(dps - baseline_dps) / normalize_dps_difference

        return ep_values

    def get_weapon_ep(self, speed_list=None, dps=False, enchants=False, normalize_ep_stat=None):
        if not normalize_ep_stat:
            normalize_ep_stat = self.normalize_ep_stat
        weapons = ('mh', 'oh')
        if speed_list is not None or dps:
            baseline_dps = self.get_dps()
            normalize_dps = self.ep_helper(normalize_ep_stat)

        for hand in weapons:
            ep_values = {}

            # Weapon dps EP
            if dps:
                getattr(self.stats, hand).weapon_dps += 1.
                new_dps = self.get_dps()
                ep = abs(new_dps - baseline_dps) / (normalize_dps - baseline_dps)
                ep_values[hand + '_dps'] = ep
                getattr(self.stats, hand).weapon_dps -= 1.

            # Enchant EP
            if enchants:
                old_enchant = None
                for enchant in getattr(self.stats, hand).allowed_melee_enchants:
                    if getattr(getattr(self.stats, hand), enchant):
                        old_enchant = enchant
                getattr(self.stats, hand).del_enchant()
                no_enchant_dps = self.get_dps()
                no_enchant_normalize_dps = self.ep_helper(normalize_ep_stat)
                for enchant in getattr(self.stats, hand).allowed_melee_enchants:
                    getattr(self.stats, hand).set_enchant(enchant)
                    new_dps = self.get_dps()
                    if new_dps != no_enchant_dps:
                        ep = abs(new_dps - no_enchant_dps) / (no_enchant_normalize_dps - no_enchant_dps)
                        ep_values[hand + '_' + enchant] = ep
                    getattr(self.stats, hand).set_enchant(old_enchant)

            # Weapon speed EP
            if speed_list is not None:
                old_speed = getattr(self.stats, hand).speed
                for speed in speed_list:
                    getattr(self.stats, hand).speed = speed
                    new_dps = self.get_dps()
                    ep = (new_dps - baseline_dps) / (normalize_dps - baseline_dps)
                    ep_values[hand + '_' + str(speed)] = ep
                    getattr(self.stats, hand).speed = old_speed

            if hand == 'mh':
                mh_ep_values = ep_values
            elif hand == 'oh':
                oh_ep_values = ep_values

        return mh_ep_values, oh_ep_values

    def get_weapon_type_ep(self, normalize_ep_stat=None):
        if not normalize_ep_stat:
            normalize_ep_stat = self.normalize_ep_stat
        weapons = ('mh', 'oh')

        baseline_dps = self.get_dps()
        normalize_dps = self.ep_helper(normalize_ep_stat)

        mh_ep_values = {}
        oh_ep_values = {}
        for hand in weapons:
            ep_values = {}

            old_type = getattr(self.stats, hand).type
            for wtype in ('dagger', 'one-hander'):
                getattr(self.stats, hand).type = wtype
                new_dps = self.get_dps()
                ep = (new_dps - baseline_dps) / (normalize_dps - baseline_dps)
                ep_values[hand + '_type_' + wtype] = ep
            getattr(self.stats, hand).type = old_type

            if hand == 'mh':
                mh_ep_values = ep_values
            elif hand == 'oh':
                oh_ep_values = ep_values

        return mh_ep_values, oh_ep_values

    def get_weapon_type_modifier_helper(self, setups=None):
        # Use this method if you want to test different weapon setups. It will
        # return one value per setup including the current one. It takes setups
        # like this one:
        # (
        #     {'hand':'mh', 'type':mh_type, 'speed':mh_speed},
        #     {'hand':'oh', 'type':oh_type, 'speed':oh_speed}
        # )
        modifiers = {}
        weapons = ('mh', 'oh')
        baseline_setup = []
        for hand in weapons:
            weapon = getattr(self.stats, hand)
            baseline_setup.append((hand, weapon.speed, weapon.type))
        modifiers[tuple(baseline_setup)] = 1

        if not setups:
            return modifiers

        baseline_dps = self.get_dps()
        for setup in setups:
            current_setup = []
            assert len(setup) == 2
            for hand in setup:
                if hand is not None:
                    weapon = getattr(self.stats, hand['hand'])
                    weapon.speed = hand['speed']
                    weapon.type = hand['type']
                    current_setup.append((hand['hand'], hand['speed'], hand['type']))
            try:
                new_dps = self.get_dps()
                if new_dps != baseline_dps:
                    modifiers[tuple(current_setup)] = new_dps / baseline_dps
            except InputNotModeledException:
                modifiers[tuple(current_setup)] = _('not allowed')
            for hand in baseline_setup:
                hand_name, speed, type = hand
                weapon = getattr(self.stats, hand_name)
                weapon.speed = speed
                weapon.type = type

        return modifiers

    def get_oh_weapon_modifier(self, setups, format=True):
        # Override this in your modeler to pass default oh weapons to test.
        modifiers = self.get_weapon_type_modifier_helper(setups)
        if not format:
            return modifiers
        formatted_mods = {}
        for setup in modifiers:
            for hand in setup:
                if hand[0] == 'mh':
                    continue
                formatted_mods['_'.join((hand[0], str(hand[1]), hand[2]))] = modifiers[setup]
        return formatted_mods

    def get_dw_weapon_modifier(self, setups, format=True):
        # Override this in your modeler to pass default dw setups to test.
        modifiers = self.get_weapon_type_modifier_helper(setups)
        pass

    def get_2h_weapon_modifier(self, setups, format=True):
        # Override this in your modeler to pass default 2h setups to test.
        modifiers = self.get_weapon_type_modifier_helper(setups)
        pass

    def get_other_ep(self, list, normalize_ep_stat=None):
        if not normalize_ep_stat:
            normalize_ep_stat = self.normalize_ep_stat
        # This method computes ep for every other buff/proc not covered by
        # get_ep or get_weapon_ep. Weapon enchants, being tied to the
        # weapons they are on, are computed by get_weapon_ep.
        ep_values = {}
        baseline_dps = self.get_dps()
        if normalize_ep_stat == 'dps':
            normalize_dps_difference = 1.
        else:
            normalize_dps = self.ep_helper(normalize_ep_stat)
            normalize_dps_difference = normalize_dps - baseline_dps

        procs_list = []
        gear_buffs_list = []
        for i in list:
            if i in self.stats.procs.allowed_procs:
                procs_list.append(i)
            elif i in self.stats.gear_buffs.allowed_buffs:
                gear_buffs_list.append(i)
            else:
                ep_values[i] = _('not allowed')

        for i in gear_buffs_list:
            # Note that activated abilites like trinkets, potions, or
            # engineering gizmos are handled as gear buffs by the engine.
            setattr(self.stats.gear_buffs, i, not getattr(self.stats.gear_buffs, i))
            new_dps = self.get_dps()
            ep_values[i] = abs(new_dps - baseline_dps) / (normalize_dps_difference)
            setattr(self.stats.gear_buffs, i, not getattr(self.stats.gear_buffs, i))

        for i in procs_list:
            try:
                if getattr(self.stats.procs, i):
                    delattr(self.stats.procs, i)
                else:
                    self.stats.procs.set_proc(i)
                new_dps = self.get_dps()
                ep_values[i] = abs(new_dps - baseline_dps) / (normalize_dps_difference)
                if getattr(self.stats.procs, i):
                    delattr(self.stats.procs, i)
                else:
                    self.stats.procs.set_proc(i)
            except InvalidProcException:
                # Data for these procs is not complete/correct
                ep_values[i] = _('not supported')
                delattr(self.stats.procs, i)

        return ep_values

    def get_upgrades_ep(self, _list, normalize_ep_stat=None):
        if not normalize_ep_stat:
            normalize_ep_stat = self.normalize_ep_stat
        # This method computes ep for every other buff/proc not covered by
        # get_ep or get_weapon_ep. Weapon enchants, being tied to the
        # weapons they are on, are computed by get_weapon_ep.

        active_procs_cache = []
        procs_list = []
        ep_values = {}
        for i in _list:
            if i in self.stats.procs.allowed_procs:
                procs_list.append( (i, _list[i]) )
                if getattr(self.stats.procs, i):
                    active_procs_cache.append((i, getattr(self.stats.procs, i).item_level))
                    delattr(self.stats.procs, i)
            else:
                ep_values[i] = _('not allowed')

        baseline_dps = self.get_dps()
        normalize_dps = self.ep_helper(normalize_ep_stat)
        for i in procs_list:
            proc_name, item_levels = i
            ep_values[proc_name] = {}
            try:
                if getattr(self.stats.procs, proc_name):
                    old_proc = getattr(self.stats.procs, proc_name)
                    delattr(self.stats.procs, proc_name)
                    base_dps = self.get_dps()
                    base_normalize_dps = self.ep_helper(normalize_ep_stat)
                else:
                    old_proc = False
                    base_dps = baseline_dps
                    base_normalize_dps = normalize_dps
                self.stats.procs.set_proc(proc_name)
                proc = getattr(self.stats.procs, proc_name)
                for group in item_levels:
                    if not isinstance(group, (list,tuple)):
                        group = group,
                    for l in group:
                        proc.item_level = l
                        proc.update_proc_value() # after setting item_level re-set the proc value
                        new_dps = self.get_dps()
                        if new_dps != base_dps:
                            ep = abs(new_dps - base_dps) / (base_normalize_dps - base_dps)
                            ep_values[proc_name][l] = ep
                if old_proc:
                    self.stats.procs.set_proc(proc_name)
                else:
                    delattr(self.stats.procs, proc_name)
            except InvalidProcException:
                # Data for these procs is not complete/correct
                ep_values[i].append(_('not supported'))
                delattr(self.stats.procs, proc_name)

        for proc in active_procs_cache:
            self.stats.procs.set_proc(proc[0])
            getattr(self.stats.procs, proc[0]).item_level = proc[1]

        return ep_values

    # this function is in comparison to get_upgrades_ep a lot faster but not 100% accurate
    # the error is around 1% which is accurate enough for the ranking in Shadowcraft-UI
    def get_upgrades_ep_fast(self, _list, normalize_ep_stat=None, exclude_list=None):
        if not normalize_ep_stat:
            normalize_ep_stat = self.normalize_ep_stat
        # This method computes ep for every other buff/proc not covered by
        # get_ep or get_weapon_ep. Weapon enchants, being tied to the
        # weapons they are on, are computed by get_weapon_ep.

        active_procs_cache = [] #procs removed by ranker, all procs if no exclude_list provided
        procs_list = [] #holds all procs to consider
        ep_values = {}
        for i in _list:

            if i in self.stats.procs.allowed_procs:
                procs_list.append( (i, _list[i]) )
                #if an excludelist is provided only add values on exclude_list to active_proc_cache
                #if no exclude_list add all procs to active_proc_cache
                if (exclude_list and i in exclude_list) or (not exclude_list and getattr(self.stats.procs, i)):
                    active_procs_cache.append((i, getattr(self.stats.procs, i).item_level))
                    delattr(self.stats.procs, i)
            else:
                ep_values[i] = _('not allowed')

        baseline_dps = self.get_dps()
        normalize_dps = self.ep_helper(normalize_ep_stat)

        for i in procs_list:
            proc_name, item_levels = i
            ep_values[proc_name] = {}
            try:
                if getattr(self.stats.procs, proc_name):
                    old_proc = getattr(self.stats.procs, proc_name)
                    delattr(self.stats.procs, proc_name)
                    base_dps = self.get_dps()
                    base_normalize_dps = self.ep_helper(normalize_ep_stat)
                else:
                    old_proc = False
                    base_dps = baseline_dps
                    base_normalize_dps = normalize_dps
                self.stats.procs.set_proc(proc_name)
                proc = getattr(self.stats.procs, proc_name)
                for group in item_levels:
                    if not isinstance(group, (list,tuple)):
                        group = group,
                    if proc.scaling:
                        proc.item_level = group[0]
                        proc.update_proc_value() # after setting item_level re-set the proc value
                        item_level = proc.item_level
                        scale_factor = self.tools.get_random_prop_point(item_level)
                    new_dps = self.get_dps()
                    if new_dps != base_dps:
                        for l in group:
                            ep = abs(new_dps - base_dps) / (base_normalize_dps - base_dps)
                            if l > proc.item_level:
                                upgraded_scale_factor = self.tools.get_random_prop_point(l)
                                ep *= upgraded_scale_factor / scale_factor
                            ep_values[proc_name][l] = ep
                if old_proc:
                    self.stats.procs.set_proc(proc_name)
                else:
                    delattr(self.stats.procs, proc_name)
            except InvalidProcException:
                # Data for these procs is not complete/correct
                ep_values[i].append(_('not supported'))
                delattr(self.stats.procs, i)

        for proc in active_procs_cache:
            self.stats.procs.set_proc(proc[0])
            getattr(self.stats.procs, proc[0]).item_level = proc[1]

        return ep_values

    def get_talents_ranking(self, list=None):
        talents_ranking = {}
        existing_talents = self.talents.get_talent_string()

        tier_levels = [15, 30, 45, 60, 75, 90, 100] #list of levels for our tiers, because it is not in the talent data
        allowed_talent_list = self.talents.get_allowed_talents_for_level() if list == None else list #cache

        for tier, level in zip(self.talents.class_talents, tier_levels):
            tier_ranking = {} #reinitialized to clear dict for each new tier
            self.talents.initialize_talents(existing_talents)
            self.talents.set_talent(tier[0], False) # Wipes the row
            baseline_dps = self.get_dps()
            for talent in tier:
                if talent in allowed_talent_list:
                    try:
                        self.talents.set_talent(talent, True)
                        new_dps = self.get_dps()
                        if new_dps != baseline_dps:
                            tier_ranking[talent] = abs(new_dps - baseline_dps)
                        else:
                            tier_ranking[talent] = 'not implemented' #unique error: no dps delta for this talent
                    except:
                        tier_ranking[talent] = 'implementation error' #unique error: error attempting to calc dps with this talent
            talents_ranking[level] = tier_ranking #place each tier into the talent tree
        self.talents.initialize_talents(existing_talents)
        return talents_ranking

    def get_trait_ranking(self, list=None):
        trait_ranking = {}
        baseline_dps = self.get_dps()
        trait_list = []

        if not list:
            trait_list = self.traits.get_trait_list()
        else:
            trait_list = list

        single_rank = self.traits.get_single_rank_trait_list()

        for trait in trait_list:
            base_trait_rank = getattr(self.traits, trait)
            if trait in single_rank and base_trait_rank:
                setattr(self.traits, trait, 0)
            else:
                setattr(self.traits, trait, base_trait_rank+1)
            try:
                new_dps = self.get_dps()
                if new_dps != baseline_dps:
                    trait_ranking[trait] = abs(new_dps-baseline_dps)
            except:
                trait_ranking[trait] = _('not_implemented')
            setattr(self.traits, trait, base_trait_rank)
        return trait_ranking

    def get_engine_info(self):
        data = {
            'wow_build_target': self.WOW_BUILD_TARGET,
            'shadowcraft_build': self.SHADOWCRAFT_BUILD
        }
        return data

    def get_dps(self):
        # Overwrite this function with your calculations/simulations/whatever;
        # this is what callers will (initially) be looking at.
        pass

    def armor_mitigation_multiplier(self, armor=None):
        if not armor:
            armor = self.target_base_armor
        return self.attacker_k_value / (self.attacker_k_value + armor)

    def armor_mitigate(self, damage, armor):
        # Pass in raw physical damage and armor value, get armor-mitigated
        # damage value.
        return damage * self.armor_mitigation_multiplier(armor)

    def melee_hit_chance(self, base_miss_chance, dodgeable, parryable, blockable=False):
        miss_chance = base_miss_chance

        if dodgeable:
            dodge_chance = self.base_dodge_chance
        else:
            dodge_chance = 0

        if parryable:
            parry_chance = self.base_parry_chance
        else:
            parry_chance = 0

        if blockable:
            block_chance = self.base_block_chance
        else:
            block_chance = 0

        return (1 - (miss_chance + dodge_chance + parry_chance)) * (1 - block_chance)

    def melee_spells_hit_chance(self, bonus_hit=0):
        hit_chance = self.melee_hit_chance(self.base_one_hand_miss_rate, dodgeable=False, parryable=False)
        return hit_chance

    def one_hand_melee_hit_chance(self, dodgeable=False, parryable=False, blockable=False):
        # Most attacks by DPS aren't parryable due to positional negation. But
        # if you ever want to attacking from the front, you can just set that
        # to True.
        hit_chance = self.melee_hit_chance(self.base_one_hand_miss_rate, dodgeable, parryable, blockable)
        return hit_chance

    def off_hand_melee_hit_chance(self, dodgeable=False, parryable=False, bonus_hit=0):
        # Most attacks by DPS aren't parryable due to positional negation. But
        # if you ever want to attacking from the front, you can just set that
        # to True.
        hit_chance = self.melee_hit_chance(self.base_one_hand_miss_rate, dodgeable, parryable)
        return hit_chance

    def dual_wield_mh_hit_chance(self, dodgeable=False, parryable=False, dw_miss=None):
        # Most attacks by DPS aren't parryable due to positional negation. But
        # if you ever want to attacking from the front, you can just set that
        # to True.
        hit_chance = self.dual_wield_hit_chance(dodgeable, parryable, dw_miss=dw_miss)
        return hit_chance

    def dual_wield_oh_hit_chance(self, dodgeable=False, parryable=False, dw_miss=None):
        # Most attacks by DPS aren't parryable due to positional negation. But
        # if you ever want to attacking from the front, you can just set that
        # to True.
        hit_chance = self.dual_wield_hit_chance(dodgeable, parryable, dw_miss=dw_miss)
        return hit_chance

    def dual_wield_hit_chance(self, dodgeable, parryable, dw_miss=None):
        if not dw_miss:
            dw_miss = self.base_dw_miss_rate
        hit_chance = self.melee_hit_chance(dw_miss, dodgeable, parryable)
        return hit_chance

    def buff_melee_crit(self):
        return self.buffs.buff_all_crit()

    def crit_damage_modifiers(self, crit_damage_bonus_modifier=1):
        # The obscure formulae for the different crit enhancers can be found here
        # http://elitistjerks.com/f31/t13300-shaman_relentless_earthstorm_ele/#post404567
        base_modifier = 2
        crit_damage_modifier = self.stats.gear_buffs.metagem_crit_multiplier()
        if self.race.might_of_the_mountain:
            crit_damage_modifier *= 1.02 #2x base becomes 2.04x with MotM
        total_modifier = 1 + (base_modifier * crit_damage_modifier - 1) * crit_damage_bonus_modifier
        return total_modifier

    def target_armor(self, armor=None):
        # Passes base armor reduced by armor debuffs or overridden armor
        if armor is None:
            armor = self.target_base_armor
        return armor #* self.buffs.armor_reduction_multiplier()
