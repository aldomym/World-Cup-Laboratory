import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data import TEAMS
from engine import initial_state, simulate_qualifiers, perform_draw, simulate_final_tournament

class WorldCupEngineTests(unittest.TestCase):
    def test_team_catalog(self):
        self.assertEqual(len(TEAMS), 215)
        self.assertEqual(sum(t["isFifaMember"] for t in TEAMS), 211)
        extras = {t["name"] for t in TEAMS if not t["isFifaMember"]}
        self.assertEqual(extras, {"Greenland", "Northern Mariana Islands", "Tuvalu", "Marshall Islands"})

    def test_full_cycle(self):
        state = initial_state("test", "Test Cup", 2030, "mexico", 424242, "now")
        state = simulate_qualifiers(state)
        self.assertEqual(len(state["finalTeams"]), 48)
        self.assertEqual(len(set(state["finalTeams"])), 48)
        self.assertEqual(len(state["qualifiers"]["intercontinental"]["candidates"]), 6)
        self.assertEqual(len(state["qualifiers"]["intercontinental"]["winners"]), 2)

        state = perform_draw(state)
        self.assertEqual([len(p["teamIds"]) for p in state["pots"]], [12, 12, 12, 12])
        self.assertEqual(len(state["groups"]), 12)
        self.assertTrue(all(len(g["teamIds"]) == 4 for g in state["groups"]))

        state = simulate_final_tournament(state)
        self.assertEqual(len(state["tournament"]["groupMatches"]), 72)
        self.assertEqual(
            [len(r["matches"]) for r in state["tournament"]["knockoutRounds"]],
            [16, 8, 4, 2, 1]
        )
        self.assertIn(state["tournament"]["championId"], state["finalTeams"])

    def test_extra_team_can_host(self):
        state = initial_state("extra", "Tuvalu Cup", 2034, "tuvalu", 1234, "now")
        state = simulate_qualifiers(state)
        self.assertIn("tuvalu", state["finalTeams"])
        self.assertEqual(len(state["finalTeams"]), 48)

if __name__ == "__main__":
    unittest.main()
