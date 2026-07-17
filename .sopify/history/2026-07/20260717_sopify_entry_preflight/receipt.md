---
plan_id: 20260717_sopify_entry_preflight
outcome: completed
---

# completed

## Summary

Completed the intent-first managed-work entry preflight: objective lite status facts, writer-only and non-overwrite protocol state, checkpoint and stale-pointer interaction rules, bilingual host prompts and public docs, automated matrix coverage, one representative Codex isolation replay, and independent product-delivery plus architecture reviews.

## Key Decisions

- Only explicit managed-work intent such as continue or ~go enters resume handling; ordinary questions and small fixes are handled directly.
- The four-file protocol remains canonical and MCP is an optional read accelerator that returns objective facts only.
- active_plan remains a pure plan_id pointer; plan files are semantic truth, handoff is a recovery hint, and machine truth is written only through sopify_writer.
- An invalid stale pointer does not add a cleanup question to an explicitly authorized new or valid continue action; switching away from a valid plan still requires confirmation.
- Non-active-plan audit remains a read-only verifier sidepath, with the host validating the target and the writer creating a non-overwriting plan receipt.
- Session identifiers are provenance only; only the three documented parallel-progress signals stop side-effecting work, followed by a latest-state reread.
- Codex is the representative host replay for this plan, not evidence that every supported host was replayed.
