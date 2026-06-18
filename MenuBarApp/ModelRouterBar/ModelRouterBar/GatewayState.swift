import Foundation
import Combine

// MARK: - Data models

enum GatewayStatus {
    case healthy, degraded, down, unknown

    var color: String {
        switch self {
        case .healthy:  return "statusGreen"
        case .degraded: return "statusYellow"
        case .down:     return "statusRed"
        case .unknown:  return "statusGray"
        }
    }

    var label: String {
        switch self {
        case .healthy:  return "Healthy"
        case .degraded: return "Degraded"
        case .down:     return "Down"
        case .unknown:  return "Checking…"
        }
    }
}

struct CostWindow: Codable {
    let total_usd: Double
    let requests: Int
    let tokens: Int
}

struct CostModel: Codable, Identifiable {
    var id: String { model }
    let model: String
    let provider: String
    let cost_usd: Double
    let tokens: Int
    let requests: Int
}

struct CostRollup: Codable {
    let windows: [String: CostWindow]
    let by_model: [String: [CostModel]]
    let no_data: Bool?
}

struct EnterpriseState: Codable {
    var enterprise_mode: Bool
    var handoff_allowed: Bool
    var handoff_target_family: String?
    var handoff_expires_at: Double?
    var locked_family: String?
    var updated_at: Int?
}

// MARK: - Observable state

@MainActor
class GatewayState: ObservableObject {
    // Preferences (read from UserDefaults, populated by SettingsView)
    @Published var gatewayURL: String = UserDefaults.standard.string(forKey: "gatewayURL") ?? "http://127.0.0.1:3000"
    @Published var widgetURL: String  = UserDefaults.standard.string(forKey: "widgetURL")  ?? "http://localhost:8765"
    @Published var masterKey: String  = UserDefaults.standard.string(forKey: "masterKey")  ?? ""

    // Live state
    @Published var status: GatewayStatus = .unknown
    @Published var healthyInstances: Int = 0
    @Published var totalInstances: Int = 0
    @Published var cost24h: Double = 0
    @Published var requests24h: Int = 0
    @Published var topModels: [CostModel] = []
    @Published var enterprise: EnterpriseState = EnterpriseState(
        enterprise_mode: false,
        handoff_allowed: false,
        handoff_target_family: nil,
        handoff_expires_at: nil,
        locked_family: nil,
        updated_at: nil
    )
    @Published var isLoading: Bool = false
    @Published var lastError: String?
    @Published var lastRefreshed: Date?

    private var timer: Timer?

    init() {
        startPolling()
    }

    func startPolling() {
        refresh()
        timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            Task { await self?.refresh() }
        }
    }

    func refresh() {
        Task {
            await withTaskGroup(of: Void.self) { group in
                group.addTask { await self.fetchHealth() }
                group.addTask { await self.fetchCost() }
                group.addTask { await self.fetchEnterprise() }
            }
            self.lastRefreshed = Date()
        }
    }

    // MARK: - Health

    private func fetchHealth() async {
        guard let url = URL(string: "\(gatewayURL)/health") else { return }
        var req = URLRequest(url: url, timeoutInterval: 5)
        if !masterKey.isEmpty { req.setValue("Bearer \(masterKey)", forHTTPHeaderField: "Authorization") }
        do {
            let (data, _) = try await URLSession.shared.data(for: req)
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                let healthy = json["healthy_instances"] as? Int ?? 0
                let total   = json["total_instances"]   as? Int ?? 0
                self.healthyInstances = healthy
                self.totalInstances   = total
                self.status = healthy > 0 ? .healthy : (total > 0 ? .degraded : .down)
            }
        } catch {
            self.status = .down
        }
    }

    // MARK: - Cost

    private func fetchCost() async {
        guard let url = URL(string: "\(widgetURL)/snapshot.json") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let rollupRaw = json["costRollup"] {
                let rollupData = try JSONSerialization.data(withJSONObject: rollupRaw)
                let rollup = try JSONDecoder().decode(CostRollup.self, from: rollupData)
                self.cost24h     = rollup.windows["24h"]?.total_usd  ?? 0
                self.requests24h = rollup.windows["24h"]?.requests    ?? 0
                self.topModels   = (rollup.by_model["24h"] ?? []).prefix(5).map { $0 }
            }
        } catch { /* cost data not critical */ }
    }

    // MARK: - Enterprise

    private func fetchEnterprise() async {
        guard let url = URL(string: "\(widgetURL)/enterprise/state") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let state = try JSONDecoder().decode(EnterpriseState.self, from: data)
            self.enterprise = state
        } catch { /* enterprise state optional */ }
    }

    // MARK: - Actions

    func setEnterpriseMode(_ enabled: Bool, lockedFamily: String? = nil) {
        Task {
            guard let url = URL(string: "\(widgetURL)/enterprise/mode") else { return }
            var req = URLRequest(url: url)
            req.httpMethod = "POST"
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            var body: [String: Any] = ["enabled": enabled]
            if let fam = lockedFamily { body["locked_family"] = fam }
            req.httpBody = try? JSONSerialization.data(withJSONObject: body)
            _ = try? await URLSession.shared.data(for: req)
            await fetchEnterprise()
        }
    }

    func allowHandoff(targetFamily: String? = nil, ttlSeconds: Double = 120) {
        Task {
            guard let url = URL(string: "\(widgetURL)/enterprise/handoff") else { return }
            var req = URLRequest(url: url)
            req.httpMethod = "POST"
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            var body: [String: Any] = ["ttl_seconds": ttlSeconds]
            if let fam = targetFamily { body["family"] = fam }
            req.httpBody = try? JSONSerialization.data(withJSONObject: body)
            _ = try? await URLSession.shared.data(for: req)
            await fetchEnterprise()
        }
    }

    func cancelHandoff() {
        Task {
            guard let url = URL(string: "\(widgetURL)/enterprise/cancel-handoff") else { return }
            var req = URLRequest(url: url)
            req.httpMethod = "POST"
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            _ = try? await URLSession.shared.data(for: req)
            await fetchEnterprise()
        }
    }

    func startGateway() {
        runMr("start")
    }

    func stopGateway() {
        runMr("stop")
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) { self.refresh() }
    }

    func restartGateway() {
        runMr("restart")
        DispatchQueue.main.asyncAfter(deadline: .now() + 4) { self.refresh() }
    }

    private func runMr(_ command: String) {
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        let mrPath = "\(home)/Dev/modelrouter/mr"
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/bin/bash")
        task.arguments = ["-c", "\"\(mrPath)\" \(command)"]
        try? task.run()
    }

    func savePreferences() {
        UserDefaults.standard.set(gatewayURL, forKey: "gatewayURL")
        UserDefaults.standard.set(widgetURL,  forKey: "widgetURL")
        UserDefaults.standard.set(masterKey,  forKey: "masterKey")
        refresh()
    }

    // MARK: - Helpers

    func formattedCost(_ usd: Double) -> String {
        if usd == 0 { return "$0.00" }
        if usd < 0.001 { return String(format: "$%.6f", usd) }
        if usd < 0.01  { return String(format: "$%.4f", usd) }
        return String(format: "$%.3f", usd)
    }
}
