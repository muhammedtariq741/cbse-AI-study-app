
import requests
import json
import sys

def test_backend():
    url = "http://127.0.0.1:8000/api/v1/query"
    payload = {
        "question": "What is matter?",
        "subject": "Science",
        "marks": 1
    }
    
    print(f"Testing URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        
        print(f"\nStatus Code: {response.status_code}")
        if response.status_code == 200:
            print("\n✅ Success! Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\n❌ Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Connection Failed: {e}")

if __name__ == "__main__":
    test_backend()
