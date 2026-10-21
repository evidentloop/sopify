---
plan_id: 20261020_sopify_narrow_focus
outcome: completed
plan_version: sha256:8f23aae56c4e49426f7b84d3c228d29f120e90dd12dee1ed816dde5b682c0980
---

# completed

## Summary

Sopify narrowed to Git-versioned AI coding plans and evidence that resume across tools, teammates and agents. The release adds a full test gate, installers that keep user instruction files, first-run project binding, Antigravity and Trae baselines, an Orca guide and a rewritten README. Merged through PR #76 and released as 2026-10-21.151943.

## Key Decisions

- Narrow positioning to plans and verification evidence versioned in Git; ask-first stays as a baseline capability.
- Shared home instruction files use one managed block; whole-file installs since 2026-06-10 migrate by stable anchors.
- Host rules call the installed bootstrap helper before the first managed write and when local state is not ignored.
- Antigravity and Trae share a flat Skill layout; new hosts start at baseline and Doctor keeps behavior checks separate.
- One owner writes protocol state through sopify_writer; Orca workers report, reviewers accept, and worker_done is not verify.
