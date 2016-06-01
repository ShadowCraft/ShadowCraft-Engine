from shadowcraft.core import exceptions
from shadowcraft.objects import artifact_data

class InvalidTraitException(exceptions.InvalidInputException):
    pass

class Artifact(object):
    def __init__(self, class_spec, game_class, trait_string='', trait_dict= {}):
        self.allowed_traits = artifact_data.traits[(game_class, class_spec)]

        if trait_string:
            self.initialize_traits(trait_string)

        else:
            self.traits = {}
            for trait in self.allowed_traits:
                if trait in trait_dict:
                    self.traits[trait] = trait_dict[trait]
                else:
                    self.traits[trait] = 0


    def __getattr__(self, attr):
        if attr in self.traits:
            return self.traits[attr]
        return False

    def __setattr__(self, attr, value):
        if attr not in self.traits:
            raise InvalidTraitException(_('Invalid trait name {trait}').format(trait=attr))
        self.traits[attr] = value

    def initialize_traits(self, trait_string):
        if len(trait_string) != 18:
            raise InvalidTraitException(_('Trait strings must be 18 characters long'))
        self.traits = {}
        for trait in xrange(18):
            setattr(self, self.allowed_traits[trait], int(trait_string[trait]))

    def get_trait_list(self):
        return list(self.allowed_traits)