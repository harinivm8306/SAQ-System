import google.generativeai as genai
import sys

def test_api():
    key = "AIzaSyAA2EPgHkJCJ3XZY2vJAEatfmPm8Ry3WaY"
    genai.configure(api_key=key)
    print("Testing authorized models...")
    try:
        models = genai.list_models()
        for m in models:
            print(f"Found: {m.name}")
    except Exception as e:
        print(f"List Models Failure: {e}")

    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        print("Testing generation with gemini-1.5-flash...")
        response = model.generate_content("Hello")
        print("SUCCESS: " + response.text)
    except Exception as e:
        print("Generation Failure: " + str(e))

if __name__ == "__main__":
    test_api()
