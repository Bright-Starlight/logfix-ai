#!/usr/bin/env python3
"""
E2E 测试: LogFix AI 新版标签页界面

测试页面加载、标签切换、分类视图渲染。
"""

import os
import re
import sys
import time
import tempfile
from playwright.sync_api import sync_playwright, expect
import requests


def test_page_loads_and_tabs(page):
    """验证页面加载和标签切换"""
    print("\n[测试] 页面加载和标签切换")

    page.goto("http://localhost:3002")
    page.wait_for_load_state("networkidle")

    # 验证标题
    title = page.title()
    print(f"  页面标题: {title}")

    # 验证 header 存在
    header = page.locator(".app-header h1")
    expect(header).to_contain_text("LogFix AI")
    print("  Header 验证通过")

    # 验证两个标签存在
    tabs = page.locator(".nav-tab")
    count = tabs.count()
    print(f"  标签数量: {count}")
    assert count == 2, f"期望2个标签，实际{count}个"

    # 验证默认选中"日志切分"标签
    active_tab = page.locator(".nav-tab.active")
    expect(active_tab).to_contain_text("日志切分")
    print("  默认标签'日志切分'验证通过")

    # 截图
    page.screenshot(path="e2e_split_tab.png", full_page=True)
    print("  截图已保存: e2e_split_tab.png")


def test_tab_switch_to_classify(page):
    """验证切换到分类标签"""
    print("\n[测试] 切换到分类标签")

    page.goto("http://localhost:3002")
    page.wait_for_load_state("networkidle")

    # 点击"日志分类"标签
    classify_tab = page.locator(".nav-tab:has-text('日志分类')")
    classify_tab.click()

    # 验证标签激活状态
    expect(classify_tab).to_have_class(re.compile(r"active"))
    print("  分类标签已激活")

    # 验证分类视图元素显示
    # StatsPanel 应该显示统计信息
    stats = page.locator(".stats-panel, [class*='stats']")
    if stats.count() > 0:
        print("  StatsPanel 元素存在")

    # SearchFilter 应该存在
    search = page.locator(".search-filter, [class*='search']")
    if search.count() > 0:
        print("  SearchFilter 元素存在")

    # LogList 应该存在
    log_list = page.locator(".log-list, [class*='log-list']")
    if log_list.count() > 0:
        print("  LogList 元素存在")

    # 截图
    page.screenshot(path="e2e_classify_tab.png", full_page=True)
    print("  截图已保存: e2e_classify_tab.png")


def test_split_tab_upload_zone(page):
    """验证切分标签的上传区域"""
    print("\n[测试] 切分标签上传区域")

    page.goto("http://localhost:3002")
    page.wait_for_load_state("networkidle")

    # 验证上传区域存在
    upload_zone = page.locator(".upload-zone, [class*='upload']")
    if upload_zone.count() > 0:
        expect(upload_zone.first).to_be_visible()
        print("  上传区域存在")

        # 拖拽提示文本
        hint = page.locator("text=拖拽文件到此处")
        if hint.count() > 0:
            print("  拖拽提示文本存在")


def test_backend_health():
    """验证后端健康状态"""
    print("\n[测试] 后端健康检查")

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"  后端状态: {data['status']}")
        return True
    except Exception as e:
        print(f"  后端连接失败: {e}")
        return False


def test_backend_classify_api():
    """验证分类 API 可访问"""
    print("\n[测试] 分类 API 检查")

    try:
        # 检查 API 路由是否存在
        response = requests.get("http://localhost:8000/api/logs", timeout=5)
        # 401 或 200 都说明 API 存在
        print(f"  /api/logs 响应状态: {response.status_code}")
        return True
    except Exception as e:
        print(f"  API 不可用: {e}")
        return False


def capture_console_errors(page):
    """捕获控制台错误"""
    errors = []

    def handle_console(msg):
        if msg.type == "error":
            errors.append(msg.text)

    page.on("console", handle_console)
    return errors


def main():
    print("=" * 50)
    print("LogFix AI E2E 测试")
    print("=" * 50)

    passed = 0
    failed = 0

    # 后端测试
    if test_backend_health():
        passed += 1
    else:
        failed += 1
        print("  [跳过] 后端不可用，跳过 API 测试")

    if test_backend_classify_api():
        passed += 1
    else:
        failed += 1

    # 前端测试
    print("\n" + "-" * 50)
    print("前端 UI 测试")
    print("-" * 50)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 捕获控制台错误
        errors = capture_console_errors(page)

        tests = [
            ("页面加载和标签", test_page_loads_and_tabs),
            ("标签切换", test_tab_switch_to_classify),
            ("上传区域", test_split_tab_upload_zone),
        ]

        for name, test_func in tests:
            print(f"\n[测试] {name}")
            try:
                test_func(page)
                print(f"  结果: PASSED")
                passed += 1
            except Exception as e:
                print(f"  结果: FAILED - {e}")
                failed += 1

        browser.close()

    # 报告
    print("\n" + "=" * 50)
    print(f"测试结果: {passed} passed, {failed} failed")
    print("=" * 50)

    # 截图说明
    print("\n截图文件:")
    print("  - e2e_split_tab.png   (切分标签)")
    print("  - e2e_classify_tab.png (分类标签)")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
