# Platform Compatibility Matrix

Status applies only to the evidence described. It does not imply that the public draft can be deployed as-is.

| Capability | Current environment evidence in the inventory | Public draft status | Qoder CN status |
|---|---|---|---|
| Read and write the private project archive | Used by the current production workflow | Not tested by this draft | Unverified |
| External source access through a local MCP service | Current environment has a working local source integration | No adapter included | Unverified |
| Scheduled execution | Existing runtime has an enabled scheduled workflow | Architecture only; not deployed here | Unverified |
| Gate execution before model invocation | Disk-source observation: the inspected Hermes task has a pre-run Gate; a successful `wakeAgent=false` result skips the Agent path, while a non-zero script exit continues into it (see below) | Independent protocol example only; not a copy of, or production adapter for, Hermes | Unverified |
| Pre-run script error propagation | Disk-source observation: a non-zero exit's error text and exit code are added to Agent context as a Script Error, with an instruction to report it; this does not establish diagnosis-only mode or hard-block ordinary task operations | The public protocol documents explicit scheduler error handling and does not model this observed Hermes path | Unverified |
| Skip model call when there is no change | Reported for the current runtime | Not validated in this draft | Unverified |
| Two independent watermarks | Present in the current workflow | Explained, not implemented | Unverified |
| Collection and organization stages | Current workflow has separate stages | Described as a pattern only | Unverified |
| Attachment handling and read-back verification | Part of the current workflow | Not implemented in this draft | Unverified |
| Unattended operation and recovery | Existing workflow has limited observed evidence; recovery behavior needs more validation | Not tested | Unverified |
| Cross-computer migration | Requires fresh authorization and environment-specific checks | Not tested | Unverified |

## Qoder CN questions to validate

Do not describe these as supported until tested in the intended setup:

- Can it invoke a local MCP service with the required transport and request semantics?
- Can a Gate short-circuit the Agent so that a no-change run makes no model call?
- Can scheduled work run unattended, with clear retry and failure behavior?
- Does its file access remain stable across runs and preserve checkpoints?
- Can it safely handle attachments and verify writes before advancing watermarks?
- Which data is sent to the model service when local files are analyzed?

The current inventory does not establish answers to these questions.

## Evidence boundary for Hermes Gate behavior

The Hermes behavior above is a **disk-source observation** tied to the inspected task configuration. It does not prove that the running Gateway loaded the same source version or that a real failure run behaved this way. The loaded Gateway version and real failure behavior remain unverified; no failure rehearsal was run.

The public Gate sample is an independent protocol example, not a copy of the Hermes production adapter. Its scheduler contract does not claim to describe Hermes runtime behavior.
