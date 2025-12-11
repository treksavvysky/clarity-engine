# Tests

Unit tests validate the deterministic packet composition and linting behavior defined for Stage 0, and now cover the FastAPI health boundary introduced in Stage-01.1.

- `test_compose_packet.py` checks that the compose tool emits stable markdown, normalized manifests, and hashes for the example input.
- `test_lint_packet.py` ensures linting flags invalid manifests and accepts the documented example.
- `test_app_health.py` verifies the FastAPI app imports cleanly and that `/healthz` returns the expected payload.

Run `python -m unittest discover -s tests -p 'test_*.py'` from the repository root; tests must pass before advancing Stage-01 work.
