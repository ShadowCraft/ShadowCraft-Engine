import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack

class OHAttack(GenericAttack):
    _name = 'oh_autoattack'
    
    def calculate_damage(self):
        # non-normalized weapon strike => (oh_weapon_damage + ap / 3.5 * weapon_speed) * weapon_damage_percentage
        print 'OH Attack: ', self.engine.stats.oh.speed * (self.engine.stats.oh.weapon_dps + self.state_values['effective_ap'] / 3.5) * .5
        return self.engine.stats.oh.speed * (self.engine.stats.oh.weapon_dps + self.state_values['effective_ap'] / 3.5) * .5
    
    def setup_queues(self, timeline, buffs):
        timeline.append((self.time + self.engine.stats.oh.speed, 'oh_autoattack'))
    