from shadowcraft.core import exceptions

class Settings(object):

    def __init__(self, cycle, response_time=.5, latency=.03, merge_damage=True):
        self.cycle = cycle
        self.response_time = response_time
        self.latency = latency
        self.merge_damage = merge_damage
        
    def get_spec(self):
        return self.cycle._cycle_type
    
    def is_assassination_rogue(self):
        return self.get_spec() == 'assassination'

    def is_combat_rogue(self):
        return self.get_spec() == 'combat'

    def is_subtlety_rogue(self):
        return self.get_spec() == 'subtlety'

class Cycle(object):
    # Base class for cycle objects.  Can't think of anything that particularly
    # needs to go here yet, but it seems worth keeping options open in that
    # respect.

    # When subclassing, define _cycle_type to be one of 'assassination',
    # 'combat', or 'subtlety' - this is how the damage calculator makes sure
    # you have an appropriate cycle object to go with your talent trees, etc.
    _cycle_type = ''


class AssassinationCycle(Cycle):
    _cycle_type = 'assassination'

    def __init__(self):
        return


class CombatCycle(Cycle):
    _cycle_type = 'combat'

    def __init__(self):
        return
        
class SubtletyCycle(Cycle):
    _cycle_type = 'subtlety'

    def __init__(self):
        return
