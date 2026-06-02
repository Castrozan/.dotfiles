import CoreGraphics
import Darwin
import Foundation

enum DaemonConfiguration {
    static let commandSocketPath = "/tmp/workspace-switcher.sock"
    static let activationFlagFilePath = "/tmp/workspace-switcher.active"
    static let performanceLogFilePath = "/tmp/workspace-switcher-perf.log"

    static let cardWidth: CGFloat = 140
    static let cardHeight: CGFloat = 120
    static let cardIconSize: CGFloat = 64
    static let cardSpacing: CGFloat = 12
    static let overlayPadding: CGFloat = 16
    static let overlayCornerRadius: CGFloat = 14
    static let cardCornerRadius: CGFloat = 10
    static let titleFontSize: CGFloat = 11
    static let selectionBorderWidth: CGFloat = 3
    static let cardIconTopPadding: CGFloat = 16
    static let cardTitleHorizontalInset: CGFloat = 6
    static let cardTitleBottomOffset: CGFloat = 4
    static let cardTitleHeight: CGFloat = 28

    static let commitTimeoutSeconds: TimeInterval = 10.0
    static let datagramReadBufferSize = 4096
    static let kernelReceiveBufferBytes: Int32 = 1024 * 1024
    static let commandSocketFileMode: mode_t = 0o666
    static let aerospaceIpcTimeoutSeconds: Int = 2
}
