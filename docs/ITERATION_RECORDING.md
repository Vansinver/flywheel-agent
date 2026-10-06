# Agent Iteration Recording

## When to create a record

Create an iteration record when the Agent or its operating system has actually changed, such as a change to behavior rules, configuration, tools, permissions, data structures, workflow, or a verified fix.

An idea or ordinary discussion is not a completed iteration. A candidate record may be opened when the work has entered a real design or implementation process; status must show its actual maturity.

## Status

| Status | Meaning |
|---|---|
| Candidate | A real issue is being explored or designed; no implementation is complete. |
| Implemented | The change has been made, but evidence does not yet establish that it works as intended. |
| Verified | Inspectable evidence supports the stated result in the named environment. |
| Reverted | The change was removed or rolled back. Preserve why and what was learned. |

Discussion is not implementation. Implementation is not verification.

## Record template

~~~markdown
# ITER-XXX — Short title

Date:
Status:
Change type:
Environment:
Source of evidence:

## Timeline

## 1. Problem or need

## 2. Change or method

## 3. Resulting behavior

## 4. Verification evidence

## 5. Limits, failures, or counterexamples

## 6. Reusable lesson
~~~

Use a neutral sequential identifier such as ITER-XXX; do not reuse an assigned identifier.

## Time and evidence

- Never invent dates or times.
- Use only timestamps supported by logs, file metadata, receipts, or current observation.
- Record the precision the evidence supports; if a time cannot be established, say so.
- Keep concise, checked facts in the iteration record.
- Store long raw receipts separately with access controls; link to them without copying their contents into public records.

## Permission boundary

The Agent may document changes that have happened. The act of documenting a lesson does not authorize changing core rules, permissions, configuration, integrations, schedules, or user goals. Obtain the required user decision and review before such changes.

Keep unsuccessful attempts, reversions, and verification limits in the history. Update any timeline or index only when the associated record exists.