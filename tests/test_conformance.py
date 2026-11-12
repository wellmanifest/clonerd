import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "conformance", ROOT / "standard/conformance.py"
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ConformanceTests(unittest.TestCase):
    def test_canonical_profile(self):
        c.validate(c.read(ROOT / "profiles/clonerd.v1.json"))

    def test_validator_cache_reuses_compiled_validators(self):
        first = c._validator("schemas/profile.schema.json")
        second = c._validator("schemas/profile.schema.json")
        self.assertIs(first, second)

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

    def test_duplicate_keys_and_nonfinite_constants_rejected(self):
        with self.assertRaises(ValueError):
            c.unique_object([("schema", "good"), ("schema", "bad")])
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for payload in ('{"x": NaN}', '{"x": Infinity}', '{"x": -Infinity}'):
                sample = tmp_path / "bad.json"
                sample.write_text(payload, encoding="utf-8")
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    c.read(sample)

    def test_read_rejects_symlinks_directories_and_oversized_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            real_file = tmp_path / "real.json"
            real_file.write_text('{"ok": true}', encoding="utf-8")
            link_file = tmp_path / "link.json"
            link_file.symlink_to(real_file)
            with self.assertRaisesRegex(ValueError, "CLONERD-IO-001"):
                c.read(link_file)
            with self.assertRaisesRegex(ValueError, "CLONERD-IO-002"):
                c.read(tmp_path)
            huge_file = tmp_path / "huge.json"
            huge_file.write_bytes(b" " * (c.MAX_JSON_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "CLONERD-IO-003"):
                c.read(huge_file)

    def test_all_modes_and_session_states(self):
        expected = {
            (False, "demo"): "anonymous",
            (False, "user"): "anonymous",
            (False, "auto"): "anonymous",
            (True, "demo"): "demo",
            (True, "user"): "authenticated",
            (True, "auto"): "auto",
        }
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

    def test_owned_python_modules_stay_under_500_lines(self):
        for relpath in ("standard/conformance.py", "tests/test_conformance.py"):
            lines = (ROOT / relpath).read_text(encoding="utf-8").splitlines()
            self.assertLess(len(lines), 500, relpath)


class EnvironmentTests(unittest.TestCase):
    def example(self):
        return c.read(ROOT / "profiles/environment.example.json")

    def test_local_and_remote_examples(self):
        c.validate_environment(self.example())
        for kind in ("existing-service", "self-hosted"):
            p = self.example()
            p["deployment"] = kind
            p["endpoints"] = {
                "api": "https://api.example.org",
                "identity": "https://accounts.example.org",
            }
            p["auth"] = {"method": "device-token", "tokenEnv": "MY_DEVICE_TOKEN"}
            c.validate_environment(p)
        intranet = self.example()
        intranet["deployment"] = "self-hosted"
        intranet["endpoints"] = {
            "api": "https://10.20.30.40:8443",
            "identity": "https://10.20.30.41:8443",
        }
        c.validate_environment(intranet)

    def test_invalid_urls_and_secrets_rejected(self):
        for url in (
            "https://user:secret@example.org",
            "http://example.org",
            "file:///tmp/a",
            "http://localhost:8891/v1",
            "http://localhost:8891?token=secret",
        ):
            p = self.example()
            p["endpoints"]["api"] = url
            with (
                self.subTest(url=url),
                self.assertRaises((ValueError, ValidationError)),
            ):
                c.validate_environment(p)
        for url in (
            "http://localhost:0",
            "http://localhost:99999",
            "http://localhost:bad",
            "http://localhost:8891\n",
        ):
            p = self.example()
            p["endpoints"]["api"] = url
            with self.subTest(url=url), self.assertRaises(ValueError):
                c.validate_environment(p)
        for auth in (
            {"method": "device-token"},
            {"method": "device-token", "tokenEnv": "real-secret-value"},
            {"method": "user-session", "password": "secret"},
        ):
            p = self.example()
            p["auth"] = auth
            with self.assertRaises(ValidationError):
                c.validate_environment(p)

    def test_remote_http_loopback_link_local_and_shared_cookie_host_rejected(self):
        p = self.example()
        p["deployment"] = "self-hosted"
        with self.assertRaises(ValueError):
            c.validate_environment(p)
        for unsafe_origin in (
            "https://localhost:8443",
            "https://sub.localhost:8443",
            "https://127.0.0.1:8443",
            "https://[::1]:8443",
            "https://0.0.0.0:8443",
            "https://169.254.169.254",
            "https://[fe80::1]:8443",
            "https://[::ffff:127.0.0.1]:8443",
            "https://[::ffff:0.0.0.0]:8443",
            "https://[::ffff:169.254.169.254]:8443",
            "https://[::ffff:224.0.0.1]:8443",
        ):
            p = self.example()
            p["deployment"] = "existing-service"
            p["endpoints"] = {
                "api": unsafe_origin,
                "identity": "https://accounts.example.org",
            }
            with (
                self.subTest(origin=unsafe_origin),
                self.assertRaisesRegex(ValueError, "CLONERD-ENV-006"),
            ):
                c.validate_environment(p)
        p = self.example()
        p["endpoints"]["device"] = "http://localhost:8790"
        with self.assertRaises(ValueError):
            c.validate_environment(p)

    def test_missing_pin_and_unknown_option_rejected(self):
        for key, value in (("sourceRevision", "main"), ("secret", "do-not-store")):
            p = self.example()
            p[key] = value
            with self.assertRaises(ValidationError):
                c.validate_environment(p)

    def test_ticket_004_parent_symlinks_float_overflow_surrogates_and_cookie_host_aliases(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            real_dir = tmp_path / "real_dir"
            real_dir.mkdir()
            real_file = real_dir / "doc.json"
            real_file.write_text('{"ok": true}', encoding="utf-8")
            sym_dir = tmp_path / "sym_dir"
            sym_dir.symlink_to(real_dir)

            for symlink_path in (
                sym_dir / "doc.json",
                Path(str(sym_dir) + "/../real_dir/doc.json"),
            ):
                with (
                    self.subTest(path=str(symlink_path)),
                    self.assertRaisesRegex(ValueError, "CLONERD-IO-001"),
                ):
                    c.read(symlink_path)
            with self.assertRaisesRegex(ValueError, "CLONERD-IO-002"):
                c.read(str(real_file) + "\x00evil")

            for bad_json, code in (
                ('{"x": 1e309}', "CLONERD-PROFILE-004"),
                ('{"x": -1e309}', "CLONERD-PROFILE-004"),
                ('{"x": "\\ud800"}', "CLONERD-PROFILE-005"),
                ('{"\\udfff": 1}', "CLONERD-PROFILE-005"),
            ):
                bad_path = real_dir / "bad_payload.json"
                bad_path.write_text(bad_json, encoding="utf-8")
                with (
                    self.subTest(payload=bad_json),
                    self.assertRaisesRegex(ValueError, code),
                ):
                    c.read(bad_path)

        # DEL and C1 control characters in URLs are rejected
        for ctrl_url in ("http://localhost:8891\x7f", "http://localhost:8891\x85"):
            p = self.example()
            p["endpoints"]["api"] = ctrl_url
            with (
                self.subTest(ctrl_url=repr(ctrl_url)),
                self.assertRaises((ValueError, ValidationError)),
            ):
                c.validate_environment(p)

        # Broadcast/reserved IPs are rejected for remote service endpoints while intranet 10.x stays allowed
        for reserved_origin in (
            "https://255.255.255.255:8443",
            "https://[::ffff:255.255.255.255]:8443",
        ):
            p = self.example()
            p["deployment"] = "self-hosted"
            p["endpoints"] = {
                "api": reserved_origin,
                "identity": "https://accounts.example.org",
            }
            with (
                self.subTest(origin=reserved_origin),
                self.assertRaisesRegex(ValueError, "CLONERD-ENV-006"),
            ):
                c.validate_environment(p)

        # Uncompressed IPv6 loopback alias and trailing-dot localhost cannot bypass separate simulator cookie hostnames
        for id_origin, dev_origin in (
            ("http://[::1]:8790", "http://[0:0:0:0:0:0:0:1]:8791"),
            ("http://localhost.:8790", "http://localhost:8791"),
        ):
            p = self.example()
            p["endpoints"]["identity"] = id_origin
            p["endpoints"]["device"] = dev_origin
            with (
                self.subTest(pair=(id_origin, dev_origin)),
                self.assertRaisesRegex(ValueError, "CLONERD-ENV-005"),
            ):
                c.validate_environment(p)


if __name__ == "__main__":
    unittest.main()
