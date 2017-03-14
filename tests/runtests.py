from __future__ import absolute_import
import unittest
from os import path
import sys
sys.path.append(path.abspath(path.dirname(__file__)))
sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))

from calcs_tests import TestDamageCalculator
from calcs_tests.rogue_tests import TestOutlawRogueDamageCalculator
from calcs_tests.rogue_tests import TestAssassinationRogueDamageCalculator
from calcs_tests.rogue_tests import TestSubtletyRogueDamageCalculator
from calcs_tests.rogue_tests import TestAOEOutlawRogueDamageCalculator
from calcs_tests.rogue_tests import TestAOEAssassinationRogueDamageCalculator
from calcs_tests.rogue_tests import TestAOESubtletyRogueDamageCalculator
from core_tests.exceptions_tests import TestInvalidInputException
from objects_tests.buffs_tests import TestBuffsTrue, TestBuffsFalse
from objects_tests.stats_tests import TestStats, TestGearBuffs
from objects_tests.procs_tests import TestProcsList, TestProc
from objects_tests.race_tests import TestRace
from objects_tests.rogue_tests.rogue_talents_tests import TestAssassinationTalents
from objects_tests.rogue_tests.rogue_talents_tests import TestCombatTalents
from objects_tests.rogue_tests.rogue_talents_tests import TestSubtletyTalents
from objects_tests.rogue_tests.rogue_talents_tests import TestRogueTalents

if __name__ == "__main__":
    unittest.main()
