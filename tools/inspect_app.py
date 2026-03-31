"""
APP 元素定位辅助工具

使用场景：在配置 APP_CHECKIN_RESOURCE_ID / APP_CHECKIN_TEXT / APP_CHECKIN_XPATH 之前，
用本工具截图并打印当前页面所有可点击元素的属性，帮助你找到打卡按钮的定位方式。

用法：
    # 打开目标打卡 APP 并导航到打卡页面，然后运行：
    python tools/inspect_app.py

    # 指定设备 serial（多设备时）：
    python tools/inspect_app.py --serial <device_serial>

    # iOS 模式：
    python tools/inspect_app.py --platform ios --wda-url http://127.0.0.1:8100

输出：
    - screenshot.png：当前屏幕截图
    - elements.txt：当前页面所有可交互元素的属性列表
"""

import argparse
import sys
import os
import json
from pathlib import Path

# 确保可以 import ai_sign 包
sys.path.insert(0, str(Path(__file__).parent.parent))


def inspect_android(serial: str | None) -> None:
    try:
        import uiautomator2 as u2
    except ImportError:
        print("请先安装：pip install uiautomator2")
        sys.exit(1)

    print(f"连接 Android 设备{'（' + serial + '）' if serial else '（自动检测）'} ...")
    d = u2.connect(serial) if serial else u2.connect()
    print(f"已连接：{d.info.get('productName', 'Unknown')}")

    # 截图
    screenshot_path = "screenshot.png"
    d.screenshot(screenshot_path)
    print(f"截图已保存：{screenshot_path}")

    # 打印所有可点击 / 可输入元素
    print("\n" + "=" * 60)
    print("当前页面可交互元素（可用于配置打卡按钮定位）：")
    print("=" * 60)

    elements_info = []
    hierarchy = d.dump_hierarchy()

    # 简单解析：找所有 clickable="true" 的节点
    import re
    pattern = re.compile(
        r'<node[^>]+clickable="true"[^>]*>', re.DOTALL
    )
    nodes = pattern.findall(hierarchy)

    def attr(node: str, name: str) -> str:
        m = re.search(rf'{name}="([^"]*)"', node)
        return m.group(1) if m else ""

    for i, node in enumerate(nodes, 1):
        text = attr(node, "text")
        resource_id = attr(node, "resource-id")
        content_desc = attr(node, "content-desc")
        bounds = attr(node, "bounds")
        class_name = attr(node, "class")

        if not text and not resource_id and not content_desc:
            continue

        info = {
            "序号": i,
            "text": text,
            "resource-id": resource_id,
            "content-desc": content_desc,
            "class": class_name,
            "bounds": bounds,
        }
        elements_info.append(info)

        print(f"\n[{i}]")
        if text:
            print(f"  文字（APP_CHECKIN_TEXT）：{text}")
        if resource_id:
            print(f"  resource-id（APP_CHECKIN_RESOURCE_ID）：{resource_id}")
        if content_desc:
            print(f"  content-desc：{content_desc}")
        print(f"  位置：{bounds}")

    # 保存到文件
    with open("elements.txt", "w", encoding="utf-8") as f:
        f.write("当前页面可交互元素\n")
        f.write("=" * 60 + "\n")
        for info in elements_info:
            f.write(json.dumps(info, ensure_ascii=False) + "\n")
    print(f"\n元素列表已保存：elements.txt")

    print("\n" + "=" * 60)
    print("配置建议：")
    print("  将对应的值填入 .env 文件：")
    print("  APP_CHECKIN_RESOURCE_ID=<resource-id>  （推荐，最稳定）")
    print("  APP_CHECKIN_TEXT=<文字>                 （简单直接）")
    print("=" * 60)

    # 也打印包名/Activity 信息
    print("\n当前前台 APP 信息（用于配置 APP_PACKAGE / APP_ACTIVITY）：")
    try:
        import subprocess
        result = subprocess.run(
            ["adb"] + (["-s", serial] if serial else []) + ["shell", "dumpsys", "window", "|", "grep", "mCurrentFocus"],
            capture_output=True, text=True, shell=False
        )
        # adb shell 需要一条命令
        cmd = f"adb {'  -s ' + serial if serial else ''} shell dumpsys window | grep mCurrentFocus"
        result2 = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result2.stdout:
            print(f"  {result2.stdout.strip()}")
    except Exception:
        print("  请手动执行：adb shell dumpsys window | grep mCurrentFocus")


def inspect_ios(wda_url: str) -> None:
    try:
        import wda
    except ImportError:
        print("请先安装：pip install facebook-wda")
        sys.exit(1)

    print(f"连接 WDA：{wda_url} ...")
    c = wda.Client(wda_url)
    print(f"WDA 已连接")

    screenshot_path = "screenshot.png"
    c.screenshot(screenshot_path)
    print(f"截图已保存：{screenshot_path}")

    s = c.session()

    print("\n" + "=" * 60)
    print("当前页面可交互元素：")
    print("=" * 60)

    elements = s.xpath("//*[@visible='true']").all()
    for i, elem in enumerate(elements, 1):
        try:
            label = elem.attrib.get("label", "")
            name = elem.attrib.get("name", "")
            elem_type = elem.attrib.get("type", "")
            enabled = elem.attrib.get("enabled", "")
            if not label and not name:
                continue
            print(f"\n[{i}]")
            if label:
                print(f"  label（APP_CHECKIN_TEXT）：{label}")
            if name:
                print(f"  name：{name}")
            print(f"  type：{elem_type}  enabled：{enabled}")
        except Exception:
            pass

    print("\n配置建议：将 label 值填入 .env 的 APP_CHECKIN_TEXT")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="APP 元素定位辅助工具：打印当前页面可点击元素，帮助配置打卡按钮",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--platform", choices=["android", "ios"], default="android")
    parser.add_argument("--serial", help="Android 设备 serial（多设备时指定）")
    parser.add_argument("--wda-url", default="http://127.0.0.1:8100", help="iOS WDA 服务地址")
    args = parser.parse_args()

    if args.platform == "android":
        inspect_android(args.serial)
    else:
        inspect_ios(args.wda_url)


if __name__ == "__main__":
    main()
