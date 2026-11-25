# 🛡️ StoreGuard-CLI

> 🚨 Static store-compliance scanner for Android & iOS projects — catch rejection risks before you submit.
> 静态扫描移动项目中的应用商店合规风险。

Language / 语言: [简体中文](README.md) | [繁體中文](README.zh-TW.md) | **English**

---

## 🎉 Introduction

**StoreGuard-CLI** is a zero-dependency (pure Python stdlib) command-line tool that statically scans Android / iOS projects and detects the most common store-rejection risks (Google Play / App Store) against a built-in rule catalogue:

- 🤖 **Android**: parses `AndroidManifest.xml` and `build.gradle` to check exported declarations, debuggable, dangerous/sensitive permissions, cleartext traffic, targetSdk and more
- 🍎 **iOS**: parses `Info.plist` and `PrivacyInfo.xcprivacy`, cross-checking source code for privacy APIs, required-reason APIs, placeholder texts, background modes and more

Reports are available in **text / markdown / json**, with a CI-friendly strict mode and exit-code contract.

> ✅ Implemented entirely with the Python standard library — no third-party runtime dependencies; distributable as a single zipapp file.

## ✨ Features

- 🧩 **17 built-in rules**: missing exported, debuggable, dangerous/sensitive permissions, missing usage descriptions, undeclared required-reason APIs, placeholder texts, background-mode abuse, low targetSdk and more
- 🔍 **Source cross-checking**: goes beyond config files — scans `.kt/.java/.swift/.m` sources to catch deeper issues such as "permission declared but never requested at runtime" or "privacy API used without a usage description"
- 📊 **Three report formats**: text (human-readable with fix suggestions), markdown (paste into PRs/Issues), json (machine-readable for CI/CD)
- 🚦 **CI exit-code contract**: `0` pass / `1` ERROR findings / `2` usage error; `--strict` or `--fail-on warning` for tighter gates
- 🪶 **Zero-dependency single file**: `storeguard-x.y.z.zipapp` runs anywhere Python 3 exists
- 🌏 **Bilingual reports**: Chinese-English findings out of the box

## 🚀 Quick Start

**Option 1: zipapp (recommended)**

```bash
python3 storeguard-1.0.0.zipapp scan /path/to/android-or-ios-project
```

**Option 2: from source**

```bash
git clone https://github.com/gitstq/StoreGuard-CLI.git
cd StoreGuard-CLI
python3 -m storeguard scan /path/to/project
```

**Option 3: pip**

```bash
pip install .
storeguard scan /path/to/project
```

## 📖 Usage Guide

```bash
# Scan with auto platform detection
storeguard scan ./MyApp

# Choose platform and format
storeguard scan ./MyApp --platform ios --format markdown --output report.md

# CI strict mode: WARNING also fails
storeguard scan ./MyApp --strict

# List all built-in rules
storeguard rules
```

**Exit codes:**

| Code | Meaning |
| --- | --- |
| `0` | No ERROR-level findings |
| `1` | ERROR-level findings exist (WARNING too with `--strict`) |
| `2` | Usage error (e.g. invalid path) |

**Built-in rules overview (17):**

| Platform | Rules | Level |
| --- | --- | --- |
| Android | SG-AND-001 missing exported · SG-AND-002 debuggable · SG-AND-008 sensitive permissions | 🔴 ERROR |
| Android | SG-AND-003 allowBackup · SG-AND-004 cleartext traffic · SG-AND-006 dangerous permissions · SG-AND-009 no runtime request | 🟠 WARNING |
| Android | SG-AND-005 dataExtractionRules · SG-AND-007 networkSecurityConfig · SG-AND-010 targetSdk | 🔵 INFO |
| iOS | SG-IOS-001 missing usage description · SG-IOS-003 tracking description · SG-IOS-004 required-reason API · SG-IOS-005 placeholder text | 🔴 ERROR |
| iOS | SG-IOS-002 missing privacy manifest · SG-IOS-007 background modes | 🟠 WARNING |
| iOS | SG-IOS-006 encryption exemption | 🔵 INFO |

## 💡 Design Iterations

- **v1.0.0**: first stable release. 17 rules, three report formats, CI exit-code contract, zipapp packaging, 29 unit tests.
- **Planned**:
  - 📌 Configurable rules via `storeguard.yml`
  - 📌 AST-level Kotlin/Java analysis to reduce false positives
  - 📌 Cross-checking privacy policy text against data-safety declarations
  - 📌 Official GitHub Action integration

Open an issue to suggest the rules you want next.

## 📦 Packaging & Deployment

```bash
# Build a cross-platform zipapp in one command
bash scripts/build.sh
# Output: dist/storeguard-1.0.0.zipapp
python3 dist/storeguard-1.0.0.zipapp --help
```

CI integration example (GitHub Actions):

```yaml
- name: StoreGuard scan
  run: |
    python3 storeguard-1.0.0.zipapp scan ./android_app --format json --output report.json --strict
```

## 🤝 Contributing

PRs are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md). When adding a rule: keep rule IDs unique, include tests with fixtures, and update the docs.

## 📄 License

[MIT](LICENSE) © 2026 gitstq
