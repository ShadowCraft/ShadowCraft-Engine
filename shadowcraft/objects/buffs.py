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
        'flask_legion_agi',                 #Flask of the Seventh Demon
        'food_legion_masstery_450',         #
        'food_legion_crit_450',             #
        'food_legion_haste_450',            #
        'food_legion_haste_450',            #
        'food_legion_masstery_600',         #
        'food_legion_crit_600',             #
        'food_legion_haste_600',            #
        'food_legion_haste_600',            #
        'food_legion_masstery_700',         #
        'food_legion_crit_700',             #
        'food_legion_haste_700',            #
        'food_legion_haste_700',            #
        'food_legion_damage_1',             #
        'food_legion_damage_2',             #
        'food_legion_damage_3',             #
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
        self.level = kwargs.get('level', 100)

    def __getattr__(self, name):
        # Any buff we haven't assigned a value to, we don't have.
        if name in self.allowed_buffs:
            return False
        object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'level':
            self._set_constants_for_level()

    def buff_agi(self, race=False):
        bonus_agi = 0
        bonus_agi += 114 * self.agi_flask_mop
        bonus_agi += 200 * self.flask_wod_agi_200
        bonus_agi += 250 * self.flask_wod_agi
        bonus_agi += 34 * self.food_mop_agi * [1, 2][race]
        bonus_agi += 1300 * self.flask_legion_agi
        return bonus_agi
    
    def buff_haste(self, race=False):
        bonus_haste = 0
        bonus_haste += 125 * self.food_wod_haste_125 * [1, 2][race]
        bonus_haste += 100 * self.food_wod_haste * [1, 2][race]
        bonus_haste += 75 * self.food_wod_haste_75 * [1, 2][race]
        bonus_haste += 450 * self.food_wod_haste_450 * [1, 2][race]
        bonus_haste += 600 * self.food_wod_haste_600 * [1, 2][race]
        bonus_haste += 700 * self.food_wod_haste_700 * [1, 2][race]
        return bonus_haste
    
    def buff_crit(self, race=False):
        bonus_crit = 0
        bonus_crit += 125 * self.food_wod_crit_125 * [1, 2][race]
        bonus_crit += 100 * self.food_wod_crit * [1, 2][race]
        bonus_crit += 75 * self.food_wod_crit_75 * [1, 2][race]
        bonus_crit += 450 * self.food_wod_crit_450 * [1, 2][race]
        bonus_crit += 600 * self.food_wod_crit_600 * [1, 2][race]
        bonus_crit += 700 * self.food_wod_crit_700 * [1, 2][race]
        return bonus_crit
    
    def buff_mast(self, race=False):
        bonus_mastery = 0
        bonus_mastery += [0, self.mast_buff_bonus][self.mastery_buff]
        bonus_mastery += 125 * self.food_wod_mastery_125 * [1, 2][race]
        bonus_mastery += 100 * self.food_wod_mastery * [1, 2][race]
        bonus_mastery += 75 * self.food_wod_mastery_75 * [1, 2][race]
        bonus_mastery += 450 * self.food_wod_mastery_450 * [1, 2][race]
        bonus_mastery += 600 * self.food_wod_mastery_600 * [1, 2][race]
        bonus_mastery += 700 * self.food_wod_mastery_700 * [1, 2][race]
        return bonus_mastery
    
    def buff_versatility(self, race=False):
        bonus_versatility = 0
        bonus_versatility += 125 * self.food_wod_versatility_125 * [1, 2][race]
        bonus_versatility += 100 * self.food_wod_versatility * [1, 2][race]
        bonus_versatility += 75 * self.food_wod_versatility_75 * [1, 2][race]
        bonus_versatility += 450 * self.food_wod_versatility_450 * [1, 2][race]
        bonus_versatility += 600 * self.food_wod_versatility_600 * [1, 2][race]
        bonus_versatility += 700 * self.food_wod_versatility_700 * [1, 2][race]
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
