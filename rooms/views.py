from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Room, RoomMember
from dashboard.utils import generate_room_questions
import json

@login_required
def create_room_view(request):
    if request.method == "POST":
        topic = request.POST.get('topic')
        patterns = {
            'mcq': 'mcq' in request.POST,
            'match': 'match' in request.POST,
            'typing': 'typing' in request.POST,
            'arrange': 'arrange' in request.POST,
        }
        
        # Ensure at least one pattern is selected
        if not any(patterns.values()):
            patterns['mcq'] = True
            
        room = Room.objects.create(
            creator=request.user,
            topic=topic,
            pattern_mcq=patterns['mcq'],
            pattern_match=patterns['match'],
            pattern_typing=patterns['typing'],
            pattern_arrange=patterns['arrange']
        )
        # Creator also joins the room
        RoomMember.objects.create(room=room, user=request.user)
        return redirect('room_detail', room_code=room.code)
        
    return render(request, 'rooms/create.html')

@login_required
def room_detail(request, room_code):
    room = get_object_or_404(Room, code=room_code)
    is_creator = (room.creator == request.user)
    
    # Check if user is a member
    is_member = RoomMember.objects.filter(room=room, user=request.user).exists()
    if not is_member and not is_creator:
        return redirect('join_room')
        
    # Generate full invite link
    invite_link = request.build_absolute_uri(f"/rooms/join/?code={room.code}")
    
    context = {
        'room': room,
        'is_creator': is_creator,
        'invite_link': invite_link,
        'members_count': room.members.count(),
    }
    return render(request, 'rooms/detail.html', context)

@login_required
def join_room_view(request):
    code_from_url = request.GET.get('code', '')
    
    if request.method == "POST":
        code = request.POST.get('code')
        try:
            room = Room.objects.get(code=code, is_active=True)
            RoomMember.objects.get_or_create(room=room, user=request.user)
            return redirect('room_detail', room_code=room.code)
        except Room.DoesNotExist:
            return render(request, 'rooms/join.html', {'error': 'Invalid Room Code', 'code': code})
            
    return render(request, 'rooms/join.html', {'code': code_from_url})

@login_required
def generate_room_quiz_api(request, room_code):
    room = get_object_or_404(Room, code=room_code)
    if room.creator != request.user:
        return JsonResponse({'error': 'Only creator can generate questions'}, status=403)
        
    patterns = {
        'mcq': room.pattern_mcq,
        'match': room.pattern_match,
        'typing': room.pattern_typing,
        'arrange': room.pattern_arrange,
    }
    
    result = generate_room_questions(room.topic, patterns)
    if result and 'questions' in result:
        room.questions_data = result
        room.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'error': 'AI Generation failed'}, status=500)

@login_required
def get_room_questions_api(request, room_code):
    room = get_object_or_404(Room, code=room_code)
    if not RoomMember.objects.filter(room=room, user=request.user).exists():
        return JsonResponse({'error': 'Not a member'}, status=403)
        
    if not room.questions_data:
        return JsonResponse({'status': 'waiting'})
        
    return JsonResponse({'status': 'ready', 'data': room.questions_data})
