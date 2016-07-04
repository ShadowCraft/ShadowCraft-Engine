from shadowcraft.objects import procs
from shadowcraft.objects import proc_data
from shadowcraft.core import exceptions

class Stats(object):
    # For the moment, lets define this as raw stats from gear + race; AP is
    # only AP bonuses from gear and level.  Do not include multipliers like
    # Vitality and Sinister Calling; this is just raw stats.  See calcs page
    # rows 1-9 from my WotLK spreadsheets to see how these are typically
    # defined, though the numbers will need to updated for level 85.

    crit_rating_conversion_values        = {60:13.0, 70:14.0,  80:15.0,  85:17.0,  90:23.0,  100:110.0,  110:350.0}
    haste_rating_conversion_values       = {60:9.00, 70:10.0,  80:12.0,  85:14.0,  90:20.0,  100:100.0,  110:325.0}
    mastery_rating_conversion_values     = {60:13.0, 70:14.0,  80:15.0,  85:17.0,  90:23.0,  100:110.0,  110:350.0}
    versatility_rating_conversion_values = {60:13.0, 70:14.0,  80:15.0,  85:17.0,  90:27.0,  100:130.0,  110:400.0}

    def __init__(self, mh, oh, procs, gear_buffs, str=0, agi=0, int=0, spirit=0, stam=0, ap=0, crit=0, haste=0, mastery=0, 
                versatility=0, level=None):
        # This will need to be adjusted if at any point we want to support
        # other classes, but this is probably the easiest way to do it for
        # the moment.
        self.str = str
        self.agi = agi
        self.int = int
        self.spirit = spirit
        self.stam = stam
        self.ap = ap
        self.crit = crit
        self.haste = haste
        self.mastery = mastery
        self.versatility = versatility
        self.mh = mh
        self.oh = oh
        self.procs = procs
        self.gear_buffs = gear_buffs
        self.level = level
    def _set_constants_for_level(self):
        self.procs.level = self.level
        try:
            self.crit_rating_conversion        = self.crit_rating_conversion_values[self.level]
            self.haste_rating_conversion       = self.haste_rating_conversion_values[self.level]
            self.mastery_rating_conversion     = self.mastery_rating_conversion_values[self.level]
            self.versatility_rating_conversion = self.versatility_rating_conversion_values[self.level]
        except KeyError:
            raise exceptions.InvalidLevelException(_('No conversion factor available for level {level}').format(level=self.level))

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'level' and value is not None:
            self._set_constants_for_level()
    
    def get_mastery_from_rating(self, rating=None):
        if rating is None:
            rating = self.mastery
        return 8 + rating / self.mastery_rating_conversion

    def get_crit_from_rating(self, rating=None):
        if rating is None:
            rating = self.crit
        return rating / (100. * self.crit_rating_conversion)

    def get_haste_multiplier_from_rating(self, rating=None):
        if rating is None:
            rating = self.haste
        return 1 + rating / (100. * self.haste_rating_conversion)
    
    def get_versatility_multiplier_from_rating(self, rating=None):
        if rating is None:
            rating = self.versatility
        return 1. + rating / (100. * self.versatility_rating_conversion)

class Weapon(object):
    allowed_melee_enchants = proc_data.allowed_melee_enchants

    def __init__(self, damage, speed, weapon_type, enchant=None):
        self.speed = speed
        self.weapon_dps = damage * 1.0 / speed
        self.type = weapon_type
        if enchant is not None:
            self.set_enchant(enchant)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'type':
            self.set_normalization_speed()

    def set_normalization_speed(self):
        #if self.type in ['gun', 'bow', 'crossbow']:
        #    self._normalization_speed = 2.8
        #elif self.type in ['2h_sword', '2h_mace', '2h_axe', 'polearm']:
        #    self._normalization_speed = 3.3
        #elif
        
        # commented out for micro performance's sake
        # should be re-enabled if other classes ever make use of Shadowcraft
        if self.type == 'dagger':
            self._normalization_speed = 1.7
        else:
            self._normalization_speed = 2.4

    def set_enchant(self, enchant):
        if enchant == None:
            self.del_enchant()
        else:
            if self.is_melee():
                if enchant in self.allowed_melee_enchants:
                    self.del_enchant()
                    proc = procs.Proc(**self.allowed_melee_enchants[enchant])
                    setattr(self, enchant, proc)
                else:
                    raise exceptions.InvalidInputException(_('Enchant {enchant} is not allowed.').format(enchant=enchant))
            else:
                raise exceptions.InvalidInputException(_('Only melee weapons can be enchanted with {enchant}.').format(enchant=enchant))

    def del_enchant(self):
        for i in self.allowed_melee_enchants:
            if getattr(self, i):
                delattr(self, i)

    def __getattr__(self, name):
        # Any enchant we haven't assigned a value to, we don't have.
        if name in self.allowed_melee_enchants:
            return False
        object.__getattribute__(self, name)

    def is_melee(self):
        return not self.type in frozenset(['gun', 'bow', 'crossbow', 'thrown'])

    def damage(self, ap=0, weapon_speed=None):
        if weapon_speed == None:
            weapon_speed = self.speed
        return weapon_speed * (self.weapon_dps + ap / 3.5) #used to be 14

    def normalized_damage(self, ap=0, weapon_speed=None):
        if weapon_speed == None:
            weapon_speed = self.speed
        return weapon_speed * self.weapon_dps + self._normalization_speed * ap / 3.5 #used to be 14

# Catch-all for non-proc gear based buffs (static or activated)
class GearBuffs(object):
    other_gear_buffs = [
        'gear_specialization',          # Increase stat by 5%, previously leather specialization
        'chaotic_metagem',              # Increase critical damage by 3%
        'rogue_pvp_4pc',                # 30 Extra Energy
        'rogue_pvp_wod_4pc',            # +1s KSpree - Combat, 5CP and 100% crit after vanish - Assassination, 100 versatility after feint 5s- Sub
        'rogue_t14_2pc',                # Venom Wound damage by 20%, Sinister Strike by 15%, Backstab by 10%
        'rogue_t14_4pc',                # Shadow Blades by +12s
        'rogue_t15_2pc',                # Extra CP per finisher (max of 6)
        'rogue_t15_4pc',                # Abilities cast during Shadow Blades cost 40% less
        'rogue_t16_2pc',                # Stacking energy cost reduction (up to 5, up to 5 stacks) on NEXT RvS cast, Seal Fate Proc, or HAT proc
        'rogue_t16_4pc',                # 10% KS damage every time it hits, stacking mastery during vendetta (250 mastery, up to 20 stacks), % chance for backstab to become ambush
        'rogue_t17_2pc',                # Mut and Dispatch crits generate 7 energy, RvS has 20% higher chance to generate a CP, generate 60e when casting ShD
        'rogue_t17_4pc',                # Envenom generates 1 CP, finishers have a 20% chance to generate 5CP and next Evisc costs 0, 5 CP at the end of ShD
        'rogue_t17_4pc_lfr',            # 1.1 RPPM, 30% energy generation for 6s
        'rogue_t18_2pc',                # Dispatch deals 25% additional damage as Nature damage, SnD internal ticks have 8% change to proc ARfor 4 sec, Vanish awards 5cps and increases all damage done by 30% for 10 sec
        'rogue_t18_4pc',                # Dispatch generates +2cps, AR increased damage by 15%, Evis and Rupture reduce the CD of vanish by 1 seconds per CP
        'rogue_t18_4pc_lfr'             # Energy increased by 20, 5% increase in energy regen
    ]

    allowed_buffs = frozenset(other_gear_buffs)
    
    def __init__(self, *args):
        for arg in args:
            if not isinstance(arg, (list,tuple)):
                arg = (arg,0)
            if arg[0] in self.allowed_buffs:
                setattr(self, arg[0], True)
                

    def __getattr__(self, name):
        # Any gear buff we haven't assigned a value to, we don't have.
        if name in self.allowed_buffs:
            return False
        object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

    def metagem_crit_multiplier(self):
        if self.chaotic_metagem:
            return 1.03
        else:
            return 1
    
    def rogue_pvp_4pc_extra_energy(self):
        if self.rogue_pvp_4pc:
            return 30
        return 0
    
    def rogue_t14_2pc_damage_bonus(self, spell):
        if self.rogue_t14_2pc:
            bonus = {
                     ('assassination', 'vw', 'venomous_wounds'): 0.2,
                     ('combat', 'ss', 'sinister_strike'): 0.15,
                     ('subtlety', 'bs', 'backstab'): 0.1
            }
            for spells in bonus.keys():
                if spell in spells:
                    return 1 + bonus[spells]
        return 1
    
    def rogue_t14_4pc_extra_time(self, is_combat=False):
        if is_combat:
            return self.rogue_t14_4pc * 6
        return self.rogue_t14_4pc * 12
    
    def rogue_t15_2pc_bonus_cp(self):
        if self.rogue_t15_2pc:
            return 1
        return 0
    
    def rogue_t15_4pc_reduced_cost(self, uptime= 12. / 180.): #This is for Mut calcs
        cost_reduction = .15
        if self.rogue_t15_4pc:
            return 1. - (cost_reduction * uptime)
        return 1.
    
    def rogue_t15_4pc_modifier(self, is_sb=False): #This is for Combat/Sub calcs
        if self.rogue_t15_4pc and is_sb:
            return .85 # 1 - .15
        return 1.
    
    def rogue_t16_2pc_bonus(self):
        if self.rogue_t16_2pc:
            return True
        return False
    
    def rogue_t16_4pc_bonus(self):
        if self.rogue_t16_4pc:
            return True
        return False
    
    def rogue_t17_2pc_bonus(self):
        if self.rogue_t17_2pc:
            return True
        return False
    
    def rogue_t17_4pc_bonus(self):
        if self.rogue_t17_4pc:
            return True
        return False

    def rogue_t18_2pc_bonus(self):
        if self.rogue_t18_2pc:
            return True
        return False
       
    def rogue_t18_4pc_bonus(self):
        if self.rogue_T18_4pc:
            return True
        return False
    
    def gear_specialization_multiplier(self):
        if self.gear_specialization:
            return 1.05
        else:
            return 1
