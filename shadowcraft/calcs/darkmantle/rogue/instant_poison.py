import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack
from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data

class InstantPoison(GenericAttack):
    _name = 'instant_poison'
    _cost = 0
    _cast_time = 0.0
    
    def calculate_damage(self):
        # non-normalized weapon strike => (mh_weapon_damage + ap / 3.5 * weapon_speed) * weapon_damage_percentage
        print 'Instant Poison: ', self.state_values['effective_ap'] * .20
        return self.state_values['effective_ap'] * .20 #???
    
    def setup_queues(self, timeline, buffs):
        return #nothing else to trigger for now
    