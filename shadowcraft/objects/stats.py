from __future__ import division
from builtins import object
from shadowcraft.objects import buffs
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data
from shadowcraft.objects import race
from shadowcraft.core import exceptions

import gettext
_ = gettext.gettext

class Stats(object):
    # For the moment, lets define this as raw stats from gear
    # AP is only AP bonuses from gear (as of Legion usually 0)
    # Other base stat bonuses are added in get_character_base_stats
    # Multipliers are added in get_character_stat_multipliers

    crit_rating_conversion_values        = {60:13.0, 70:14.0,  80:15.0,  85:17.0,  90:23.0,  100:110.0,  110:400.0}
    haste_rating_conversion_values       = {60:9.00, 70:10.0,  80:12.0,  85:14.0,  90:20.0,  100:100.0,  110:375.0}
    mastery_rating_conversion_values     = {60:13.0, 70:14.0,  80:15.0,  85:17.0,  90:23.0,  100:110.0,  110:400.0}
    versatility_rating_conversion_values = {60:13.0, 70:14.0,  80:15.0,  85:17.0,  90:27.0,  100:130.0,  110:475.0}

    def __init__(self, mh, oh, procs, gear_buffs, str=0, agi=0, int=0, stam=0, ap=0, crit=0, haste=0, mastery=0,
                versatility=0, level=None):
        # This will need to be adjusted if at any point we want to support
        # other classes, but this is probably the easiest way to do it for
        # the moment.
        self.str = str
        self.agi = agi
        self.int = int
        self.stam = stam
        self.ap = ap
        self.crit = crit
        self.haste = haste
        self.mastery = mastery
        self.versatility = versatility
        self.mh = mh
        self.oh = oh
        self.gear_buffs = gear_buffs
        self.level = level
        self.procs = procs

    def _set_constants_for_level(self):
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

    def get_character_base_stats(self, race, traits=None, buffs=None):
        base_stats = {
            'str': self.str + race.racial_str,
            'int': self.int + race.racial_int,
            'agi': self.agi + race.racial_agi,
            'ap': self.ap,
            'crit': self.crit,
            'haste': self.haste,
            'mastery': self.mastery,
            'versatility': self.versatility,
        }
        if buffs is not None:
            buff_bonuses = buffs.get_stat_bonuses(race.epicurean)
            for bonus in buff_bonuses:
                base_stats[bonus] += buff_bonuses[bonus]

        #netherlight crucible t2
        if traits is not None:
            if traits.light_speed:
                base_stats['haste'] += 500 * traits.light_speed
            if traits.master_of_shadows:
                base_stats['mastery'] += 500 * traits.master_of_shadows

        # Other bonuses
        if self.gear_buffs.rogue_orderhall_6pc:
            base_stats['agi'] += 500

        return base_stats

    def get_character_stat_multipliers(self, race):
        # assume rogue for gear spec
        stat_multipliers = {
            'str': 1.,
            'int': 1.,
            'agi': self.gear_buffs.gear_specialization_multiplier(),
            'ap': 1,
            'crit': 1. + (0.02 * race.human_spirit),
            'haste': 1. + (0.02 * race.human_spirit),
            'mastery': 1. + (0.02 * race.human_spirit),
            'versatility': 1. + (0.02 * race.human_spirit),
        }
        return stat_multipliers

    def get_character_stats(self, race, traits=None, buffs=None):
        base = self.get_character_base_stats(race, traits, buffs)
        mult = self.get_character_stat_multipliers(race)
        stats = { }
        for stat in base:
            stats[stat] = base[stat] * mult[stat]
        return stats

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
        'rogue_t18_4pc_lfr',            # Energy increased by 20, 5% increase in energy regen
        'rogue_t19_2pc',                # Mutilate causes 30% bleed over 8 seconds, Nightblades lasts additional 2 seconds per CP
        'rogue_t19_4pc',                # 10% envenom damage per bleed, 30% SSk generates additional CP if nightblade up
        'rogue_t20_2pc',                # Garrote deals 40% increased damage, Symbols of Death increases your damage done by an additional 10%.
        'rogue_t20_4pc',                # Garrote's cost is reduced by 25 Energy and cooldown is reduced by 12 sec, Symbols of Death has 5 sec reduced cooldown and generates 2 Energy per sec while active.
        'jacins_ruse_2pc',              # Proc 3000 mastery for 15s, 1 rppm
        'march_of_the_legion_2pc',      # Proc 35K damage when fighting demons, 6+Haste RPPM
        'journey_through_time_2pc',     # The effect from Chrono Shard now increases your movement speed by 30%, and grants an additional 1000 Haste.
        'kara_empowered_2pc',           # 30% increase to paired trinkets
        'rogue_orderhall_6pc',          # Agility increased by 500
        'rogue_orderhall_8pc',          # Your finishing moves have a chance to increase your Haste by 2000 for 12 sec.
        #Legendaries
        'the_dreadlords_deceit',             #fok/ssk damage increased by 35% per 2 seconds up to 1 minute
        'duskwalkers_footpads',              #Vendetta CD reduced by 1 second for each 65 energy spent
        'thraxis_tricksy_treads',            #
        'shadow_satyrs_walk',                #3+1/3yd energy refund on ssk
        'insignia_of_ravenholdt',            #15% damage as shadow on cp generators
        'zoldyck_family_training_shackles',  #Poisons and Bleeds deal 30% additional damage below 30% health
        'greenskins_waterlogged_wristcuffs', #
        'denial_of_the_half_giants',         # Finishers extend ShB by 0.3 seconds per cp spent
        'shivarran_symmetry',                #
        'mantle_of_the_master_assassin',     #100% crit during stealth and for 6 seconds after
        'cinidaria_the_symbiote',            #30% additional damage to enemies above 90% health
        'sephuzs_secret',                    #2% haste
        'the_empty_crown',                   #Kingsbane generates 40 Energy over 5 sec.
        'the_first_of_the_dead',             #For 2 sec after activating Symbols of Death, Shadowstrike generates 3 additional combo points and Backstab generates 4 additional combo points.
        'the_curse_of_restlessness',         #NYI
        'soul_of_the_shadowblade',           #Gain the Vigor talent.
        #Other
        'jeweled_signet_of_melandrus',       #Increases your autoattack damage by 10%.
        'gnawed_thumb_ring',                 #Use: Have a nibble, increasing your healing and magic damage done by 5% for 12 sec. (3 Min Cooldown)
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
            for spells in list(bonus.keys()):
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

    def rogue_t15_4pc_reduced_cost(self, uptime=12/180): #This is for Mut calcs
        cost_reduction = .15
        if self.rogue_t15_4pc:
            return 1. - (cost_reduction * uptime)
        return 1.

    def rogue_t15_4pc_modifier(self, is_sb=False): #This is for Combat/Sub calcs
        if self.rogue_t15_4pc and is_sb:
            return .85 # 1 - .15
        return 1.

    def gear_specialization_multiplier(self):
        if self.gear_specialization:
            return 1.05
        else:
            return 1
