import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data

class GenericEvent(object):
    
    def __init__(self, engine, breakdown, time, timeline, total_damage, state_values):
        self.engine = engine
        self.breakdown = breakdown
        self.time = time
        self.timeline = timeline
        self.total_damage = total_damage
        self.state_values = state_values
        
        self.can_crit = True
    
    def setup_queues(self, timeline, buffs):
        pass #to be overwritten by actual actions
