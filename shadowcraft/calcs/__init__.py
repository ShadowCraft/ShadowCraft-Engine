import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.core import exceptions
from shadowcraft.calcs import armor_mitigation
from shadowcraft.objects import class_data
from shadowcraft.objects import talents
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

    TARGET_BASE_ARMOR_VALUES = {88:11977., 93:24835., 103:100000.}
    AOE_TARGET_CAP = 20
    
    # Override this in your class specfic subclass to list appropriate stats
    # possible values are agi, str, spi, int, white_hit, spell_hit, yellow_hit,
    # haste, crit, mastery, dodge_exp, parry_exp, oh_dodge_exp, mh_dodge_exp,
    # oh_parry_exp, mh_parry_exp
    default_ep_stats = []
    # normalize_ep_stat is the stat with value 1 EP, override in your subclass
    normalize_ep_stat = None

    def __init__(self, stats, talents, glyphs, buffs, race, settings=None, level=85, target_level=None, char_class='rogue'):
        self.WOW_BUILD_TARGET = '6.0.0' # should reflect the game patch being targetted
        self.SHADOWCRAFT_BUILD = '0.09' # <1 for beta builds, 1.00 is GM, >1 for any bug fixes, reset for each warcraft patch
        self.tools = class_data.Util()
        self.stats = stats
        self.talents = talents
        self.glyphs = glyphs
        self.buffs = buffs
        self.race = race
        self.char_class = char_class
        self.settings = settings
        self.target_level = [target_level, level + 3][target_level is None] #assumes 3 levels higher if not explicit

        #racials
        if self.race.race_name == 'undead':
            self.stats.procs.set_proc('touch_of_the_grave')
        
        if self.settings.is_pvp:
            self.level_difference = 0
            self.base_one_hand_miss_rate = .00
            self.base_parry_chance = .03
            self.base_dodge_chance = .03
        else:
            self.level_difference = max(self.target_level - level, 0)
            self.base_one_hand_miss_rate = 0
            self.base_parry_chance = .01 * self.level_difference
            self.base_dodge_chance = 0
        
        self.dw_miss_penalty = .17
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
        self.armor_mitigation_parameter = armor_mitigation.parameter(self.level)
        # target level dependent constants
        try:
            self.target_base_armor = self.TARGET_BASE_ARMOR_VALUES[self.target_level]
        except KeyError as e:
            raise exceptions.InvalidInputException(_('There\'s no armor value for a target level {level}').format(level=str(e)))
        self.melee_crit_reduction = .01 * self.level_difference
        self.spell_crit_reduction = .01 * self.level_difference

    def _set_constants_for_class(self):
        # These factors are class-specific. Generaly those go in the class module,
        # unless it's basic stuff like combat ratings or base stats that we can
        # datamine for all classes/specs at once.
        if self.talents.game_class != self.glyphs.game_class:
            raise exceptions.InvalidInputException(_('You must specify the same class for your talents and glyphs'))
        self.game_class = self.talents.game_class
    
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
            haste *= self.stats.get_haste_multiplier_from_rating(self.base_stats['haste']) * self.buffs.haste_multiplier() * self.true_haste_mod
        #The 1.1307 is a value that increases the proc rate due to bad luck prevention. It /should/ be constant among all rppm proc styles
        if not proc.icd:
            if proc.max_stacks <= 1:
                proc.uptime = 1.1307 * (1 - math.e ** (-1 * haste * proc.get_rppm_proc_rate() * proc.duration / 60))
            else:
                lambd = haste * proc.get_rppm_proc_rate() * proc.duration / 60
                e_lambda = math.e ** lambd
                e_minus_lambda = math.e ** (-1 * lambd)
                proc.uptime = 1.1307 * (e_lambda - 1) * (1 - ((1 - e_minus_lambda) ** proc.max_stacks))
        else:
            mean_proc_time = 60. / (haste * proc.get_rppm_proc_rate()) + proc.icd - min(proc.icd, 10)
            proc.uptime = 1.1307 * proc.duration / mean_proc_time
    
    def set_uptime(self, proc, attacks_per_second, crit_rates):
        if proc.is_real_ppm():
            self.set_rppm_uptime(proc)
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
    
    def ep_helper(self, stat):
        setattr(self.stats, stat, getattr(self.stats, stat) + 1.)
        dps = self.get_dps()
        setattr(self.stats, stat, getattr(self.stats, stat) - 1.)
        
        return dps

    def get_ep(self, ep_stats=None, normalize_ep_stat=None, baseline_dps=None):
        if not normalize_ep_stat:
            normalize_ep_stat = self.normalize_ep_stat
        if not ep_stats:
            ep_stats = self.default_ep_stats
        ep_values = {}
        for stat in ep_stats:
            ep_values[stat] = 0
        if baseline_dps == None:
            baseline_dps = self.get_dps()
        
        if normalize_ep_stat == 'dps':
            normalize_dps_difference = 1.
        else:
            normalize_dps = self.ep_helper(normalize_ep_stat)
            normalize_dps_difference = normalize_dps - baseline_dps
        if normalize_dps_difference == 0:
            normalize_dps_difference = 1
        
        for stat in ep_values:
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
        normalize_dps = self.ep_helper(normalize_ep_stat)

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
            ep_values[i] = abs(new_dps - baseline_dps) / (normalize_dps - baseline_dps)
            setattr(self.stats.gear_buffs, i, not getattr(self.stats.gear_buffs, i))

        for i in procs_list:
            try:
                if getattr(self.stats.procs, i):
                    delattr(self.stats.procs, i)
                else:
                    self.stats.procs.set_proc(i)
                new_dps = self.get_dps()
                ep_values[i] = abs(new_dps - baseline_dps) / (normalize_dps - baseline_dps)
                if getattr(self.stats.procs, i):
                    delattr(self.stats.procs, i)
                else:
                    self.stats.procs.set_proc(i)
            except InvalidProcException:
                # Data for these procs is not complete/correct
                ep_values[i] = _('not supported')
                delattr(self.stats.procs, i)

        return ep_values
    
    def get_upgrades_ep(self, list, normalize_ep_stat=None):
        if not normalize_ep_stat:
            normalize_ep_stat = self.normalize_ep_stat
        # This method computes ep for every other buff/proc not covered by
        # get_ep or get_weapon_ep. Weapon enchants, being tied to the
        # weapons they are on, are computed by get_weapon_ep.
        
        active_procs_cache = []
        active_gear_buffs_cache = []
        procs_list = []
        gear_buffs_list = []
        ep_values = {}
        for i in list:
            if i in self.stats.procs.allowed_procs:
                procs_list.append(i)
                if getattr(self.stats.procs, i):
                    active_procs_cache.append((i, getattr(self.stats.procs, i).upgrade_level))
                    delattr(self.stats.procs, i)
            elif i in self.stats.gear_buffs.allowed_buffs:
                gear_buffs_list.append(i)
                if getattr(self.stats.gear_buffs, i):
                    active_gear_buffs_cache.append((i, self.stats.gear_buffs.activated_boosts[i]['upgrade_level']))
                    setattr(self.stats.gear_buffs, i, False)
            else:
                ep_values[i] = _('not allowed')

        baseline_dps = self.get_dps()
        normalize_dps = self.ep_helper(normalize_ep_stat)

        for i in gear_buffs_list:
            ep_values[i] = []
            if getattr(self.stats.gear_buffs, i):
                old_buff = self.stats.gear_buffs.activated_boosts[i]['upgrade_level']
                setattr(self.stats.gear_buffs, i, False)
                base_dps = self.get_dps()
                base_normalize_dps = self.ep_helper(normalize_ep_stat)
            else:
                old_buff = -1
                base_dps = baseline_dps
                base_normalize_dps = normalize_dps
            setattr(self.stats.gear_buffs, i, True)
            if 'upgradable' in self.stats.gear_buffs.activated_boosts[i] and self.stats.gear_buffs.activated_boosts[i]['upgradable'] == True and 'scaling' in self.stats.gear_buffs.activated_boosts[i]:
                if self.stats.gear_buffs.activated_boosts[i]['scaling']['quality'] == 'blue':
                    max_upgrade_level = 1
                else:
                    max_upgrade_level = 2
            else:
                max_upgrade_level = 0
            for l in xrange(max_upgrade_level+1):
                self.stats.gear_buffs.activated_boosts[i]['upgrade_level'] = l
                new_dps = self.get_dps()
                if new_dps != base_dps:
                    ep = abs(new_dps - base_dps) / (base_normalize_dps - base_dps)
                    ep_values[i].append(ep)
            if old_buff != -1:
                setattr(self.stats.gear_buffs, i, True)
                self.stats.gear_buffs.activated_boosts[i]['upgrade_level'] = old_buff
            else:
                setattr(self.stats.gear_buffs, i, False)
                self.stats.gear_buffs.activated_boosts[i]['upgrade_level'] = 0

        for i in procs_list:
            ep_values[i] = []
            try:
                if getattr(self.stats.procs, i):
                    old_proc = getattr(self.stats.procs, i)
                    delattr(self.stats.procs, i)
                    base_dps = self.get_dps()
                    base_normalize_dps = self.ep_helper(normalize_ep_stat)
                else:
                    old_proc = False
                    base_dps = baseline_dps
                    base_normalize_dps = normalize_dps
                self.stats.procs.set_proc(i)
                if getattr(self.stats.procs, i).upgradable and getattr(self.stats.procs, i).scaling:
                    if getattr(self.stats.procs, i).scaling['quality'] == 'blue':
                        max_upgrade_level = 1
                    else:
                        max_upgrade_level = 2
                else:
                    max_upgrade_level = 0
                for l in xrange(max_upgrade_level+1):
                    getattr(self.stats.procs, i).upgrade_level = l
                    new_dps = self.get_dps()
                    if new_dps != base_dps:
                        ep = abs(new_dps - base_dps) / (base_normalize_dps - base_dps)
                        ep_values[i].append(ep)
                if old_proc:
                    self.stats.procs.set_proc(i)
                    getattr(self.stats.procs, i).upgrade_level = old_proc.upgrade_level
                else:
                    delattr(self.stats.procs, i)
            except InvalidProcException:
                # Data for these procs is not complete/correct
                ep_values[i].append(_('not supported'))
                delattr(self.stats.procs, i)

        for proc in active_procs_cache:
            self.stats.procs.set_proc(proc[0])
            getattr(self.stats.procs, proc[0]).upgrade_level = proc[1]

        for gear_buff in active_gear_buffs_cache:
            setattr(self.stats.gear_buffs, gear_buff[0], True)
            self.stats.gear_buffs.activated_boosts[gear_buff[0]]['upgrade_level'] = gear_buff[1]

        return ep_values

    # this function is in comparison to get_upgrades_ep a lot faster but not 100% accurate
    # the error is around 1% which is accurate enough for the ranking in Shadowcraft-UI
    def get_upgrades_ep_fast(self, list, normalize_ep_stat=None):
        if not normalize_ep_stat:
            normalize_ep_stat = self.normalize_ep_stat
        # This method computes ep for every other buff/proc not covered by
        # get_ep or get_weapon_ep. Weapon enchants, being tied to the
        # weapons they are on, are computed by get_weapon_ep.
        
        active_procs_cache = []
        active_gear_buffs_cache = []
        procs_list = []
        gear_buffs_list = []
        ep_values = {}
        for i in list:
            if i in self.stats.procs.allowed_procs:
                procs_list.append(i)
                if getattr(self.stats.procs, i):
                    active_procs_cache.append((i, getattr(self.stats.procs, i).upgrade_level))
                    delattr(self.stats.procs, i)
            elif i in self.stats.gear_buffs.allowed_buffs:
                gear_buffs_list.append(i)
                if getattr(self.stats.gear_buffs, i):
                    active_gear_buffs_cache.append((i, self.stats.gear_buffs.activated_boosts[i]['upgrade_level']))
                    setattr(self.stats.gear_buffs, i, False)
            else:
                ep_values[i] = _('not allowed')

        baseline_dps = self.get_dps()
        normalize_dps = self.ep_helper(normalize_ep_stat)

        for i in gear_buffs_list:
            ep_values[i] = []
            if getattr(self.stats.gear_buffs, i):
                old_buff = self.stats.gear_buffs.activated_boosts[i]['upgrade_level']
                setattr(self.stats.gear_buffs, i, False)
                base_dps = self.get_dps()
                base_normalize_dps = self.ep_helper(normalize_ep_stat)
            else:
                old_buff = -1
                base_dps = baseline_dps
                base_normalize_dps = normalize_dps
            setattr(self.stats.gear_buffs, i, True)
            boost = self.stats.gear_buffs.activated_boosts[i]
            boost['upgrade_level'] = 0
            if 'upgradable' in boost and boost['upgradable'] == True and 'scaling' in boost:
                if self.stats.gear_buffs.activated_boosts[i]['scaling']['quality'] == 'blue':
                    level_steps = 8
                    max_upgrade_level = 1
                else:
                    level_steps = 4
                    max_upgrade_level = 4
                item_level = boost['scaling']['item_level']
                scale_factor = self.tools.get_random_prop_point(item_level, boost['scaling']['quality'])
            else:
                max_upgrade_level = 0
            new_dps = self.get_dps()
            for l in xrange(max_upgrade_level+1):
                if new_dps != base_dps:
                    ep = abs(new_dps - base_dps) / (base_normalize_dps - base_dps)
                    if l > 0:
                        upgraded_scale_factor = self.tools.get_random_prop_point(item_level + level_steps * l, boost['scaling']['quality'])
                        ep *= float(upgraded_scale_factor) / float(scale_factor)
                    ep_values[i].append(ep)
            if old_buff != -1:
                setattr(self.stats.gear_buffs, i, True)
            else:
                setattr(self.stats.gear_buffs, i, False)
                self.stats.gear_buffs.activated_boosts[i]['upgrade_level'] = 0

        for i in procs_list:
            ep_values[i] = []
            try:
                if getattr(self.stats.procs, i):
                    old_proc = getattr(self.stats.procs, i)
                    delattr(self.stats.procs, i)
                    base_dps = self.get_dps()
                    base_normalize_dps = self.ep_helper(normalize_ep_stat)
                else:
                    old_proc = False
                    base_dps = baseline_dps
                    base_normalize_dps = normalize_dps
                self.stats.procs.set_proc(i)
                proc = getattr(self.stats.procs, i)
                proc.upgrade_level = 0
                if proc.upgradable and proc.scaling:
                    if proc.scaling['quality'] == 'blue':
                        level_steps = 8
                        max_upgrade_level = 1
                    else:
                        level_steps = 4
                        max_upgrade_level = 4
                    item_level = proc.scaling['item_level']
                    if proc.proc_name == 'Rune of Re-Origination':
                        scale_factor = 1/(1.15**((528-item_level)/15.0)) * proc.base_ppm
                    else:
                        scale_factor = self.tools.get_random_prop_point(item_level, proc.scaling['quality'])
                else:
                    max_upgrade_level = 0
                new_dps = self.get_dps()
                for l in xrange(max_upgrade_level+1):
                    if new_dps != base_dps:
                        ep = abs(new_dps - base_dps) / (base_normalize_dps - base_dps)
                        if l > 0:
                            if proc.proc_name == 'Rune of Re-Origination':
                                 upgraded_scale_factor = 1/(1.15**((528-(item_level + level_steps * l))/15.0)) * proc.base_ppm
                            else:
                                upgraded_scale_factor = self.tools.get_random_prop_point(item_level + level_steps * l, proc.scaling['quality'])
                            ep *= float(upgraded_scale_factor) / float(scale_factor)
                        ep_values[i].append(ep)
                if old_proc:
                    self.stats.procs.set_proc(i)
                else:
                    delattr(self.stats.procs, i)
            except InvalidProcException:
                # Data for these procs is not complete/correct
                ep_values[i].append(_('not supported'))
                delattr(self.stats.procs, i)

        for proc in active_procs_cache:
            self.stats.procs.set_proc(proc[0])
            getattr(self.stats.procs, proc[0]).upgrade_level = proc[1]

        for gear_buff in active_gear_buffs_cache:
            setattr(self.stats.gear_buffs, gear_buff[0], True)
            self.stats.gear_buffs.activated_boosts[gear_buff[0]]['upgrade_level'] = gear_buff[1]

        return ep_values

    def get_glyphs_ranking(self, list=None):
        glyphs = []
        glyphs_ranking = {}
        baseline_dps = self.get_dps()

        if list == None:
            glyphs = self.glyphs.allowed_glyphs
        else:
            glyphs = list

        for i in glyphs:
            setattr(self.glyphs, i, not getattr(self.glyphs, i))
            try:
                new_dps = self.get_dps()
                if new_dps != baseline_dps:
                    glyphs_ranking[i] = abs(new_dps - baseline_dps)
            except:
                glyphs_ranking[i] = _('not implemented')
            setattr(self.glyphs, i, not getattr(self.glyphs, i))

        return glyphs_ranking

    def get_talents_ranking(self, list=None):
        talents_ranking = {}
        baseline_dps = self.get_dps()
        talent_list = []

        if list is None:
            talent_list = self.talents.get_allowed_talents_for_level()
        else:
            talent_list = list

        for talent in talent_list:
            setattr(self.talents, talent, not getattr(self.talents, talent))
            try:
                new_dps = self.get_dps()
                if new_dps != baseline_dps:
                    talents_ranking[talent] = abs(new_dps - baseline_dps)
            except:
                talents_ranking[talent] = _('not implemented')
            setattr(self.talents, talent, not getattr(self.talents, talent))
        
        return talents_ranking

    def get_dps(self):
        # Overwrite this function with your calculations/simulations/whatever;
        # this is what callers will (initially) be looking at.
        pass

    def get_all_activated_stat_boosts(self):
        racial_boosts = self.race.get_racial_stat_boosts()
        gear_boosts = self.stats.gear_buffs.get_all_activated_boosts()
        return racial_boosts + gear_boosts

    def armor_mitigation_multiplier(self, armor):
        return armor_mitigation.multiplier(armor, cached_parameter=self.armor_mitigation_parameter)

    def armor_mitigate(self, damage, armor):
        # Pass in raw physical damage and armor value, get armor-mitigated
        # damage value.
        return damage * self.armor_mitigation_multiplier(armor)

    def melee_hit_chance(self, base_miss_chance, dodgeable, parryable, weapon_type, blockable=False, bonus_hit=0):
        miss_chance = base_miss_chance

        # Expertise represented as the reduced chance to be dodged, not true "Expertise".

        if dodgeable:
            dodge_chance = self.base_dodge_chance
        else:
            dodge_chance = 0

        if parryable:
            # Expertise will negate dodge and spell miss, *then* parry
            parry_expertise = max(expertise - self.base_dodge_chance, 0)
            parry_chance = max(self.base_parry_chance - parry_expertise, 0)
        else:
            parry_chance = 0

        block_chance = self.base_block_chance * blockable

        return (1 - (miss_chance + dodge_chance + parry_chance)) * (1 - block_chance)

    def melee_spells_hit_chance(self, bonus_hit=0):
        hit_chance = self.melee_hit_chance(self.base_one_hand_miss_rate, dodgeable=False, parryable=False, weapon_type=None)
        return hit_chance

    def one_hand_melee_hit_chance(self, dodgeable=False, parryable=False, weapon=None, bonus_hit=0):
        # Most attacks by DPS aren't parryable due to positional negation. But
        # if you ever want to attacking from the front, you can just set that
        # to True.
        if weapon == None:
            weapon = self.stats.mh
        hit_chance = self.melee_hit_chance(self.base_one_hand_miss_rate, dodgeable, parryable, weapon.type)
        return hit_chance

    def off_hand_melee_hit_chance(self, dodgeable=False, parryable=False, weapon=None, bonus_hit=0):
        # Most attacks by DPS aren't parryable due to positional negation. But
        # if you ever want to attacking from the front, you can just set that
        # to True.
        if weapon == None:
            weapon = self.stats.oh
        hit_chance = self.melee_hit_chance(self.base_one_hand_miss_rate, dodgeable, parryable, weapon.type)
        return hit_chance

    def dual_wield_mh_hit_chance(self, dodgeable=False, parryable=False, dw_miss=None):
        # Most attacks by DPS aren't parryable due to positional negation. But
        # if you ever want to attacking from the front, you can just set that
        # to True.
        hit_chance = self.dual_wield_hit_chance(dodgeable, parryable, self.stats.mh.type, dw_miss=dw_miss)
        return hit_chance

    def dual_wield_oh_hit_chance(self, dodgeable=False, parryable=False, dw_miss=None):
        # Most attacks by DPS aren't parryable due to positional negation. But
        # if you ever want to attacking from the front, you can just set that
        # to True.
        hit_chance = self.dual_wield_hit_chance(dodgeable, parryable, self.stats.oh.type, dw_miss=dw_miss)
        return hit_chance

    def dual_wield_hit_chance(self, dodgeable, parryable, weapon_type, dw_miss=None):
        if not dw_miss:
            dw_miss = self.base_dw_miss_rate
        hit_chance = self.melee_hit_chance(dw_miss, dodgeable, parryable, weapon_type)
        return hit_chance

    def buff_melee_crit(self):
        return self.buffs.buff_all_crit()

    def buff_spell_crit(self):
        return self.buffs.buff_spell_crit() + self.buffs.buff_all_crit()

    def crit_damage_modifiers(self, crit_damage_bonus_modifier=1):
        # The obscure formulae for the different crit enhancers can be found here
        # http://elitistjerks.com/f31/t13300-shaman_relentless_earthstorm_ele/#post404567
        base_modifier = 2
        if self.settings.is_pvp:
            base_modifier = 1.5
        crit_damage_modifier = self.stats.gear_buffs.metagem_crit_multiplier()
        if self.race.might_of_the_mountain:
            crit_damage_modifier *= 1.02 #2x base becomes 2.04x with MotM
        total_modifier = 1 + (base_modifier * crit_damage_modifier - 1) * crit_damage_bonus_modifier
        return total_modifier

    def target_armor(self, armor=None):
        # Passes base armor reduced by armor debuffs or overridden armor
        if armor is None:
            armor = self.target_base_armor
        return self.buffs.armor_reduction_multiplier() * armor

    def raid_settings_modifiers(self, attack_kind, armor=None, affect_resil=True):
        # This function wraps spell, bleed and physical debuffs from raid
        # along with all-damage buff and armor reduction. It should be called
        # from every damage dealing formula. Armor can be overridden if needed.
        pvp_mod = 1.
        if self.settings.is_pvp and affect_resil:
            power = self.stats.get_pvp_power_multiplier_from_rating()
            resil = self.stats.get_pvp_resil_multiplier_from_rating()
            pvp_mod = power*(1.0 - resil)
            armor = self.stats.pvp_target_armor
        if attack_kind not in ('physical', 'spell', 'bleed'):
            raise exceptions.InvalidInputException(_('Attacks must be categorized as physical, spell or bleed'))
        elif attack_kind == 'spell':
            return self.buffs.spell_damage_multiplier() * pvp_mod
        elif attack_kind == 'bleed':
            return self.buffs.bleed_damage_multiplier() * pvp_mod
        elif attack_kind == 'physical':
            armor_override = self.target_armor(armor)
            return self.buffs.physical_damage_multiplier() * self.armor_mitigation_multiplier(armor_override) * pvp_mod
