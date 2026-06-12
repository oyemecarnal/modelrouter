.PHONY: install start stop restart health logs status daemon-enable daemon-disable docker-up docker-down

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

keys-sync:
	./scripts/sync-keys.sh

keys-sync-mini:
	./scripts/sync-keys.sh --from-mini

# On kc-mini: fill .env from smalshi/coinbot/etc on that machine
keys-sync-remote:
	ssh kc-mini-lan 'cd ~/dev/modelrouter && make keys-sync && make restart'

groq-setup:
	./scripts/setup-groq.sh

push-env-mini:
	./scripts/push-env-to-mini.sh MISTRAL_API_KEY GROQ_API_KEY

keys-widget-install:
	cd tokens && ./scripts/install.sh

keys-widget:
	cd tokens && ./scripts/run_widget.sh

keys-widget-fetch:
	cd tokens && .venv/bin/python3 scripts/fetch_usage.py --print
