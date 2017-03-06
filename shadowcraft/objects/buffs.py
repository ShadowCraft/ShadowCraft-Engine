from shadowcraft.core import exceptions

class InvalidBuffException(exceptions.InvalidInputException):
    pass

class Buffs(object):

    allowed_buffs = frozenset([
        'short_term_haste_buff',           # Heroism/Blood Lust, Time Warp
        #'stat_multiplier_buff',            # Mark of the Wild, Blessing of Kings, Legacy of the Emperor
        #'crit_chance_buff',                # Leader of the Pack, Legacy of the White Tiger, Arcane Brillance
        #'haste_buff',                      # Swiftblade's Cunning, Unholy Aura
        #'multistrike_buff',                # Swiftblade's Cunning, ...
        #'attack_power_buff',               # Horn of Winter, Trueshot Aura, Battle Shout
        #'mastery_buff',                    # Blessing of Might, Grace of Air
        #'stamina_buff',                    # PW: Fortitude, Blood Pact, Commanding Shout
        #'versatility_buff',                #
        #'spell_power_buff',                # Dark Intent, Arcane Brillance
        #'armor_debuff',                     # Sunder, Expose Armor, Faerie Fire
        #'physical_vulnerability_debuff',    # Brittle Bones, Ebon Plaguebringer, Judgments of the Bold, Colossus Smash
        #'spell_damage_debuff',              # Master Poisoner, Curse of Elements
        #'slow_casting_debuff',
        'mortal_wounds_debuff',
        # consumables
        'flask_wod_agi_200',                #
        'flask_wod_agi',                    # 250
        'food_wod_mastery',                 # 100
        'food_wod_mastery_75',              # 75
        'food_wod_mastery_125',             # 125
        'food_wod_crit',                    #
        'food_wod_crit_75',                 #
        'food_wod_crit_125',                #
        'food_wod_haste',                   #
        'food_wod_haste_75',                #
        'food_wod_haste_125',               #
        'food_wod_versatility',             #
        'food_wod_versatility_75',          #
        'food_wod_versatility_125',         #
        'food_felmouth_frenzy',             # Felmouth frenzy, 2 haste scaling RPPM dealing 0.424 AP in damage
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
        'food_legion_feast_150',
        'food_legion_feast_200',
    ])

    buffs_debuffs = frozenset([
        'short_term_haste_buff',            # Heroism/Blood Lust, Time Warp
        #'stat_multiplier_buff',             # Mark of the Wild, Blessing of Kings, Legacy of the Emperor
        #'crit_chance_buff',                 # Leader of the Pack, Legacy of the White Tiger, Arcane Brillance
        #'haste_buff',                       # Swiftblade's Cunning, Unholy Aura
        #'multistrike_buff',                 # Swiftblade's Cunning, ...
        #'attack_power_buff',                # Horn of Winter, Trueshot Aura, Battle Shout
        #'mastery_buff',                     # Blessing of Might, Grace of Air
        #'spell_power_buff',                 # Dark Intent, Arcane Brillance
        #'versatility_buff',
        #'stamina_buff',                     # PW: Fortitude, Blood Pact, Commanding Shout
        #'physical_vulnerability_debuff',    # Brittle Bones, Ebon Plaguebringer, Judgments of the Bold, Colossus Smash
        #'spell_damage_debuff',              # Master Poisoner, Curse of Elements
        'mortal_wounds_debuff',
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
        bonus_agi += 200 * self.flask_wod_agi_200
        bonus_agi += 250 * self.flask_wod_agi
        bonus_agi += 1300 * self.flask_legion_agi
        bonus_agi += 150 * self.food_legion_feast_150 * [1, 2][race]
        bonus_agi += 200 * self.food_legion_feast_200 * [1, 2][race]
        return bonus_agi

    def buff_haste(self, race=False):
        bonus_haste = 0
        bonus_haste += 125 * self.food_wod_haste_125 * [1, 2][race]
        bonus_haste += 100 * self.food_wod_haste * [1, 2][race]
        bonus_haste += 75 * self.food_wod_haste_75 * [1, 2][race]
        bonus_haste += 225 * self.food_legion_haste_225 * [1, 2][race]
        bonus_haste += 300 * self.food_legion_haste_300 * [1, 2][race]
        bonus_haste += 375 * self.food_legion_haste_375 * [1, 2][race]
        return bonus_haste

    def buff_crit(self, race=False):
        bonus_crit = 0
        bonus_crit += 125 * self.food_wod_crit_125 * [1, 2][race]
        bonus_crit += 100 * self.food_wod_crit * [1, 2][race]
        bonus_crit += 75 * self.food_wod_crit_75 * [1, 2][race]
        bonus_crit += 225 * self.food_legion_crit_225 * [1, 2][race]
        bonus_crit += 300 * self.food_legion_crit_300 * [1, 2][race]
        bonus_crit += 375 * self.food_legion_crit_375 * [1, 2][race]
        return bonus_crit

    def buff_mast(self, race=False):
        bonus_mastery = 0
        bonus_mastery += 125 * self.food_wod_mastery_125 * [1, 2][race]
        bonus_mastery += 100 * self.food_wod_mastery * [1, 2][race]
        bonus_mastery += 75 * self.food_wod_mastery_75 * [1, 2][race]
        bonus_mastery += 225 * self.food_legion_mastery_225 * [1, 2][race]
        bonus_mastery += 300 * self.food_legion_mastery_300 * [1, 2][race]
        bonus_mastery += 375 * self.food_legion_mastery_375 * [1, 2][race]
        return bonus_mastery

    def buff_versatility(self, race=False):
        bonus_versatility = 0
        bonus_versatility += 125 * self.food_wod_versatility_125 * [1, 2][race]
        bonus_versatility += 100 * self.food_wod_versatility * [1, 2][race]
        bonus_versatility += 75 * self.food_wod_versatility_75 * [1, 2][race]
        bonus_versatility += 225 * self.food_legion_versatility_225 * [1, 2][race]
        bonus_versatility += 300 * self.food_legion_versatility_300 * [1, 2][race]
        bonus_versatility += 375 * self.food_legion_versatility_375 * [1, 2][race]
        return bonus_versatility

    def felmouth_food(self):
        if self.food_felmouth_frenzy :
            return True
        return False

    def damage_food(self):
        if self.food_legion_damage_1:
            return 1
        if self.food_legion_damage_2:
            return 2
        if self.food_legion_damage_3:
            return 3
        return 0
