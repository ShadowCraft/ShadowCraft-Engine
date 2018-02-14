from builtins import object
from shadowcraft.core import exceptions

import gettext
_ = gettext.gettext

class InvalidBuffException(exceptions.InvalidInputException):
    pass

class Buffs(object):

    allowed_buffs = frozenset([
        'short_term_haste_buff',            # Heroism/Blood Lust, Time Warp
        'spell_damage_debuff',              # Chaos Brand
        'physical_vulnerability_debuff',    # Expose Armor
        'attack_power_buff',                # Battle Shout
        #'stat_multiplier_buff',            # Mark of the Wild, Blessing of Kings, Legacy of the Emperor
        #'crit_chance_buff',                 # Leader of the Pack, Legacy of the White Tiger, Arcane Brillance
        #'stamina_buff',                     # PW: Fortitude, Blood Pact, Commanding Shout
        #'spell_power_buff',                 # Dark Intent, Arcane Brillance
        #'armor_debuff',                     # Sunder, Expose Armor, Faerie Fire
        #'slow_casting_debuff',
        #'haste_buff',                       # Demon Speed
        #'versatility_buff',                 # Mark of the Wild
        #'mastery_buff',                     # Legacy of the Emperor
        #'primary_stat_buff',                # Battle Shout

        # consumables
        ###LEGION###
        'flask_legion_agi',                 # Flask of the Seventh Demon
        'food_legion_mastery_225',          # Pickeled Stormray
        'food_legion_crit_225',             # Salt & Pepper Shank
        'food_legion_haste_225',            # Deep-Fried Mossgill
        'food_legion_versatility_225',      # Faronaar Fizz
        'food_legion_mastery_300',          # Barracude Mrglgagh
        'food_legion_crit_300',             # Leybeque Ribs
        'food_legion_haste_300',            # Suramar Surf and Turf
        'food_legion_versatility_300',      # Koi-Scented Stormray
        'food_legion_mastery_375',          # Nightborne Delicacy Platter
        'food_legion_crit_375',             # The Hungry Magister
        'food_legion_haste_375',            # Azshari Salad
        'food_legion_versatility_375',      # Seed-Battered Fish Plate
        'food_legion_damage_1',             # Spiced Rib Roast
        'food_legion_damage_2',             # Drogbar-Style Salmon
        'food_legion_damage_3',             # Fishbrul Special
        'food_legion_feast_400',
        'food_legion_feast_500',
    ])

    buffs_debuffs = frozenset([
        'short_term_haste_buff',            # Heroism/Blood Lust, Time Warp
        'spell_damage_debuff',              # Curse of the Elements
        'physical_vulnerability_debuff',    # Expose Armor
        'attack_power_buff',                # Battle Shout
        #'stat_multiplier_buff',             # Mark of the Wild, Blessing of Kings, Legacy of the Emperor
        #'crit_chance_buff',                 # Leader of the Pack, Legacy of the White Tiger, Arcane Brillance
        #'multistrike_buff',                 # Swiftblade's Cunning, ...
        #'spell_power_buff',                 # Dark Intent, Arcane Brillance
        #'stamina_buff',                     # PW: Fortitude, Blood Pact, Commanding Shout
        #'haste_buff',                       # Demon Speed
        #'versatility_buff',                 # Mark of the Wild
        #'mastery_buff',                     # Legacy of the Emperor
        #'primary_stat_buff',                # Battle Shout
    ])

    def __init__(self, *args, **kwargs):
        for buff in args:
            if buff not in self.allowed_buffs:
                raise InvalidBuffException(_('Invalid buff {buff}').format(buff=buff))
            setattr(self, buff, True)

    def __getattr__(self, name):
        # Any buff we haven't assigned a value to, we don't have.
        if name in self.allowed_buffs:
            return False
        object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

    def get_stat_bonuses(self, epicurean=False):
        bonuses = {
            'agi': self.buff_agi(epicurean),
            'crit': self.buff_crit(epicurean),
            'haste': self.buff_haste(epicurean),
            'mastery': self.buff_mast(epicurean),
            'versatility': self.buff_versatility(epicurean),
        }
        return bonuses

    def buff_agi(self, race=False):
        bonus_agi = 0
        bonus_agi += 1300 * self.flask_legion_agi
        bonus_agi += 400 * self.food_legion_feast_400 * [1, 2][race]
        bonus_agi += 500 * self.food_legion_feast_500 * [1, 2][race]
        return bonus_agi

    def buff_haste(self, race=False):
        bonus_haste = 0
        bonus_haste += 225 * self.food_legion_haste_225 * [1, 2][race]
        bonus_haste += 300 * self.food_legion_haste_300 * [1, 2][race]
        bonus_haste += 375 * self.food_legion_haste_375 * [1, 2][race]
        return bonus_haste

    def buff_crit(self, race=False):
        bonus_crit = 0
        bonus_crit += 225 * self.food_legion_crit_225 * [1, 2][race]
        bonus_crit += 300 * self.food_legion_crit_300 * [1, 2][race]
        bonus_crit += 375 * self.food_legion_crit_375 * [1, 2][race]
        return bonus_crit

    def buff_mast(self, race=False):
        bonus_mastery = 0
        bonus_mastery += 225 * self.food_legion_mastery_225 * [1, 2][race]
        bonus_mastery += 300 * self.food_legion_mastery_300 * [1, 2][race]
        bonus_mastery += 375 * self.food_legion_mastery_375 * [1, 2][race]
        return bonus_mastery

    def buff_versatility(self, race=False):
        bonus_versatility = 0
        bonus_versatility += 225 * self.food_legion_versatility_225 * [1, 2][race]
        bonus_versatility += 300 * self.food_legion_versatility_300 * [1, 2][race]
        bonus_versatility += 375 * self.food_legion_versatility_375 * [1, 2][race]
        return bonus_versatility

    def damage_food(self):
        if self.food_legion_damage_1:
            return 1
        if self.food_legion_damage_2:
            return 2
        if self.food_legion_damage_3:
            return 3
        return 0
