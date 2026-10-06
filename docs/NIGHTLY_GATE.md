# Scheduled Gate and Two-Watermark Flow

This document describes a portable design pattern, not a deployment guide or a copy of any production configuration.

## Responsibilities

1. Scheduler starts a bounded check at a user-selected time.
2. Gate validates a source status summary and the private checkpoint state, then emits a machine-readable decision.
3. Scheduler checks both the process exit code and the JSON status. A non-zero exit code or status=error is a failed Gate run and must be surfaced or retried according to policy.
4. Scheduler must not treat a failed run as a normal skip by reading only wakeAgent. Error output has no wakeAgent field; malformed, unavailable, or inconsistent input must never be converted into a successful wakeAgent=false result.
5. Agent runs only after a successful Gate result with wakeAgent=true; it follows a separate, reviewed task specification.
6. Collection stage reads new source items and stores them in a private inbox, with attachments handled under the same privacy boundary.
7. Organization stage creates summaries or observations only from collected evidence.

The scheduler, Gate, Agent, external source adapter, and file store are separate components. A platform's support for one does not establish support for the others.

## Input contract

The input is one JSON object containing exactly these fields:

| Field | Type | Meaning |
|---|---|---|
| source_available | boolean | Whether the source adapter completed a valid status read. |
| latest_marker | non-empty string or null | Marker for the latest available source item. |
| last_read_marker | non-empty string or null | Latest marker whose collection has been verified. |
| last_organized_marker | non-empty string or null | Latest collected marker whose organization has been verified. |

A JSON null marker is the sole representation of an empty position. A valid empty source is represented by source_available=true and all three markers null. That means “the source was read successfully and contains no items,” not “the read failed.” A failed read is source_available=false and is an error. Empty strings, whitespace-only strings, booleans, numbers, missing fields, extra fields, and non-object JSON are invalid.

If latest_marker is null while either checkpoint is non-null, the source and checkpoints are inconsistent. This may mean that the source was cleared or reset. The Gate returns status=error with the stable error code source_checkpoint_mismatch, omits wakeAgent, and exits non-zero. It does not wake the Agent and does not advance or reset either watermark. A person must inspect the source and make a controlled baseline decision. The adapter must not use null to conceal a read failure.

## Decision order

The Gate applies these steps in order:

1. Validate the JSON object and all required fields. Missing fields or invalid types/markers return status=error and a non-zero exit code.
2. If source_available is false, return status=error and a non-zero exit code.
3. If latest_marker is null and either checkpoint is non-null, return status=error, error=source_checkpoint_mismatch, no wakeAgent field, and a non-zero exit code.
4. If last_read_marker != last_organized_marker, return status=ok, wakeAgent=true, reason=organization_backlog.
5. If latest_marker != last_read_marker, return status=ok, wakeAgent=true, reason=unread_source.
6. If all three markers are null, return status=ok, wakeAgent=false, reason=no_change_detected. Any other equal-marker state also returns that no-change result.

When unread source and organization backlog are both present with a non-null latest marker, organization_backlog wins because it is checked first. The null-latest mismatch check precedes both backlog checks.

## Gate output and exit codes

Successful output is JSON with status=ok, a boolean wakeAgent, and a reason. The process exits 0.

Failure output is JSON with status=error and a stable error code/message, with no wakeAgent field. The process exits 2. The scheduler must check both. It must not interpret an absent or false wakeAgent value as a successful skip.

The example in templates/gate_protocol.py implements this input validation, decision order, mismatch error, and output contract. Run python gate_protocol.py --self-test to execute its built-in sample tests. The script does not connect to a source, persist checkpoints, call an Agent, or prove runtime compatibility.

## Two-watermark principle

- last_read advances only after collected data and attachments have been written and verified by read-back.
- last_organized advances only after organization output has been written and verified.
- The Gate reads marker state but never advances or resets either watermark.
- If a write or verification fails, keep the prior watermark and surface the failure for review.
- A source/checkpoint mismatch requires human inspection and a controlled baseline decision; never auto-reset a watermark.

## Portability notes

- Keep source-specific authentication outside public files.
- Use configurable paths and adapters; avoid machine-specific paths and account identifiers.
- Validate duplicate handling, retries, timeouts, attachment behavior, and checkpoint recovery in the target environment.
- No production Gate, local MCP service, data source, or model is invoked by the sample tests.