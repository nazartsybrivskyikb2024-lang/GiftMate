from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from gifts.models import Gift
from django.utils import timezone
from django.utils.timezone import localtime
from gifts.models import SavedItem
from django.views.decorators.http import require_http_methods
from django.shortcuts import HttpResponse
from django.core.serializers import serialize
from django.forms.models import model_to_dict


@login_required
def inbox(request):
    convs = request.user.conversations.all().order_by('-created_at')
    # prepare list of conversations with the 'other' participant for templates
    convs_with_other = []
    for c in convs:
        others = c.participants.exclude(id=request.user.id)
        other = others.first() if others.exists() else None
        convs_with_other.append({'conv': c, 'other': other})
    return render(request, 'chat/inbox.html', {'conversations': convs_with_other})


@login_required
def conversation_view(request, conv_id):
    conv = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    msgs = conv.messages.all().order_by('created_at')
    # determine the other participant (if any) to show their avatar/name in template
    others = conv.participants.exclude(id=request.user.id)
    other = others.first() if others.exists() else None
    # prepare user's conversations list for client-side UI (id + label)
    user_convs = []
    for c in request.user.conversations.all().order_by('-created_at'):
        others_c = c.participants.exclude(id=request.user.id)
        other_c = others_c.first() if others_c.exists() else None
        label = other_c.username if other_c else f'Розмова {c.id}'
        user_convs.append({'id': c.id, 'label': label})

    # prepare saved gifts for the modal
    saved = []
    for si in request.user.saved_items.select_related('gift').all():
        g = si.gift
        saved.append({'id': g.id, 'title': g.title, 'image': g.image.url if g.image else None})

    return render(request, 'chat/conversation.html', {
        'conversation': conv,
        'chat_messages': msgs,
        'other': other,
        'user_conversations': user_convs,
        'saved_gifts': saved,
    })


@login_required
def send_message(request, conv_id):
    if request.method == 'POST':
        conv = get_object_or_404(Conversation, id=conv_id, participants=request.user)
        text = request.POST.get('text', '')
        photo = request.FILES.get('photo')
        fwd_id = request.POST.get('forwarded_gift_id')
        forwarded = None
        if fwd_id:
            try:
                forwarded = Gift.objects.get(id=int(fwd_id))
            except (Gift.DoesNotExist, ValueError):
                forwarded = None
        
        msg = Message(conversation=conv, sender=request.user, text=text, forwarded_gift=forwarded)
        if photo:
            msg.photo = photo
        msg.save()

        # prepare timestamp for client
        created_local = localtime(msg.created_at)
        created_display = created_local.strftime('%H:%M')
        data = {
            'status': 'ok',
            'id': msg.id,
            'text': msg.text,
            'sender': request.user.username,
            'created_at': msg.created_at.isoformat(),
            'created_at_display': created_display,
        }
        if msg.photo:
            data['photo_url'] = msg.photo.url
        if forwarded:
            data['forwarded'] = {'id': forwarded.id, 'title': forwarded.title, 'image': forwarded.image.url if forwarded.image else None}
        return JsonResponse(data)
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def new_conversation(request):
    User = get_user_model()
    q = request.GET.get('q')
    results = []
    if q:
        results = User.objects.filter(username__icontains=q).exclude(id=request.user.id)[:20]
    if request.method == 'POST':
        other_id = request.POST.get('user_id')
        try:
            other = User.objects.get(id=other_id)
        except User.DoesNotExist:
            other = None
        if other:
            # find existing conversation with these two participants
            convs = request.user.conversations.filter(participants=other).distinct()
            if convs.exists():
                conv = convs.first()
            else:
                conv = Conversation.objects.create()
                conv.participants.add(request.user, other)
            return redirect('chat:conversation', conv.id)
    return render(request, 'chat/new.html', {'results': results})


@login_required
@require_http_methods(['GET','POST'])
def forward_saved(request, conv_id):
    # page to list user's saved gifts and send selected to conv_id
    conv = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    if request.method == 'POST':
        gift_id = request.POST.get('gift_id')
        if gift_id:
            try:
                g = Gift.objects.get(id=int(gift_id))
            except (Gift.DoesNotExist, ValueError):
                g = None
            if g:
                Message.objects.create(conversation=conv, sender=request.user, text=f'Поділився подарунком', forwarded_gift=g)
        return redirect('chat:conversation', conv_id)

    # GET -> render list of saved gifts
    saved = []
    for si in request.user.saved_items.select_related('gift').all():
        g = si.gift
        saved.append({'id': g.id, 'title': g.title, 'image': g.image.url if g.image else None})
    return render(request, 'chat/forward_saved.html', {'conversation': conv, 'saved_gifts': saved})


@login_required
def get_messages(request, conv_id):
    """Return JSON list of messages for conversation conv_id newer than optional since_id.

    GET params:
      since_id - integer message id; only messages with id > since_id are returned.
    """
    conv = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    since = request.GET.get('since_id')
    qs = conv.messages.all().order_by('created_at')
    if since:
        try:
            since_id = int(since)
            qs = qs.filter(id__gt=since_id)
        except ValueError:
            pass

    data = []
    for m in qs:
        item = {
            'id': m.id,
            'text': m.text,
            'sender': m.sender.username,
            'created_at': m.created_at.isoformat(),
            'created_at_display': m.created_at.astimezone().strftime('%H:%M'),
        }
        if m.photo:
            item['photo_url'] = m.photo.url
        if m.forwarded_gift_id:
            item['forwarded'] = {
                'id': m.forwarded_gift_id,
                'title': getattr(m.forwarded_gift, 'title', None),
                'image': m.forwarded_gift.image.url if getattr(m.forwarded_gift, 'image', None) else None,
            }
        data.append(item)
    return JsonResponse({'messages': data})
@login_required
@require_http_methods(['POST'])
def mark_notifications_read(request):
    """Позначає всі сповіщення користувача як прочитані"""
    # Використовуємо related_name='notifications' з моделі User
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


# ==================== AI ПОМІЧНИК ====================

@login_required
@require_http_methods(['POST'])
def get_gift_recommendation(request):
    """API endpoint для отримання рекомендації подарунку від AI"""
    from gifts.ai_assistant import get_ai_assistant
    import json
    
    try:
        data = json.loads(request.body)
        occasion = data.get('occasion', '')
        budget = data.get('budget', '')
        
        assistant = get_ai_assistant()
        if not assistant:
            return JsonResponse({
                'error': 'AI сервіс недоступний',
                'recommendation': 'Будь ласка, налаштуйте GEMINI_API_KEY у settings.py'
            }, status=503)
        
        # Отримуємо профіль користувача для кращих рекомендацій
        user_profile = request.user.profile if hasattr(request.user, 'profile') else None
        
        recommendation = assistant.get_gift_recommendation(
            user_profile=user_profile,
            occasion=occasion,
            budget=budget
        )
        
        return JsonResponse({
            'success': True,
            'recommendation': recommendation
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=400)


@login_required
@require_http_methods(['POST'])
def get_gift_ideas(request):
    """API endpoint для отримання ідей подарунків"""
    from gifts.ai_assistant import get_ai_assistant
    import json
    
    try:
        data = json.loads(request.body)
        interests = data.get('interests', [])
        count = data.get('count', 3)
        
        assistant = get_ai_assistant()
        if not assistant:
            return JsonResponse({
                'error': 'AI сервіс недоступний'
            }, status=503)
        
        ideas = assistant.get_gift_ideas(interests=interests, count=count)
        
        return JsonResponse({
            'success': True,
            'ideas': ideas
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=400)


@login_required
@require_http_methods(['POST'])
def suggest_for_occasion(request):
    """API endpoint для рекомендацій до конкретної нагоди"""
    from gifts.ai_assistant import get_ai_assistant
    import json
    
    try:
        data = json.loads(request.body)
        occasion = data.get('occasion', '')
        budget_min = data.get('budget_min')
        budget_max = data.get('budget_max')
        
        assistant = get_ai_assistant()
        if not assistant:
            return JsonResponse({
                'error': 'AI сервіс недоступний'
            }, status=503)
        
        suggestion = assistant.suggest_for_occasion(
            occasion=occasion,
            budget_min=budget_min,
            budget_max=budget_max
        )
        
        return JsonResponse({
            'success': True,
            'suggestion': suggestion
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=400)