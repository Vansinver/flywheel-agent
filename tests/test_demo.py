"""Standard-library tests for the deterministic fictional workflow demo."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "examples"))
from run_demo import (  # noqa: E402
    COLLECTION_TEXT,
    ORGANIZED_TEXT,
    DemoStore,
    DemoWorkflow,
    VerificationError,
    run_workflow,
)


class FaultInjectingStore(DemoStore):
    def __init__(self, fail_write=None, corrupt_read=None):
        self.fail_write = fail_write
        self.corrupt_read = corrupt_read

    def write_text(self, path, content):
        if path.name == self.fail_write:
            raise IOError("synthetic write failure")
        DemoStore.write_text(self, path, content)

    def read_text(self, path):
        content = DemoStore.read_text(self, path)
        if path.name == self.corrupt_read:
            return content + "synthetic read-back mismatch\n"
        return content


class DemoWorkflowTests(unittest.TestCase):
    def make_output_dir(self, parent):
        path = Path(parent) / "demo-output"
        path.mkdir()
        return path

    def assert_persisted_checkpoints_match(self, workflow):
        with open(str(workflow.checkpoint_path), "r", encoding="utf-8") as source:
            persisted = json.load(source)
        self.assertEqual(persisted, workflow.checkpoints)

    def test_successful_end_to_end_workflow(self):
        with tempfile.TemporaryDirectory() as parent:
            output_dir = self.make_output_dir(parent)
            workflow, result = run_workflow(output_dir)

            self.assertEqual(result["reason"], "no_change_detected")
            self.assertFalse(result["wakeAgent"])
            self.assertEqual(workflow.checkpoints["last_read_marker"], "synthetic-item-001")
            self.assertEqual(workflow.checkpoints["last_organized_marker"], "synthetic-item-001")
            self.assertEqual(
                workflow.store.read_text(output_dir / "collected.md"),
                COLLECTION_TEXT,
            )
            self.assertEqual(
                workflow.store.read_text(output_dir / "organized.md"),
                ORGANIZED_TEXT,
            )
            persisted = json.loads(workflow.store.read_text(output_dir / "checkpoints.json"))
            self.assertEqual(persisted, workflow.checkpoints)
            self.assertEqual(workflow.events[0], "Initial Gate: unread_source")
            self.assertEqual(workflow.events[-1], "Final Gate: no_change_detected")

    def test_collection_write_failure_does_not_advance_read_watermark(self):
        with tempfile.TemporaryDirectory() as parent:
            output_dir = self.make_output_dir(parent)
            workflow = DemoWorkflow(output_dir)
            workflow.store = FaultInjectingStore(fail_write="collected.md")

            with self.assertRaises(IOError):
                workflow.collect()

            self.assertIsNone(workflow.checkpoints["last_read_marker"])
            self.assertIsNone(workflow.checkpoints["last_organized_marker"])
            self.assert_persisted_checkpoints_match(workflow)

    def test_collection_readback_failure_does_not_advance_read_watermark(self):
        with tempfile.TemporaryDirectory() as parent:
            output_dir = self.make_output_dir(parent)
            workflow = DemoWorkflow(output_dir)
            workflow.store = FaultInjectingStore(corrupt_read="collected.md")

            with self.assertRaises(VerificationError):
                workflow.collect()

            self.assertIsNone(workflow.checkpoints["last_read_marker"])
            self.assertIsNone(workflow.checkpoints["last_organized_marker"])
            self.assert_persisted_checkpoints_match(workflow)

    def test_organization_write_failure_does_not_advance_organized_watermark(self):
        with tempfile.TemporaryDirectory() as parent:
            output_dir = self.make_output_dir(parent)
            workflow = DemoWorkflow(output_dir)
            workflow.collect()
            workflow.store = FaultInjectingStore(fail_write="organized.md")

            with self.assertRaises(IOError):
                workflow.organize()

            self.assertEqual(workflow.checkpoints["last_read_marker"], "synthetic-item-001")
            self.assertIsNone(workflow.checkpoints["last_organized_marker"])
            self.assert_persisted_checkpoints_match(workflow)

    def test_organization_readback_failure_does_not_advance_organized_watermark(self):
        with tempfile.TemporaryDirectory() as parent:
            output_dir = self.make_output_dir(parent)
            workflow = DemoWorkflow(output_dir)
            workflow.collect()
            workflow.store = FaultInjectingStore(corrupt_read="organized.md")

            with self.assertRaises(VerificationError):
                workflow.organize()

            self.assertEqual(workflow.checkpoints["last_read_marker"], "synthetic-item-001")
            self.assertIsNone(workflow.checkpoints["last_organized_marker"])
            self.assert_persisted_checkpoints_match(workflow)


if __name__ == "__main__":
    unittest.main()
