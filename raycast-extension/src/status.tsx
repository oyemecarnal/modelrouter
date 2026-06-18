import {
  Action,
  ActionPanel,
  Color,
  Detail,
  Icon,
  List,
  showToast,
  Toast,
  useNavigation,
} from "@raycast/api";
import { useEffect, useState } from "react";
import { fetchHealth, fetchModels, GatewayHealth, masterKey, ModelEntry, prefs, runMr, statusIcon } from "./lib";

export default function StatusCommand() {
  const p = prefs();
  const [health, setHealth] = useState<GatewayHealth | null>(null);
  const [models, setModels] = useState<ModelEntry[]>([]);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    const [h, m] = await Promise.all([fetchHealth(p), fetchModels(p)]);
    setHealth(h);
    setModels(m);
    setLoading(false);
  }

  useEffect(() => { refresh(); }, []);

  const key = masterKey(p);
  const endpoint = `${p.gatewayUrl}/v1`;
  const icon = health ? statusIcon(health.status) : "⏳";
  const statusLabel = health?.status ?? "checking...";

  const healthyCount = health?.healthy_instances ?? "—";
  const totalCount = health?.total_instances ?? "—";

  return (
    <List isLoading={loading} navigationTitle="Gateway Status">
      <List.Section title={`ModelRouter  ${icon} ${statusLabel}`}>
        <List.Item
          title="Endpoint"
          subtitle={endpoint}
          accessories={[{ text: key ? "key set" : "⚠ no key", tooltip: key ? "Key loaded from prefs or .env" : "Set key in extension preferences" }]}
          actions={
            <ActionPanel>
              <Action.CopyToClipboard title="Copy Endpoint URL" content={endpoint} />
              {key && <Action.CopyToClipboard title="Copy Master Key" content={key} />}
              <Action title="Refresh" onAction={refresh} icon={Icon.ArrowClockwise} shortcut={{ modifiers: ["cmd"], key: "r" }} />
            </ActionPanel>
          }
        />
        <List.Item
          title="Healthy instances"
          subtitle={`${healthyCount} / ${totalCount}`}
          icon={health?.status === "healthy" ? { source: Icon.CheckCircle, tintColor: Color.Green } : { source: Icon.XMarkCircle, tintColor: Color.Red }}
          actions={
            <ActionPanel>
              <Action title="Refresh" onAction={refresh} icon={Icon.ArrowClockwise} />
            </ActionPanel>
          }
        />
      </List.Section>

      {health?.status === "down" && (
        <List.Section title="Gateway is down">
          <List.Item
            title="Start Gateway"
            subtitle="Run ./mr start"
            icon={{ source: Icon.Play, tintColor: Color.Green }}
            actions={
              <ActionPanel>
                <Action
                  title="Start Gateway"
                  icon={Icon.Play}
                  onAction={async () => {
                    const toast = await showToast({ style: Toast.Style.Animated, title: "Starting gateway…" });
                    const result = runMr(p.rootPath, "start");
                    if (result.ok) {
                      toast.style = Toast.Style.Success;
                      toast.title = "Gateway started";
                      setTimeout(refresh, 3000);
                    } else {
                      toast.style = Toast.Style.Failure;
                      toast.title = "Failed to start";
                      toast.message = result.output.slice(0, 200);
                    }
                  }}
                />
              </ActionPanel>
            }
          />
        </List.Section>
      )}

      {health?.status !== "down" && (
        <List.Section title="Controls">
          <List.Item
            title="Stop Gateway"
            subtitle="Run ./mr stop"
            icon={{ source: Icon.Stop, tintColor: Color.Red }}
            actions={
              <ActionPanel>
                <Action
                  title="Stop Gateway"
                  icon={Icon.Stop}
                  onAction={async () => {
                    const toast = await showToast({ style: Toast.Style.Animated, title: "Stopping gateway…" });
                    const result = runMr(p.rootPath, "stop");
                    toast.style = result.ok ? Toast.Style.Success : Toast.Style.Failure;
                    toast.title = result.ok ? "Gateway stopped" : "Stop failed";
                    if (!result.ok) toast.message = result.output.slice(0, 200);
                    if (result.ok) setTimeout(refresh, 1500);
                  }}
                />
                <Action
                  title="Restart Gateway"
                  icon={Icon.ArrowClockwise}
                  onAction={async () => {
                    const toast = await showToast({ style: Toast.Style.Animated, title: "Restarting…" });
                    const result = runMr(p.rootPath, "restart");
                    toast.style = result.ok ? Toast.Style.Success : Toast.Style.Failure;
                    toast.title = result.ok ? "Restarted" : "Restart failed";
                    if (!result.ok) toast.message = result.output.slice(0, 200);
                    if (result.ok) setTimeout(refresh, 4000);
                  }}
                />
              </ActionPanel>
            }
          />
        </List.Section>
      )}

      {models.length > 0 && (
        <List.Section title={`Active Models (${models.length})`}>
          {models.slice(0, 20).map((m) => (
            <List.Item
              key={m.id}
              title={m.id}
              icon={Icon.Layers}
              actions={
                <ActionPanel>
                  <Action.CopyToClipboard title="Copy Model ID" content={m.id} />
                </ActionPanel>
              }
            />
          ))}
        </List.Section>
      )}

      <List.Section title="Quick Actions">
        <List.Item
          title="Open Widget Dashboard"
          subtitle={p.widgetUrl}
          icon={Icon.Globe}
          actions={
            <ActionPanel>
              <Action.OpenInBrowser title="Open Widget" url={p.widgetUrl} />
            </ActionPanel>
          }
        />
        <List.Item
          title="View Gateway Logs"
          subtitle={`${p.rootPath}/data/modelrouter.log`}
          icon={Icon.Document}
          actions={
            <ActionPanel>
              <Action.Open
                title="Open Log in Default App"
                target={`${p.rootPath}/data/modelrouter.log`}
              />
              <Action.ShowInFinder title="Show in Finder" path={`${p.rootPath}/data`} />
            </ActionPanel>
          }
        />
      </List.Section>
    </List>
  );
}
