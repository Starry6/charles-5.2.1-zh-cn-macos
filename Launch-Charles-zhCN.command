#!/bin/bash
set -euo pipefail

PACKAGE_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
APP="${CHARLES_APP_PATH:-/Applications/Charles.app}"
PATCH_DIR="$PACKAGE_DIR/patch"

show_message() {
  /usr/bin/osascript -e "display dialog \"$1\" buttons {\"好\"} default button \"好\" with title \"Charles 中文版\"" >/dev/null 2>&1 || true
}

if [[ ! -d "$APP" || ! -f "$APP/Contents/Info.plist" ]]; then
  show_message "找不到 Charles.app。默认位置是 /Applications/Charles.app；也可以设置 CHARLES_APP_PATH 指定安装位置。"
  exit 1
fi

VERSION="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP/Contents/Info.plist" 2>/dev/null || true)"
if [[ "$VERSION" != "5.2.1" ]]; then
  show_message "此汉化包适配 Charles 5.2.1，当前版本为 ${VERSION:-未知}。为避免破坏应用，已停止启动。"
  exit 1
fi

if /usr/bin/pgrep -x Charles >/dev/null 2>&1; then
  show_message "请先保存 Charles 会话并完全退出 Charles，再运行此启动器。当前运行中的 Charles 不会自动加载汉化资源。"
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  show_message "需要 Python 3 来从本机 Charles 安装中生成兼容的汉化补丁。"
  exit 1
fi

python3 "$PACKAGE_DIR/build_patch.py" --app "$APP"

# The quoted module path allows the package folder itself to contain spaces.
JAVA_OPTIONS="--patch-module=com.charlesproxy=\"$PATCH_DIR\" -Duser.language=zh -Duser.script=Hans -Duser.country=CN"
# Charles is started by Apple's native app launcher with an embedded JVM. The
# JVM reads JAVA_TOOL_OPTIONS directly; JDK_JAVA_OPTIONS is only handled by the
# `java` command-line launcher and is ignored by this native launcher.
/usr/bin/open -a "$APP" --env "JAVA_TOOL_OPTIONS=$JAVA_OPTIONS"
