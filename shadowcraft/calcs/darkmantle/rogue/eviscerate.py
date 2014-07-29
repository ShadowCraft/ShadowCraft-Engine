import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack

class Eviscerate(GenericAttack):
    _name = 'Eviscerate'
    _cost = 35
    
    def calculate_damage(self):
        # non-normalized weapon strike => (mh_weapon_damage + ap / 3.5 * weapon_speed) * weapon_damage_percentage
        print 'Eviscerate: ', self.state_values['current_second_power']
        return .3 * self.state_values['current_second_power'] * self.state_values['effective_ap']
    
    def secondary_effects(self):
        self.engine.restless_blades_impact(self.state_values['current_second_power'])
        #shift combo points, clean up residuals
        self.state_values['current_second_power'] = self.state_values['anticipation']
        self.state_values['anticipation'] = 0
    
    def setup_queues(self, timeline, buffs):
        #enable_autoattacks()
        timeline.append((self.time + self.state_values['gcd_size'], 'priority_queue'))
