# StoreGuard-CLI · 贡献指南 / Contributing Guide

感谢关注 StoreGuard-CLI！欢迎通过 Issue 反馈问题、通过 Pull Request 贡献代码。
Thanks for your interest! Please open issues for bugs and pull requests for improvements.

## 本地开发 / Local Development

```bash
git clone https://github.com/gitstq/StoreGuard-CLI.git
cd StoreGuard-CLI
python3 -m unittest discover -s tests   # 运行全量测试 / run all tests
python3 -m storeguard scan <项目路径>     # 本地验证 / verify locally
```

## 新增规则 / Adding a Rule

1. 在 `storeguard/rules_android.py` 或 `storeguard/rules_ios.py` 中定义 `Rule`（编号唯一）。
2. 在对应 `scan_*` 函数中实现检查逻辑，产出带文件定位的 `Finding`。
3. 在 `tests/` 中为该规则补充 fixture 与断言。
4. 更新三语 README 的规则清单（如涉及）。

## 提交规范 / Commit Convention

遵循 Angular 规范：`feat:` / `fix:` / `docs:` / `refactor:` / `test:` / `chore:`。
示例：`feat(ios): add required-reason API declaration check`

## 代码风格 / Style

- 仅使用 Python 标准库，不引入第三方运行时依赖。
- 关键逻辑需有注释（中英双语优先）。
- 新功能必须附带单元测试，保持测试全绿。
