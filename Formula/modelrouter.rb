# Homebrew formula for ModelRouter.
#
# HOW TO PUBLISH THIS TAP
# ========================
# 1. Create a new GitHub repo named: homebrew-modelrouter
#    (Homebrew convention: the tap name is everything after "homebrew-")
# 2. Put this file at:  Formula/modelrouter.rb
# 3. Push the formula and the main repo (with a versioned tag, e.g. v1.0.0)
# 4. Get the SHA256 of the tarball:
#    curl -sL https://github.com/oyemecarnal/modelrouter/archive/refs/tags/v1.0.0.tar.gz | shasum -a 256
# 5. Fill in url and sha256 below, then push.
# 6. Users install with:
#    brew tap oyemecarnal/modelrouter
#    brew install modelrouter
#
# DEVELOPMENT (local tap):
#    brew install --build-from-source ./Formula/modelrouter.rb

class Modelrouter < Formula
  desc "Personal LLM gateway — OpenAI-compatible proxy with cost tracking and model routing"
  homepage "https://github.com/oyemecarnal/modelrouter"
  # TODO: fill these in after tagging a release
  url "https://github.com/oyemecarnal/modelrouter/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256_REPLACE_AFTER_TAGGING"
  license "MIT"
  head "https://github.com/oyemecarnal/modelrouter.git", branch: "main"

  depends_on "python@3.12"

  def install
    venv = libexec/"venv"

    # Create a virtualenv and install the Python requirements
    system "python3", "-m", "venv", venv
    system venv/"bin/pip", "install", "-q", "-r", "requirements.txt"

    # Install the full source tree to libexec (not prefix, to avoid polluting include/)
    libexec.install Dir["*"]

    # Link the mr CLI wrapper into bin so `mr` is on PATH
    (bin/"mr").write <<~SH
      #!/usr/bin/env bash
      exec "#{libexec}/mr" "$@"
    SH
    chmod 0755, bin/"mr"
  end

  def post_install
    # Create data dir inside the user's home if it doesn't exist yet
    (var/"modelrouter").mkpath
  end

  def caveats
    <<~EOS
      To finish setup, run:
        mr init

      This will:
        • Generate a random MODELROUTER_MASTER_KEY
        • Walk you through adding provider API keys
        • Start the gateway and cost-tracking widget daemons

      Gateway endpoint (after init):
        http://127.0.0.1:3000/v1

      Widget dashboard:
        mr widget

      To start on login:
        brew services start modelrouter

      Point any OpenAI-compatible tool at your gateway:
        OPENAI_BASE_URL=http://127.0.0.1:3000/v1
        OPENAI_API_KEY=$(mr key)
    EOS
  end

  service do
    run [opt_bin/"mr", "start"]
    keep_alive true
    log_path var/"log/modelrouter.log"
    error_log_path var/"log/modelrouter.err.log"
    working_dir libexec
  end

  test do
    # Verify mr CLI is executable and returns help text
    output = shell_output("#{bin}/mr help")
    assert_match "ModelRouter", output
    assert_match "init", output
  end
end
