import SwiftUI

@main
struct ModelRouterBarApp: App {
    @StateObject private var gateway = GatewayState()

    var body: some Scene {
        MenuBarExtra {
            ContentView()
                .environmentObject(gateway)
        } label: {
            MenuBarLabel()
                .environmentObject(gateway)
        }
        .menuBarExtraStyle(.window)
    }
}
