import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.rogue import RogueDamageCalculator
from shadowcraft.calcs.darkmantle.generic_event import GenericEvent
from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data

class GenericAttack(GenericEvent):
    _name = 'generic_attack'
    _hand = 'mh'
    _cost = 0
    _cast_time = 0.0
    
    def calculate_damage(self):
        return 1 #to be overwritten by actual actions
    
    def secondary_effects(self):
        return
    
    def calculate_breakdown(self):
        if self.engine.end_calc_branch(self.time, self.total_damage):
            return self.breakdown
        normal_damage = self.calculate_damage()
        a = self.secondary_effects()
        self.state_values['current_power'] -= self._cost
        crit_rate = 0
        crit_damage = 0
        if self.can_crit:
            crit_rate = self.engine.calculate_crit_rate()
        #deal with crits at a later time
        if self._name in self.breakdown:
            self.breakdown[self._name] += normal_damage
        else:
            self.breakdown[self._name] = normal_damage
        #spawn child objects
        self.timeline = self.timeline[1:]
        self.setup_queues(self.timeline, self.state_values['auras'])
        next_attack_constructor = self.engine.get_next_attack(self.timeline[0][1])
        #                              engine,      breakdown,      time,                timeline,
        #                              total_damage,                state_values
        next = next_attack_constructor(self.engine, self.breakdown, self.timeline[0][0], self.engine.shallow_copy_array(self.timeline),
                                       self.total_damage,           self.state_values)
        next.calculate_breakdown()
        average_breakdown = self.breakdown
        return average_breakdown
