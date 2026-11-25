# -*- coding: utf-8 -*-
"""StoreGuard 单元测试 / Unit tests (unittest, stdlib only)."""

import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storeguard import core  # noqa: E402
from storeguard.cli import main  # noqa: E402

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
ANDROID_FIXTURE = os.path.join(FIXTURE_DIR, "android_sample")
IOS_FIXTURE = os.path.join(FIXTURE_DIR, "ios_sample")


class AndroidScanTests(unittest.TestCase):
    """Android 扫描规则验证 / Android rule checks."""

    def setUp(self):
        self.result = core.scan(ANDROID_FIXTURE, platform="android")
        self.ids = {f.rule_id for f in self.result.findings}

    def test_platform_detected(self):
        self.assertEqual(self.result.platform, "android")

    def test_exported_missing(self):
        self.assertIn("SG-AND-001", self.ids)

    def test_debuggable(self):
        self.assertIn("SG-AND-002", self.ids)

    def test_allow_backup(self):
        self.assertIn("SG-AND-003", self.ids)

    def test_cleartext(self):
        self.assertIn("SG-AND-004", self.ids)
        # Android 扫描不应产出 iOS 规则 / android scan must not emit ios rules
        self.assertFalse(any(i.startswith("SG-IOS") for i in self.ids))

    def test_data_extraction_rules_missing(self):
        self.assertIn("SG-AND-005", self.ids)

    def test_dangerous_permission(self):
        self.assertIn("SG-AND-006", self.ids)

    def test_network_security_config_missing(self):
        self.assertIn("SG-AND-007", self.ids)

    def test_sensitive_permission(self):
        self.assertIn("SG-AND-008", self.ids)

    def test_runtime_request_missing(self):
        self.assertIn("SG-AND-009", self.ids)

    def test_target_sdk_low(self):
        self.assertIn("SG-AND-010", self.ids)

    def test_severity_of_exported_finding_is_error(self):
        finding = next(f for f in self.result.findings if f.rule_id == "SG-AND-001")
        self.assertEqual(finding.severity, "ERROR")


class IOSScanTests(unittest.TestCase):
    """iOS 扫描规则验证 / iOS rule checks."""

    def setUp(self):
        self.result = core.scan(IOS_FIXTURE, platform="ios")
        self.ids = {f.rule_id for f in self.result.findings}

    def test_platform_detected(self):
        self.assertEqual(self.result.platform, "ios")

    def test_missing_camera_description_detected_but_placeholder_only(self):
        # 相机描述存在但为 TODO 占位 -> 只命中 SG-IOS-005
        self.assertIn("SG-IOS-005", self.ids)

    def test_privacy_manifest_missing(self):
        self.assertIn("SG-IOS-002", self.ids)

    def test_tracking_not_reported_without_att_usage(self):
        # fixture 未使用 ATTrackingManager -> 不应命中 SG-IOS-003
        self.assertNotIn("SG-IOS-003", self.ids)

    def test_required_reason_api_undeclared(self):
        # 使用 NSUserDefaults 但无隐私清单 -> 不触发 SG-IOS-004（无清单文件走 SG-IOS-002）
        self.assertNotIn("SG-IOS-004", self.ids)

    def test_background_modes(self):
        self.assertIn("SG-IOS-007", self.ids)

    def test_encryption_declaration_missing(self):
        self.assertIn("SG-IOS-006", self.ids)


class EngineTests(unittest.TestCase):
    """引擎与报告 / Engine and report rendering."""

    def test_auto_detects_android(self):
        result = core.scan(ANDROID_FIXTURE)
        self.assertEqual(result.platform, "android")

    def test_json_report_is_valid(self):
        result = core.scan(ANDROID_FIXTURE)
        data = json.loads(core.to_json(result))
        self.assertIn("summary", data)
        self.assertGreater(data["summary"]["error"], 0)

    def test_markdown_report_contains_findings(self):
        result = core.scan(IOS_FIXTURE)
        md = core.to_markdown(result)
        self.assertIn("StoreGuard", md)
        self.assertIn("SG-IOS-002", md)

    def test_rules_catalogue(self):
        rules = core.all_rules()
        ids = [r.rule_id for r in rules]
        self.assertEqual(len(ids), len(set(ids)))  # 规则编号唯一 / unique ids
        self.assertGreaterEqual(len(rules), 15)

    def test_unknown_project_platform(self):
        # 空目录不包含任何清单 / empty dir has no manifest
        import tempfile
        with tempfile.TemporaryDirectory() as empty:
            result = core.scan(empty, platform="android")
            self.assertEqual(result.platform, "unknown")

    def test_invalid_root_raises(self):
        with self.assertRaises(NotADirectoryError):
            core.scan(os.path.join(FIXTURE_DIR, "__no_such_dir__"))


class CliTests(unittest.TestCase):
    """CLI 行为验证 / CLI behaviour."""

    def test_cli_scan_exit_code_error(self):
        self.assertEqual(main(["scan", ANDROID_FIXTURE]), 1)

    def test_cli_json_output_file(self):
        out = os.path.join(FIXTURE_DIR, "_tmp_report.json")
        code = main(["scan", ANDROID_FIXTURE, "--format", "json", "--output", out])
        try:
            self.assertEqual(code, 1)
            with open(out, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertIn("findings", data)
        finally:
            os.remove(out)

    def test_cli_rules_command(self):
        self.assertEqual(main(["rules"]), 0)

    def test_module_entry_point(self):
        proc = subprocess.run(
            [sys.executable, "-m", "storeguard", "--version"],
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("StoreGuard", proc.stdout)


if __name__ == "__main__":
    unittest.main()
