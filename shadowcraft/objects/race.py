from builtins import map
from builtins import zip
from builtins import object
from shadowcraft.core import exceptions

import gettext
_ = gettext.gettext

class InvalidRaceException(exceptions.InvalidInputException):
    pass

class Race(object):
    rogue_base_stats = {
         1: (  14,   15,   11,    8,   6),
        80: ( 256,  273,  189,  151, 113),
        85: ( 288,  306,  212,  169, 127),
        90: ( 339,  361,  250,  200, 150),
        100:(1206, 1284,  890,  711, 533),
        110:(8481, 9030, 6259, 5000,   0),
    }

    #(ap,sp)
    blood_fury_bonuses = {
        80: {'ap': 20, 'sp': 20},
        85: {'ap': 30, 'sp': 30},
        90: {'ap': 50, 'sp': 50},
        100:{'ap': 120, 'sp': 120},
        110:{'ap':2243, 'sp': 2243},
    }
    touch_of_the_grave_bonuses = {
        80: {'spell_damage': 200},
        90: {'spell_damage': 400},
        100:{'spell_damage': 1000},
        #TODO: CHECK
        110:{'spell_damage': 1000},
    }

    #Arguments are ap, spellpower:fire, and int
    #This is the formula according to wowhead, with a probable typo corrected
    def calculate_rocket_barrage(self, ap, spfi, int):
        return 1 + 0.25 * ap + .429 * spfi + self.level * 2 + int * 0.50193

    racial_stat_offset = {
                       #str,agi,sta,int,spi
        "human":        ( 0,  0,  0,  0,  0),
        "dwarf":        ( 5, -4,  1, -1, -1),
        "night_elf":    (-4,  4,  0,  0,  0),
        "gnome":        (-5,  2,  0,  3,  0),
        "draenei":      ( 1, -3,  0,  0,  2),
        "worgen":       ( 3,  2,  0, -4, -1),
        "pandaren":     ( 0, -2,  1, -1,  2),
        "orc":          ( 3, -3,  1, -3,  2),
        "undead":       (-1, -2,  0, -2,  5),
        "tauren":       ( 5, -4,  1, -4,  2),
        "troll":        ( 1,  2,  0, -4,  1),
        "blood_elf":    (-3,  2,  0,  3, -2),
        "goblin":       (-3,  2,  0,  3, -2),
        "none":         ( 0,  0,  0,  0,  0),
    }

    allowed_racials = frozenset([
        "heroic_presence",          #Draenei (+x to primary stat)
        "might_of_the_mountain",    #Dwarf (2% crit damage/healing)
        "expansive_mind",           #Gnome (+5% Max Mana, Energy, Rage, or Runic Power)
        "nimble_fingers",           #Gnome (1% haste)
        "human_spirit",             #Human (+X Versatility)
        "quickness",                #Night Elf
        "touch_of_elune",           #Night Elf (1% haste at night, 1% crit at day)
        "shadowmeld",               #Night Elf
        "viciousness",              #Worgen (1% crit chance)
        "blood_fury_physical",      #Orc (+x AP for n seconds every 2min)
        "blood_fury_spell",         #Orc
        "endurance",                #Tauren (+x stam)
        "brawn",                    #Tauren (+2% crit damage/healing)
        "berserking",               #Troll (15% haste for 10s every 3min)
        "arcane_acuity",            #Blood Elf (1% crit chance)
        "arcane_torrent",           #Blood Elf (20 Runic Power, or 1HoPo, or 3% Mana, x chi, x energy)
        "rocket_barrage",           #Goblin (x magic damage every n min)
        "time_is_money",            #Goblin (1% haste)
        "epicurean",                #Pandaren (doubles food buff)
        "touch_of_the_grave",       #Undead (shadow damage chance to proc)
    ])

    activated_racial_data = {
        #Blood fury values are set when level is set
        'blood_fury_physical':      {'stat': "ap", 'value': 0, 'duration': 15, 'cooldown': 120},    #level-based ap increase
        'blood_fury_spell':         {'stat': "sp", 'value': 0, 'duration': 15, 'cooldown': 120},                           #level-based sp increase
        'berserking':               {'stat': "haste_multiplier", 'value': 1.15, 'duration': 10, 'cooldown': 180},          #15% haste increase for 10 seconds, 3 minute cd
        'arcane_torrent':           {'stat': "energy", 'value': 15, 'duration': 0, 'cooldown': 120},                       #gain 15 energy (or 15 runic power or 6% mana), 2 minute cd
        'rocket_barrage':           {'stat': "damage", 'value': calculate_rocket_barrage, 'duration': 0, 'cooldown': 120}, #deal formula-based damage, 2 min cd
    }

    racials_by_race = {
        "human":        ["human_spirit"],
        "night_elf":    ["quickness", "touch_of_elune", "shadowmeld"],
        "dwarf":        ["stoneform", "might_of_the_mountain"],
        "gnome":        ["expansive_mind", "nimble_fingers"], #TODO: Expansive Mind (multiplicative? or just +5?)
        "draenei":      ["heroic_presence"],
        "worgen":       ["viciousness"],
        "orc":          ["blood_fury_physical", "blood_fury_spell"],
        "undead":       ["touch_of_the_grave", "cannibalize"],
        "tauren":       ["endurance", "brawn"],
        "troll":        ["berserking"],
        "blood_elf":    ["arcane_torrent", "arcane_acuity"],
        "goblin":       ["rocket_barrage", "time_is_money"],
        "pandaren":     ["epicurean"],
        "none":         [],
    }

    #Note this allows invalid class-race combos
    def __init__(self, race, character_class="rogue", level=85):
        self.character_class = str.lower(character_class)
        self.race_name = race
        if self.race_name not in list(Race.racial_stat_offset.keys()):
            raise InvalidRaceException(_('Unsupported race {race}').format(race=self.race_name))
        if self.character_class == "rogue":
            self.stat_set = Race.rogue_base_stats
        else:
            raise InvalidRaceException(_('Unsupported class {character_class}').format(character_class=self.character_class))
        self.level = level
        self.set_racials()

    def set_racials(self):
        # Set all racials, so we don't invoke __getattr__ all the time
        for race, racials in list(Race.racials_by_race.items()):
            for racial in racials:
                setattr(self, racial, False)
        for racial in Race.racials_by_race[self.race_name]:
            setattr(self, racial, True)
        setattr(self, "racial_str", self.stats[0])
        setattr(self, "racial_agi", self.stats[1])
        setattr(self, "racial_sta", self.stats[2])
        setattr(self, "racial_int", self.stats[3])
        setattr(self, "racial_spi", self.stats[4])

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'level':
            self._set_constants_for_level()

    def _set_constants_for_level(self):
        try:
            self.stats = self.stat_set[self.level]
            self.activated_racial_data["blood_fury_physical"]["value"] = self.blood_fury_bonuses[self.level]["ap"]
            self.activated_racial_data["blood_fury_spell"]["value"] = self.blood_fury_bonuses[self.level]["sp"]
            # this merges racial stats with class stats (ie, racial_stat_offset and rogue_base_stats)
            self.stats = list(map(sum, list(zip(self.stats, Race.racial_stat_offset[self.race_name]))))
            self.set_racials()
        except KeyError as e:
            raise InvalidRaceException(_('Unsupported class/level combination {character_class}/{level}').format(character_class=self.character_class, level=self.level))

    def __getattr__(self, name):
        # Any racial we haven't assigned a value to, we don't have.
        if name in self.allowed_racials:
            return False
        else:
            object.__getattribute__(self, name)

    def get_racial_crit(self, is_day=False):
        crit_bonus = 0
        if self.viciousness:
            crit_bonus = .01
        if self.touch_of_elune and is_day:
            crit_bonus = .01
        if self.arcane_acuity:
            crit_bonus = .01

        return crit_bonus

    def get_racial_haste(self, is_day=False):
        haste_bonus = 0
        if self.time_is_money:
            haste_bonus = .01
        if self.touch_of_elune and not is_day:
            haste_bonus = .01
        if self.nimble_fingers:
            haste_bonus = .01

        return haste_bonus

    def get_racial_stat_boosts(self):
        racial_boosts = []
        #Only the orc racial is a straight stat boost
        if getattr(self, "blood_fury_physical"):
            racial_boosts += [self.activated_racial_data["blood_fury_physical"], self.activated_racial_data["blood_fury_spell"]]
        return racial_boosts
