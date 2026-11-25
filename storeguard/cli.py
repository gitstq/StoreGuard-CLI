# -*- coding: utf-8 -*-
"""命令行入口 / Command-line interface (argparse, stdlib only)."""

from __future__ import annotations

import argparse
import sys

from . import __version__, core
from .models import Severity


EXIT_OK = 0            # 无 ERROR 级发现 / no ERROR findings
EXIT_FINDINGS = 1      # 存在 ERROR 级发现（--strict 时 WARNING 也算）
EXIT_USAGE = 2         # 用法错误 / usage error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="storeguard",
        description="StoreGuard — 移动应用商店合规静态扫描器 / "
                    "Static store-compliance scanner for Android & iOS projects.",
    )
    parser.add_argument("--version", action="version",
                        version="StoreGuard %s" % __version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="扫描项目 / scan a project")
    p_scan.add_argument("path", help="项目根目录 / project root directory")
    p_scan.add_argument("--platform", choices=("auto", "android", "ios"),
                        default="auto", help="平台选择 / platform (default: auto)")
    p_scan.add_argument("--format", choices=("text", "markdown", "json"),
                        default="text", dest="fmt",
                        help="报告格式 / report format (default: text)")
    p_scan.add_argument("--output", "-o", default=None,
                        help="写入报告文件 / write report to file")
    p_scan.add_argument("--strict", action="store_true",
                        help="严格模式：WARNING 也返回非零退出码 / "
                             "fail on WARNING too (CI mode)")
    p_scan.add_argument("--fail-on", choices=("error", "warning", "info"),
                        default="error",
                        help="返回非零退出码的最低严重级别 / min severity to fail")

    sub.add_parser("rules", help="列出全部内置规则 / list all built-in rules")
    return parser


def _threshold(fmt_level: str) -> int:
    return {"info": 0, "warning": 1, "error": 2}[fmt_level]


def cmd_scan(args) -> int:
    try:
        result = core.scan(args.path, platform=args.platform)
    except NotADirectoryError as exc:
        print("错误 / error: %s" % exc, file=sys.stderr)
        return EXIT_USAGE

    report = {
        "text": core.to_text,
        "markdown": core.to_markdown,
        "json": core.to_json,
    }[args.fmt](result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
        print("报告已写入 / report written: %s" % args.output)
    else:
        print(report)

    threshold = _threshold(args.fail_on)
    if args.strict:
        threshold = _threshold("warning")  # strict 等价于 --fail-on warning
    worst = max((Severity.rank(f.severity) for f in result.findings), default=-1)
    if worst >= threshold and worst >= _threshold("error"):
        return EXIT_FINDINGS
    if args.strict and worst >= threshold:
        return EXIT_FINDINGS
    return EXIT_OK


def cmd_rules(_args) -> int:
    for r in core.all_rules():
        print("[%s] %s (%s, %s)" % (r.rule_id, r.title, r.platform, r.severity))
        print("    %s" % r.description)
        print("    建议: %s" % r.suggestion)
        print("")
    print("共 %d 条内置规则 / %d built-in rules" % (
        len(core.all_rules()), len(core.all_rules())))
    return EXIT_OK


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "scan":
        return cmd_scan(args)
    if args.command == "rules":
        return cmd_rules(args)
    parser.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
