import SwiftUI

struct ContentView: View {
    @EnvironmentObject var gateway: GatewayState
    @State private var showSettings = false
    @State private var showHandoffPicker = false

    var body: some View {
        VStack(spacing: 0) {
            headerSection
            Divider()
            enterpriseSection
            Divider()
            costSection
            Divider()
            actionsSection
        }
        .frame(width: 300)
        .background(.ultraThinMaterial)
        .sheet(isPresented: $showSettings) { SettingsView().environmentObject(gateway) }
    }

    // MARK: - Header

    private var headerSection: some View {
        HStack(spacing: 10) {
            ZStack {
                Circle()
                    .fill(statusColor.opacity(0.15))
                    .frame(width: 34, height: 34)
                Circle()
                    .fill(statusColor)
                    .frame(width: 10, height: 10)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text("ModelRouter")
                    .font(.headline)
                Text(gateway.status.label)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Button { gateway.refresh() } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
            .help("Refresh")
            Button { showSettings = true } label: {
                Image(systemName: "gear")
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
            .help("Settings")
        }
        .padding(12)
    }

    private var statusColor: Color {
        switch gateway.status {
        case .healthy:  return .green
        case .degraded: return .yellow
        case .down:     return .red
        case .unknown:  return .gray
        }
    }

    // MARK: - Enterprise

    private var enterpriseSection: some View {
        VStack(spacing: 8) {
            HStack {
                Label("Enterprise Mode", systemImage: "lock.shield")
                    .font(.subheadline.weight(.medium))
                Spacer()
                Toggle("", isOn: Binding(
                    get: { gateway.enterprise.enterprise_mode },
                    set: { gateway.setEnterpriseMode($0) }
                ))
                .toggleStyle(.switch)
                .labelsHidden()
                .controlSize(.small)
            }

            if gateway.enterprise.enterprise_mode {
                enterpriseModeDetail
            }
        }
        .padding(12)
        .background(gateway.enterprise.enterprise_mode
            ? Color.blue.opacity(0.06)
            : Color.clear)
    }

    @ViewBuilder
    private var enterpriseModeDetail: some View {
        VStack(spacing: 6) {
            if let family = gateway.enterprise.locked_family {
                HStack(spacing: 4) {
                    Image(systemName: "pin.fill")
                        .font(.caption2)
                        .foregroundStyle(.blue)
                    Text("Locked to \(family)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                }
            }

            HStack(spacing: 8) {
                if gateway.enterprise.handoff_allowed {
                    // Active handoff banner
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.left.arrow.right.circle.fill")
                            .foregroundStyle(.orange)
                            .font(.subheadline)
                        VStack(alignment: .leading, spacing: 1) {
                            Text("Handoff active")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(.orange)
                            if let fam = gateway.enterprise.handoff_target_family {
                                Text("→ \(fam)")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            } else {
                                Text("any family allowed")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        Spacer()
                        Button("Cancel") { gateway.cancelHandoff() }
                            .buttonStyle(.bordered)
                            .controlSize(.mini)
                            .tint(.orange)
                    }
                    .padding(8)
                    .background(Color.orange.opacity(0.08))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                } else {
                    // Handoff trigger button
                    Button {
                        showHandoffPicker = true
                    } label: {
                        Label("Allow Handoff", systemImage: "arrow.left.arrow.right.circle")
                            .font(.caption.weight(.medium))
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                    .tint(.blue)
                    .popover(isPresented: $showHandoffPicker) {
                        HandoffPickerView(isPresented: $showHandoffPicker)
                            .environmentObject(gateway)
                    }
                }
            }
        }
    }

    // MARK: - Cost

    private var costSection: some View {
        VStack(spacing: 6) {
            HStack {
                Text("24h spend")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                Text(gateway.formattedCost(gateway.cost24h))
                    .font(.subheadline.weight(.semibold).monospacedDigit())
                Text("·")
                    .foregroundStyle(.secondary)
                Text("\(gateway.requests24h) req")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            if !gateway.topModels.isEmpty {
                let maxCost = gateway.topModels.map(\.cost_usd).max() ?? 1
                ForEach(gateway.topModels.prefix(3)) { m in
                    ModelCostRow(model: m, maxCost: maxCost)
                }
            }
        }
        .padding(12)
    }

    // MARK: - Actions

    private var actionsSection: some View {
        HStack(spacing: 8) {
            if gateway.status == .down {
                ActionButton("Start", icon: "play.fill", color: .green) { gateway.startGateway() }
            } else {
                ActionButton("Restart", icon: "arrow.clockwise", color: .orange) { gateway.restartGateway() }
                ActionButton("Stop", icon: "stop.fill", color: .red) { gateway.stopGateway() }
            }
            Spacer()
            ActionButton("Widget", icon: "chart.bar.fill", color: .blue) {
                NSWorkspace.shared.open(URL(string: gateway.widgetURL)!)
            }
            ActionButton("Logs", icon: "doc.text", color: .secondary) {
                let home = FileManager.default.homeDirectoryForCurrentUser.path
                NSWorkspace.shared.open(URL(fileURLWithPath: "\(home)/Dev/modelrouter/data/modelrouter.log"))
            }
        }
        .padding(12)
    }
}

// MARK: - Sub-views

struct ModelCostRow: View {
    let model: CostModel
    let maxCost: Double

    var body: some View {
        HStack(spacing: 6) {
            Text(shortName)
                .font(.caption2)
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .frame(width: 110, alignment: .leading)
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 2)
                        .fill(Color.primary.opacity(0.08))
                    RoundedRectangle(cornerRadius: 2)
                        .fill(barColor)
                        .frame(width: geo.size.width * CGFloat(model.cost_usd / max(maxCost, 0.000001)))
                }
            }
            .frame(height: 5)
            Text(fmtCost)
                .font(.caption2.monospacedDigit())
                .frame(width: 48, alignment: .trailing)
        }
    }

    private var shortName: String {
        let parts = model.model.split(separator: "/")
        return parts.last.map(String.init) ?? model.model
    }

    private var fmtCost: String {
        if model.cost_usd == 0 { return "$0.00" }
        if model.cost_usd < 0.001 { return String(format: "$%.5f", model.cost_usd) }
        return String(format: "$%.4f", model.cost_usd)
    }

    private var barColor: Color {
        switch model.provider.lowercased() {
        case "anthropic":  return .orange
        case "openai":     return .green
        case "groq":       return .blue
        case "google":     return .yellow
        case "deepseek":   return .purple
        case "mistral":    return .teal
        default:           return .gray
        }
    }
}

struct ActionButton: View {
    let label: String
    let icon: String
    let color: Color
    let action: () -> Void

    init(_ label: String, icon: String, color: Color = .accentColor, action: @escaping () -> Void) {
        self.label = label; self.icon = icon; self.color = color; self.action = action
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Image(systemName: icon).font(.system(size: 10))
                Text(label).font(.caption.weight(.medium))
            }
        }
        .buttonStyle(.bordered)
        .controlSize(.small)
        .tint(color)
    }
}

// MARK: - Handoff Picker

struct HandoffPickerView: View {
    @EnvironmentObject var gateway: GatewayState
    @Binding var isPresented: Bool

    private let families = ["anthropic", "openai", "groq", "google", "mistral", "deepseek", "local"]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Allow Handoff")
                .font(.headline)
            Text("Grant a one-shot override — next request routes outside\nthe locked family, then locks back automatically.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)

            Divider()

            Button {
                gateway.allowHandoff(targetFamily: nil)
                isPresented = false
            } label: {
                Label("Any family (unrestricted)", systemImage: "arrow.left.arrow.right")
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .buttonStyle(.bordered)

            Text("Or choose target family:")
                .font(.caption)
                .foregroundStyle(.secondary)

            ForEach(families, id: \.self) { fam in
                Button {
                    gateway.allowHandoff(targetFamily: fam)
                    isPresented = false
                } label: {
                    HStack {
                        Image(systemName: familyIcon(fam))
                            .frame(width: 18)
                        Text(fam.capitalized)
                        Spacer()
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .buttonStyle(.bordered)
            }
        }
        .padding(16)
        .frame(width: 260)
    }

    private func familyIcon(_ family: String) -> String {
        switch family {
        case "anthropic":  return "a.circle"
        case "openai":     return "o.circle"
        case "groq":       return "bolt.circle"
        case "google":     return "g.circle"
        case "mistral":    return "wind"
        case "deepseek":   return "arrow.down.circle"
        case "local":      return "desktopcomputer"
        default:           return "circle"
        }
    }
}
