.PHONY: install start stop restart health logs status doctor daemon daemon-enable daemon-disable
.PHONY: docker-up docker-down docker-logs agents deploy-mini keys-audit keys-sync keys-sync-mini
.PHONY: keys-sync-remote groq-setup push-env-mini push-client-env-tower keys-widget-install keys-widget keys-widget-fetch
.PHONY: route-hints project-keys rotate-master-key mcp-install smoke smoke-cursor smoke-tower usage-rollup test lint cost-review homelab-status
.PHONY: check-presets consolidate-keys check-catalog core-apis sync-preset-tokens check-key-hygiene

install:
	./scripts/install.sh

start:
	./scripts/start.sh

daemon:
	./scripts/start-daemon.sh

stop:
	./scripts/stop.sh

restart: stop daemon

health:
	./scripts/healthcheck.sh

doctor:
	./scripts/doctor.sh

logs:
	tail -f data/modelrouter.log

status:
	@./scripts/healthcheck.sh || true
	@if [ -f .pids/modelrouter.pid ]; then echo "PID: $$(cat .pids/modelrouter.pid)"; fi

daemon-enable:
	cp deploy/com.modelrouter.plist ~/Library/LaunchAgents/
	launchctl load ~/Library/LaunchAgents/com.modelrouter.plist
	@echo "ModelRouter will start at login and auto-restart"

daemon-disable:
	launchctl unload ~/Library/LaunchAgents/com.modelrouter.plist 2>/dev/null || true
	rm -f ~/Library/LaunchAgents/com.modelrouter.plist

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f modelrouter

agents:
	./scripts/install-dev-agents.sh

deploy-mini:
	./scripts/deploy-to-mini.sh

keys-audit:
	./scripts/discover-keys.sh

inventory:
	./scripts/inventory-scrape.sh

inventory-mini:
	./scripts/inventory-scrape-remote.sh

keys-sync:
	./scripts/sync-keys.sh

keys-sync-mini:
	./scripts/sync-keys.sh --from-mini

keys-sync-remote:
	ssh kc-mini-lan 'cd ~/dev/modelrouter && make keys-sync && make restart'

groq-setup:
	./scripts/setup-groq.sh

push-env-mini:
	./scripts/push-env-to-mini.sh MISTRAL_API_KEY GROQ_API_KEY OPENAI_API_KEY GOOGLE_API_KEY GEMINI_API_KEY OPENROUTER_API_KEY POLYGON_API_KEY MODELROUTER_MASTER_KEY LITELLM_SALT_KEY

push-client-env-tower:
	./scripts/push-client-env-to-tower.sh

keys-widget-install:
	cd tokens && ./scripts/install.sh

keys-widget:
	cd tokens && ./scripts/run_widget.sh

keys-widget-fetch:
	cd tokens && .venv/bin/python3 scripts/fetch_usage.py --print

route-hints:
	PYTHONPATH=. .venv/bin/python -m modelrouter.route_policy --all

project-keys:
	./scripts/issue-project-keys.sh

rotate-master-key:
	./scripts/rotate-master-key.sh

rotate-salt-key:
	./scripts/rotate-salt-key.sh

mcp-install:
	.venv/bin/pip install -q -r requirements-mcp.txt

smoke:
	PYTHONPATH=. .venv/bin/python -c "import yaml; yaml.safe_load(open('config/modelrouter.minimal.yaml'))"
	PYTHONPATH=. .venv/bin/python -m modelrouter.route_policy --project smalshi-hermes

smoke-cursor:
	./scripts/smoke-cursor-wiring.sh

smoke-tower:
	./scripts/smoke-tower-gateway.sh

usage-rollup:
	./scripts/usage-rollup.sh

test:
	./scripts/test.sh

lint:
	./scripts/lint.sh

remote-health:
	./scripts/remote-health.sh

homelab-status:
	./scripts/homelab-status.sh

cost-review:
	./scripts/cost-review.sh

check-presets:
	.venv/bin/python scripts/check_presets.py

check-catalog:
	.venv/bin/python scripts/check_catalog.py

sync-preset-tokens:
	.venv/bin/python scripts/sync_preset_max_tokens.py

check-key-hygiene:
	./scripts/check-key-hygiene.sh

core-apis:
	./scripts/update-core-api-list.sh

consolidate-keys:
	./scripts/consolidate-keys.sh
