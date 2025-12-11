# Tests

Unit tests validate the deterministic packet composition and linting behavior defined for Stage 0.

- `test_compose_packet.py` checks that the compose tool emits stable markdown, normalized manifests, and hashes for the example input.
- `test_lint_packet.py` ensures linting flags invalid manifests and accepts the documented example.

Run `python -m pytest` from the repository root; tests must pass before advancing Stage-01 work.
