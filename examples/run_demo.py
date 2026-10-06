"""Run a deterministic, fictional Flywheel workflow using only Python's stdlib.

Tested on Python 3.12.10; other versions are unverified. It reuses the decision function from
templates/gate_protocol.py. This demo creates a new output directory and never
reads real user data or connects to external services.
"""
import json
import os
from pathlib import Path
import sys
import tempfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "templates"))
from gate_protocol import GateInputError, decide  # noqa: E402


SYNTHETIC_MARKER = "synthetic-item-001"
COLLECTION_TEXT = (
    "# Fictional collection record\n\n"
    "> This is entirely fictional sample data.\n\n"
    "- marker: synthetic-item-001\n"
    "- observation: A fictional learner practiced a short exercise.\n"
)
ORGANIZED_TEXT = (
    "# Fictional organization result\n\n"
    "This deterministic summary was generated from the fictional sample.\n"
    "- collected marker: synthetic-item-001\n"
    "- status: one synthetic practice observation was recorded\n"
)


class VerificationError(Exception):
    """Raised when written demo content does not match its read-back."""


class DemoStore(object):
    """Minimal local text-file store used only inside the demo output folder."""

    def write_text(self, path, content):
        with open(str(path), "w", encoding="utf-8", newline="") as output:
            output.write(content)

    def read_text(self, path):
        with open(str(path), "r", encoding="utf-8", newline="") as source:
            return source.read()


class DemoWorkflow(object):
    def __init__(self, output_dir, store=None):
        self.output_dir = Path(output_dir)
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)
        if not self.output_dir.is_dir() or next(self.output_dir.iterdir(), None) is not None:
            raise FileExistsError("demo output directory must be new and empty")

        self.store = store or DemoStore()
        self.checkpoint_path = self.output_dir / "checkpoints.json"
        self.checkpoints = {
            "last_read_marker": None,
            "last_organized_marker": None,
        }
        self.events = []
        self._write_and_verify(self.checkpoint_path, self._checkpoint_text(self.checkpoints))

    @staticmethod
    def _checkpoint_text(checkpoints):
        return json.dumps(checkpoints, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    def _write_and_verify(self, path, expected):
        self.store.write_text(path, expected)
        actual = self.store.read_text(path)
        if actual != expected:
            raise VerificationError("read-back did not match written content: " + path.name)

    def _commit_checkpoints(self, candidate):
        """Verify a staged checkpoint before atomically replacing the old one."""
        staged_path = self.output_dir / ".checkpoints.json.tmp"
        expected = self._checkpoint_text(candidate)
        self._write_and_verify(staged_path, expected)
        os.replace(str(staged_path), str(self.checkpoint_path))
        self.checkpoints = candidate

    @staticmethod
    def _source_status(last_read, last_organized):
        return {
            "source_available": True,
            "latest_marker": SYNTHETIC_MARKER,
            "last_read_marker": last_read,
            "last_organized_marker": last_organized,
        }

    def collect(self):
        gate = decide(self._source_status(
            self.checkpoints["last_read_marker"],
            self.checkpoints["last_organized_marker"],
        ))
        self.events.append("Initial Gate: " + gate["reason"])
        if not gate["wakeAgent"]:
            return gate

        collection_path = self.output_dir / "collected.md"
        self._write_and_verify(collection_path, COLLECTION_TEXT)
        candidate = dict(self.checkpoints)
        candidate["last_read_marker"] = SYNTHETIC_MARKER
        self._commit_checkpoints(candidate)
        self.events.append("Collection written and read-back verified; last_read advanced")
        return gate

    def organize(self):
        if self.checkpoints["last_read_marker"] != SYNTHETIC_MARKER:
            raise RuntimeError("collection must be verified before organization")

        organization_path = self.output_dir / "organized.md"
        self._write_and_verify(organization_path, ORGANIZED_TEXT)
        candidate = dict(self.checkpoints)
        candidate["last_organized_marker"] = SYNTHETIC_MARKER
        self._commit_checkpoints(candidate)
        self.events.append("Organization written and read-back verified; last_organized advanced")

    def finish(self):
        gate = decide(self._source_status(
            self.checkpoints["last_read_marker"],
            self.checkpoints["last_organized_marker"],
        ))
        self.events.append("Final Gate: " + gate["reason"])
        return gate

    def run(self):
        self.collect()
        self.organize()
        result = self.finish()
        if result["wakeAgent"] or result["reason"] != "no_change_detected":
            raise RuntimeError("final Gate did not report no change")
        return result


def run_workflow(output_dir, store=None):
    workflow = DemoWorkflow(output_dir, store=store)
    result = workflow.run()
    return workflow, result


def main():
    output_dir = Path(tempfile.mkdtemp(prefix="flywheel-agent-demo-"))
    try:
        workflow, result = run_workflow(output_dir)
    except (OSError, VerificationError, GateInputError, RuntimeError) as error:
        print("Demo failed: " + str(error), file=sys.stderr)
        print("Output directory: " + str(output_dir))
        return 1

    print("Deterministic fictional Flywheel demo complete.")
    for event in workflow.events:
        print("- " + event)
    print("- Final decision: " + result["reason"])
    print("Output directory: " + str(output_dir))
    print("No AI, network, real data source, or production system was used.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
