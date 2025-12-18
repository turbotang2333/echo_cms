import requests
import random

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

url = "https://www.taptap.cn/app/786394?os=android"

try:
    resp = requests.get(url, headers={"User-Agent": USER_AGENTS[0], "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    print(f"Status: {resp.status_code}")
    with open("taptap_debug.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("Saved taptap_debug.html")
except Exception as e:
    print(e)







