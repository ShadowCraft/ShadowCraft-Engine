from shadowcraft.core import exceptions

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

	def compile__modifier_dict(self):
		lumped_modifier = {s:1 for s in self.sources}
		for mod in self.modifiers.values():
			if mod.whitelist:
				for ability in mod.ability_list:
					lumped_modifier[ability] *= mod.value
			if mod.blacklist:
				for ability in self.sources:
					if not ability in mod.ability_list:
						lumped_modifier[ability] *= mod.value
		return lumped_modifier

class DamageModifier(object):
	def __init__(self, name, value, ability_list, whitelist=True, blacklist=False):
		if not (whitelist ^ blacklist):
			raise exceptions.InvalidInputException(_('Damage Modifier {mod} must be either a blacklist or whitelist').format(mod=name))
		self.name = name
		self.value = value
		self.ability_list = ability_list
		self.blacklist = blacklist
		self.whitelist = whitelist

