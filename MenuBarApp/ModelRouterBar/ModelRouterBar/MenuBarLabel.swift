import SwiftUI

/// Status bar icon — shows a router glyph with a colored dot.
struct MenuBarLabel: View {
    @EnvironmentObject var gateway: GatewayState

    var body: some View {
        HStack(spacing: 3) {
            Image(systemName: "arrow.triangle.branch")
                .font(.system(size: 13, weight: .medium))
            Circle()
                .fill(dotColor)
                .frame(width: 6, height: 6)
        }
    }

    private var dotColor: Color {
        switch gateway.status {
        case .healthy:  return .green
        case .degraded: return .yellow
        case .down:     return .red
        case .unknown:  return .gray
        }
    }
}
