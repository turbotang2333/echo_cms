with open("taptap_debug.html", "r", encoding="utf-8") as f:
    content = f.read()

keywords = ["关注", "预约", "rating"]
for kw in keywords:
    idx = content.find(kw)
    if idx != -1:
        start = max(0, idx - 200)
        end = min(len(content), idx + 200)
        print(f"\n=== Context for '{kw}' ===\n")
        print(content[start:end])
    else:
        print(f"\n=== '{kw}' NOT FOUND ===")



















