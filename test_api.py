"""
简单的 API 测试脚本
运行方式：先启动服务器 (uvicorn main:app --reload)，然后在另一个终端运行此脚本
"""
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_create_user():
    """测试创建用户"""
    print("测试创建用户...")
    user_data = {"id": 1, "name": "张三", "age": 25}
    response = requests.post(f"{BASE_URL}/users", json=user_data)
    print(f"创建用户响应: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_get_users():
    """测试获取所有用户"""
    print("\n测试获取所有用户...")
    response = requests.get(f"{BASE_URL}/users")
    print(f"获取用户列表响应: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_get_user():
    """测试获取单个用户"""
    print("\n测试获取单个用户...")
    response = requests.get(f"{BASE_URL}/users/1")
    print(f"获取用户响应: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_update_user():
    """测试更新用户"""
    print("\n测试更新用户...")
    user_data = {"id": 1, "name": "李四", "age": 30}
    response = requests.put(f"{BASE_URL}/users/1", json=user_data)
    print(f"更新用户响应: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_delete_user():
    """测试删除用户"""
    print("\n测试删除用户...")
    response = requests.delete(f"{BASE_URL}/users/1")
    print(f"删除用户响应: {response.status_code} - {response.json()}")
    return response.status_code == 200

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("开始测试 FastAPI 用户 CRUD 接口")
        print("=" * 50)
        
        test_create_user()
        test_get_users()
        test_get_user()
        test_update_user()
        test_get_user()
        test_delete_user()
        test_get_users()
        
        print("\n" + "=" * 50)
        print("测试完成！")
        print("=" * 50)
    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到服务器。请确保服务器已启动:")
        print("uvicorn main:app --reload")
    except Exception as e:
        print(f"\n错误: {e}")
