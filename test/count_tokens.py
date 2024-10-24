import requests

# 定义请求的URL
url = "http://localhost:8000/count-tokens"

# 定义请求的数据
data = {
    "query": "中华人们共和国！"
}

# 发送POST请求
response = requests.post(url, json=data)

# 解析响应
if response.status_code == 200:
    result = response.json()
    if result["ok"]:
        print(f"Tokens length: {result['tokens_length']}")
    else:
        print(f"Error: {result['message']}")
else:
    print(f"Request failed with status code: {response.status_code}")