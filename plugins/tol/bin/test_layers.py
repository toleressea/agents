import tempfile
import unittest
from pathlib import Path

from layers import render, resolve

SHIPPED = """
extensible = ["lenses"]
[lenses.correctness]
instructions = "bugs"
[lenses.security]
instructions = "trust"
[verify]
rounds = 1
fix = "ask"
"""


class LayersTest(unittest.TestCase):
    def run_layers(self, user=None, repo=None):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "skill").mkdir()
            (d / "skill" / "config.toml").write_text(SHIPPED)
            for text, base in ((user, d / "home"), (repo, d / "repo")):
                if text is not None:
                    p = base / ".agents" / "config" / "tol" / "review.toml"
                    p.parent.mkdir(parents=True)
                    p.write_text(text)
            return render(*resolve("tol", "review", d / "skill", d / "repo", home=d / "home"))

    def test_shipped_only(self):
        out = self.run_layers()
        self.assertIn('lenses.security.instructions = "trust"  # shipped', out)
        self.assertNotIn("CONFIG ERROR", out)

    def test_layers_merge_in_order(self):
        out = self.run_layers(
            user='[lenses.correctness]\nskill = "x:review"\n[verify]\nrounds = 2',
            repo='[verify]\nrounds = 3\n[lenses]\nsecurity = "off"\n[lenses.perf]\ninstructions = "slow"',
        )
        self.assertIn('lenses.correctness.skill = "x:review"  # user', out)
        self.assertIn('lenses.correctness.instructions = "bugs"  # shipped', out)
        self.assertIn("verify.rounds = 3  # repo", out)
        self.assertIn("lenses.security = off  # repo (off)", out)
        self.assertNotIn('"trust"', out)
        self.assertIn('lenses.perf.instructions = "slow"  # repo', out)

    def test_off_is_a_value_for_scalars(self):
        out = self.run_layers(repo='[verify]\nfix = "off"')
        self.assertIn('verify.fix = "off"  # repo', out)

    def test_empty_string_unsets_a_binding_field(self):
        out = self.run_layers(repo='[lenses.correctness]\ninstructions = ""\nskill = "x:y"')
        self.assertNotIn("lenses.correctness.instructions", out)
        self.assertIn('lenses.correctness.skill = "x:y"  # repo', out)

    def test_unknown_key_and_bad_toml_are_reported(self):
        out = self.run_layers(user="[verfy]\nrounds = 2", repo="not = = toml")
        self.assertIn("CONFIG ERROR: user: unknown key `verfy`", out)
        self.assertIn("CONFIG ERROR:", out.split("unknown key")[1])


if __name__ == "__main__":
    unittest.main()
