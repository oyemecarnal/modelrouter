import { getPreferenceValues, showToast, Toast } from "@raycast/api";
import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

export interface Preferences {
  gatewayUrl: string;
  masterKey: string;
  widgetUrl: string;
  rootPath: string;
}

export function prefs(): Preferences {
  const p = getPreferenceValues<Preferences>();
  return {
    gatewayUrl: (p.gatewayUrl || "http://127.0.0.1:3000").replace(/\/$/, ""),
    masterKey: p.masterKey || "",
    widgetUrl: (p.widgetUrl || "http://localhost:8765").replace(/\/$/, ""),
    rootPath: (p.rootPath || "~/Dev/modelrouter").replace(/^~/, os.homedir()),
  };
}

// ── .env reader (fallback when no key is set in preferences) ─────────────────

export function readEnvKey(rootPath: string, varName: string): string {
  const envPath = path.join(rootPath, ".env");
  if (!fs.existsSync(envPath)) return "";
  try {
    const lines = fs.readFileSync(envPath, "utf-8").split("\n");
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("#") || !trimmed.includes("=")) continue;
      const [k, ...rest] = trimmed.split("=");
      if (k.trim() === varName) return rest.join("=").trim();
    }
  } catch {
    // ignore
  }
  return "";
}

export function masterKey(p: Preferences): string {
  return p.masterKey || readEnvKey(p.rootPath, "MODELROUTER_MASTER_KEY");
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

export interface GatewayHealth {
  status: "healthy" | "alive" | "degraded" | "down";
  healthy_instances?: number;
  total_instances?: number;
  router_model_names?: string[];
}

export async function fetchHealth(p: Preferences): Promise<GatewayHealth> {
  const key = masterKey(p);
  try {
    const res = await fetch(`${p.gatewayUrl}/health`, {
      headers: key ? { Authorization: `Bearer ${key}` } : {},
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) return { status: "degraded" };
    const json = (await res.json()) as Record<string, unknown>;
    const healthy = typeof json.healthy_instances === "number" ? json.healthy_instances : undefined;
    return {
      status: healthy !== undefined && healthy > 0 ? "healthy" : "alive",
      healthy_instances: healthy,
      total_instances:
        typeof json.total_instances === "number" ? json.total_instances : undefined,
      router_model_names: Array.isArray(json.router_model_names)
        ? (json.router_model_names as string[])
        : undefined,
    };
  } catch {
    return { status: "down" };
  }
}

export interface ModelEntry {
  id: string;
}

export async function fetchModels(p: Preferences): Promise<ModelEntry[]> {
  const key = masterKey(p);
  if (!key) return [];
  try {
    const res = await fetch(`${p.gatewayUrl}/v1/models`, {
      headers: { Authorization: `Bearer ${key}` },
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) return [];
    const json = (await res.json()) as { data?: unknown[] };
    return (json.data || []) as ModelEntry[];
  } catch {
    return [];
  }
}

// ── Snapshot (from widget server) ─────────────────────────────────────────────

export interface CostWindow {
  total_usd: number;
  requests: number;
  tokens: number;
}

export interface CostModel {
  model: string;
  provider: string;
  cost_usd: number;
  tokens: number;
  requests: number;
}

export interface CostRollup {
  updated_at?: number;
  windows: Record<string, CostWindow>;
  by_model: Record<string, CostModel[]>;
  no_data?: boolean;
  error?: string;
}

export interface Snapshot {
  costRollup?: CostRollup;
  policyPresets?: Record<string, unknown>;
}

export async function fetchSnapshot(p: Preferences): Promise<Snapshot> {
  try {
    const res = await fetch(`${p.widgetUrl}/snapshot.json`, {
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) return {};
    return (await res.json()) as Snapshot;
  } catch {
    return {};
  }
}

// ── Shell exec (start/stop gateway) ──────────────────────────────────────────

export function runMr(rootPath: string, command: string): { ok: boolean; output: string } {
  const mrPath = path.join(rootPath, "mr");
  if (!fs.existsSync(mrPath)) {
    return { ok: false, output: `mr not found at ${mrPath}` };
  }
  try {
    const output = execSync(`bash "${mrPath}" ${command}`, {
      cwd: rootPath,
      timeout: 30_000,
      env: { ...process.env, PATH: `/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:${process.env.PATH}` },
    }).toString();
    return { ok: true, output };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return { ok: false, output: msg };
  }
}

// ── Formatting helpers ────────────────────────────────────────────────────────

export function fmtUsd(usd: number): string {
  if (usd === 0) return "$0.00";
  if (usd < 0.001) return `$${usd.toFixed(6)}`;
  if (usd < 0.01) return `$${usd.toFixed(4)}`;
  return `$${usd.toFixed(3)}`;
}

export function fmtTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export function statusIcon(status: GatewayHealth["status"]): string {
  return { healthy: "🟢", alive: "🟡", degraded: "🟠", down: "🔴" }[status];
}

export async function withToast<T>(
  title: string,
  fn: () => Promise<T>
): Promise<T | undefined> {
  const toast = await showToast({ style: Toast.Style.Animated, title });
  try {
    const result = await fn();
    toast.style = Toast.Style.Success;
    toast.title = title + " done";
    return result;
  } catch (e: unknown) {
    toast.style = Toast.Style.Failure;
    toast.title = "Failed";
    toast.message = e instanceof Error ? e.message : String(e);
    return undefined;
  }
}
