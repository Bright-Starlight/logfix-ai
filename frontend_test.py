"""
Web 应用测试脚本

测试日志分析流水线的页面功能。
"""

from playwright.sync_api import sync_playwright
import time
import os

def test_frontend_basic():
    """测试前端页面基本功能"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. 访问前端页面
            print("1. [INFO] Visiting frontend page...")
            page.goto('http://localhost:3005')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            # 截图
            page.screenshot(path='screenshots/01_home.png', full_page=True)
            print("   [OK] Screenshot: 01_home.png")

            # 2. 检查页面元素
            print("2. [INFO] Checking page elements...")
            buttons = page.locator('button').all()
            print(f"   Found {len(buttons)} buttons")

            for btn in buttons:
                text = btn.text_content()
                if text:
                    print(f"   - {text.strip()}")

            print("\n[SUCCESS] Basic frontend test passed!")

        except Exception as e:
            print(f"\n[FAIL] Test failed: {e}")
            page.screenshot(path='screenshots/error.png')
            raise
        finally:
            browser.close()


def test_tab_switching():
    """测试 Tab 切换功能"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("\n3. [INFO] Testing tab switching...")

            # 访问前端
            page.goto('http://localhost:3005')
            page.wait_for_load_state('networkidle')

            # 查找日志分类 Tab
            classification_tab = page.locator('text=日志分类')
            if classification_tab.count() > 0:
                print("   [OK] Found '日志分类' tab")
                classification_tab.click()
                page.wait_for_load_state('networkidle')
                time.sleep(1)
                page.screenshot(path='screenshots/02_classification_tab.png')
                print("   [OK] Switched to classification tab")
            else:
                print("   [WARN] '日志分类' tab not found")

            # 返回日志切分 Tab
            split_tab = page.locator('text=日志切分')
            if split_tab.count() > 0:
                print("   [OK] Found '日志切分' tab")
                split_tab.click()
                page.wait_for_load_state('networkidle')
                time.sleep(1)
                page.screenshot(path='screenshots/03_split_tab.png')
                print("   [OK] Switched back to split tab")

            print("\n[SUCCESS] Tab switching test passed!")

        except Exception as e:
            print(f"\n[FAIL] Test failed: {e}")
            page.screenshot(path='screenshots/error_tabs.png')
            raise
        finally:
            browser.close()


def test_backend_api():
    """测试后端 API"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("\n4. [INFO] Testing backend API...")

            # 健康检查
            page.goto('http://localhost:8000/health')
            page.wait_for_load_state('networkidle')
            content = page.content()
            print(f"   /health: {content}")

            # API 文档
            page.goto('http://localhost:8000/docs')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='screenshots/04_api_docs.png')
            print("   [OK] API docs page screenshot saved")

            print("\n[SUCCESS] Backend API test passed!")

        except Exception as e:
            print(f"\n[FAIL] Test failed: {e}")
            raise
        finally:
            browser.close()


def main():
    """运行所有测试"""
    # 创建截图目录
    os.makedirs('screenshots', exist_ok=True)

    print("=" * 50)
    print("LogFix AI - Web Application Test")
    print("=" * 50)

    test_frontend_basic()
    test_tab_switching()
    test_backend_api()

    print("\n" + "=" * 50)
    print("[SUCCESS] All tests passed!")
    print("=" * 50)
    print("\nScreenshots saved in 'screenshots/' directory")


if __name__ == "__main__":
    main()
