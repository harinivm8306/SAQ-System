import google.generativeai as genai # pyre-ignore
# Types are accessed via genai.types if needed
import json
from django.conf import settings # pyre-ignore
from dashboard.models import Category, UserCategoryStats, Profile # pyre-ignore
from django.db.models import Avg, Sum # pyre-ignore

def generate_quiz_questions(topic, difficulty, count, extra_comments=""):
    """
    Generates quiz questions using Gemini AI (Optimized for speed).
    """
    try:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in settings.py")

        genai.configure(api_key=settings.GEMINI_API_KEY)
        client = genai.GenerativeModel('gemini-flash-latest')

        prompt = f"""
        Generate a {topic} quiz ({difficulty}). Count: {count}.
        Instructions: {extra_comments}

        Return JSON with:
        1. "questions": list of {count} objects:
           "question": string,
           "options": list of 4,
           "answer": must match one option exactly,
           "explanation": concise explanation (MAX 2 sentences).
        2. "learning_resources": list of 3 strings "Title - URL".
        """

        response = client.generate_content(
            contents=prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type='application/json',
                temperature=0,
            ),
        )
        return json.loads(response.text)

    except Exception as e:
        import traceback
        print(f"Error generating quiz: {e}")
        traceback.print_exc()
        return None

def update_leaderboard_stats(user, attempt):
    """
    Updates the user's profile and category-specific stats for the leaderboard.
    """
    profile, _ = Profile.objects.get_or_create(user=user)
    
    # 1. Update Global Profile Stats
    profile.total_score += attempt.score
    profile.quizzes_completed += 1
    
    # Calculate global accuracy
    from quizzes.models import QuizAttempt # pyre-ignore
    all_completed = QuizAttempt.objects.filter(user=user, is_completed=True)
    total_q = all_completed.aggregate(total=Sum('total_questions'))['total'] or 0
    total_c = all_completed.aggregate(total=Sum('score'))['total'] or 0
    
    if total_q > 0:
        accuracy = float((total_c / total_q) * 100)
        profile.avg_accuracy = round(accuracy, 1) # pyre-ignore
    
    # Update highest streak from this attempt
    from quizzes.models import QuizQuestion # pyre-ignore
    attempt_questions = QuizQuestion.objects.filter(attempt=attempt).order_by('id')
    current_streak = 0
    max_attempt_streak = 0
    for q in attempt_questions:
        if q.is_correct:
            current_streak += 1
            max_attempt_streak = max(max_attempt_streak, current_streak)
        else:
            current_streak = 0
    
    if max_attempt_streak > profile.highest_streak:
        profile.highest_streak = max_attempt_streak
        
    profile.save()
    
    # 2. Update Category Stats
    if attempt.subcategory and attempt.subcategory.category:
        cat_stats, _ = UserCategoryStats.objects.get_or_create(
            user=user, 
            category=attempt.subcategory.category
        )
        cat_stats.total_score += attempt.score
        cat_stats.quizzes_completed += 1
        cat_stats.save()
