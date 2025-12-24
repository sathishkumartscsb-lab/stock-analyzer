import requests
import sys

def test_webapp():
    url = "http://127.0.0.1:5000/analyze"
    print(f"Sending POST to {url}...")
    try:
        response = requests.post(url, data={'stock_name': 'TATAMOTORS'})
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)
        
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        if "TATAMOTORS" in response.text and "Fundamentals" in response.text:
            print("SUCCESS: Result page contains expected data.")
            # Optionally save for inspection
            with open("test_output.html", "w", encoding="utf-8") as f:
                f.write(response.text)
        else:
            print("FAILURE: Result page missing key data.")
            print(response.text[:500])
    else:
        print("FAILURE: Non-200 status code.")

if __name__ == "__main__":
    test_webapp()
