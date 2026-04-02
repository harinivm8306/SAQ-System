from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Room, RoomMember, RoomAnswer
import json
import datetime
from django.views.decorators.csrf import csrf_exempt

@login_required
def live_quiz_view(request, room_code):
    room = get_object_or_404(Room, code=room_code)
    is_creator = (room.creator == request.user)
    is_member = RoomMember.objects.filter(room=room, user=request.user).exists()
    
    if not is_creator and not is_member:
        return redirect('join_room')
        
    return render(request, 'rooms/live_quiz.html', {'room': room, 'is_creator': is_creator})

@login_required
def status_api(request, room_code):
    room = get_object_or_404(Room, code=room_code)
    
    # Leaderboard logic
    leaderboard = []
    if room.status == 'leaderboard' or room.status == 'finished':
        members = RoomMember.objects.filter(room=room).order_by('-score')
        for m in members:
            leaderboard.append({'username': m.user.username, 'score': m.score})

    question_data = None
    if room.status == 'active' and room.questions_data:
        q_list = room.questions_data.get('questions', [])
        idx = room.current_question_index
        if idx < len(q_list):
            question_data = dict(q_list[idx])
            # Hide answer for participants
            if room.creator != request.user:
                question_data.pop('answer', None)
                if 'match_pairs' in question_data: 
                    # keep keys, remove values for participant to solve
                    keys = list(question_data['match_pairs'].keys())
                    vals = list(question_data['match_pairs'].values())
                    import random
                    random.shuffle(vals)
                    question_data['match_keys'] = keys
                    question_data['match_vals'] = vals
                    question_data.pop('match_pairs', None)
                if 'items' in question_data:
                    items = list(question_data['items'])
                    import random
                    random.shuffle(items)
                    question_data['shuffled_items'] = items
                    question_data.pop('items', None)

    time_left = 0
    if room.status == 'active' and room.timer_end:
        now = timezone.now()
        diff = (room.timer_end - now).total_seconds()
        time_left = max(0, int(diff))
        if time_left == 0 and room.creator == request.user:
            room.status = 'leaderboard'
            room.save()

    return JsonResponse({
        'status': room.status, # waiting, active, leaderboard, finished
        'question_index': room.current_question_index,
        'question': question_data,
        'time_left': time_left,
        'leaderboard': leaderboard,
        'members_count': room.members.count(),
        'total_questions': len(room.questions_data.get('questions', [])) if room.questions_data else 0
    })

@csrf_exempt
@login_required
def next_question_api(request, room_code):
    room = get_object_or_404(Room, code=room_code)
    if room.creator != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    num_questions = len(room.questions_data.get('questions', [])) if room.questions_data else 0
    
    if room.status == 'waiting' or room.status == 'leaderboard':
        if room.status == 'leaderboard':
            room.current_question_index += 1
            
        if room.current_question_index >= num_questions:
            room.status = 'finished'
        else:
            room.status = 'active'
            room.timer_end = timezone.now() + datetime.timedelta(seconds=20) # 20 sec per q
        room.save()
        return JsonResponse({'status': 'success'})
        
    return JsonResponse({'error': 'Invalid state transition'}, status=400)

@csrf_exempt
@login_required
def submit_answer_api(request, room_code):
    room = get_object_or_404(Room, code=room_code)
    if room.status != 'active':
        return JsonResponse({'error': 'Not active'}, status=400)
        
    if request.method == 'POST':
        data = json.loads(request.body)
        user_answer = data.get('answer')
        
        idx = room.current_question_index
        q_list = room.questions_data.get('questions', [])
        if idx >= len(q_list):
            return JsonResponse({'error': 'Out of bounds'}, status=400)
            
        correct = False
        q_data = q_list[idx]
        q_type = q_data.get('type', 'mcq')
        
        if q_type == 'mcq' or q_type == 'typing':
            correct = (str(user_answer).strip().lower() == str(q_data.get('answer')).strip().lower())
        elif q_type == 'arrange':
            correct = (user_answer == q_data.get('items'))
        elif q_type == 'match':
            correct = (user_answer == q_data.get('match_pairs'))
            
        time_taken = 20
        if room.timer_end:
            now = timezone.now()
            left = (room.timer_end - now).total_seconds()
            time_taken = max(0, 20 - left)
            
        points = 0
        if correct:
            points = max(10, int((20 - time_taken) * 10)) # Max 200, min 10
            
        RoomAnswer.objects.update_or_create(
            room=room, user=request.user, question_index=idx,
            defaults={'is_correct': correct, 'points': points, 'time_taken': time_taken}
        )
        
        # update total score
        member = RoomMember.objects.get(room=room, user=request.user)
        total_points = sum(a.points for a in RoomAnswer.objects.filter(room=room, user=request.user))
        member.score = total_points
        member.save()
        
        return JsonResponse({'status': 'success', 'correct': correct, 'points': points})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@login_required
def download_report(request, room_code):
    room = get_object_or_404(Room, code=room_code)
    
    # Simple HTML print rendering as a "PDF export" layout
    members = RoomMember.objects.filter(room=room).order_by('-score')
    
    html = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; }}
                h1 {{ color: #ff8c00; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .btn {{ padding: 10px 20px; background: #28a745; color: white; border: none; cursor: pointer; text-decoration: none; }}
                @media print {{
                   .no-print {{ display: none; }}
                }}
            </style>
        </head>
        <body>
            <button class="btn no-print" onclick="window.print()">Print / Save as PDF</button>
            <a href="/rooms/detail/{room.code}/" class="btn no-print" style="background:#666;">Back to Room</a>
            <h1>Quiz Report: Room #{room.code} - {room.topic}</h1>
            <p>Total Questions: {len(room.questions_data.get('questions', [])) if room.questions_data else 0}</p>
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Total Score</th>
                </tr>
    """
    
    for i, m in enumerate(members):
        html += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{m.user.username}</td>
                    <td>{m.score}</td>
                </tr>
        """
        
    html += """
            </table>
        </body>
    </html>
    """
    return HttpResponse(html)
