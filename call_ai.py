import requests
import json
import os

# 替换为你的实际API密钥
API_KEY = os.getenv('GEMINI_API_KEY')
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# 请求头
headers = {
    'Content-Type': 'application/json'
}

# 请求体数据
data = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Hi ,how are you"
                }
            ]
        }
    ]
}

try:
    # 发送POST请求
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    # 检查请求是否成功
    response.raise_for_status()
    
    # 打印响应内容
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.HTTPError as errh:
    print(f"HTTP错误: {errh}")
except requests.exceptions.ConnectionError as errc:
    print(f"连接错误: {errc}")
except requests.exceptions.Timeout as errt:
    print(f"超时错误: {errt}")
except requests.exceptions.RequestException as err:
    print(f"其他错误: {err}")
