.PHONY: install start stop restart health logs status doctor doctor-fix daemon daemon-enable daemon-disable smoke-hermes-fast smoke-routes dedupe-env ensure-alt-slots
.PHONY: docker-up docker-down docker-logs agents deploy-mini bootstrap-mini daemon-enable-mini enable-auto-rotate-mini push-alt-keys-mini check-alt-keys check-alt-keys-mini vault-sync-alts vault-sync-alts-restart vault-bootstrap-alts vault-ingest-alts vault-rotate-drill connect-alt-key keys-audit keys-sync keys-sync-mini
.PHONY: keys-sync-remote groq-setup push-env-mini push-client-env-tower keys-widget-install keys-widget keys-widget-fetch
.PHONY: route-hints project-keys rotate-master-key mcp-install smoke smoke-cursor smoke-tower smoke-hermes-smart smoke-hermes-fast smoke-routes usage-rollup test lint cost-review homelab-status connect-groq connect-anthropic connect-openai connect-mistral connect-google connect-deepseek connect-together connect-fireworks connect-cohere connect-provider connect-alt-key audit-tower-wires clean-tower-wires guide-tower-strays strip-tower-llm-keys ensure-gateway ship-check oauth-start check-presets consolidate-keys check-catalog core-apis sync-preset-tokens check-key-hygiene package-personal inventory inventory-mini vault-scrape vault-scrape-collect vault-list vault-export vault-export-dry vault-ingest-alts vault-sync-alts vault-sync-alts-restart vault-bootstrap-alts enable-auto-rotate-mini vault-rotate-drill vault-rotate-simulate vault-rotate-export vault-rotate-export-dry vault-rotate-push vault-rotate-push-dry

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

doctor-fix:
	./scripts/ensure-gateway.sh

logs:
	tail -f data/modelrouter.log

status:
	@./scripts/healthcheck.sh || true
	@if [ -f .pids/modelrouter.pid ]; then echo "PID: $$(cat .pids/modelrouter.pid)"; fi

daemon-enable:
	cp deploy/com.modelrouter.plist ~/Library/LaunchAgents/
	@MR_UID=$$(id -u); PLIST=$$HOME/Library/LaunchAgents/com.modelrouter.plist; \
	launchctl bootout gui/$$MR_UID/com.modelrouter 2>/dev/null || launchctl unload "$$PLIST" 2>/dev/null || true; \
	if launchctl bootstrap gui/$$MR_UID "$$PLIST" 2>/dev/null; then \
	  echo "ModelRouter launchd job loaded (bootstrap)"; \
	elif launchctl load "$$PLIST" 2>/dev/null; then \
	  echo "ModelRouter launchd job loaded (load)"; \
	else \
	  echo "launchd load failed — run: launchctl bootstrap gui/$$MR_UID $$PLIST" >&2; exit 1; \
	fi
	@echo "ModelRouter will start at login and auto-restart"

daemon-disable:
	@MR_UID=$$(id -u); PLIST=$$HOME/Library/LaunchAgents/com.modelrouter.plist; \
	launchctl bootout gui/$$MR_UID/com.modelrouter 2>/dev/null || launchctl unload "$$PLIST" 2>/dev/null || true; \
	rm -f "$$PLIST"

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

bootstrap-mini:
	chmod +x scripts/bootstrap-mini.sh scripts/daemon-enable-mini.sh scripts/push-alt-keys-mini.sh scripts/check-alt-keys.sh
	./scripts/bootstrap-mini.sh

daemon-enable-mini:
	chmod +x scripts/daemon-enable-mini.sh
	./scripts/daemon-enable-mini.sh

push-alt-keys-mini:
	chmod +x scripts/push-alt-keys-mini.sh
	./scripts/push-alt-keys-mini.sh

check-alt-keys:
	chmod +x scripts/check-alt-keys.sh
	./scripts/check-alt-keys.sh

check-alt-keys-mini:
	chmod +x scripts/check-alt-keys-mini.sh
	./scripts/check-alt-keys-mini.sh

vault-sync-alts:
	chmod +x scripts/vault-sync-alts.sh
	./scripts/vault-sync-alts.sh

vault-sync-alts-restart:
	chmod +x scripts/vault-sync-alts.sh
	./scripts/vault-sync-alts.sh --restart-mini

vault-bootstrap-alts:
	chmod +x scripts/vault-bootstrap-alts.sh
	./scripts/vault-bootstrap-alts.sh

vault-bootstrap-alts-restart:
	chmod +x scripts/vault-bootstrap-alts.sh
	./scripts/vault-bootstrap-alts.sh --restart-mini

dedupe-env:
	chmod +x scripts/dedupe-env.sh
	./scripts/dedupe-env.sh

dedupe-env-apply:
	chmod +x scripts/dedupe-env.sh
	./scripts/dedupe-env.sh --apply

ensure-alt-slots:
	chmod +x scripts/ensure-alt-slots.sh
	./scripts/ensure-alt-slots.sh

enable-auto-rotate-mini:
	chmod +x scripts/enable-auto-rotate-mini.sh
	./scripts/enable-auto-rotate-mini.sh

enable-auto-rotate-mini-enable:
	chmod +x scripts/enable-auto-rotate-mini.sh
	./scripts/enable-auto-rotate-mini.sh --enable

vault-rotate-drill:
	chmod +x scripts/vault-rotate-drill.sh
	./scripts/vault-rotate-drill.sh

vault-rotate-simulate:
	chmod +x scripts/vault-rotate-simulate.sh
	./scripts/vault-rotate-simulate.sh $(or $(PROVIDER),groq)

vault-rotate-simulate-cleanup:
	chmod +x scripts/vault-rotate-simulate.sh
	./scripts/vault-rotate-simulate.sh $(or $(PROVIDER),groq) --cleanup

connect-alt-key:
	chmod +x scripts/connect-alt-key.sh
	./scripts/connect-alt-key.sh $(or $(PROVIDER),)

keys-audit:
	./scripts/discover-keys.sh

inventory:
	./scripts/inventory-scrape.sh

inventory-mini:
	./scripts/inventory-scrape-remote.sh

vault-scrape:
	chmod +x scripts/vault-scrape.sh scripts/vault-export.sh
	./scripts/vault-scrape.sh

vault-scrape-collect:
	chmod +x scripts/vault-scrape.sh
	./scripts/vault-scrape.sh --collect

vault-list:
	PYTHONPATH=. .venv/bin/python -m modelrouter.key_vault list

vault-export-dry:
	./scripts/vault-export.sh --dry-run

vault-ingest-alts:
	PYTHONPATH=. .venv/bin/python -m modelrouter.key_vault ingest-alts

vault-export:
	./scripts/vault-export.sh

vault-rotate-export-dry:
	chmod +x scripts/vault-rotate-export.sh
	./scripts/vault-rotate-export.sh --dry-run

vault-rotate-export:
	chmod +x scripts/vault-rotate-export.sh
	./scripts/vault-rotate-export.sh

vault-rotate-push-dry:
	chmod +x scripts/vault-rotate-push.sh
	./scripts/vault-rotate-push.sh --dry-run

vault-rotate-push:
	chmod +x scripts/vault-rotate-push.sh
	./scripts/vault-rotate-push.sh

keys-sync:
	./scripts/sync-keys.sh

keys-sync-mini:
	./scripts/sync-keys.sh --from-mini

keys-sync-remote:
	ssh kc-mini-lan 'cd ~/dev/modelrouter && make keys-sync && make restart'

groq-setup:
	./scripts/setup-groq.sh

connect-groq:
	./scripts/connect-groq.sh

connect-anthropic:
	./scripts/connect-anthropic.sh

connect-openai:
	./scripts/connect-openai.sh

connect-mistral:
	./scripts/connect-mistral.sh

connect-google:
	./scripts/connect-google.sh

connect-deepseek:
	./scripts/connect-deepseek.sh

connect-together:
	./scripts/connect-together.sh

connect-fireworks:
	./scripts/connect-fireworks.sh

connect-cohere:
	./scripts/connect-cohere.sh

connect-provider:
	./scripts/connect-provider.sh $(or $(PROVIDER),)

push-env-mini:
	./scripts/push-env-to-mini.sh MISTRAL_API_KEY GROQ_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY GOOGLE_API_KEY GEMINI_API_KEY DEEPSEEK_API_KEY TOGETHER_API_KEY FIREWORKS_API_KEY COHERE_API_KEY OPENROUTER_API_KEY POLYGON_API_KEY MODELROUTER_MASTER_KEY LITELLM_SALT_KEY

package-personal:
	./scripts/package-personal.sh

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

smoke-hermes-smart:
	./scripts/smoke-hermes-smart.sh

smoke-hermes-fast:
	chmod +x scripts/smoke-hermes-fast.sh
	./scripts/smoke-hermes-fast.sh

smoke-routes:
	chmod +x scripts/smoke-routes.sh scripts/smoke-hermes-fast.sh scripts/smoke-hermes-smart.sh
	./scripts/smoke-routes.sh

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

audit-tower-wires:
	./scripts/audit-tower-wires.sh

clean-tower-wires:
	./scripts/clean-tower-wires.sh

guide-tower-strays:
	./scripts/guide-tower-strays.sh

strip-tower-llm-keys:
	./scripts/strip-tower-llm-keys.sh

ensure-gateway:
	./scripts/ensure-gateway.sh

ship-check:
	./scripts/ship-check.sh

oauth-start:
	./scripts/oauth-start.sh $(or $(PROVIDER),)

core-apis:
	./scripts/update-core-api-list.sh

consolidate-keys:
	./scripts/consolidate-keys.sh
