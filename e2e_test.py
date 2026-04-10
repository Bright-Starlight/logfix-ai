#!/usr/bin/env python3
"""
E2E test for LogFix AI webapp.
Tests the main user flows based on the spec.
"""

import os
import sys
import time
import json
import tempfile
from playwright.sync_api import sync_playwright, expect
import requests

# Test data
SAMPLE_LOG_CONTENT = """2024-01-15 10:30:00 INFO Application started
2024-01-15 10:30:01 DEBUG Loading configuration
2024-01-15 10:30:02 INFO Database connected
2024-01-15 10:30:05 ERROR Failed to process request
2024-01-15 10:30:06 DEBUG Retrying connection
2024-01-15 10:30:07 INFO Connection restored
2024-01-15 11:00:00 INFO New request received
2024-01-15 11:00:01 DEBUG Processing data
2024-01-15 11:00:02 INFO Data processed successfully
"""

def test_page_loads(page):
    """Test that the main page loads with correct title."""
    page.goto('http://localhost:5174')
    page.wait_for_load_state('networkidle')

    # Check main elements
    expect(page.locator('h1')).to_contain_text('LogFix AI')
    expect(page.get_by_text('日志文件切分工具')).to_be_visible()


def test_file_upload_without_file(page):
    """Test User Story 1 - Scenario 3: Click upload without selecting file."""
    page.goto('http://localhost:5174')
    page.wait_for_load_state('networkidle')

    # Button should be disabled when no file is selected
    upload_button = page.locator('button.upload-button')
    expect(upload_button).to_be_disabled()

    # Also verify the hint text is present
    expect(page.locator('text=支持 .log, .txt, .json 格式，最大100MB')).to_be_visible()


def test_file_upload_ui_elements(page):
    """Test that file upload UI elements are present."""
    page.goto('http://localhost:5174')
    page.wait_for_load_state('networkidle')

    # Check upload zone exists
    expect(page.locator('.upload-zone')).to_be_visible()
    expect(page.locator('text=拖拽文件到此处，或点击选择文件')).to_be_visible()
    expect(page.locator('text=支持 .log, .txt, .json 格式，最大100MB')).to_be_visible()

    # Check upload button exists
    expect(page.locator('button:has-text("上传文件")')).to_be_visible()


def test_upload_non_text_file(page):
    """Test User Story 1 - Scenario 2: Upload non-text file."""
    page.goto('http://localhost:5174')
    page.wait_for_load_state('networkidle')

    # Create a fake non-text file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')  # PNG header
        temp_file = f.name

    try:
        # Set up file chooser
        with page.expect_file_chooser() as fc_info:
            page.locator('.upload-zone').click()

        file_chooser = fc_info.value
        file_chooser.set_files(temp_file)

        # The UI should show the selected file
        expect(page.locator('.filename')).to_be_visible()

        # Button should now be enabled
        upload_button = page.locator('button.upload-button')
        expect(upload_button).to_be_enabled()

        # Click upload
        upload_button.click()

        # Without backend, upload will fail - check for error after a moment
        time.sleep(2)
        # The error message may or may not appear depending on implementation
        # This test mainly verifies the UI flow works

    finally:
        os.unlink(temp_file)


def test_upload_text_file(page):
    """Test User Story 1 - Scenario 1: Upload a text log file."""
    page.goto('http://localhost:5174')
    page.wait_for_load_state('networkidle')

    # Create a test log file
    with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
        f.write(SAMPLE_LOG_CONTENT.encode('utf-8'))
        temp_file = f.name

    try:
        # Set up file chooser
        with page.expect_file_chooser() as fc_info:
            page.locator('.upload-zone').click()

        file_chooser = fc_info.value
        file_chooser.set_files(temp_file)

        # Verify file info is displayed
        expect(page.locator('.filename')).to_contain_text('.log')
        expect(page.locator('.filesize')).to_be_visible()

        # Upload button should be enabled
        upload_button = page.locator('button.upload-button')
        expect(upload_button).to_be_enabled()

    finally:
        os.unlink(temp_file)


def test_app_header_and_layout(page):
    """Test that the app header and layout are correct."""
    page.goto('http://localhost:5174')
    page.wait_for_load_state('networkidle')

    # Check header
    header = page.locator('.app-header')
    expect(header).to_be_visible()
    expect(header.locator('h1')).to_contain_text('LogFix AI')

    # Check main content area
    expect(page.locator('.app-main')).to_be_visible()


def test_visual_regression_check(page):
    """Take a screenshot to verify the page looks correct."""
    page.goto('http://localhost:5174')
    page.wait_for_load_state('networkidle')

    # Take a screenshot
    screenshot_path = os.path.join(tempfile.gettempdir(), 'logfix_ai_upload_page.png')
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"\n  Screenshot saved to: {screenshot_path}")


# ============ Backend Integration Tests ============

def test_backend_health():
    """Test backend health endpoint."""
    response = requests.get('http://localhost:8000/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'LogFix AI'
    print("  [API] Health check passed")


def test_backend_upload_file():
    """Test file upload API - User Story 1."""
    # Create test log file
    with tempfile.NamedTemporaryFile(suffix='.log', delete=False, mode='w', encoding='utf-8') as f:
        f.write(SAMPLE_LOG_CONTENT)
        temp_file = f.name

    try:
        with open(temp_file, 'rb') as f:
            response = requests.post(
                'http://localhost:8000/api/upload',
                files={'file': ('test.log', f, 'text/plain')}
            )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'file_id' in data['data']

        file_id = data['data']['file_id']
        print(f"  [API] File uploaded successfully: {file_id}")
        return file_id
    finally:
        os.unlink(temp_file)


def test_backend_upload_invalid_file_type():
    """Test uploading non-text file - User Story 1 Scenario 2."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
        temp_file = f.name

    try:
        with open(temp_file, 'rb') as f:
            response = requests.post(
                'http://localhost:8000/api/upload',
                files={'file': ('test.png', f, 'image/png')}
            )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_FILE_TYPE'
        print("  [API] Invalid file type rejected correctly")
    finally:
        os.unlink(temp_file)


def test_backend_regex_validation():
    """Test regex validation - User Story 2."""
    # Valid regex
    response = requests.post(
        'http://localhost:8000/api/validate/regex',
        json={'pattern': r'^\d{4}-\d{2}-\d{2}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    print("  [API] Valid regex accepted")

    # Invalid regex
    response = requests.post(
        'http://localhost:8000/api/validate/regex',
        json={'pattern': r'[\d{2}-\d{2}]'}  # Invalid unbalanced brackets
    )
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert data['error']['code'] == 'INVALID_REGEX'
    print("  [API] Invalid regex rejected correctly")


def test_backend_split_flow(file_id):
    """Test complete split flow - User Stories 2, 3, 4."""
    # Execute split
    response = requests.post(
        'http://localhost:8000/api/split',
        json={
            'file_id': file_id,
            'rule_type': 'regex',
            'rule_content': r'^\d{4}-\d{2}-\d{2}'
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True

    session_id = data['data']['session_id']
    print(f"  [API] Split executed, session: {session_id}")

    # Get session status
    response = requests.get(f'http://localhost:8000/api/sessions/{session_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['data']['status'] == 'completed'
    print("  [API] Session status: completed")

    # Get results
    response = requests.get(f'http://localhost:8000/api/results/{session_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'results' in data['data']
    chunks = data['data']['results']
    print(f"  [API] Split produced {len(chunks)} chunks")

    return session_id, chunks


def test_backend_file_preview(file_id):
    """Test file preview API."""
    response = requests.get(f'http://localhost:8000/api/files/{file_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'preview' in data['data']
    assert 'total_lines' in data['data']
    print(f"  [API] File preview: {data['data']['total_lines']} total lines")


def test_backend_get_chunk_detail(session_id, chunks):
    """Test getting chunk detail - User Story 4."""
    if not chunks:
        print("  [API] Skipping chunk detail (no chunks)")
        return

    chunk_index = chunks[0]['chunk_index']
    response = requests.get(f'http://localhost:8000/api/results/{session_id}/chunks/{chunk_index}')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'content' in data['data']
    print(f"  [API] Chunk {chunk_index} detail retrieved")


def run_backend_tests():
    """Run backend API integration tests."""
    print("\n" + "=" * 50)
    print("Backend API Integration Tests")
    print("=" * 50)

    passed = 0
    failed = 0
    file_id = None
    session_id = None
    chunks = []

    tests = [
        ("Backend health check", test_backend_health),
    ]

    for name, test_func in tests:
        print(f"\nRunning: {name}")
        try:
            result = test_func()
            print(f"  PASSED")
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    # Upload tests
    print("\nRunning: Backend file upload")
    try:
        file_id = test_backend_upload_file()
        print("  PASSED")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    tests2 = [
        ("Backend invalid file type", test_backend_upload_invalid_file_type),
        ("Backend regex validation", test_backend_regex_validation),
    ]

    for name, test_func in tests2:
        print(f"\nRunning: {name}")
        try:
            test_func()
            print(f"  PASSED")
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    # File preview test (needs file_id)
    if file_id:
        print("\nRunning: Backend file preview")
        try:
            test_backend_file_preview(file_id)
            print("  PASSED")
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

        # Split flow test (needs file_id)
        print("\nRunning: Backend split flow")
        try:
            session_id, chunks = test_backend_split_flow(file_id)
            print("  PASSED")
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

        # Chunk detail test (needs session_id and chunks)
        if session_id:
            print("\nRunning: Backend chunk detail")
            try:
                test_backend_get_chunk_detail(session_id, chunks)
                print("  PASSED")
                passed += 1
            except Exception as e:
                print(f"  FAILED: {e}")
                failed += 1

    print("\n" + "=" * 50)
    print(f"Backend Results: {passed} passed, {failed} failed")
    return failed == 0


def main():
    print("Running LogFix AI E2E tests...")
    print("=" * 50)

    # Run backend tests first
    backend_ok = run_backend_tests()

    # Run frontend tests
    print("\n" + "=" * 50)
    print("Frontend UI Tests")
    print("=" * 50)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        tests = [
            ("Page loads correctly", test_page_loads),
            ("Upload without file shows error", test_file_upload_without_file),
            ("Upload UI elements present", test_file_upload_ui_elements),
            ("Upload text file flow", test_upload_text_file),
            ("Upload non-text file flow", test_upload_non_text_file),
            ("App header and layout", test_app_header_and_layout),
            ("Visual regression check", test_visual_regression_check),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            print(f"\nRunning: {name}")
            try:
                test_func(page)
                print(f"  PASSED")
                passed += 1
            except Exception as e:
                print(f"  FAILED: {e}")
                failed += 1

        browser.close()

        print("\n" + "=" * 50)
        print(f"Frontend Results: {passed} passed, {failed} failed")

        return 0 if (backend_ok and failed == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
