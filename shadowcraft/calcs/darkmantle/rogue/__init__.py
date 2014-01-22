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

class DarkmantleCalculator(object):
    #

    def __init__(self, stats, talents, glyphs, buffs, race, settings=None, level=85, target_level=None, char_class='rogue'):
        self.tools = class_data.Util()
        self.stats = stats
        self.talents = talents
        self.glyphs = glyphs
        self.buffs = buffs
        self.race = race
        self.char_class = char_class
        self.settings = settings
        self.target_level = [target_level, level + 3][target_level is None]
        if self.settings.is_pvp:
            self.level_difference = 0
        else:
            self.level_difference = max(self.target_level - level, 0)
        self.level = level
        if self.stats.gear_buffs.mixology and (self.buffs.agi_flask or self.buffs.agi_flask_mop):
            self.stats.agi += self.stats.gear_buffs.tradeskill_bonus()
        if self.stats.gear_buffs.master_of_anatomy:
            self.stats.crit += self.stats.gear_buffs.tradeskill_bonus('master_of_anatomy')
        if self.race.race_name == 'undead':
            self.stats.procs.set_proc('touch_of_the_grave')
        self._set_constants_for_class()
        
        if self.settings.is_pvp:
            self.base_one_hand_miss_rate = .03
            self.base_parry_chance = .05
            self.base_dodge_chance = .03
            self.base_spell_miss_rate = .06
        else:
            self.base_one_hand_miss_rate = 0 #.03 + .015 * self.level_difference
            self.base_parry_chance = .03 + .015 * self.level_difference
            self.base_dodge_chance = 0 #.03 + .015 * self.level_difference
            self.base_spell_miss_rate = 0 #.06 + .03 * self.level_difference
        
        self.base_dw_miss_rate = self.base_one_hand_miss_rate + .19
        self.base_block_chance = .03 + .015 * self.level_difference
        #load stats, class, procs, etc to main content
        #load class modules
        #load class global settings to global_settings
        #load spell/mechanic data to global data
        return
    
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
    
    def assassination_dps_estimate(self):
        return sum(self.assassination_dps_breakdown().values())
    def assassination_dps_breakdown(self):
        #determine pre-fight sequence, establish baseline event_queue and auras
        #read priority list, determine first action
        #load event_state object with event_queue
        return
    
    def combat_dps_estimate(self):
        return sum(self.combat_dps_breakdown().values())
    def combat_dps_breakdown(self):
        #determine pre-fight sequence, establish baseline event_queue and auras
        #read priority list, determine first action
        #load event_state object with event_queue
        return
    
    def subtlety_dps_estimate(self):
        return sum(self.subtlety_dps_breakdown().values())
    def subtlety_dps_breakdown(self):
        #determine pre-fight sequence, establish baseline event_queue and auras
        #read priority list, determine first action
        #load event_state object with event_queue
        return
