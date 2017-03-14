import unittest
from shadowcraft.objects import procs

class TestProcsList(unittest.TestCase):
    def setUp(self):
        self.procsList = procs.ProcsList('fury_of_xuen','legendary_capacitive_meta')

    def test__init__(self):
        self.assertRaises(procs.InvalidProcException, procs.ProcsList, 'fake_proc')
        self.procsList = procs.ProcsList('fury_of_xuen')
        self.assertEqual(len(self.procsList.get_all_procs_for_stat(stat=None)), 1)

    def test__getattr__(self):
        self.assertRaises(AttributeError, self.procsList.__getattr__, 'fake_proc')
        self.assertTrue(self.procsList.fury_of_xuen)
        self.assertFalse(self.procsList.touch_of_the_grave)

    def test_get_all_procs_for_stat(self):
        self.assertEqual(len(self.procsList.get_all_procs_for_stat(stat=None)), 2)
        self.procsList = procs.ProcsList()
        self.assertEqual(len(self.procsList.get_all_procs_for_stat(stat=None)), 0)

    def test_get_all_damage_procs(self):
        self.assertEqual(len(self.procsList.get_all_damage_procs()), 2)
        self.procsList = procs.ProcsList()
        self.assertEqual(len(self.procsList.get_all_damage_procs()), 0)


class TestProc(unittest.TestCase):
    def setUp(self):
        self.proc = procs.Proc(**procs.ProcsList.allowed_procs['bloodthirsty_instinct'])

    def test__init__(self):
        self.assertEqual(self.proc.stat, 'stats')
        self.assertEqual(self.proc.value['haste'], 2880)
        self.assertEqual(self.proc.duration, 10)
        self.assertEqual(self.proc.proc_rate, 3)
        self.assertEqual(self.proc.trigger, 'all_attacks')
        self.assertEqual(self.proc.icd, 0)
        self.assertEqual(self.proc.max_stacks, 1)
        self.assertEqual(self.proc.on_crit, False)
        self.assertEqual(self.proc.proc_name, 'Bloodthirsty Instinct')

    def test_procs_off_auto_attacks(self):
        self.assertTrue(self.proc.procs_off_auto_attacks())

    def test_procs_off_strikes(self):
        self.assertTrue(self.proc.procs_off_strikes())

    def test_procs_off_harmful_spells(self):
        self.assertFalse(self.proc.procs_off_harmful_spells())

    def test_procs_off_heals(self):
        self.assertFalse(self.proc.procs_off_heals())

    def test_procs_off_periodic_spell_damage(self):
        self.assertFalse(self.proc.procs_off_periodic_spell_damage())

    def test_procs_off_periodic_heals(self):
        self.assertFalse(self.proc.procs_off_periodic_heals())

    def test_procs_off_apply_debuff(self):
        self.assertTrue(self.proc.procs_off_apply_debuff())

    def test_procs_off_bleeds(self):
        self.assertFalse(self.proc.procs_off_bleeds())

    def test_procs_off_crit_only(self):
        self.assertFalse(self.proc.procs_off_crit_only())

    def test_is_ppm(self):
        self.assertFalse(self.proc.is_ppm())
