from shadowcraft.core.exceptions import InvalidLevelException

# tiered parameters for use in armor mitigation calculations. first tuple
# element is the minimum level of the tier. the tuples must be in descending
# order of minimum level for the lookup to work. parameters taken from
# http://code.google.com/p/simulationcraft/source/browse/branches/mop/engine/sc_player.cpp#1365
PARAMETERS = [ (91, 1938, 3610.0), #lvl 100 371830 3610.0
               (86, 1200, 317117.5), #lvl 90
               (81, 8000, 158167.5), #lvl 85
               (60, 4000,  22167.5),
               ( 1, 85.0,   -400.0) ] # yes, negative 400

def _get_appropriate_level_for_armor_table(level):
    for i in xrange(0, len(PARAMETERS)):
        if level >= PARAMETERS[i][0]:
            return i

def lookup_parameters(level):
    for parameters in PARAMETERS:
        if level >= parameters[0]:
            return parameters
    raise InvalidLevelException(_('No armor mitigation parameters available for level {level}').format(level=level))

def parameter(level=100):
    parameters = lookup_parameters(level)
    return level * parameters[1] - parameters[2]

# this is the fraction of damage reduced by the armor
def mitigation(armor, level=100, cached_parameter=None):
    if cached_parameter == None:
        cached_parameter = parameter(level)
        #cached_parameter = lookup_parameters(level)
    return armor / (armor + cached_parameter)

# this is the fraction of damage retained despite the armor, 1 - mitigation. 
def multiplier(armor, level=100, cached_parameter=None):
    if cached_parameter == None:
        cached_parameter = parameter(level)
    table_level = _get_appropriate_level_for_armor_table(level)
    return PARAMETERS[table_level][2] / (PARAMETERS[table_level][1] + PARAMETERS[table_level][2])