from shadowcraft.core import exceptions
from shadowcraft.objects import artifact_data

class InvalidTraitException(exceptions.InvalidInputException):
    pass

class Artifact(object):
    def __init__(self, class_spec, game_class, trait_string='', trait_dict= {}):
        self.allowed_traits = artifact_data.traits[(game_class, class_spec)]
        self.single_rank_traits = artifact_data.single_rank[(game_class, class_spec)]

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

    def set_trait(self, trait, value):
        if trait not in self.allowed_traits:
            raise InvalidTraitException(_('Invalid trait name {trait}').format(trait=trait))
        self.traits[trait] = value

    def initialize_traits(self, trait_string):
        if len(trait_string) != len(self.allowed_traits):
            raise InvalidTraitException(_('Trait strings must be {traits} characters long').format(traits=len(self.allowed_traits)))
        self.traits = {}
        for trait in xrange(len(self.allowed_traits)):
            self.set_trait(self.allowed_traits[trait], int(trait_string[trait]))

    def get_trait_list(self):
        return list(self.allowed_traits)

    def get_single_rank_trait_list(self):
        return list(self.single_rank_traits)