import {
  Action,
  ActionPanel,
  Color,
  Icon,
  List,
} from "@raycast/api";
import { useEffect, useState } from "react";
import { CostModel, CostRollup, fetchSnapshot, fmtTokens, fmtUsd, prefs } from "./lib";

const WINDOWS = ["1h", "24h", "7d", "30d"] as const;
type Window = (typeof WINDOWS)[number];

const WINDOW_LABELS: Record<Window, string> = {
  "1h": "Last hour",
  "24h": "Last 24 hours",
  "7d": "Last 7 days",
  "30d": "Last 30 days",
};

function providerColor(provider: string): Color {
  const map: Record<string, Color> = {
    anthropic: Color.Orange,
    openai: Color.Green,
    groq: Color.Blue,
    google: Color.Yellow,
    deepseek: Color.Purple,
    together: Color.Magenta,
    fireworks: Color.Red,
    mistral: Color.SecondaryText,
    openrouter: Color.SecondaryText,
  };
  return map[provider.toLowerCase()] ?? Color.SecondaryText;
}

function barString(fraction: number, width = 10): string {
  const filled = Math.round(fraction * width);
  return "█".repeat(filled) + "░".repeat(width - filled);
}

export default function CostCommand() {
  const p = prefs();
  const [rollup, setRollup] = useState<CostRollup | null>(null);
  const [loading, setLoading] = useState(true);
  const [window, setWindow] = useState<Window>("24h");

  async function refresh() {
    setLoading(true);
    const snap = await fetchSnapshot(p);
    setRollup(snap.costRollup ?? null);
    setLoading(false);
  }

  useEffect(() => { refresh(); }, []);

  const windowData = rollup?.windows?.[window];
  const models: CostModel[] = rollup?.by_model?.[window] ?? [];
  const maxCost = models.length > 0 ? Math.max(...models.map((m) => m.cost_usd)) : 0;

  const totalUsd = windowData?.total_usd ?? 0;
  const totalReqs = windowData?.requests ?? 0;
  const totalTok = windowData?.tokens ?? 0;

  const updatedAt = rollup?.updated_at
    ? new Date(rollup.updated_at).toLocaleTimeString()
    : "—";

  const hasData = models.length > 0;
  const noData = rollup?.no_data || (!loading && !hasData);

  return (
    <List
      isLoading={loading}
      isShowingDetail={hasData}
      navigationTitle="LLM Cost Dashboard"
      searchBarAccessory={
        <List.Dropdown
          tooltip="Time window"
          value={window}
          onChange={(v) => setWindow(v as Window)}
        >
          {WINDOWS.map((w) => (
            <List.Dropdown.Item key={w} title={WINDOW_LABELS[w]} value={w} />
          ))}
        </List.Dropdown>
      }
    >
      {/* Summary row */}
      <List.Section title={`${WINDOW_LABELS[window]}  ·  updated ${updatedAt}`}>
        <List.Item
          title="Total spend"
          subtitle={fmtUsd(totalUsd)}
          accessories={[
            { text: `${totalReqs} reqs`, icon: Icon.Message },
            { text: fmtTokens(totalTok) + " tok", icon: Icon.Layers },
          ]}
          icon={{ source: Icon.BankNote, tintColor: totalUsd > 0 ? Color.Yellow : Color.SecondaryText }}
          detail={
            <List.Item.Detail
              markdown={[
                `## Spend summary — ${WINDOW_LABELS[window]}`,
                "",
                `| | |`,
                `|---|---|`,
                `| **Total cost** | ${fmtUsd(totalUsd)} |`,
                `| **Requests** | ${totalReqs.toLocaleString()} |`,
                `| **Tokens** | ${fmtTokens(totalTok)} |`,
                "",
                noData ? "_No requests logged yet. Make a request through the gateway to start tracking costs._" : "",
              ].join("\n")}
            />
          }
          actions={
            <ActionPanel>
              <Action title="Refresh" icon={Icon.ArrowClockwise} onAction={refresh} shortcut={{ modifiers: ["cmd"], key: "r" }} />
              <Action.OpenInBrowser title="Open Widget Dashboard" url={p.widgetUrl} />
            </ActionPanel>
          }
        />
      </List.Section>

      {/* Per-model rows */}
      {hasData && (
        <List.Section title={`By model (${models.length})`}>
          {models.map((m, i) => {
            const fraction = maxCost > 0 ? m.cost_usd / maxCost : 0;
            const bar = barString(fraction);
            const avgCostPerReq = m.requests > 0 ? m.cost_usd / m.requests : 0;

            return (
              <List.Item
                key={m.model}
                title={m.model}
                subtitle={`${bar}  ${fmtUsd(m.cost_usd)}`}
                accessories={[
                  { tag: { value: m.provider, color: providerColor(m.provider) } },
                  { text: `${m.requests} req` },
                ]}
                icon={{ source: Icon.Circle, tintColor: i === 0 ? Color.Yellow : Color.SecondaryText }}
                detail={
                  <List.Item.Detail
                    markdown={[
                      `## ${m.model}`,
                      `Provider: **${m.provider}**`,
                      "",
                      `| Metric | Value |`,
                      `|---|---|`,
                      `| Cost | **${fmtUsd(m.cost_usd)}** |`,
                      `| Requests | ${m.requests.toLocaleString()} |`,
                      `| Avg cost/req | ${fmtUsd(avgCostPerReq)} |`,
                      `| Tokens | ${fmtTokens(m.tokens)} |`,
                      "",
                      `**Share of spend:** ${(fraction * 100).toFixed(1)}%`,
                      `\`${bar}\``,
                    ].join("\n")}
                  />
                }
                actions={
                  <ActionPanel>
                    <Action.CopyToClipboard title="Copy Model Name" content={m.model} />
                    <Action title="Refresh" icon={Icon.ArrowClockwise} onAction={refresh} />
                  </ActionPanel>
                }
              />
            );
          })}
        </List.Section>
      )}

      {noData && !loading && (
        <List.Section title="No data yet">
          <List.Item
            title="Make your first request"
            subtitle="Run: ./mr status · or use any OpenAI-compatible client"
            icon={Icon.Info}
            actions={
              <ActionPanel>
                <Action.OpenInBrowser title="Open Widget" url={p.widgetUrl} />
                <Action title="Refresh" icon={Icon.ArrowClockwise} onAction={refresh} />
              </ActionPanel>
            }
          />
        </List.Section>
      )}
    </List>
  );
}
