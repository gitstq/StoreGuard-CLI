# -*- coding: utf-8 -*-
"""iOS 平台规则与检查器 / iOS rules and checkers.

解析 Info.plist 与 PrivacyInfo.xcprivacy，结合 Swift/ObjC 源码关键词，
检测 App Store 常见被拒风险（隐私描述缺失、占位文案、必需理由 API 未申报等）。
Pure stdlib: plist parsed via xml.etree (supports XML plists).
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET

from .models import Rule, ScanResult, Severity

# 隐私 API 使用痕迹 -> 所需 Info.plist 键 / code keyword -> required usage key
PRIVACY_API_MAP = {
    "UIImagePickerController": "NSPhotoLibraryUsageDescription",
    "PHPhotoLibrary": "NSPhotoLibraryUsageDescription",
    "AVCaptureDevice": "NSCameraUsageDescription",
    "AVAudioRecorder": "NSMicrophoneUsageDescription",
    "AVAudioSession": "NSMicrophoneUsageDescription",
    "CLLocationManager": "NSLocationWhenInUseUsageDescription",
    "CNContactStore": "NSContactsUsageDescription",
    "EKEventStore": "NSCalendarsUsageDescription",
    "CBPeripheralManager": "NSBluetoothPeripheralUsageDescription",
    "CBCentralManager": "NSBluetoothPeripheralUsageDescription",
    "UNUserNotificationCenter": "NSUserNotificationsUsageDescription",
}

# Apple 必需理由 API（PrivacyInfo.xcprivacy 申报范围） / required-reason API keywords
REQUIRED_REASON_APIS = {
    "NSUserDefaults": "CA92.1（用户默认值写入）",
    "FileHandle.creationDate": "C617.1（文件时间戳）",
    "modificationDate": "C617.1（文件时间戳）",
    "systemUptime": "35F9.1（系统启动时间）",
    "mach_absolute_time": "35F9.1（系统启动时间）",
    "volumeAvailableCapacity": "E174.1（磁盘空间）",
}

PLACEHOLDER_PATTERNS = [
    re.compile(r"^\s*(TODO|TBD|XXX|N/A|None|test|placeholder)\s*$", re.I),
]

RULES = [
    Rule("SG-IOS-001", "ios", Severity.ERROR,
         "源码使用了隐私 API 但 Info.plist 缺少对应用途描述",
         "访问相机/相册/定位等隐私能力而缺少 NSxxxUsageDescription 会直接崩溃，"
         "且是 App Store 审核最常见的被拒原因（Guideline 5.1.1）。",
         "在 Info.plist 中补充对应 NSxxxUsageDescription 并写明具体使用场景。"),
    Rule("SG-IOS-002", "ios", Severity.WARNING,
         "缺少 PrivacyInfo.xcprivacy 隐私清单",
         "Apple 要求上架应用携带隐私清单文件，说明数据收集与必需理由 API。",
         "在 App target 中添加 PrivacyInfo.xcprivacy 并如实申报。"),
    Rule("SG-IOS-003", "ios", Severity.ERROR,
         "使用了广告追踪 API 但缺少 NSUserTrackingUsageDescription",
         "引用 ATTrackingManager/ASIdentifierManager 而缺少追踪用途描述会被拒（Guideline 5.1.1/2.1）。",
         "添加 NSUserTrackingUsageDescription 并接入 ATT 授权流程。"),
    Rule("SG-IOS-004", "ios", Severity.ERROR,
         "使用了必需理由 API 但未在隐私清单中申报",
         "NSUserDefaults/文件时间戳/系统启动时间/磁盘空间等 API 属 Apple 必需理由 API，"
         "未申报会导致审核被拒。",
         "在 PrivacyInfo.xcprivacy 的 NSPrivacyAccessedAPITypes 中补充对应 Category。"),
    Rule("SG-IOS-005", "ios", Severity.ERROR,
         "用途描述为占位文案或过短",
         "TODO/无意义文案或过短的用途描述会被判定为不符合元数据要求（Guideline 2.3 / 5.1.1）。",
         "写明具体业务场景，例如“拍摄头像上传需要使用相机”。"),
    Rule("SG-IOS-006", "ios", Severity.INFO,
         "未声明 ITSAppUsesNonExemptEncryption",
         "未声明加密豁免情况可能延长审核时间。",
         "在 Info.plist 中声明 ITSAppUsesNonExemptEncryption=true（仅使用系统加密时）。"),
    Rule("SG-IOS-007", "ios", Severity.WARNING,
         "声明了敏感 UIBackgroundModes",
         "audio/location/voip 等后台模式需与核心功能匹配，滥用会导致被拒（Guideline 2.5.4）。",
         "确认后台模式确属核心功能，否则移除。"),
]


def _find_files(root: str, names, skip_dirs=("build", ".git", "Pods", "DerivedData")):
    """按文件名定位 / Locate files by exact name (case-insensitive)."""
    wanted = {n.lower() for n in names}
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            if fn.lower() in wanted:
                found.append(os.path.join(dirpath, fn))
    return found


def _plist_dict(path: str):
    """解析 XML 格式 plist / Parse XML plist into a plain dict."""
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != "plist" or len(root) == 0:
        return {}, root
    return _plist_node(root[0]), root


def _plist_node(node):
    """递归转换 plist 节点 / Convert a plist node recursively."""
    tag = node.tag
    if tag == "dict":
        result = {}
        children = list(node)
        for i in range(0, len(children) - 1, 2):
            key = children[i].text or ""
            result[key] = _plist_node(children[i + 1])
        return result
    if tag == "array":
        return [_plist_node(c) for c in node]
    if tag in ("true",):
        return True
    if tag in ("false",):
        return False
    return node.text or ""


def _iter_source_files(root: str):
    """遍历 Swift/ObjC 源码 / Iterate over Swift/ObjC sources."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in ("build", ".git", "Pods", "DerivedData", "node_modules")]
        for fn in filenames:
            if fn.endswith((".swift", ".m", ".mm")):
                yield os.path.join(dirpath, fn)


def scan_ios(root: str, result: ScanResult) -> None:
    """执行 iOS 扫描 / Run iOS checks and append findings."""
    info_paths = _find_files(root, ["Info.plist"])
    if not info_paths:
        return  # 非 iOS 项目 / not an iOS project
    result.platform = "ios" if result.platform == "unknown" else result.platform
    info_path = info_paths[0]
    rel = os.path.relpath(info_path, root)
    rules_by_id = {r.rule_id: r for r in RULES}

    try:
        plist, _ = _plist_dict(info_path)
    except (ET.ParseError, OSError) as exc:
        result.findings.append(rules_by_id["SG-IOS-001"].finding(
            "Info.plist 无法解析：%s" % exc, rel, 1))
        return

    # 源码隐私 API 扫描 / source-level privacy API scan
    used_apis = set()
    code_uses_tracking = False
    required_reason_hits = {}
    source_files = 0
    for src in _iter_source_files(root):
        source_files += 1
        try:
            with open(src, "r", encoding="utf-8", errors="replace") as fh:
                code = fh.read()
        except OSError:
            continue
        for api in PRIVACY_API_MAP:
            if api in code:
                used_apis.add(api)
        if "ATTrackingManager" in code or "ASIdentifierManager" in code:
            code_uses_tracking = True
        for api in REQUIRED_REASON_APIS:
            if api.split(".")[0] in code:
                required_reason_hits.setdefault(api, os.path.relpath(src, root))

    # SG-IOS-001 缺少用途描述 / missing usage descriptions
    for api in sorted(used_apis):
        key = PRIVACY_API_MAP[api]
        value = plist.get(key)
        if not isinstance(value, str) or not value.strip():
            result.findings.append(rules_by_id["SG-IOS-001"].finding(
                "源码使用 %s，但 Info.plist 缺少 %s" % (api, key), rel, 1))

    # SG-IOS-005 占位/过短描述 / placeholder or too-short descriptions
    for key, value in plist.items():
        if key.endswith("UsageDescription") and isinstance(value, str):
            stripped = value.strip()
            if len(stripped) < 10 or any(p.match(stripped) for p in PLACEHOLDER_PATTERNS):
                result.findings.append(rules_by_id["SG-IOS-005"].finding(
                    "%s 内容无效或过短：%r" % (key, value), rel, 1))

    # SG-IOS-003 追踪描述 / tracking description
    if code_uses_tracking and not plist.get("NSUserTrackingUsageDescription"):
        result.findings.append(rules_by_id["SG-IOS-003"].finding(
            "源码使用 ATTrackingManager/ASIdentifierManager，但缺少 NSUserTrackingUsageDescription",
            rel, 1))

    # SG-IOS-002 / SG-IOS-004 隐私清单 / privacy manifest
    privacy_paths = _find_files(root, ["PrivacyInfo.xcprivacy"])
    if not privacy_paths:
        result.findings.append(rules_by_id["SG-IOS-002"].finding(
            "项目中未找到 PrivacyInfo.xcprivacy", rel, 1))
    else:
        declared = set()
        try:
            p_plist, _ = _plist_dict(privacy_paths[0])
            for item in p_plist.get("NSPrivacyAccessedAPITypes", []) or []:
                if isinstance(item, dict):
                    declared.add(item.get("NSPrivacyAccessedAPIType", ""))
        except (ET.ParseError, OSError):
            pass
        if source_files and required_reason_hits and not declared:
            for api, src in sorted(required_reason_hits.items()):
                result.findings.append(rules_by_id["SG-IOS-004"].finding(
                    "源码使用必需理由 API %s（%s），但隐私清单未申报" % (
                        api, REQUIRED_REASON_APIS[api]),
                    os.path.relpath(privacy_paths[0], root), 1))

    # SG-IOS-006 加密豁免 / encryption exemption
    if "ITSAppUsesNonExemptEncryption" not in plist:
        result.findings.append(rules_by_id["SG-IOS-006"].finding(
            "Info.plist 未声明 ITSAppUsesNonExemptEncryption", rel, 1))

    # SG-IOS-007 后台模式 / background modes
    bg = plist.get("UIBackgroundModes")
    if isinstance(bg, list):
        sensitive = [m for m in bg if m in ("audio", "location", "voip", "bluetooth-central")]
        if sensitive:
            result.findings.append(rules_by_id["SG-IOS-007"].finding(
                "声明了敏感后台模式：%s" % ", ".join(sensitive), rel, 1))
