from shadowcraft.objects import procs
from shadowcraft.objects import proc_data
from shadowcraft.core import exceptions

class Stats(object):
    # For the moment, lets define this as raw stats from gear + race; AP is
    # only AP bonuses from gear and level.  Do not include multipliers like
    # Vitality and Sinister Calling; this is just raw stats.  See calcs page
    # rows 1-9 from my WotLK spreadsheets to see how these are typically
    # defined, though the numbers will need to updated for level 85.

    crit_rating_conversion_values = {60:14.0, 70:22.0769, 80:45.906, 85:179.28, 90:600.0, 100:1000}
    haste_rating_conversion_values = {60:10.0, 70:15.7692, 80:32.79, 85:128.057, 90:425.0, 100:800}
    mastery_rating_conversion_values = {60:14, 70:22.0769, 80:45.906, 85:179.28, 90:600.0, 100:1000}
    multistrike_rating_conversion_values = {60:14, 70:22.0769, 80:45.906, 85:179.28, 90:200.0, 100:5000}
    readiness_rating_conversion_values = {60:14, 70:22.0769, 80:45.906, 85:179.28, 90:200.0, 100:5000}
    pvp_power_rating_conversion_values = {60:7.96, 70:12.55, 80:26.11, 85:79.12, 90:400.0, 100:800}
    pvp_resil_rating_conversion_values = {60:9.29, 70:14.65, 80:30.46, 85:92.31, 90:310.0, 100:600}

    def __init__(self, mh, oh, procs, gear_buffs, str=0, agi=0, int=0, spirit=0, stam=0, ap=0, crit=0, haste=0, mastery=0, 
                 readiness=0, multistrike=0, level=None, pvp_power=0, pvp_resil=0, pvp_target_armor=None):
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
        self.readiness = readiness
        self.multistrike = multistrike
        self.mh = mh
        self.oh = oh
        self.procs = procs
        self.gear_buffs = gear_buffs
        self.level = level
        self.pvp_power = pvp_power
        self.pvp_resil = pvp_resil
        self.pvp_target_armor = pvp_target_armor

    def _set_constants_for_level(self):
        self.procs.level = self.level
        try:
            self.crit_rating_conversion        = self.crit_rating_conversion_values[self.level]
            self.haste_rating_conversion       = self.haste_rating_conversion_values[self.level]
            self.mastery_rating_conversion     = self.mastery_rating_conversion_values[self.level]
            self.multistrike_rating_conversion = self.multistrike_rating_conversion_values[self.level]
            self.readiness_rating_conversion   = self.readiness_rating_conversion_values[self.level]
            self.pvp_power_rating_conversion   = self.pvp_power_rating_conversion_values[self.level]
            self.pvp_resil_rating_conversion   = self.pvp_resil_rating_conversion_values[self.level]
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
        return rating / (100 * self.crit_rating_conversion)

    def get_haste_multiplier_from_rating(self, rating=None):
        if rating is None:
            rating = self.haste
        return 1 + rating / (100 * self.haste_rating_conversion)
    
    def get_readiness_multiplier_from_rating(self, rating=None, readiness_conversion=1):
        if rating is None:
            rating = self.readiness
        return 1 / (1 + (readiness_conversion * rating) / (self.readiness_rating_conversion * 100))
    
    def get_multistrike_chance_from_rating(self, rating=None):
        if rating is None:
            rating = self.multistrike
        return rating / (100 * self.multistrike_rating_conversion)
    
    def get_pvp_power_multiplier_from_rating(self, rating=None):
        if rating is None:
            rating = self.pvp_power
        return 1 + rating / (100 * self.pvp_power_rating_conversion)
    
    def get_pvp_resil_multiplier_from_rating(self, rating=None):
        if rating is None:
            rating = self.pvp_resil
        return 0.6*(rating/(rating+11727)) + .65 # .65 is base resil

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
        if self.type in ['gun', 'bow', 'crossbow']:
            self._normalization_speed = 2.8
        elif self.type in ['2h_sword', '2h_mace', '2h_axe', 'polearm']:
            self._normalization_speed = 3.3
        elif self.type == 'dagger':
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

    def damage(self, ap=0):
        return self.speed * (self.weapon_dps + ap / 14.)

    def normalized_damage(self, ap=0):
        return self.speed * self.weapon_dps + self._normalization_speed * ap / 14.

# Catch-all for non-proc gear based buffs (static or activated)
class GearBuffs(object):
    other_gear_buffs = [
        'leather_specialization',       # Increase %stat by 5%
        'chaotic_metagem',              # Increase critical damage by 3%
        'rogue_pvp_4pc',                # 30 Extra Energy
        'rogue_t13_legendary',          # Increase 45% damage on SS and RvS, used in case the rogue only equips the mh of a set.
        'rogue_t14_2pc',                # Venom Wound damage by 20%, Sinister Strike by 15%, Backstab by 10%
        'rogue_t14_4pc',                # Shadow Blades by +12s
        'rogue_t15_2pc',                # Extra CP per finisher (max of 6)
        'rogue_t15_4pc',                # Abilities cast during Shadow Blades cost 40% less
        'rogue_t16_2pc',                # Stacking energy cost reduction (up to 5, up to 5 stacks) on NEXT RvS cast, Seal Fate Proc, or HAT proc
        'rogue_t16_4pc',                # 10% KS damage every time it hits, stacking mastery during vendetta (250 mastery, up to 20 stacks), every 5th backstab is an ambush
        'mixology',
        'master_of_anatomy',
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
    
    def rogue_t16_2pc_bonus(self):
        if self.rogue_t16_2pc:
            return True
        else:
            return False
    
    def rogue_t16_4pc_bonus(self):
        if self.rogue_t16_4pc:
            return True
        else:
            return False
    
    def leather_specialization_multiplier(self):
        if self.leather_specialization:
            return 1.05
        else:
            return 1