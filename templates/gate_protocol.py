"""Illustrative Gate decision protocol with embedded standard-library tests.

This example consumes sanitized JSON and prints a decision. It performs no
network or file access, stores no state, and contains no credentials.
"""
import json
import sys
import unittest


REQUIRED_FIELDS = {
    "source_available",
    "latest_marker",
    "last_read_marker",
    "last_organized_marker",
}


class GateInputError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def validate(status: object) -> dict:
    if not isinstance(status, dict):
        raise GateInputError("invalid_type", "input must be a JSON object")

    missing = sorted(REQUIRED_FIELDS - status.keys())
    extra = sorted(status.keys() - REQUIRED_FIELDS)
    if missing:
        raise GateInputError("missing_fields", "required fields are missing")
    if extra:
        raise GateInputError("unexpected_fields", "input contains unsupported fields")

    if type(status["source_available"]) is not bool:
        raise GateInputError("invalid_source_available", "source_available must be boolean")

    for field in ("latest_marker", "last_read_marker", "last_organized_marker"):
        marker = status[field]
        if marker is not None and (
            not isinstance(marker, str) or not marker.strip()
        ):
            raise GateInputError(
                "invalid_marker",
                field + " must be a non-empty string or null",
            )

    return status


def decide(status: object) -> dict:
    status = validate(status)

    if status["source_available"] is not True:
        raise GateInputError("source_unavailable", "data source is unavailable")

    latest = status["latest_marker"]
    last_read = status["last_read_marker"]
    last_organized = status["last_organized_marker"]

    # A readable empty source cannot be reconciled with existing checkpoints.
    if latest is None and (last_read is not None or last_organized is not None):
        raise GateInputError(
            "source_checkpoint_mismatch",
            "empty source marker conflicts with a non-empty checkpoint",
        )

    # Organization backlog takes precedence over unread source when both exist.
    if last_read != last_organized:
        return {
            "status": "ok",
            "wakeAgent": True,
            "reason": "organization_backlog",
        }

    if latest != last_read:
        return {
            "status": "ok",
            "wakeAgent": True,
            "reason": "unread_source",
        }

    return {
        "status": "ok",
        "wakeAgent": False,
        "reason": "no_change_detected",
    }


class GateProtocolTests(unittest.TestCase):
    def test_no_change(self):
        result = decide({
            "source_available": True,
            "latest_marker": "item-2",
            "last_read_marker": "item-2",
            "last_organized_marker": "item-2",
        })
        self.assertEqual((result["wakeAgent"], result["reason"]),
                         (False, "no_change_detected"))

    def test_new_message_not_collected(self):
        result = decide({
            "source_available": True,
            "latest_marker": "item-3",
            "last_read_marker": "item-2",
            "last_organized_marker": "item-2",
        })
        self.assertEqual((result["wakeAgent"], result["reason"]),
                         (True, "unread_source"))

    def test_organization_backlog(self):
        result = decide({
            "source_available": True,
            "latest_marker": "item-3",
            "last_read_marker": "item-3",
            "last_organized_marker": "item-2",
        })
        self.assertEqual((result["wakeAgent"], result["reason"]),
                         (True, "organization_backlog"))

    def test_unread_and_organization_backlog_prefers_backlog(self):
        result = decide({
            "source_available": True,
            "latest_marker": "item-4",
            "last_read_marker": "item-3",
            "last_organized_marker": "item-2",
        })
        self.assertEqual((result["wakeAgent"], result["reason"]),
                         (True, "organization_backlog"))

    def test_unavailable_source_is_error(self):
        with self.assertRaises(GateInputError) as context:
            decide({
                "source_available": False,
                "latest_marker": None,
                "last_read_marker": None,
                "last_organized_marker": None,
            })
        self.assertEqual(context.exception.code, "source_unavailable")

    def test_missing_field_is_error(self):
        with self.assertRaises(GateInputError) as context:
            decide({
                "source_available": True,
                "latest_marker": None,
                "last_read_marker": None,
            })
        self.assertEqual(context.exception.code, "missing_fields")

    def test_malformed_field_is_error(self):
        with self.assertRaises(GateInputError) as context:
            decide({
                "source_available": "yes",
                "latest_marker": None,
                "last_read_marker": None,
                "last_organized_marker": None,
            })
        self.assertEqual(context.exception.code, "invalid_source_available")

    def test_valid_empty_source(self):
        result = decide({
            "source_available": True,
            "latest_marker": None,
            "last_read_marker": None,
            "last_organized_marker": None,
        })
        self.assertEqual((result["wakeAgent"], result["reason"]),
                         (False, "no_change_detected"))

    def test_null_latest_and_matching_nonempty_checkpoints_is_mismatch(self):
        with self.assertRaises(GateInputError) as context:
            decide({
                "source_available": True,
                "latest_marker": None,
                "last_read_marker": "item-7",
                "last_organized_marker": "item-7",
            })
        self.assertEqual(context.exception.code, "source_checkpoint_mismatch")

    def test_null_latest_and_different_checkpoints_is_mismatch_first(self):
        with self.assertRaises(GateInputError) as context:
            decide({
                "source_available": True,
                "latest_marker": None,
                "last_read_marker": "item-7",
                "last_organized_marker": "item-6",
            })
        self.assertEqual(context.exception.code, "source_checkpoint_mismatch")


def main() -> int:
    if sys.argv[1:] == ["--self-test"]:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(GateProtocolTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1

    try:
        status = json.load(sys.stdin)
    except json.JSONDecodeError:
        error = GateInputError("invalid_json", "input is not valid JSON")
    else:
        try:
            result = decide(status)
        except GateInputError as exc:
            error = exc
        else:
            print(json.dumps(result, ensure_ascii=False))
            return 0

    # Error output deliberately has no wakeAgent field. The scheduler must
    # treat the non-zero exit code and status=error as a failed Gate run.
    print(json.dumps({
        "status": "error",
        "error": error.code,
        "message": error.message,
    }, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())