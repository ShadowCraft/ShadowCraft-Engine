import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack

class MHAttack(GenericAttack):
    _name = 'mh_autoattack'
    
    def calculate_damage(self):
        # non-normalized weapon strike => (mh_weapon_damage + ap / 3.5 * weapon_speed) * weapon_damage_percentage
        print 'MH Attack: ', self.engine.stats.mh.speed * (self.engine.stats.mh.weapon_dps + self.state_values['effective_ap'] / 3.5)
        return self.engine.stats.mh.speed * (self.engine.stats.mh.weapon_dps + self.state_values['effective_ap'] / 3.5)
    
    def setup_queues(self, timeline, buffs):
        timeline.append((self.time + self.engine.stats.mh.speed, 'mh_autoattack'))
