import copy
import importlib.util
import unittest
from pathlib import Path

from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("conformance", ROOT / "standard/conformance.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ConformanceTests(unittest.TestCase):
    def test_canonical_profile(self):
        c.validate(c.read(ROOT / "profiles/clonerd.v1.json"))

    def test_unsafe_profile_mutations_rejected(self):
        cases = [
            ("presentation", "anonymous", "#21efad"),
            ("presentation", "demo", "#21efad"),
            ("presentation", "auto", "#21efad"),
            ("presentation", "authorityFromPresentation", True),
            ("isolation", "demoEffects", "allowed"),
            ("isolation", "tenantScope", "client-only"),
            ("isolation", "cloudLocalFallback", "allowed"),
            ("isolation", "secretsInReceipts", "allowed"),
            ("contracts", "projections", "hand-edited"),
            ("contracts", "nlOutput", "execution-grant"),
            ("delivery", "selfApproval", True),
            ("delivery", "administrativeBypass", True),
            ("delivery", "requiredAppChecks", ["onedev/local-verify"]),
            ("delivery", "subjectBinding", ["head"]),
            ("continuation", "timeoutTransfersOwnership", True),
            ("continuation", "expiredLease", "overwrite-file"),
        ]
        for section, key, value in cases:
            with self.subTest(section=section, key=key):
                p = copy.deepcopy(c.read(ROOT / "profiles/clonerd.v1.json"))
                p[section][key] = value
                with self.assertRaises(ValidationError):
                    c.validate(p)

    def test_missing_and_unknown_fields_rejected(self):
        for mutation in ("missing", "extra"):
            p = c.read(ROOT / "profiles/clonerd.v1.json")
            if mutation == "missing":
                del p["continuation"]
            else:
                p["approval"] = "self-issued"
            with self.assertRaises(ValidationError):
                c.validate(p)

    def test_duplicate_keys_rejected(self):
        with self.assertRaises(ValueError):
            c.unique_object([("schema", "good"), ("schema", "bad")])

    def test_all_modes_and_session_states(self):
        expected = {(False, "demo"): "anonymous", (False, "user"): "anonymous",
                    (False, "auto"): "anonymous", (True, "demo"): "demo",
                    (True, "user"): "authenticated", (True, "auto"): "auto"}
        for args, state in expected.items():
            with self.subTest(args=args):
                self.assertEqual(c.presentation(*args)["state"], state)
                self.assertIs(c.presentation(*args)["grantsAuthority"], False)
        self.assertEqual(c.presentation(False, "auto")["accent"], "#22d3ee")
        self.assertEqual(c.presentation(True, "demo")["accent"], "#22d3ee")

    def test_invalid_inputs_rejected(self):
        for args in [("false", "user"), (1, "auto"), (True, "admin"), (False, None)]:
            with self.assertRaises(ValueError):
                c.presentation(*args)


if __name__ == "__main__":
    unittest.main()
