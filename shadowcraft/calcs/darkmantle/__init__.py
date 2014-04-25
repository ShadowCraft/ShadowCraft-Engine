import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.core import exceptions
from shadowcraft.calcs import armor_mitigation
from shadowcraft.objects import class_data
from shadowcraft.objects.procs import InvalidProcException
from shadowcraft.calcs.darkmantle import rogue

class InputNotModeledException(exceptions.InvalidInputException):
    # I'll return these when inputs don't make sense to the model.
    pass

class DarkmantleCalculator(object):
    #

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
        self.global_variables = {}
        self.global_variables['current_stats'] = {'agi': stats.agi,
                         'str': stats.str,
                         'stam': stats.stam,
                         'crit': stats.crit,
                         'haste': stats.haste,
                         'mastery': stats.mastery,
                         'readiness': stats.readiness,
                         'multistrike': stats.multistrike}
        self.global_variables['temporary_buffs'] = {}
        
        #combat tables
        self.base_one_hand_miss_rate = 0
        self.base_parry_chance = .03
        self.base_dodge_chance = 0
        self.base_spell_miss_rate = 0
        self.base_dw_miss_rate = .17
        self.base_block_chance = .075
        self.crit_reduction = .01 * self.level_difference
        
        #load class module data
        self.class_variables = self._get_values_for_class()
        