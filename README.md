# 🛡️ StoreGuard-CLI

> 🚨 移动应用商店合规静态扫描器 —— 在提审前发现被拒风险
> Static store-compliance scanner for Android & iOS projects — catch rejection risks before submission.

语言切换 / Language: **简体中文** | [繁體中文](README.zh-TW.md) | [English](README.en.md)

---

## 🎉 介绍

**StoreGuard-CLI** 是一个零依赖（pure Python stdlib）的命令行工具，用于静态扫描 Android / iOS 项目，按内置规则库检测应用商店（Google Play / App Store）最常见的被拒风险：

- 🤖 **Android**：解析 `AndroidManifest.xml` 与 `build.gradle`，检查 exported 声明、debuggable、危险权限、敏感权限、明文流量、targetSdk 等
- 🍎 **iOS**：解析 `Info.plist` 与 `PrivacyInfo.xcprivacy`，交叉核对源码中的隐私 API、必需理由 API、占位文案、后台模式等

输出支持 **text / markdown / json** 三种格式，并提供 CI 友好的严格模式与退出码约定。

> ✅ 全部功能仅使用 Python 标准库实现，无任何第三方运行时依赖，单文件 zipapp 即可分发。

## ✨ 特性

- 🧩 **17 条内置规则**：覆盖 exported 缺失、debuggable、危险/敏感权限、隐私描述缺失、必需理由 API 未申报、占位文案、后台模式滥用、targetSdk 过低等
- 🔍 **源码交叉核对**：不仅看配置文件，还扫描 `.kt/.java/.swift/.m` 源码，识别“声明了权限却没有运行时申请”、“用了隐私 API 却没写用途描述”等深层问题
- 📊 **三种报告格式**：text（人类可读，带修复建议）、markdown（可贴 PR/Issue）、json（机器可读，可接 CI/CD）
- 🚦 **CI 退出码约定**：`0` 通过 / `1` 存在 ERROR 级发现 / `2` 用法错误；`--strict` 或 `--fail-on warning` 支持更严格门禁
- 🪶 **零依赖单文件**：`storeguard-x.y.z.zipapp` 跨平台分发，`python3` 存在即可运行
- 🌏 **中英双语报告**：报告内容中英对照，团队协作无门槛

## 🚀 快速开始

**方式一：zipapp 单文件（推荐）**

```bash
python3 storeguard-1.0.0.zipapp scan /path/to/android-or-ios-project
```

**方式二：源码运行**

```bash
git clone https://github.com/gitstq/StoreGuard-CLI.git
cd StoreGuard-CLI
python3 -m storeguard scan /path/to/project
```

**方式三：pip 安装**

```bash
pip install .
storeguard scan /path/to/project
```

## 📖 使用指南

```bash
# 扫描（自动识别平台）
storeguard scan ./MyApp

# 指定平台与格式
storeguard scan ./MyApp --platform ios --format markdown --output report.md

# CI 严格模式：WARNING 也算失败
storeguard scan ./MyApp --strict
echo $?   # 1 = 存在 ERROR/WARNING 发现

# 查看全部内置规则
storeguard rules
```

**退出码约定：**

| 退出码 | 含义 |
| --- | --- |
| `0` | 无 ERROR 级发现 |
| `1` | 存在 ERROR 级发现（`--strict` 时含 WARNING） |
| `2` | 用法错误（路径不存在等） |

**内置规则概览（17 条）：**

| 平台 | 规则 | 级别 |
| --- | --- | --- |
| Android | SG-AND-001 exported 缺失 · SG-AND-002 debuggable · SG-AND-008 敏感权限 | 🔴 ERROR |
| Android | SG-AND-003 allowBackup · SG-AND-004 明文流量 · SG-AND-006 危险权限 · SG-AND-009 缺运行时申请 | 🟠 WARNING |
| Android | SG-AND-005 dataExtractionRules · SG-AND-007 networkSecurityConfig · SG-AND-010 targetSdk | 🔵 INFO |
| iOS | SG-IOS-001 用途描述缺失 · SG-IOS-003 追踪描述 · SG-IOS-004 必需理由 API · SG-IOS-005 占位文案 | 🔴 ERROR |
| iOS | SG-IOS-002 隐私清单缺失 · SG-IOS-007 后台模式 | 🟠 WARNING |
| iOS | SG-IOS-006 加密豁免声明 | 🔵 INFO |

## 💡 设计迭代

- **v1.0.0**：首个正式版本。17 条内置规则、三格式报告、CI 退出码约定、zipapp 打包、29 个单元测试。
- **规划中**：
  - 📌 规则可配置化（`storeguard.yml` 启用/禁用与阈值调整）
  - 📌 Kotlin/Java AST 级分析，减少误报
  - 📌 隐私政策文本与数据安全表交叉核对
  - 📌 GitHub Action 官方集成

欢迎通过 Issue 提出你想看到的规则方向。

## 📦 打包部署

```bash
# 一键构建跨平台 zipapp
bash scripts/build.sh
# 产物：dist/storeguard-1.0.0.zipapp
python3 dist/storeguard-1.0.0.zipapp --help
```

CI 集成示例（GitHub Actions）：

```yaml
- name: StoreGuard scan
  run: |
    python3 storeguard-1.0.0.zipapp scan ./android_app --format json --output report.json --strict
```

## 🤝 贡献

欢迎 PR！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。新增规则请确保：规则编号唯一、附带测试与 fixture、更新文档。

## 📄 协议

[MIT](LICENSE) © 2026 gitstq
