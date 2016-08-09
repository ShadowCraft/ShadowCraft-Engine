from shadowcraft.core import exceptions

class Settings(object):
    # Settings object for AldrianasRogueDamageCalculator.

    def __init__(self, cycle, response_time=.5, latency=.03, duration=300, adv_params=None,
                 merge_damage=True, num_boss_adds=0, feint_interval=0, default_ep_stat='ap', is_day=False, is_demon=False):
        self.cycle = cycle
        self.response_time = response_time
        self.latency = latency
        self.duration = duration
        self.feint_interval = feint_interval
        self.is_day = is_day
        self.is_demon = is_demon
        self.num_boss_adds = max(num_boss_adds, 0)
        self.adv_params = self.interpret_adv_params(adv_params)
        self.default_ep_stat = default_ep_stat

    def interpret_adv_params(self, s=""):
        data = {}
        max_effects = 8
        current_effects = 0
        if s != "" and s:
            for e in s.split(';'):
                if e != "":
                    tmp = e.split(':')
                    try:
                        data[tmp[0].strip().lower()] = tmp[1].strip().lower() #strip() and lower() needed so that everyone is on the same page                        print data[tmp[0].strip().lower()] + ' : ' + tmp[0].strip().lower()
                        current_effects += 1
                        if current_effects == max_effects:
                            return data
                    except:
                        raise exceptions.InvalidInputException(_('Advanced Parameter ' + e + ' found corrupt. Properly structure params and try again.'))
        return data

    def is_assassination_rogue(self):
        return self.cycle._cycle_type == 'assassination'

    def is_combat_rogue(self):
        return self.cycle._cycle_type == 'combat'

    def is_subtlety_rogue(self):
        return self.cycle._cycle_type == 'subtlety'

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

    allowed_values = (1, 2, 3, 4, 5)

    def __init__(self, min_envenom_size_non_execute=4, min_envenom_size_execute=5):
        assert min_envenom_size_non_execute in self.allowed_values
        self.min_envenom_size_non_execute = min_envenom_size_non_execute

        assert min_envenom_size_execute in self.allowed_values
        self.min_envenom_size_execute = min_envenom_size_execute

class CombatCycle(Cycle):
    _cycle_type = 'combat'

    def __init__(self, ksp_immediately=True, revealing_strike_pooling=True, blade_flurry=False, dfa_during_ar=False):
        self.blade_flurry = bool(blade_flurry)
        self.ksp_immediately = bool(ksp_immediately) # Determines whether to KSp the instant it comes off cool or wait until Bandit's Guile stacks up.
        self.revealing_strike_pooling = bool(revealing_strike_pooling)
        self.dfa_during_ar = bool(dfa_during_ar)

class SubtletyCycle(Cycle):
    _cycle_type = 'subtlety'

    def __init__(self, cp_builder='backstab', dance_cp_builder='shadowstrike', positional_uptime=1.0, symbols_policy='just',
                 eviscerate_cps=5, finality_eviscerate_cps=5, nightblade_cps=5, finality_nightblade_cps=5,
                 dance_finisher_priority=[]):
        self.cp_builder = cp_builder #Allowed values: fok, backstab, gloomblade
        self.dance_cp_builder = dance_cp_builder #Allowed values: fok, shadowstrike
        self.positional_uptime = positional_uptime #Range 0.0 to 1.0, time behind target
        self.symbols_policy = symbols_policy #Allowed values:
                                             #'always' - use SoD every dance (macro)
                                             #'just'   - Only use SoD when needed to refresh
        #Finisher thresholds for each finisher, Allowed Values: 0, 1, 2, 3, 4, 5, 6
        self.eviscerate_cps = eviscerate_cps
        self.finality_eviscerate_cps = finality_eviscerate_cps
        self.nightblade_cps = nightblade_cps
        self.finality_nightblade_cps = finality_nightblade_cps

        #List of following keys: 'eviscerate', 'nightblade', 'finality:eviscerate', 'finality:nightblade'
        #Priority of finisher usage during dance
        #Keys not included will not be used during dance
        self.dance_finisher_priority = dance_finisher_priority

