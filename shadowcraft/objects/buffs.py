from shadowcraft.core import exceptions

class InvalidBuffException(exceptions.InvalidInputException):
    pass


class Buffs(object):

    allowed_buffs = frozenset([
        'short_term_haste_buff',           # Heroism/Blood Lust, Time Warp
        'stat_multiplier_buff',            # Mark of the Wild, Blessing of Kings, Legacy of the Emperor
        'crit_chance_buff',                # Leader of the Pack, Legacy of the White Tiger, Arcane Brillance
        'haste_buff',                      # Swiftblade's Cunning, Unholy Aura
        'multistrike_buff',                # Swiftblade's Cunning, ...
        'attack_power_buff',               # Horn of Winter, Trueshot Aura, Battle Shout
        'mastery_buff',                    # Blessing of Might, Grace of Air
        'stamina_buff',                    # PW: Fortitude, Blood Pact, Commanding Shout
        'versatility_buff',                #
        'spell_power_buff',                # Dark Intent, Arcane Brillance
        #'armor_debuff',                     # Sunder, Expose Armor, Faerie Fire
        'physical_vulnerability_debuff',    # Brittle Bones, Ebon Plaguebringer, Judgments of the Bold, Colossus Smash
        'spell_damage_debuff',              # Master Poisoner, Curse of Elements
        #'slow_casting_debuff',
        'mortal_wounds_debuff',
        'agi_flask_mop',                    # Flask of Spring Blossoms
        'food_mop_agi',                     # Sea Mist Rice Noodles
        'flask_wod_mastery',                #
        'food_wod_mastery',                 #
    ])
    
    buffs_debuffs = frozenset([
        'short_term_haste_buff',            # Heroism/Blood Lust, Time Warp
        'stat_multiplier_buff',             # Mark of the Wild, Blessing of Kings, Legacy of the Emperor
        'crit_chance_buff',                 # Leader of the Pack, Legacy of the White Tiger, Arcane Brillance
        'haste_buff',                       # Swiftblade's Cunning, Unholy Aura
        'multistrike_buff',                 # Swiftblade's Cunning, ...
        'attack_power_buff',                # Horn of Winter, Trueshot Aura, Battle Shout
        'mastery_buff',                     # Blessing of Might, Grace of Air
        'spell_power_buff',                 # Dark Intent, Arcane Brillance
        'versatility_buff',
        'stamina_buff',                     # PW: Fortitude, Blood Pact, Commanding Shout
        'physical_vulnerability_debuff',    # Brittle Bones, Ebon Plaguebringer, Judgments of the Bold, Colossus Smash
        'spell_damage_debuff',              # Master Poisoner, Curse of Elements
        'mortal_wounds_debuff',
    ])

    buff_scaling = {80: 91, 85: 102, 90: 118, 100: 458}

    def __init__(self, *args, **kwargs):
        for buff in args:
            if buff not in self.allowed_buffs:
                raise InvalidBuffException(_('Invalid buff {buff}').format(buff=buff))
            setattr(self, buff, True)
        self.level = kwargs.get('level', 85)

    def __getattr__(self, name):
        # Any buff we haven't assigned a value to, we don't have.
        if name in self.allowed_buffs:
            return False
        object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'level':
            self._set_constants_for_level()

    def _set_constants_for_level(self):
        try:
            self.mast_buff_bonus = round(1.7545000315 * self.buff_scaling[self.level])
        except KeyError as e:
            raise exceptions.InvalidLevelException(_('No conversion factor available for level {level}').format(level=self.level))
    
    def get_max_buffs(self):
        return frozenset(buffs_debuffs + ['food_300_agi', 'agi_flask_mop'])

    def stat_multiplier(self):
        return [1, 1.05][self.stat_multiplier_buff]

    def spell_damage_multiplier(self):
        return [1, 1.08][self.spell_damage_debuff]

    def physical_damage_multiplier(self):
        return [1, 1.05][self.physical_vulnerability_debuff]

    def bleed_damage_multiplier(self):
        return self.physical_damage_multiplier()

    def attack_power_multiplier(self):
        return [1, 1.1][self.attack_power_buff]

    def haste_multiplier(self):
        return [1, 1.05][self.haste_buff]
    
    def versatility_bonus(self):
        return [0, 0.03][self.versatility_buff]
    
    def buff_all_crit(self):
        return [0, .05][self.crit_chance_buff]

    def multistrike_bonus(self):
        return [0, 0.05][self.multistrike_buff]
    
    #stat buffs
    def buff_str(self, race=False):
        return 0

    def buff_agi(self, race=False):
        bonus_agi = 0
        bonus_agi += 114 * self.agi_flask_mop
        bonus_agi += 34 * self.food_mop_agi * [1, 2][race]
        return bonus_agi
    
    def buff_haste(self, race=False):
        return 0
    
    def buff_crit(self, race=False):
        return 0
    
    def buff_mast(self, race=False):
        bonus_mastery = 0
        bonus_mastery += [0, self.mast_buff_bonus][self.mastery_buff]
        bonus_mastery += 500 * self.flask_wod_mastery
        bonus_mastery += 125 * self.food_wod_mastery * [1, 2][race]
        return bonus_mastery
    
    def buff_versatility(self, race=False):
        return 0
    
    def buff_multistrike(self, race=False):
        return 0
    
    def buff_readiness(self, race=False):
        return 0
