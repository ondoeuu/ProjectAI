import requests
try:
    resp = requests.post("http://127.0.0.1:8086/api/onboard", json={"intent_text": "chci zalozit autoopravnu a.s."})
    print(resp.status_code)
    print(resp.json())
except Exception as e:
    print(e)
