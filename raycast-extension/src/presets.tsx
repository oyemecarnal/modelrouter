import {
  Action,
  ActionPanel,
  Color,
  Icon,
  List,
  showHUD,
  Clipboard,
} from "@raycast/api";
import { useEffect, useState } from "react";
import { fetchSnapshot, masterKey, prefs, Snapshot } from "./lib";

// Presets bundled locally as fallback — these mirror config/modelrouter.yaml
const BUILTIN_PRESETS: PresetInfo[] = [
  {
    name: "cheap",
    description: "Lowest cost — fast inference, capable for most tasks",
    models: ["groq/llama-3.3-70b-versatile", "deepseek/deepseek-chat"],
    tags: ["cost", "fast"],
  },
  {
    name: "fast",
    description: "Optimized for low latency",
    models: ["groq/llama-3.1-8b-instant", "groq/llama-3.3-70b-versatile"],
    tags: ["latency"],
  },
  {
    name: "smart",
    description: "Best reasoning — Sonnet or GPT-4o class",
    models: ["anthropic/claude-sonnet-4-6", "openai/gpt-4o"],
    tags: ["reasoning", "quality"],
  },
  {
    name: "code",
    description: "Code-focused — long context, high accuracy",
    models: ["anthropic/claude-sonnet-4-6", "openai/gpt-4o", "deepseek/deepseek-coder"],
    tags: ["code"],
  },
  {
    name: "review",
    description: "Deep review — Opus / o3 class, no cost limit",
    models: ["anthropic/claude-opus-4-8", "openai/o3"],
    tags: ["review", "quality"],
  },
  {
    name: "local",
    description: "Local Ollama inference — no API key required",
    models: ["ollama/llama3.2", "ollama/qwen2.5-coder"],
    tags: ["local", "private"],
  },
  {
    name: "offline",
    description: "Alias for local — fully offline",
    models: ["ollama/llama3.2"],
    tags: ["local", "private"],
  },
];

interface PresetInfo {
  name: string;
  description: string;
  models: string[];
  tags: string[];
}

function tagColor(tag: string): Color {
  const map: Record<string, Color> = {
    cost: Color.Green,
    fast: Color.Blue,
    latency: Color.Blue,
    reasoning: Color.Purple,
    quality: Color.Orange,
    code: Color.Yellow,
    review: Color.Red,
    local: Color.SecondaryText,
    private: Color.SecondaryText,
  };
  return map[tag] ?? Color.SecondaryText;
}

export default function PresetsCommand() {
  const p = prefs();
  const key = masterKey(p);
  const endpoint = `${p.gatewayUrl}/v1`;
  const [search, setSearch] = useState("");
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);

  useEffect(() => {
    fetchSnapshot(p).then(setSnapshot);
  }, []);

  // Merge live presets from snapshot with builtin fallback
  const livePresets = snapshot?.policyPresets;
  const presets: PresetInfo[] = livePresets
    ? Object.keys(livePresets).map((name) => {
        const builtin = BUILTIN_PRESETS.find((b) => b.name === name);
        return builtin ?? { name, description: "Custom preset", models: [], tags: [] };
      })
    : BUILTIN_PRESETS;

  const filtered = search
    ? presets.filter(
        (p) =>
          p.name.includes(search.toLowerCase()) ||
          p.tags.some((t) => t.includes(search.toLowerCase())) ||
          p.description.toLowerCase().includes(search.toLowerCase())
      )
    : presets;

  async function copyConfig(preset: PresetInfo, format: "openai" | "curl" | "python" | "model") {
    let text = "";
    if (format === "model") {
      text = preset.name;
    } else if (format === "openai") {
      text = JSON.stringify({ model: preset.name, openai_api_base: endpoint, openai_api_key: key || "<your-key>" }, null, 2);
    } else if (format === "curl") {
      text = [
        `curl ${endpoint}/chat/completions \\`,
        `  -H "Authorization: Bearer ${key || "<your-key>"}" \\`,
        `  -H "Content-Type: application/json" \\`,
        `  -d '{"model":"${preset.name}","messages":[{"role":"user","content":"hello"}]}'`,
      ].join("\n");
    } else if (format === "python") {
      text = [
        `from openai import OpenAI`,
        `client = OpenAI(base_url="${endpoint}", api_key="${key || "<your-key>"}")`,
        `response = client.chat.completions.create(`,
        `    model="${preset.name}",`,
        `    messages=[{"role": "user", "content": "hello"}]`,
        `)`,
        `print(response.choices[0].message.content)`,
      ].join("\n");
    }
    await Clipboard.copy(text);
    await showHUD(`Copied ${format} config for "${preset.name}"`);
  }

  return (
    <List
      isLoading={!snapshot}
      searchText={search}
      onSearchTextChange={setSearch}
      searchBarPlaceholder="Filter presets…"
      navigationTitle="ModelRouter Presets"
    >
      {filtered.map((preset) => (
        <List.Item
          key={preset.name}
          title={preset.name}
          subtitle={preset.description}
          accessories={preset.tags.map((t) => ({
            tag: { value: t, color: tagColor(t) },
          }))}
          detail={
            <List.Item.Detail
              markdown={[
                `## ${preset.name}`,
                `${preset.description}`,
                "",
                `**Endpoint:** \`${endpoint}\``,
                "",
                preset.models.length > 0
                  ? `**Models (fallback order):**\n${preset.models.map((m) => `- \`${m}\``).join("\n")}`
                  : "",
              ].join("\n")}
            />
          }
          actions={
            <ActionPanel>
              <ActionPanel.Section title="Copy Config">
                <Action
                  title="Copy Model Name"
                  icon={Icon.Clipboard}
                  onAction={() => copyConfig(preset, "model")}
                  shortcut={{ modifiers: ["cmd"], key: "c" }}
                />
                <Action
                  title="Copy as curl Command"
                  icon={Icon.Terminal}
                  onAction={() => copyConfig(preset, "curl")}
                  shortcut={{ modifiers: ["cmd", "shift"], key: "c" }}
                />
                <Action
                  title="Copy as Python Snippet"
                  icon={Icon.Code}
                  onAction={() => copyConfig(preset, "python")}
                  shortcut={{ modifiers: ["cmd", "opt"], key: "c" }}
                />
                <Action
                  title="Copy as JSON (openai SDK)"
                  icon={Icon.Document}
                  onAction={() => copyConfig(preset, "openai")}
                />
              </ActionPanel.Section>
              <ActionPanel.Section title="Run">
                <Action.OpenInBrowser
                  title="Open Endpoint in Browser"
                  url={`${endpoint}/models`}
                  shortcut={{ modifiers: ["cmd"], key: "o" }}
                />
              </ActionPanel.Section>
            </ActionPanel>
          }
        />
      ))}
    </List>
  );
}
