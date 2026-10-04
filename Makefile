.PHONY: phase4-up phase4-down phase4-logs phase4-smoke phase4-test

phase4-up:
	docker compose up -d --build

phase4-down:
	docker compose down

phase4-logs:
	docker compose logs -f

phase4-smoke:
	cd gateway-node && bun test tests/runtime-stack.integration.test.ts

phase4-test:
	cd gateway-node && bun run build && bun test
	cd analytics-py && python -m pytest -q
	cmake -S engine-cpp -B build -DCMAKE_BUILD_TYPE=Release
	cmake --build build -j"$$(nproc)"
	ctest --test-dir build --output-on-failure
