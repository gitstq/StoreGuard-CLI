# 🛡️ StoreGuard-CLI

> 🚨 行動應用程式商店合規靜態掃描器 —— 在送審前發現被拒風險
> Static store-compliance scanner for Android & iOS projects.

語言切換 / Language: [简体中文](README.md) | **繁體中文** | [English](README.en.md)

---

## 🎉 介紹

**StoreGuard-CLI** 是一個零依賴（pure Python stdlib）的命令列工具，用於靜態掃描 Android / iOS 專案，依內建規則庫偵測應用程式商店（Google Play / App Store）最常見的被拒風險：

- 🤖 **Android**：解析 `AndroidManifest.xml` 與 `build.gradle`，檢查 exported 宣告、debuggable、危險權限、敏感權限、明文流量、targetSdk 等
- 🍎 **iOS**：解析 `Info.plist` 與 `PrivacyInfo.xcprivacy`，交叉核對原始碼中的隱私 API、必需理由 API、佔位文字、背景模式等

輸出支援 **text / markdown / json** 三種格式，並提供 CI 友善的嚴格模式與結束代碼約定。

> ✅ 全部功能僅使用 Python 標準庫實現，無任何第三方執行時依賴，單一 zipapp 檔案即可散布。

## ✨ 特性

- 🧩 **17 條內建規則**：涵蓋 exported 缺失、debuggable、危險／敏感權限、隱私描述缺失、必需理由 API 未申報、佔位文字、背景模式濫用、targetSdk 過低等
- 🔍 **原始碼交叉核對**：不只看設定檔，還掃描 `.kt/.java/.swift/.m` 原始碼，找出「宣告了權限卻沒有執行期申請」、「用了隱私 API 卻沒寫用途描述」等深層問題
- 📊 **三種報告格式**：text（人類可讀，含修復建議）、markdown（適合貼入 PR/Issue）、json（機器可讀，可接 CI/CD）
- 🚦 **CI 結束代碼約定**：`0` 通過 / `1` 存在 ERROR 級發現 / `2` 用法錯誤；`--strict` 或 `--fail-on warning` 支援更嚴格門檻
- 🪶 **零依賴單檔**：`storeguard-x.y.z.zipapp` 跨平台散布，只要有 `python3` 即可執行
- 🌏 **中英雙語報告**：報告內容中英對照，跨團隊協作無門檻

## 🚀 快速開始

**方式一：zipapp 單一檔案（推薦）**

```bash
python3 storeguard-1.0.0.zipapp scan /path/to/android-or-ios-project
```

**方式二：原始碼執行**

```bash
git clone https://github.com/gitstq/StoreGuard-CLI.git
cd StoreGuard-CLI
python3 -m storeguard scan /path/to/project
```

**方式三：pip 安裝**

```bash
pip install .
storeguard scan /path/to/project
```

## 📖 使用指南

```bash
# 掃描（自動識別平台）
storeguard scan ./MyApp

# 指定平台與格式
storeguard scan ./MyApp --platform ios --format markdown --output report.md

# CI 嚴格模式：WARNING 也視為失敗
storeguard scan ./MyApp --strict

# 檢視全部內建規則
storeguard rules
```

**結束代碼約定：**

| 結束代碼 | 意義 |
| --- | --- |
| `0` | 無 ERROR 級發現 |
| `1` | 存在 ERROR 級發現（`--strict` 時含 WARNING） |
| `2` | 用法錯誤（路徑不存在等） |

**內建規則概覽（17 條）：**

| 平台 | 規則 | 等級 |
| --- | --- | --- |
| Android | SG-AND-001 exported 缺失 · SG-AND-002 debuggable · SG-AND-008 敏感權限 | 🔴 ERROR |
| Android | SG-AND-003 allowBackup · SG-AND-004 明文流量 · SG-AND-006 危險權限 · SG-AND-009 缺執行期申請 | 🟠 WARNING |
| Android | SG-AND-005 dataExtractionRules · SG-AND-007 networkSecurityConfig · SG-AND-010 targetSdk | 🔵 INFO |
| iOS | SG-IOS-001 用途描述缺失 · SG-IOS-003 追蹤描述 · SG-IOS-004 必需理由 API · SG-IOS-005 佔位文字 | 🔴 ERROR |
| iOS | SG-IOS-002 隱私清單缺失 · SG-IOS-007 背景模式 | 🟠 WARNING |
| iOS | SG-IOS-006 加密豁免宣告 | 🔵 INFO |

## 💡 設計迭代

- **v1.0.0**：首個正式版本。17 條內建規則、三格式報告、CI 結束代碼約定、zipapp 打包、29 個單元測試。
- **規劃中**：
  - 📌 規則可設定化（`storeguard.yml` 啟用／停用與門檻調整）
  - 📌 Kotlin/Java AST 級分析，減少誤報
  - 📌 隱私政策文字與資料安全表交叉核對
  - 📌 GitHub Action 官方整合

歡迎透過 Issue 提出你希望看到的規則方向。

## 📦 打包部署

```bash
# 一鍵建構跨平台 zipapp
bash scripts/build.sh
# 產物：dist/storeguard-1.0.0.zipapp
python3 dist/storeguard-1.0.0.zipapp --help
```

CI 整合範例（GitHub Actions）：

```yaml
- name: StoreGuard scan
  run: |
    python3 storeguard-1.0.0.zipapp scan ./android_app --format json --output report.json --strict
```

## 🤝 貢獻

歡迎 PR！請先閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)。新增規則請確保：規則編號唯一、附帶測試與 fixture、同步更新文件。

## 📄 授權條款

[MIT](LICENSE) © 2026 gitstq
