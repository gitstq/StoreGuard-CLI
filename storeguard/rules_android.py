# -*- coding: utf-8 -*-
"""Android 平台规则与检查器 / Android rules and checkers.

解析 AndroidManifest.xml 并结合源码关键词，检测 Google Play 常见被拒风险。
Parse AndroidManifest.xml (plus light source keyword checks) to detect common
Google Play rejection risks. Pure stdlib, no external dependencies.
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET

from .models import Rule, ScanResult, Severity

# Android 命名空间 / Android manifest namespace
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

# 高敏感权限清单（需运行时授权或政策重点审查）
DANGEROUS_PERMISSIONS = {
    "CAMERA", "RECORD_AUDIO",
    "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION",
    "ACCESS_BACKGROUND_LOCATION",
    "READ_CONTACTS", "WRITE_CONTACTS",
    "READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE",
    "READ_MEDIA_IMAGES", "READ_MEDIA_VIDEO", "READ_MEDIA_AUDIO",
    "CALL_PHONE", "SEND_SMS", "READ_SMS", "RECEIVE_SMS",
    "READ_PHONE_STATE", "READ_CALL_LOG",
    "BODY_SENSORS", "ACTIVITY_RECOGNITION",
}

# 政策敏感权限（Google Play 审查重点）
SENSITIVE_POLICY_PERMISSIONS = {
    "REQUEST_INSTALL_PACKAGES": "安装其它应用需满足 Google Play 特定政策，极易触发下架",
    "RECEIVE_BOOT_COMPLETED": "开机自启需有明确核心功能支撑",
    "SYSTEM_ALERT_WINDOW": "悬浮窗权限易被判定为恶意行为",
    "PACKAGE_USAGE_STATS": "使用情况访问权限属受限权限",
    "QUERY_ALL_PACKAGES": "查询全部应用列表属受限权限",
}

RUNTIME_HINT_KEYWORDS = [
    "requestPermissions", "ActivityCompat.requestPermissions",
    "PermissionChecker", "checkSelfPermission",
]

RULES = [
    Rule("SG-AND-001", "android", Severity.ERROR,
         "带 intent-filter 的组件缺少显式 android:exported",
         "targetSdk 31+ 时，含 intent-filter 的组件必须显式声明 exported，"
         "否则安装失败；误导出的组件也是商店审核风险。",
         "为每个含 intent-filter 的 activity/service/receiver 显式设置 android:exported=\"true|false\"。"),
    Rule("SG-AND-002", "android", Severity.ERROR,
         "application 配置了 android:debuggable=\"true\"",
         "调试开关在发布包中开启会被 Google Play 拒绝，并造成严重安全风险。",
         "发布构建中移除 debuggable 或在 release 构建类型中设为 false。"),
    Rule("SG-AND-003", "android", Severity.WARNING,
         "android:allowBackup 未显式关闭",
         "允许完整备份可能泄露用户敏感数据，涉及隐私政策合规。",
         "如无备份需求，设置 android:allowBackup=\"false\" 并配置 dataExtractionRules。"),
    Rule("SG-AND-004", "android", Severity.WARNING,
         "android:usesCleartextTraffic=\"true\"",
         "允许明文 HTTP 传输会被判定为不安全的数据传输实践。",
         "改用 HTTPS，或通过 networkSecurityConfig 仅对必要域名放行。"),
    Rule("SG-AND-005", "android", Severity.INFO,
         "缺少 android:dataExtractionRules 配置",
         "targetSdk 31+ 建议声明数据提取规则，明确云备份/设备迁移的数据边界。",
         "添加 dataExtractionRules XML 并在 application 上引用。"),
    Rule("SG-AND-006", "android", Severity.WARNING,
         "使用了危险权限（需运行时授权与隐私披露）",
         "危险权限必须运行时动态申请，且需在商店隐私政策与数据安全表中如实申报。",
         "实现 requestPermissions 流程，并在商店数据安全部分如实申报用途。"),
    Rule("SG-AND-007", "android", Severity.INFO,
         "未配置 networkSecurityConfig",
         "自定义网络安全配置可显式管控明文流量与证书信任，利于审核说明。",
         "添加 networkSecurityConfig 并引用。"),
    Rule("SG-AND-008", "android", Severity.ERROR,
         "声明了政策敏感权限",
         "受限/敏感权限若与核心功能无直接关联，会被 Google Play 拒绝甚至下架。",
         "评估业务必要性，移除不必要的权限，或按政策提交专项声明。"),
    Rule("SG-AND-009", "android", Severity.WARNING,
         "使用危险权限但源码中未发现运行时申请逻辑",
         "仅静态声明而缺少 requestPermissions/checkSelfPermission 调用，"
         "说明权限可能被滥用或运行时必然失败。",
         "补充运行时权限申请与被拒后的降级逻辑，或移除该权限。"),
    Rule("SG-AND-010", "android", Severity.INFO,
         "android:targetSdkVersion 未声明或低于 34",
         "Google Play 要求新应用/更新 targetSdk 达到近期要求线（当前为 34）。",
         "将 targetSdkVersion 升级至 34 及以上。"),
]


def find_manifest(root: str):
    """在项目内定位 AndroidManifest.xml / Locate AndroidManifest.xml."""
    for dirpath, _dirnames, filenames in os.walk(root):
        if "build" in dirpath.split(os.sep):
            continue  # 跳过构建产物 / skip build artifacts
        if "AndroidManifest.xml" in filenames:
            return os.path.join(dirpath, "AndroidManifest.xml")
    return None


def find_gradle(root: str):
    """定位 app 级 build.gradle(.kts) 以读取 targetSdk / Locate app-level gradle file."""
    for dirpath, _dirnames, filenames in os.walk(root):
        if "build" in dirpath.split(os.sep):
            continue
        for name in ("build.gradle", "build.gradle.kts"):
            if name in filenames:
                return os.path.join(dirpath, name)
    return None


def _parse_target_sdk(gradle_path: str):
    """从 gradle 文件提取 targetSdk / Extract targetSdk from gradle."""
    try:
        with open(gradle_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    m = re.search(r"targetSdk(?:Version)?\s*=?\s*(\d+)", text)
    return int(m.group(1)) if m else None


def scan_android(root: str, result: ScanResult) -> None:
    """执行 Android 扫描 / Run Android checks and append findings."""
    manifest_path = find_manifest(root)
    if manifest_path is None:
        return  # 非 Android 项目 / not an Android project
    result.platform = "android" if result.platform == "unknown" else result.platform

    rel = os.path.relpath(manifest_path, root)
    try:
        tree = ET.parse(manifest_path)
    except ET.ParseError as exc:
        result.findings.append(Rule("SG-AND-000", "android", Severity.ERROR,
                                    "AndroidManifest.xml 解析失败",
                                    "清单文件无法解析：%s" % exc,
                                    rel).finding("XML 解析错误：%s" % exc, rel))
        return
    root_el = tree.getroot()
    app_el = root_el.find("application")
    if app_el is None:
        return

    # SG-AND-001 / SG-AND-002 / SG-AND-003 / SG-AND-004 / SG-AND-005 / SG-AND-007
    rules_by_id = {r.rule_id: r for r in RULES}

    if app_el.get(ANDROID_NS + "debuggable", "").lower() == "true":
        result.findings.append(rules_by_id["SG-AND-002"].finding(
            "application 声明了 android:debuggable=\"true\"", rel, 1))

    allow_backup = app_el.get(ANDROID_NS + "allowBackup")
    if allow_backup is None or allow_backup.lower() == "true":
        result.findings.append(rules_by_id["SG-AND-003"].finding(
            "allowBackup 未显式设为 false（当前值：%s）" % (allow_backup or "未声明"),
            rel, 1))

    if app_el.get(ANDROID_NS + "usesCleartextTraffic", "").lower() == "true":
        result.findings.append(rules_by_id["SG-AND-004"].finding(
            "application 允许明文流量 usesCleartextTraffic=\"true\"", rel, 1))

    if app_el.get(ANDROID_NS + "dataExtractionRules") is None:
        result.findings.append(rules_by_id["SG-AND-005"].finding(
            "application 未引用 dataExtractionRules", rel, 1))

    if app_el.get(ANDROID_NS + "networkSecurityConfig") is None:
        result.findings.append(rules_by_id["SG-AND-007"].finding(
            "application 未配置 networkSecurityConfig", rel, 1))

    # 组件 exported 检查 / component exported checks
    for tag in ("activity", "activity-alias", "service", "receiver", "provider"):
        for comp in root_el.iter(tag):
            has_filter = comp.find("intent-filter") is not None
            exported = comp.get(ANDROID_NS + "exported")
            if has_filter and exported is None:
                name = comp.get(ANDROID_NS + "name", tag)
                result.findings.append(rules_by_id["SG-AND-001"].finding(
                    "组件 %s 含 intent-filter 但未声明 android:exported" % name,
                    rel, 1))

    # 权限检查 / permission checks
    dangerous, sensitive = [], []
    perm_elems = list(root_el.iter("uses-permission"))
    for perm in perm_elems:
        name = (perm.get(ANDROID_NS + "name") or "").split(".")[-1]
        if name in DANGEROUS_PERMISSIONS:
            dangerous.append(name)
        if name in SENSITIVE_POLICY_PERMISSIONS:
            sensitive.append(name)
    if dangerous:
        result.findings.append(rules_by_id["SG-AND-006"].finding(
            "声明了危险权限：%s" % ", ".join(sorted(set(dangerous))), rel, 1))
    for name in sorted(set(sensitive)):
        result.findings.append(rules_by_id["SG-AND-008"].finding(
            "声明了政策敏感权限 %s：%s" % (name, SENSITIVE_POLICY_PERMISSIONS[name]),
            rel, 1))

    # SG-AND-009 源码运行时申请检查 / runtime request cross-check
    if dangerous:
        hint_found = False
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ("build", ".git")]
            for fn in filenames:
                if fn.endswith((".kt", ".java")):
                    path = os.path.join(dirpath, fn)
                    try:
                        with open(path, "r", encoding="utf-8", errors="replace") as fh:
                            code = fh.read()
                    except OSError:
                        continue
                    if any(k in code for k in RUNTIME_HINT_KEYWORDS):
                        hint_found = True
                        break
            if hint_found:
                break
        if not hint_found:
            result.findings.append(rules_by_id["SG-AND-009"].finding(
                "未在 *.kt/*.java 中发现运行时权限申请调用（requestPermissions/checkSelfPermission）",
                rel, 1))

    # SG-AND-010 targetSdk 检查 / targetSdk check
    gradle_path = find_gradle(root)
    if gradle_path:
        sdk = _parse_target_sdk(gradle_path)
        if sdk is None or sdk < 34:
            result.findings.append(rules_by_id["SG-AND-010"].finding(
                "targetSdkVersion 为 %s（低于 34）" % (sdk if sdk is not None else "未声明"),
                os.path.relpath(gradle_path, root), 1))
