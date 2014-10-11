from shadowcraft.core import exceptions

class Settings(object):
    # Settings object for AldrianasRogueDamageCalculator.

    def __init__(self, cycle, time_in_execute_range=.35, response_time=.5, latency=.03, dmg_poison='dp', utl_poison=None,
                 duration=300, use_opener='always', opener_name='default', is_pvp=False, shiv_interval=0, adv_params=None,
                 merge_damage=True, num_boss_adds=0, feint_interval=0, default_ep_stat='agi', is_day=False):
        self.cycle = cycle
        self.time_in_execute_range = time_in_execute_range
        self.response_time = response_time
        self.latency = latency
        self.dmg_poison = dmg_poison
        self.utl_poison = utl_poison
        self.duration = duration
        self.use_opener = use_opener # Allowed values are 'always' (vanish/shadowmeld on cooldown), 'opener' (once per fight) and 'never'
        self.opener_name = opener_name
        self.is_pvp = is_pvp
        self.feint_interval = feint_interval
        self.merge_damage = merge_damage
        self.is_day = is_day
        self.num_boss_adds = max(num_boss_adds, 0)
        self.shiv_interval = float(shiv_interval)
        self.adv_params = self.interpret_adv_params(adv_params)
        self.default_ep_stat = default_ep_stat
        if self.shiv_interval < 10 and not self.shiv_interval == 0:
            self.shiv_interval = 10
        allowed_openers_per_spec = {
            'assassination': ('mutilate', 'dispatch', 'envenom'),
            'combat': ('sinister_strike', 'revealing_strike', 'eviscerate'),
            'subtlety': ()
        }
        allowed_openers = allowed_openers_per_spec[self.cycle._cycle_type] + ('ambush', 'garrote', 'default', 'cpg')
        if opener_name not in allowed_openers:
            raise exceptions.InvalidInputException(_('Opener {opener} is not allowed in {cycle} cycles.').format(opener=opener_name, cycle=self.cycle._cycle_type))
        if opener_name == 'default':
            default_openers = {
                'assassination': 'mutilate',
                'combat': 'ambush',
                'subtlety': 'ambush'}
            self.opener_name = default_openers[self.cycle._cycle_type]
        if dmg_poison not in (None, 'dp', 'wp'):
            raise exceptions.InvalidInputException(_('You can only choose Deadly(dp) or Wound(wp) as a damage poison'))
        if utl_poison not in (None, 'cp', 'mnp', 'lp', 'pp'):
            raise exceptions.InvalidInputException(_('You can only choose Crippling(cp), Mind-Numbing(mnp), Leeching(lp) or Paralytic(pp) as a non-lethal poison'))

    def get_spec(self):
        return self.cycle._cycle_type
    
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

    def __init__(self, min_envenom_size_non_execute=4, min_envenom_size_execute=5, prioritize_rupture_uptime_non_execute=True, prioritize_rupture_uptime_execute=True):
        assert min_envenom_size_non_execute in self.allowed_values
        self.min_envenom_size_non_execute = min_envenom_size_non_execute

        assert min_envenom_size_execute in self.allowed_values
        self.min_envenom_size_execute = min_envenom_size_execute
        
        # There are two fundamental ways you can manage rupture; one is to
        # reapply with whatever CP you have as soon as you can after the old
        # rupture drops; we will call this priorotizing uptime over size.
        # The second is to use ruptures that are the same size as your
        # envenoms, which we will call prioritizing size over uptime. True
        # means the first of these options; False means the second.
        # There are theoretically other things you can do (say, 4+ envenom and
        # 5+ ruptures) but such things are significantly harder to model so I'm
        # not going to worry about them until we have reason to believe they're
        # actually better.
        self.prioritize_rupture_uptime_non_execute = prioritize_rupture_uptime_non_execute
        self.prioritize_rupture_uptime_execute = prioritize_rupture_uptime_execute


class CombatCycle(Cycle):
    _cycle_type = 'combat'

    def __init__(self, ksp_immediately=True, revealing_strike_pooling=True, blade_flurry=False, dfa_during_ar=False):
        self.blade_flurry = bool(blade_flurry)
        self.ksp_immediately = bool(ksp_immediately) # Determines whether to KSp the instant it comes off cool or wait until Bandit's Guile stacks up.
        self.revealing_strike_pooling = bool(revealing_strike_pooling)
        self.dfa_during_ar = bool(dfa_during_ar)

class SubtletyCycle(Cycle):
    _cycle_type = 'subtlety'

    def __init__(self, raid_crits_per_second, use_hemorrhage='uptime'):
        self.raid_crits_per_second = raid_crits_per_second #used to calculate HAT procs per second.
        self.use_hemorrhage = use_hemorrhage # Allowed values are 'always' (main CP generator),
                                                                 #'never' (default to backstab),
                                                                 #'uptime' (cast when hemo is down),
        
