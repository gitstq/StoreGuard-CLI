# -*- coding: utf-8 -*-
"""扫描引擎与报告渲染 / Scan engine and report renderers."""

from __future__ import annotations

import json
import os
from collections import Counter

from . import rules_android, rules_ios
from .models import ScanResult, Severity


def scan(project_root: str, platform: str = "auto") -> ScanResult:
    """对项目执行合规扫描 / Scan a project for store-compliance risks.

    platform: auto / android / ios
    """
    root = os.path.abspath(project_root)
    if not os.path.isdir(root):
        raise NotADirectoryError("项目路径不存在：%s" % root)

    result = ScanResult(project_root=root)
    if platform in ("auto", "android"):
        rules_android.scan_android(root, result)
    if platform in ("auto", "ios"):
        rules_ios.scan_ios(root, result)

    if result.platform == "unknown" and platform == "auto":
        result.platform = "unknown"  # 未识别到移动项目 / no mobile project detected

    # 统计扫描文件数 / count scanned files
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in
                       ("build", ".git", "Pods", "DerivedData", "node_modules")]
        total += len(filenames)
    result.files_scanned = total

    # 按 严重度 > 平台 > 规则 排序 / sort findings for stable reports
    result.findings.sort(key=lambda f: (
        -Severity.rank(f.severity), f.platform, f.rule_id, f.file, f.line))
    return result


def to_text(result: ScanResult) -> str:
    """渲染纯文本报告 / Render a plain-text report."""
    lines = []
    lines.append("=" * 62)
    lines.append("StoreGuard 扫描报告 / Scan Report")
    lines.append("项目 / Project : %s" % result.project_root)
    lines.append("平台 / Platform: %s" % result.platform)
    lines.append("文件 / Files   : %d" % result.files_scanned)
    lines.append("-" * 62)
    if not result.findings:
        lines.append("✅ 未发现问题 / No findings. 项目通过全部内置规则。")
    else:
        for f in result.findings:
            icon = {"ERROR": "🔴", "WARNING": "🟠", "INFO": "🔵"}.get(f.severity, "⚪")
            lines.append("%s [%s] %s %s" % (icon, f.severity, f.rule_id, f.title))
            lines.append("   位置 / Location: %s%s" % (
                f.file, ":%d" % f.line if f.line else ""))
            lines.append("   说明 / Detail : %s" % f.message)
            if f.suggestion:
                lines.append("   建议 / Fix    : %s" % f.suggestion)
            lines.append("")
    lines.append("-" * 62)
    lines.append("汇总 / Summary: 🔴 ERROR %d | 🟠 WARNING %d | 🔵 INFO %d" % (
        result.error_count, result.warning_count, result.info_count))
    lines.append("=" * 62)
    return "\n".join(lines)


def to_markdown(result: ScanResult) -> str:
    """渲染 Markdown 报告 / Render a Markdown report."""
    out = ["# StoreGuard 扫描报告", ""]
    out.append("| 项目 | 值 |")
    out.append("| --- | --- |")
    out.append("| 项目路径 | `%s` |" % result.project_root)
    out.append("| 识别平台 | %s |" % result.platform)
    out.append("| 扫描文件 | %d |" % result.files_scanned)
    out.append("| 发现问题 | 🔴 %d / 🟠 %d / 🔵 %d |" % (
        result.error_count, result.warning_count, result.info_count))
    out.append("")
    if result.findings:
        out.append("## 发现明细 / Findings")
        out.append("")
        for f in result.findings:
            out.append("### [%s] %s — %s" % (f.severity, f.rule_id, f.title))
            out.append("- **位置**：%s%s" % (f.file, ":%d" % f.line if f.line else ""))
            out.append("- **说明**：%s" % f.message)
            if f.suggestion:
                out.append("- **建议**：%s" % f.suggestion)
            out.append("")
    else:
        out.append("✅ 未发现问题 / No findings.")
    return "\n".join(out)


def to_json(result: ScanResult) -> str:
    """渲染 JSON 报告 / Render a JSON report (CI friendly)."""
    return json.dumps({
        "project": result.project_root,
        "platform": result.platform,
        "files_scanned": result.files_scanned,
        "summary": {
            "error": result.error_count,
            "warning": result.warning_count,
            "info": result.info_count,
        },
        "findings": [f.as_dict() for f in result.findings],
    }, ensure_ascii=False, indent=2)


def all_rules():
    """汇总全部内置规则 / Return all built-in rules."""
    return rules_android.RULES + rules_ios.RULES


def severity_distribution(findings) -> Counter:
    """严重度分布统计 / Severity distribution helper."""
    return Counter(f.severity for f in findings)
