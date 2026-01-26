# scripts/test_api.py
"""
API 测试脚本
用于快速测试各个接口是否正常工作
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


def test_health_check():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_create_user():
    """测试创建用户"""
    print("\n=== 测试创建用户 ===")
    user_data = {
        "uid": "test_user_001",
        "member_level": 1,
        "modeler_level": 0,
        "sex": "male",
        "country": "China",
        "province": "Beijing",
        "city": "Beijing"
    }
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_get_users():
    """测试获取用户列表"""
    print("\n=== 测试获取用户列表 ===")
    response = requests.get(f"{BASE_URL}/users/?skip=0&limit=10")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_get_user(uid):
    """测试获取单个用户"""
    print(f"\n=== 测试获取用户 {uid} ===")
    response = requests.get(f"{BASE_URL}/users/{uid}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_update_user(uid):
    """测试更新用户"""
    print(f"\n=== 测试更新用户 {uid} ===")
    update_data = {
        "city": "Shanghai",
        "member_level": 1
    }
    response = requests.put(f"{BASE_URL}/users/{uid}", json=update_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_create_item():
    """测试创建商品"""
    print("\n=== 测试创建商品 ===")
    item_data = {
        "id": "test_item_001",
        "group_name": "测试3D模型",
        "first_level_category_name": "模型",
        "second_level_category_name": "建筑模型",
        "tags_name_list": "建筑,现代,高清",
        "group_desc": "这是一个测试商品"
    }
    response = requests.post(f"{BASE_URL}/items/", json=item_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_get_items():
    """测试获取商品列表"""
    print("\n=== 测试获取商品列表 ===")
    response = requests.get(f"{BASE_URL}/items/?skip=0&limit=10")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_get_item(item_id):
    """测试获取单个商品"""
    print(f"\n=== 测试获取商品 {item_id} ===")
    response = requests.get(f"{BASE_URL}/items/{item_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_update_item(item_id):
    """测试更新商品"""
    print(f"\n=== 测试更新商品 {item_id} ===")
    update_data = {
        "group_desc": "更新后的商品描述",
        "tags_name_list": "建筑,现代,高清,热门"
    }
    response = requests.put(f"{BASE_URL}/items/{item_id}", json=update_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试 API")
    print("=" * 60)
    
    # 测试健康检查
    test_health_check()
    
    # 测试用户相关接口
    test_create_user()
    test_get_users()
    test_get_user("test_user_001")
    test_update_user("test_user_001")
    
    # 测试商品相关接口
    test_create_item()
    test_get_items()
    test_get_item("test_item_001")
    test_update_item("test_item_001")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
