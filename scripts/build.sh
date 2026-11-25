#!/usr/bin/env bash
# 一键打包脚本：生成跨平台 zipapp 单文件 / Build a cross-platform zipapp.
# 用法 / Usage: bash scripts/build.sh [输出目录 / output dir]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT_DIR/dist}"
APP_NAME="storeguard"

mkdir -p "$OUT_DIR"

# 读取版本号 / read version from package
VERSION="$(python3 -c 'import sys; sys.path.insert(0, "'"$ROOT_DIR"'"); from storeguard import __version__; print(__version__)')"
TARGET="$OUT_DIR/${APP_NAME}-${VERSION}.zipapp"

# 清理旧构建 / clean previous build
rm -f "$TARGET"

python3 - "$ROOT_DIR/storeguard" "$TARGET" "$APP_NAME" <<'PYEOF'
import sys, zipfile, os
src, target, main_mod = sys.argv[1], sys.argv[2], sys.argv[3]
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            if fn.endswith(".py"):
                full = os.path.join(dirpath, fn)
                arc = os.path.join(main_mod, os.path.relpath(full, src))
                zf.write(full, arc)
    # 生成 __main__.py 使 zipapp 可直接执行 / make the zipapp executable
    zf.writestr("__main__.py", "import %s.cli as c; c.main()\n" % main_mod)
PYEOF

chmod +x "$TARGET"
echo "构建完成 / built: $TARGET"
echo "运行方式 / run: python3 $TARGET --help  或  ./$TARGET --help"
