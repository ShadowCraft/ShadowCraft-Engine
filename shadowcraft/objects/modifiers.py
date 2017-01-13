from shadowcraft.core import exceptions

#ModifierList contains all modifiers needed for dps computation.
#ModifierList is used to compile all modifiers into a single lumped modifier per damage source.
#Typical use case registers all modifiers needed at the beginning of the computation with a
#None value and then updates later.
#Before final damage computation a dict is compiled and used for damage computation
class ModifierList(object):
	def __init__(self, sources):
		self.sources = sources
		self.modifiers = {}

	def register_modifier(self, modifier):
		self.modifiers[modifier.name] = modifier
		for ability in modifier.ability_list:
			if ability not in self.sources:
				raise exceptions.InvalidInputException(_('Unknown source {source} in damage modifier {mod}').format(source=ability, mod=modifier.name))

	def update_modifier_value(self, modifier_name, value):
		self.modifiers[modifier_name].value = value

	def compile_modifier_dict(self):
		lumped_modifier = {s:1 for s in self.sources}
		for mod in self.modifiers.values():
			if mod.value is None:
				raise exceptions.InvalidInputException(_('Modifier {mod} is uninitialized').format(mod=mod.name))
			if not mod.blacklist:
				for ability in mod.ability_list:
					lumped_modifier[ability] *= mod.value
			else:
				for ability in self.sources:
					if not ability in mod.ability_list:
						lumped_modifier[ability] *= mod.value
		return lumped_modifier

#DamageModifier specifies any type of modifier applied to ability damage.
#Each modifier is specified as a value applied to either a whitelist or blacklist of abilities.
#Whitelist is default since it is more compact for most modifiers
#but all damage modifiers can be represented either way
class DamageModifier(object):
	def __init__(self, name, value, ability_list, blacklist=False):
		self.name = name
		self.value = value
		self.ability_list = ability_list
		self.blacklist = blacklist

