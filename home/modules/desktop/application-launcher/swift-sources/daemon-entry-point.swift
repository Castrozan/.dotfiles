import AppKit

@main
struct ApplicationLauncherDaemonEntryPoint {
    static func main() {
        let compositionRoot = ApplicationLauncherDaemonCompositionRoot()
        compositionRoot.bootstrapAndRunForever()
    }
}
