import unittest
from shadowcraft.objects.talents import Talents
from shadowcraft.objects.talents import InvalidTalentException

class TestAssassinationTalents(unittest.TestCase):
    # Tests for the abstract class objects.talents.TalentTree
    def setUp(self):
        self.talents = Talents('1231231', 'assassination', 'rogue')

    def test__getattr__(self):
        self.assertRaises(AttributeError, self.talents.__getattr__, 'fake_talent')
        self.assertEqual(self.talents.master_poisoner, True)
        self.assertEqual(self.talents.nightstalker, False)

    def test_set_talent(self):
        self.assertRaises(InvalidTalentException, self.talents.set_talent, 'fake_talent')
        self.assertRaises(InvalidTalentException, self.talents.set_talent, 'vendetta')
        self.assertRaises(InvalidTalentException, self.talents.set_talent, 'vendetta')

class TestCombatTalents(unittest.TestCase):
    pass


class TestSubtletyTalents(unittest.TestCase):
    pass


class TestRogueTalents(unittest.TestCase):
    def setUp(self):
        self.talents = Talents('1231231', 'assassination', 'rogue')

    def test(self):
        self.assertEqual(self.talents.master_poisoner, 1)
        self.assertEqual(self.talents.subterfuge, 1)
        self.assertEqual(self.talents.vigor, 1)
        self.assertEqual(self.talents.cheat_death, 0)
        self.assertEqual(self.talents.thuggee, 0)