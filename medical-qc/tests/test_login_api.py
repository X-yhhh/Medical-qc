import requests
import sys

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_login():
    print("Testing Login...")
    # 尝试登录一个可能存在的用户（或者先注册）
    username = "test_user_001"
    password = "password123"
    
    # 1. Register
    print(f"Registering {username}...")
    reg_data = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "full_name": "Test User",
        "hospital": "Test Hospital",
        "department": "Radiology"
    }
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
        print(f"Register Status: {resp.status_code}")
        print(f"Register Response: {resp.text}")
    except Exception as e:
        print(f"Register Failed: {e}")

    # 2. Login
    print(f"Logging in {username}...")
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login Status: {resp.status_code}")
        print(f"Login Response: {resp.text}")
        
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            print(f"✅ Login Success! Token: {token}")
            return True
        else:
            print("❌ Login Failed")
            return False
            
    except Exception as e:
        print(f"Login Exception: {e}")
        return False

if __name__ == "__main__":
    test_login()
