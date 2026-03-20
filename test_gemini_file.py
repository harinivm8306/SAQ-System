import google.generativeai as genai
import sys

def log_test():
    with open('gemini_debug.log', 'w') as f:
        key = "AIzaSyAA2EPgHkJCJ3XZY2vJAEatfmPm8Ry3WaY"
        genai.configure(api_key=key)
        f.write("Testing API Key...\n")
        try:
            models = genai.list_models()
            f.write("Authorized Models:\n")
            for m in models:
                f.write(f"- {m.name}\n")
        except Exception as e:
            f.write(f"List Models Failure: {str(e)}\n")

        model = genai.GenerativeModel('gemini-flash-latest')
        try:
            f.write("Testing generation with gemini-flash-latest...\n")
            response = model.generate_content("Hello")
            f.write(f"SUCCESS: {response.text}\n")
        except Exception as e:
            f.write(f"Generation Failure: {str(e)}\n")

if __name__ == "__main__":
    log_test()
