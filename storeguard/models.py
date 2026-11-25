# -*- coding: utf-8 -*-
"""数据模型 / Data models shared by the scan engine and reporters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Severity:
    """严重级别 / Severity levels (ordered)."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

    _ORDER = {"INFO": 0, "WARNING": 1, "ERROR": 2}

    @classmethod
    def rank(cls, level: str) -> int:
        return cls._ORDER.get(level, -1)


@dataclass
class Finding:
    """单条扫描发现 / One scan finding."""
    rule_id: str            # 规则编号, e.g. SG-AND-001
    severity: str           # INFO / WARNING / ERROR
    platform: str           # android / ios / common
    title: str              # 规则标题
    message: str            # 具体问题描述
    file: str               # 相关文件（相对路径）
    line: int = 0           # 行号（0 表示不适用）
    suggestion: str = ""    # 修复建议

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "platform": self.platform,
            "title": self.title,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "suggestion": self.suggestion,
        }


@dataclass
class Rule:
    """内置规则定义 / Built-in rule definition."""
    rule_id: str
    platform: str           # android / ios
    severity: str
    title: str
    description: str        # 规则说明（对应商店政策方向）
    suggestion: str         # 通用修复建议

    def finding(self, message: str, file: str, line: int = 0,
                suggestion: Optional[str] = None) -> Finding:
        return Finding(
            rule_id=self.rule_id,
            severity=self.severity,
            platform=self.platform,
            title=self.title,
            message=message,
            file=file,
            line=line,
            suggestion=suggestion or self.suggestion,
        )


@dataclass
class ScanResult:
    """一次扫描的汇总结果 / Aggregated result of one scan."""
    project_root: str = ""
    platform: str = "unknown"
    files_scanned: int = 0
    findings: list = field(default_factory=list)

    def count(self, severity: str) -> int:
        return sum(1 for f in self.findings if f.severity == severity)

    @property
    def error_count(self) -> int:
        return self.count(Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return self.count(Severity.WARNING)

    @property
    def info_count(self) -> int:
        return self.count(Severity.INFO)
