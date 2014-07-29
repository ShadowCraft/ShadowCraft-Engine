import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.core import exceptions
from shadowcraft.calcs import armor_mitigation
from shadowcraft.objects import class_data
from shadowcraft.objects.procs import InvalidProcException

class InputNotModeledException(exceptions.InvalidInputException):
    pass

class DarkmantleCalculator(object):

    def __init__(self, stats, talents, glyphs, buffs, race, settings=None, level=100, target_level=103, char_class='rogue'):
        #load stats, class, procs, etc to main content
        self.tools = class_data.Util()
        self.stats = stats
        self.talents = talents
        self.glyphs = glyphs
        self.buffs = buffs
        self.race = race
        self.char_class = char_class
        self.settings = settings
        self.target_level = target_level
        self.level = level
        
        self.buffs.level = self.level
        self.stats.level = self.level
        self.race.level = self.level
        self.stats.gear_buffs.level = self.level
        # calculate and cache the level-dependent armor mitigation parameter
        self.armor_mitigation_parameter = armor_mitigation.parameter(self.level)
        
        #setup global variables, these get deep-copy and passed to new objects
        self.state_values = {}
        self.state_values['damage_multiplier'] = 1.0
        self.state_values['gcd_size'] = 1.0
        self.state_values['trinket_1'] = {'name':'null', 'last_proc_time': -600}
        self.state_values['trinket_2'] = {'name':'null', 'last_proc_time': -600}
        self.state_values['weapon_proc_1'] = {'name':'null', 'last_proc_time': -600}
        self.state_values['weapon_proc_2'] = {'name':'null', 'last_proc_time': -600}
        self.state_values['cooldown'] = {}
        self.state_values['stat_multipliers'] = {
            'primary':self.stats.gear_buffs.gear_specialization_multiplier(), #armor specialization
            'ap':self.buffs.attack_power_multiplier(),
            'haste':1.0,
            'crit':1.0,
            'mastery':1.0,
            'versatility':1.0,
            'readiness':1.0,
            'multistrike':1.0,
        }
        self.state_values['current_stats'] = {
            'str': (self.stats.str), #useless for rogues now
            'agi': (self.stats.agi + self.race.racial_agi), #+ self.buffs.buff_agi()
            'int': (self.stats.int), #useless for rogues now
            'ap': (self.stats.ap),
            'crit': (self.stats.crit),
            'haste': (self.stats.haste),
            'mastery': (self.stats.mastery), # + self.buffs.buff_mast()
            'readiness': (self.stats.readiness),
            'multistrike': (self.stats.multistrike),
            'versatility': (self.stats.versatility),
        }
        self.calculate_effective_ap()

        self.state_values['auras'] = [] #handles permanent and temporary
        for e in self.buffs.buffs_debuffs:
            self.state_values['auras'].append((e, 'inf')) # ('name', time), time = 'inf' or number
            
        #change stats to match buffs
        
        #combat tables
        self.base_one_hand_miss_rate = 0
        self.base_parry_chance = .03
        self.base_dodge_chance = 0
        self.base_spell_miss_rate = 0
        self.base_dw_miss_rate = .17
        self.base_block_chance = .075
        self.crit_reduction = .01 * (self.target_level - self.level)
        
        #load class module data
        class_variables = self._get_values_for_class()
        for key in class_variables:
            self.state_values[key] = class_variables[key]
            
    def calculate_effective_ap(self):
        self.state_values['effective_ap'] = (self.state_values['current_stats']['agi'] * self.state_values['stat_multipliers']['primary'] + self.stats.ap)
        self.state_values['effective_ap'] *= self.state_values['stat_multipliers']['ap']
        
    def end_calc_branch(self, current_time, total_damage_done):
        if self.settings.style == 'time' and current_time >= self.settings.limit:
            print 'Stopping calculations at: ', current_time, ' seconds'
            print '--------'
            return True
        if self.settings.style == 'health' and total_damage_done >= self.settings.limit:
            print 'Stopping calculations at: ', total_damage_done, ' damage'
            print '--------'
            return True
        return False
        
    def shallow_copy_table(self, base):
        #need a deep copy variant
        table = {}
        for key in base:
            table[key] = base[key]
        return table
    
    def shallow_copy_array(self, base):
        lst = []
        for e in base:
            lst.append(e)
        return lst
    
    def _class_bonus_crit(self):
        return 0 #should be overwritten by individual class modules if the crit rate needs to be shifted
    
    def calculate_crit_rate(self):
        crit = self.stats.get_crit_from_rating(rating=self.state_values['current_stats']['crit'])
        crit += self._class_bonus_crit() + self.buffs.buff_all_crit()
        return crit
        