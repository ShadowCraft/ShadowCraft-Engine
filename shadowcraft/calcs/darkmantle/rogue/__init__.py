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

class RogueDarkmantleCalculator(DarkmantleCalculator):
    #
    
    def _get_values_for_class(self):
        #override global states if necessary
        if self.settings.is_combat_rogue():
            self.base_dw_miss_rate = 0
        
        #initialize variables into global constants table that won't change throughout the calculations
        #additionally, set up data structures (like combo points)
        class_table = {}
        
        class_table['current_combo_points'] = 0
        return class_table
    
    def get_dps(self):
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
