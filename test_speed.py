import os
import django
import time
import json

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from dashboard.utils import generate_quiz_questions

def test_generation_speed(max_retries=3):
    topic = "Python Programming"
    difficulty = "Medium"
    count = 10

    print(f"Starting quiz generation for {topic} ({difficulty}, {count} questions)...")

    for attempt in range(1, max_retries + 1):
        print(f"\nAttempt {attempt} of {max_retries}...")
        start_time = time.time()

        result = generate_quiz_questions(topic, difficulty, count)

        end_time = time.time()
        duration = end_time - start_time

        if result and 'questions' in result:
            print(f"SUCCESS: Generated {len(result['questions'])} questions in {duration:.2f} seconds.")
            # print(json.dumps(result, indent=2))
            return
        else:
            print(f"FAILED: Generation failed or returned invalid format in {duration:.2f} seconds.")
            if attempt < max_retries:
                wait = 60
                print(f"Waiting {wait}s before retrying (rate-limit cooldown)...")
                time.sleep(wait)

    print("\nAll attempts exhausted. Please check your API key quota at https://ai.dev/rate-limit")

if __name__ == "__main__":
    test_generation_speed()
