import base64
import requests

with open("screenshot.png", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

response = requests.post("http://localhost:8000/ocr", json={
    "image_base64": image_b64,
    "prompt_type": "ocr_layout"
})
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500] if response.text else 'Empty'}")
if response.ok:
    print(response.json())