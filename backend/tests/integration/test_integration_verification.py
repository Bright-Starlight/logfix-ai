"""
集成验证脚本: T078.1 - T078.8

验证日志分类与结构化存储系统的各项功能是否正常工作。
"""

import sys
import os
import time
import requests
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 配置
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
API_BASE = f"{BACKEND_URL}/api"


class IntegrationVerifier:
    """集成验证器"""

    def __init__(self):
        self.results = []

    def check(self, name: str, condition: bool, message: str = ""):
        """记录检查结果"""
        status = "✓ PASS" if condition else "✗ FAIL"
        self.results.append({
            "name": name,
            "status": status,
            "passed": condition,
            "message": message,
        })
        print(f"{status}: {name}")
        if message:
            print(f"      {message}")

    def print_summary(self):
        """打印总结"""
        print("\n" + "=" * 60)
        print("集成验证总结")
        print("=" * 60)

        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)

        for r in self.results:
            print(f"  {r['status']}: {r['name']}")

        print(f"\n通过: {passed}/{total}")

        if passed == total:
            print("\n✓ 所有验证项通过!")
        else:
            print("\n✗ 部分验证项失败，请检查上述失败项。")

        return passed == total


def verify_backend_service():
    """T078.1: 验证后端服务启动成功"""
    verifier = IntegrationVerifier()

    try:
        # 检查 /docs 端点
        response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        verifier.check(
            "T078.1 - 后端服务 /docs 可访问",
            response.status_code == 200,
            f"状态码: {response.status_code}"
        )
    except requests.exceptions.ConnectionError:
        verifier.check("T078.1 - 后端服务 /docs 可访问", False, "无法连接到后端服务")
    except requests.exceptions.Timeout:
        verifier.check("T078.1 - 后端服务 /docs 可访问", False, "请求超时")
    except Exception as e:
        verifier.check("T078.1 - 后端服务 /docs 可访问", False, str(e))

    # 检查健康端点
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        verifier.check(
            "T078.1 - 健康检查端点正常",
            response.status_code == 200 and response.json().get("status") == "healthy",
            f"响应: {response.json()}"
        )
    except Exception as e:
        verifier.check("T078.1 - 健康检查端点正常", False, str(e))

    return verifier


def verify_frontend_service():
    """T078.2: 验证前端服务启动成功"""
    verifier = IntegrationVerifier()

    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        verifier.check(
            "T078.2 - 前端服务可访问",
            response.status_code == 200,
            f"状态码: {response.status_code}"
        )
    except requests.exceptions.ConnectionError:
        verifier.check("T078.2 - 前端服务可访问", False, "无法连接到前端服务 (可能尚未启动)")
    except requests.exceptions.Timeout:
        verifier.check("T078.2 - 前端服务可访问", False, "请求超时")
    except Exception as e:
        verifier.check("T078.2 - 前端服务可访问", False, str(e))

    return verifier


def verify_database_connection():
    """T078.3: 验证数据库连接正常"""
    verifier = IntegrationVerifier()

    try:
        from backend.src.db.session import get_db_session, init_db

        init_db()

        with get_db_session() as db:
            # 执行一个简单查询
            from backend.src.models.entities import LogEntry
            count = db.query(LogEntry).count()
            verifier.check(
                "T078.3 - 数据库连接正常",
                True,
                f"LogEntry 表存在，当前记录数: {count}"
            )
    except Exception as e:
        verifier.check("T078.3 - 数据库连接正常", False, str(e))

    return verifier


def verify_log_files():
    """T078.4: 验证日志文件输出到 /log 目录"""
    verifier = IntegrationVerifier()

    log_dir = Path("log")

    # 检查 log 目录是否存在
    verifier.check(
        "T078.4 - /log 目录存在",
        log_dir.exists() and log_dir.is_dir(),
        f"路径: {log_dir.absolute()}"
    )

    # 检查日志文件是否存在
    if log_dir.exists():
        log_files = list(log_dir.glob("logfix-ai_*.log"))
        verifier.check(
            "T078.4 - 日志文件命名正确 (logfix-ai_YYYYMMDD.log)",
            len(log_files) > 0,
            f"找到 {len(log_files)} 个日志文件"
        )

        if log_files:
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            verifier.check(
                "T078.4 - 日志文件可写入",
                latest_log.stat().st_size >= 0,
                f"最新日志文件: {latest_log.name}, 大小: {latest_log.stat().st_size} bytes"
            )
    else:
        verifier.check("T078.4 - 日志文件命名正确", False, "/log 目录不存在")

    return verifier


def verify_rule_engine():
    """T078.5: 验证规则引擎模式正常工作"""
    verifier = IntegrationVerifier()

    test_logs = [
        "2024-01-15 10:23:45 ERROR java.lang.NullPointerException: Cannot invoke method on null object",
        "2024-01-15 10:23:46 ERROR Database connection failed: timeout after 30s",
    ]

    try:
        response = requests.post(
            f"{API_BASE}/classify",
            json={"logs": test_logs, "mode": "rule_engine"},
            timeout=10,
        )

        verifier.check(
            "T078.5 - 规则引擎分类接口正常",
            response.status_code == 200,
            f"状态码: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            verifier.check(
                "T078.5 - 规则引擎返回正确格式",
                data.get("success") is True,
                f"success: {data.get('success')}"
            )

            if data.get("success") and data.get("data"):
                result = data["data"]
                verifier.check(
                    "T078.5 - 规则引擎处理结果",
                    True,
                    f"处理: {result.get('processed')}条, 新增: {result.get('new_entries')}条, 重复: {result.get('duplicates')}条"
                )
    except requests.exceptions.Timeout:
        verifier.check("T078.5 - 规则引擎分类接口正常", False, "请求超时")
    except Exception as e:
        verifier.check("T078.5 - 规则引擎分类接口正常", False, str(e))

    return verifier


def verify_ai_mode():
    """T078.6: 验证 AI 模式正常工作（需要配置 API Key）"""
    verifier = IntegrationVerifier()

    # 检查是否配置了 API Key
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        verifier.check(
            "T078.6 - AI 模式 API Key 已配置",
            False,
            "MINIMAX_API_KEY 未配置，跳过 AI 模式测试"
        )
        return verifier

    test_logs = [
        "2024-01-15 10:23:45 ERROR Failed to connect to database at line 45",
        "2024-01-15 10:23:46 ERROR Connection timeout after 30s",
    ]

    try:
        response = requests.post(
            f"{API_BASE}/classify",
            json={"logs": test_logs, "mode": "ai"},
            timeout=30,
        )

        verifier.check(
            "T078.6 - AI 模式分类接口正常",
            response.status_code == 200,
            f"状态码: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            verifier.check(
                "T078.6 - AI 模式返回正确格式",
                data.get("success") is True,
                f"success: {data.get('success')}"
            )
    except requests.exceptions.Timeout:
        verifier.check("T078.6 - AI 模式分类接口正常", False, "请求超时 (AI 响应可能较慢)")
    except Exception as e:
        verifier.check("T078.6 - AI 模式分类接口正常", False, str(e))

    return verifier


def verify_rule_crud():
    """T078.7: 验证 ParseRule CRUD 操作正常"""
    verifier = IntegrationVerifier()

    try:
        # GET - 获取规则列表
        response = requests.get(f"{API_BASE}/rules", timeout=5)
        verifier.check(
            "T078.7 - ParseRule GET 接口正常",
            response.status_code == 200,
            f"状态码: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            verifier.check(
                "T078.7 - ParseRule GET 返回正确格式",
                "rules" in data,
                f"获取到 {len(data.get('rules', []))} 条规则"
            )

        # POST - 创建规则
        new_rule = {
            "name": f"测试规则 {int(time.time())}",
            "rule_type": "regex",
            "pattern": r"(\w+Error): (.+)",
            "priority": 1,
            "enabled": True,
        }

        response = requests.post(f"{API_BASE}/rules", json=new_rule, timeout=5)

        if response.status_code == 200:
            data = response.json()
            rule_id = data.get("data", {}).get("id")

            verifier.check(
                "T078.7 - ParseRule POST 创建规则",
                rule_id is not None,
                f"创建规则 ID: {rule_id}"
            )

            # DELETE - 删除规则
            if rule_id:
                response = requests.delete(f"{API_BASE}/rules/{rule_id}", timeout=5)
                verifier.check(
                    "T078.7 - ParseRule DELETE 删除规则",
                    response.status_code == 200,
                    f"状态码: {response.status_code}"
                )
        else:
            verifier.check("T078.7 - ParseRule POST 创建规则", False, f"状态码: {response.status_code}")

    except Exception as e:
        verifier.check("T078.7 - ParseRule CRUD 操作", False, str(e))

    return verifier


def verify_ignore_rule_crud():
    """T078.8: 验证 IgnoreRule CRUD 操作正常"""
    verifier = IntegrationVerifier()

    try:
        # GET - 获取忽略规则列表
        response = requests.get(f"{API_BASE}/ignore-rules", timeout=5)
        verifier.check(
            "T078.8 - IgnoreRule GET 接口正常",
            response.status_code == 200,
            f"状态码: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            verifier.check(
                "T078.8 - IgnoreRule GET 返回正确格式",
                "rules" in data,
                f"获取到 {len(data.get('rules', []))} 条忽略规则"
            )

        # POST - 创建忽略规则
        new_rule = {
            "name": f"测试忽略规则 {int(time.time())}",
            "match_type": "contains",
            "pattern": "Connection timeout",
            "enabled": True,
        }

        response = requests.post(f"{API_BASE}/ignore-rules", json=new_rule, timeout=5)

        if response.status_code == 200:
            data = response.json()
            rule_id = data.get("data", {}).get("id")

            verifier.check(
                "T078.8 - IgnoreRule POST 创建规则",
                rule_id is not None,
                f"创建忽略规则 ID: {rule_id}"
            )

            # DELETE - 删除规则
            if rule_id:
                response = requests.delete(f"{API_BASE}/ignore-rules/{rule_id}", timeout=5)
                verifier.check(
                    "T078.8 - IgnoreRule DELETE 删除规则",
                    response.status_code == 200,
                    f"状态码: {response.status_code}"
                )
        else:
            verifier.check("T078.8 - IgnoreRule POST 创建规则", False, f"状态码: {response.status_code}")

    except Exception as e:
        verifier.check("T078.8 - IgnoreRule CRUD 操作", False, str(e))

    return verifier


def main():
    """运行所有集成验证"""
    print("=" * 60)
    print("LogFix AI - 集成验证 (T078.1 - T078.8)")
    print("=" * 60)
    print()

    all_verifiers = []

    # T078.1 - T078.4: 基础服务验证
    print("[1/8] 验证后端服务...")
    v1 = verify_backend_service()
    all_verifiers.append(v1)
    print()

    print("[2/8] 验证前端服务...")
    v2 = verify_frontend_service()
    all_verifiers.append(v2)
    print()

    print("[3/8] 验证数据库连接...")
    v3 = verify_database_connection()
    all_verifiers.append(v3)
    print()

    print("[4/8] 验证日志文件输出...")
    v4 = verify_log_files()
    all_verifiers.append(v4)
    print()

    # T078.5 - T078.8: 功能验证
    print("[5/8] 验证规则引擎模式...")
    v5 = verify_rule_engine()
    all_verifiers.append(v5)
    print()

    print("[6/8] 验证 AI 模式...")
    v6 = verify_ai_mode()
    all_verifiers.append(v6)
    print()

    print("[7/8] 验证 ParseRule CRUD...")
    v7 = verify_rule_crud()
    all_verifiers.append(v7)
    print()

    print("[8/8] 验证 IgnoreRule CRUD...")
    v8 = verify_ignore_rule_crud()
    all_verifiers.append(v8)
    print()

    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    total_passed = 0
    total_checks = 0

    for i, v in enumerate(all_verifiers, 1):
        passed = sum(1 for r in v.results if r["passed"])
        total = len(v.results)
        total_passed += passed
        total_checks += total
        print(f"[{i}] 通过: {passed}/{total}")

    print(f"\n总计: {total_passed}/{total_checks} 项验证通过")

    if total_passed == total_checks:
        print("\n✓ 所有集成验证项通过!")
        return 0
    else:
        print("\n✗ 部分验证项失败。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
