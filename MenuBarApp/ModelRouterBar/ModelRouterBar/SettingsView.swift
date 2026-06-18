import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var gateway: GatewayState
    @Environment(\.dismiss) private var dismiss

    @State private var gatewayURL: String = ""
    @State private var widgetURL: String  = ""
    @State private var masterKey: String  = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Settings")
                .font(.headline)

            Group {
                field("Gateway URL", value: $gatewayURL, placeholder: "http://127.0.0.1:3000")
                field("Widget URL", value: $widgetURL, placeholder: "http://localhost:8765")
                field("Master Key", value: $masterKey, placeholder: "sk-…", secure: true)
            }

            Text("The master key is read from preferences. If empty, the app\nreads MODELROUTER_MASTER_KEY directly from ~/Dev/modelrouter/.env.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)

            Divider()

            HStack {
                Button("Cancel") { dismiss() }
                    .buttonStyle(.bordered)
                Spacer()
                Button("Save") {
                    gateway.gatewayURL = gatewayURL
                    gateway.widgetURL  = widgetURL
                    gateway.masterKey  = masterKey
                    gateway.savePreferences()
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(20)
        .frame(width: 320)
        .onAppear {
            gatewayURL = gateway.gatewayURL
            widgetURL  = gateway.widgetURL
            masterKey  = gateway.masterKey
        }
    }

    @ViewBuilder
    private func field(_ label: String, value: Binding<String>, placeholder: String, secure: Bool = false) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.caption.weight(.medium))
                .foregroundStyle(.secondary)
            if secure {
                SecureField(placeholder, text: value)
                    .textFieldStyle(.roundedBorder)
                    .font(.system(.body, design: .monospaced))
            } else {
                TextField(placeholder, text: value)
                    .textFieldStyle(.roundedBorder)
                    .font(.system(.body, design: .monospaced))
            }
        }
    }
}
