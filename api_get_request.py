import requests
url = 'https://api.example.com/data'
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f'Có lỗi xảy ra: {response.status_code}')
