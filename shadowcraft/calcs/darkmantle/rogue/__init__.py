import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

import shadowcraft
from shadowcraft.calcs.darkmantle import DarkmantleCalculator
from shadowcraft.calcs.darkmantle.rogue import mh_attack
from shadowcraft.calcs.darkmantle.rogue import oh_attack
from shadowcraft.calcs.darkmantle.rogue import instant_poison
from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data


class InputNotModeledException(exceptions.InvalidInputException):
    # I'll return these when inputs don't make sense to the model.
    pass

class RogueDarkmantleCalculator(DarkmantleCalculator):
    abilities_list = {
        'mh_autoattack': mh_attack,
        'oh_autoattack': oh_attack,
        'instant_poison': instant_poison,
    }    
    ability_constructors = {
        'mh_autoattack': mh_attack.MHAttack,
        'oh_autoattack': oh_attack.OHAttack,
        'instant_poison': instant_poison.InstantPoison,
    }
    
    def get_next_attack(self, name):
        #pulls the constructor, not the module
        if name not in self.ability_constructors:
            raise InputNotModeledException(_('Can\'t locate action: {action}').format(action=str(name)))
        return self.ability_constructors[name]
    
    def can_cast_ability(self, name):
        if abilities_list._cost < self.state_values['current_power'] and self.state_values['cooldown'][name] < self.time:
            return True
        return False
    
    def _get_values_for_class(self):
        #override global states if necessary
        if self.settings.is_combat_rogue():
            self.base_dw_miss_rate = 0
        
        #initialize variables into a table that won't disappear throughout the calculations
        #additionally, set up data structures (like combo points)
        class_table = {}
        class_table['current_second_power'] = 0 #combot points
        class_table['max_second_power'] = 5 #can only get to 5 CP (for now?)
        
        class_table['max_power'] = 100 #energy
        if self.settings.is_assassination_rogue():
            class_table['max_power'] += 20
        if self.glyphs.energy:
            class_table['max_power'] += 20
        if self.talents.lemon_zest:
            class_table['max_power'] += 15
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            class_table['max_power'] += 30
        class_table['current_power'] = class_table['max_power']
        class_table['base_power_regen'] = 10
        if self.settings.is_combat_rogue():
            class_table['base_power_regen'] *= 1.2
        
        if self.talents.anticipation:
            class_table['anticipation'] = 0
            class_table['anticipation_max'] = 5
        if self.settings.is_combat_rogue():
            class_table['bg_counter'] = 0
        
        return class_table
    
    def _class_bonus_crit(self):
        return .05 #rogues get a "free" 5% extra crit
    
    def get_dps(self):
        if self.settings.is_assassination_rogue():
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
        return {'none':1.}
    
    def combat_dps_estimate(self):
        return sum(self.combat_dps_breakdown().values())
    def combat_dps_breakdown(self):
        print 'Calculating Combat Breakdown...'
        breakdown = {}
        event_queue = []
        #determine pre-fight sequence, establish baseline event_queue and auras
        #read priority list, determine first action
        #load event_state object with event_queue
        event_queue = [(0.0, 'mh_autoattack'), (0.01, 'oh_autoattack')] #temporary for development purposes
        #self.combat_priority_list() #should determine opener, as well as handle normal rotational decisions
        root_event = mh_attack.MHAttack(self, breakdown, 0, event_queue, 0, self.state_values) #timer always starts at 0, prefight has no bearing
        root_event.calculate_breakdown()
        return breakdown
    def combat_priority_list(self, cost):
        action = 'wait'
        if self.state_values['current_energy'] > cost and self.state_values['combo_points'] < self.state_values['max_second_power']:
            action = 'sinister_strike'
        if self.state_values['current_energy'] > cost and self.state_values['combo_points'] == self.state_values['max_second_power']:
            action = 'eviscerate'
        if self.state_values:
            return
        return action
    
    def subtlety_dps_estimate(self):
        return sum(self.subtlety_dps_breakdown().values())
    def subtlety_dps_breakdown(self):
        #determine pre-fight sequence, establish baseline event_queue and auras
        #read priority list, determine first action
        #load event_state object with event_queue
        return {'none':1.}
    
    def reset_bandits_guile(self):
        self.state_values['bg_counter'] = 0
        self.state_values['damage_multiplier'] *= 1.0 / 1.5 #BG30 is now 50%
    
    def set_bandits_guile_level(self):
        c = self.state_values['bg_counter']
        level = math.min(c // 4, 3) #BG30/50 is highest level
        if level == 3:
            self.state_values['damage_multiplier'] *= 1.5 / 1.2 #would be 1.3/1.2 if under level 100
        else:
            self.state_values['damage_multiplier'] *= (1 + .1 * level) / (1 + .1 * (level-1))
            
    def restless_blades_impact(self, cp):
        self.state_values['cooldown']['killing_spree'] -= 2 * cp
        self.state_values['cooldown']['adrenaline_rush'] -= 2 * cp
    
    def set_sanguinary_veins(self, enabled=True):
        if enabled:
            self.state_values['damage_multiplier'] *= 1.2
        else:
            self.state_values['damage_multiplier'] *= 1.0/1.2
    