from django.shortcuts import render, redirect, get_object_or_404 # pyre-ignore
from django.contrib.auth.decorators import login_required # pyre-ignore
from django.http import JsonResponse, HttpResponse # pyre-ignore
from django.utils import timezone # pyre-ignore
from quizzes.models import QuizAttempt, QuizQuestion # pyre-ignore
from dashboard.models import Subcategory # pyre-ignore
from dashboard.utils import update_leaderboard_stats # pyre-ignore
import json
import datetime

def category_list(request):
    return HttpResponse("Quizzes app is working 🚀")

@login_required
def take_quiz(request):
    """
    Initializes the quiz attempt in DB when the user starts a fresh quiz.
    """
    quiz_data_raw = request.session.get('generated_quiz_data', {})
    settings = request.session.get('quiz_settings', {})
    
    if not quiz_data_raw or not settings:
        return redirect('categories')
    
    subcategory = Subcategory.objects.get(id=settings['subcategory_id'])
    
    attempt = QuizAttempt.objects.create(
        user=request.user,
        subcategory=subcategory,
        total_questions=len(quiz_data_raw['questions']),
        timer_enabled=settings['timer_enabled'],
        timer_duration=settings['timer_duration'],
        learning_resources=quiz_data_raw.get('learning_resources', []),
        started_at=timezone.now(),
        is_completed=False
    )
    
    for q_data in quiz_data_raw['questions']:
        QuizQuestion.objects.create(
            attempt=attempt,
            question_text=q_data['question'],
            options=q_data['options'],
            correct_answer=q_data['answer'],
            explanation=q_data.get('explanation', "No explanation provided.")
        )
    
    if 'generated_quiz_data' in request.session:
        del request.session['generated_quiz_data']
    
    return redirect('resume_quiz', attempt_id=attempt.id)

@login_required
def resume_quiz(request, attempt_id):
    """
    Renders the in-progress quiz interface, loading saved progress.
    """
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    if attempt.is_completed:
        return redirect('quiz_result', attempt_id=attempt.id)
        
    questions_query = attempt.questions.all().order_by('id')
    questions_list = []
    for q in questions_query:
        questions_list.append({
            'db_id': q.id,
            'question': q.question_text,
            'options': q.options,
            'answer': q.correct_answer,
            'user_answer': q.user_answer,
            'explanation': q.explanation
        })
        
    # Calculate remaining time if timer is enabled
    timer_remaining = 0
    if attempt.timer_enabled and attempt.timer_duration:
        time_elapsed = (timezone.now() - attempt.started_at).total_seconds()
        remaining = attempt.timer_duration * 60 - time_elapsed
        timer_remaining = int(max(remaining, 0))
        
    context = {
        'attempt': attempt,
        'questions': questions_list,
        'subcategory_name': attempt.subcategory.name,
        'total_questions': attempt.total_questions,
        'timer_remaining': timer_remaining,
        'timer_enabled': attempt.timer_enabled
    }
    return render(request, 'quizzes/take_quiz.html', context)

@login_required
def save_progress(request, attempt_id):
    """
    Iteratively saves answers into DB while the quiz is in-progress.
    """
    if request.method == 'POST':
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
        try:
            data = json.loads(request.body)
            answers = data.get('answers', {})
            # answers map is index -> user_answer
            questions_query = list(attempt.questions.all().order_by('id'))
            updated_questions = []
            for idx, q in enumerate(questions_query):
                str_idx = str(idx)
                if str_idx in answers and answers[str_idx]:
                    q.user_answer = answers[str_idx]
                    updated_questions.append(q)
            if updated_questions:
                QuizQuestion.objects.bulk_update(updated_questions, ['user_answer'])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid Method'}, status=405)

@login_required
def abandon_quiz(request, attempt_id):
    """
    Deletes an uncompleted quiz attempt.
    """
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    if not attempt.is_completed:
        attempt.delete()
    return redirect('dashboard')

@login_required
def submit_quiz(request, attempt_id):
    """
    Finalizes the quiz submission.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
        if attempt.is_completed:
            return JsonResponse({'error': 'Already submitted'}, status=400)
             
        data = json.loads(request.body)
        user_answers = data.get('answers', {})
        
        # Initializing score count
        calculated_score = 0
        questions_query = list(attempt.questions.all().order_by('id'))
        
        for idx, q in enumerate(questions_query):
            str_idx = str(idx)
            if str_idx in user_answers:
                q.user_answer = user_answers[str_idx]
                
            is_correct_bool = (q.user_answer == q.correct_answer)
            q.is_correct = is_correct_bool
            
            if is_correct_bool:
                calculated_score += 1  # pyre-ignore
                
        # Bulk save all changes to questions
        QuizQuestion.objects.bulk_update(questions_query, ['user_answer', 'is_correct'])
        
        attempt.score = calculated_score
        attempt.is_completed = True
        attempt.save()
        
        # Update Leaderboard Stats
        update_leaderboard_stats(request.user, attempt)
        
        # Store attempt ID in session for backwards compatibility if needed
        request.session['last_attempt_id'] = attempt.id
        
        return JsonResponse({'status': 'success', 'redirect_url': f'/quizzes/result/{attempt.id}/'})
        
    except Exception as e:
        print(f"Submission error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def quiz_result(request, attempt_id):
    """
    Displays the detailed results of a quiz attempt.
    """
    import re
    try:
        attempt = QuizAttempt.objects.select_related('subcategory').prefetch_related('questions').get(id=attempt_id, user=request.user)
        
        # Process learning resources to extract URLs
        processed_resources = []
        if attempt.learning_resources:
            for res in attempt.learning_resources:
                # Match "Title - URL" or just "URL"
                match = re.search(r'(.*?)\s*-\s*(https?://\S+)', res)
                if match:
                    processed_resources.append({
                        'title': match.group(1).strip(),
                        'url': match.group(2).strip()
                    })
                else:
                    # Fallback for just URLs or different formats
                    url_match = re.search(r'(https?://\S+)', res)
                    if url_match:
                        url = url_match.group(1)
                        title = res.replace(url, "").strip(" -").strip() or "Resource"
                        processed_resources.append({'title': title, 'url': url})
                    else:
                        processed_resources.append({'title': res, 'url': '#'})
        
        return render(request, 'quizzes/quiz_result.html', {
            'attempt': attempt,
            'processed_resources': processed_resources
        })
    except QuizAttempt.DoesNotExist:
        return redirect('categories')
