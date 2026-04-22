# Clarity Engine Mission (Extended)

Clarity Engine exists to make intent and context portable across humans and agents. It does this by generating context packets that are unambiguous, testable, and easy to audit so contributors can align quickly without rereading entire histories.

## Principles
- **Contract-first:** Templates, schemas, and manifests define the source of truth for every packet.
- **Deterministic output:** Composition and linting tools should produce stable results for the same inputs.
- **Traceability:** Packets carry the mission, constraints, and acceptance criteria needed to reason about changes and verify outcomes.
- **Agent-friendly:** Outputs are structured so MCP/LLM agents can consume, validate, and act without guesswork.

## Implementation Status
Stages 01–06 are shipped. The HTTP service, MCP server, content-addressed registry, JCT enqueue envelope, and browser UI all exist. See `current_reality.md` for the facts-only inventory.

### Clarity Engine is not a workflow runner.
It does not execute tasks or orchestrate agents; it produces the contracts that other systems use. Its purpose is to externalize intent, not to interpret or act on that intent.

### Context Packets are the atomic unit of alignment.
Everything Clarity Engine emits is designed to be portable, reviewable, and archivable—so that humans and agents can resume work from the packet alone, without needing operational memory or historical context.
