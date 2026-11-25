import UIKit
import AVFoundation

class ViewController: UIViewController {
    let session = AVCaptureSession()
    let defaults = NSUserDefaults.standardUserDefaults

    override func viewDidLoad() {
        super.viewDidLoad()
        AVCaptureDevice.requestAccess(for: .video) { _ in }
    }
}
