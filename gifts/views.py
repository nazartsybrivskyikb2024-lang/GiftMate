from django.shortcuts import render, get_object_or_404, redirect
from .models import Gift, Category, Profile, SavedItem, Story
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, ProfileForm, StoryForm
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Like, Comment



@login_required
def home(request):
    from django.core.paginator import Paginator
    from .friend_suggestions import get_suggested_friends
    from .models import Profile
    
    # Ensure user has a profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    # Get personalized friend suggestions
    suggested_friends = get_suggested_friends(request.user)
    
    categories = Category.objects.all()
    qs = Gift.objects.select_related('category').all().order_by('-created_at')
    cat = request.GET.get('category')
    selected_cat = None
    if cat:
        qs = qs.filter(category__id=cat)
        try:
            selected_cat = int(cat)
        except Exception:
            selected_cat = None
    paginator = Paginator(qs, 12)
    page = request.GET.get('page')
    gifts = paginator.get_page(page)
    return render(request, 'gifts/home.html', {
        'categories': categories,
        'gifts': gifts,
        'selected_cat': selected_cat,
        'suggested_friends': suggested_friends
    })


@login_required
def catalog(request):
    """Enhanced catalog page with advanced filtering and sorting options."""
    from django.core.paginator import Paginator
    from django.db.models import Count

    # Get categories with gift count
    categories = Category.objects.annotate(gift_count=Count('gifts'))
    
    # Base queryset
    qs = Gift.objects.select_related('category').all()

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | 
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        )

    # Category filter
    cat = request.GET.get('category')
    selected_cat = None
    if cat:
        try:
            selected_cat = int(cat)
            qs = qs.filter(category__id=selected_cat)
        except ValueError:
            pass

    # Price range filter
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min:
        try:
            qs = qs.filter(price__gte=float(price_min))
        except (ValueError, TypeError):
            pass
    if price_max:
        try:
            qs = qs.filter(price__lte=float(price_max))
        except (ValueError, TypeError):
            pass

    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        qs = qs.order_by('created_at')
    elif sort == 'popular':
        qs = qs.annotate(
            like_count=Count('likes'),
            save_count=Count('saveditem')
        ).order_by('-like_count', '-save_count')
    elif sort == 'price_low':
        qs = qs.order_by('price')
    elif sort == 'price_high':
        qs = qs.order_by('-price')
    else:  # newest
        qs = qs.order_by('-created_at')

    # Pagination
    paginator = Paginator(qs, 12)
    page = request.GET.get('page')
    gifts = paginator.get_page(page)

    # Get category for breadcrumb if selected
    selected_category = None
    if selected_cat:
        selected_category = Category.objects.filter(id=selected_cat).first()

    context = {
        'categories': categories,
        'gifts': gifts,
        'selected_cat': selected_cat,
        'selected_category': selected_category,
        'q': q,
        'sort': sort,
        'price_min': price_min,
        'price_max': price_max
    }

    return render(request, 'gifts/catalog.html', context)


@login_required
def profile(request):
    try:
        profile = request.user.profile
    except:
        profile = Profile.objects.create(user=request.user)
    
    saved = SavedItem.objects.filter(user=request.user).select_related('gift')
    return render(request, 'gifts/profile.html', {'profile': profile, 'saved': saved, 'hide_sidebar': True})


@login_required
def edit_profile(request):
    try:
        profile = request.user.profile
    except:
        profile = Profile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('gifts:profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'gifts/edit_profile.html', {'form': form})


@login_required
def toggle_like(request, gift_id):
    gift = get_object_or_404(Gift, id=gift_id)
    like, created = Like.objects.get_or_create(user=request.user, gift=gift)
    if not created:
        like.delete()
        status = 'unliked'
    else:
        status = 'liked'
    return JsonResponse({'status': status, 'likes_count': gift.likes.count()})


@login_required
def toggle_save(request, gift_id):
    gift = get_object_or_404(Gift, id=gift_id)
    saved, created = SavedItem.objects.get_or_create(user=request.user, gift=gift)
    if not created:
        saved.delete()
        status = 'unsaved'
    else:
        status = 'saved'
    return JsonResponse({'status': status})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # ensure profile exists (signals may already create it)
            try:
                Profile.objects.get_or_create(user=user)
            except Exception:
                pass
            login(request, user)
            return redirect('gifts:home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def gift_detail(request, gift_id):
    gift = get_object_or_404(Gift, id=gift_id)
    # prepare user's conversations list for client-side quick share (id + label)
    user_convs = []
    if request.user.is_authenticated:
        for c in request.user.conversations.all().order_by('-created_at'):
            others = c.participants.exclude(id=request.user.id)
            other = others.first() if others.exists() else None
            label = other.username if other else f'Розмова {c.id}'
            user_convs.append({'id': c.id, 'label': label})
    return render(request, 'gifts/gift_detail.html', {'gift': gift, 'user_conversations': user_convs})


@require_POST
@login_required
def add_comment(request, gift_id):
    gift = get_object_or_404(Gift, id=gift_id)
    text = request.POST.get('text')
    if text:
        Comment.objects.create(user=request.user, gift=gift, text=text)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


# ==================== AI CHAT SUPPORT ====================

@login_required
@require_POST
def ai_chat(request):
    """AI помічник (локальний Ollama) для розповсюджування інформації та підтримки"""
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Читаємо тіло запиту
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Невірний формат запиту'
            }, status=400)
        
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Повідомлення не може бути порожнім'
            }, status=400)
        
        # Обмеження на довжину повідомлення
        if len(user_message) > 1000:
            user_message = user_message[:1000]
        
        # Спробуємо підключитися до Ollama
        try:
            import ollama
        except ImportError:
            logger.error("Ollama package not installed")
            return JsonResponse({
                'success': False,
                'error': 'Ollama не встановлена. Встановіть: pip install ollama'
            }, status=503)
        
        # Формуємо контекстний промпт для питання про сайт
        context_prompt = f"""Ти - дружелюбний AI помічник сайту GiftMate (соціальна мережа для поділу списками подарунків).

GiftMate дозволяє користувачам:
- Створювати та ділитися списками бажаних подарунків
- Знаходити друзів та стежити їхні списки подарунків
- Спілкуватися через приватні чати
- Отримувати рекомендації подарунків від AI
- Переглядати каталог подарунків по категоріям
- Зберігати улюблені подарунки
- Отримувати сповіщення про дні народження друзів

Користувач запитує: {user_message}

Відповідай коротко (2-3 речення), дружелюбно, на українській мові.
Якщо питання про функціонал сайту - пояснай ясно.
Якщо питання про вибір подарунку - дай корисні поради.
Якщо питання не стосується сайту - ввічливо перенаправ на функціонал GiftMate."""
        
        # Отримуємо відповідь від Ollama локально
        try:
            response = ollama.generate(
                model='neural-chat:7b',
                prompt=context_prompt,
                stream=False,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 300,
                }
            )
            
            ai_response = response['response'].strip()
            
            if not ai_response:
                logger.warning("Empty AI response received")
                return JsonResponse({
                    'success': False,
                    'error': 'Не удалось отримати відповідь від AI'
                }, status=500)
            
            return JsonResponse({
                'success': True,
                'response': ai_response
            })
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ollama generation error: {error_msg}")
            
            # Якщо Ollama не запущена
            if "connection refused" in error_msg.lower() or "refused" in error_msg.lower():
                return JsonResponse({
                    'success': False,
                    'error': 'Ollama не запущена. Запустіть: ollama serve'
                }, status=503)
            
            return JsonResponse({
                'success': False,
                'error': f'Помилка генерації: {error_msg[:100]}'
            }, status=500)
    
    except Exception as e:
        logger.error(f"Unexpected error in ai_chat: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Непередбачена помилка: {str(e)}'
        }, status=500)


# ==================== STORIES ==================== #

@login_required
def stories_feed(request):
    """Сторіс стрічка - показує історії від друзів (24 години)"""
    user = request.user
    profile = user.profile
    
    # Отримуємо друзів користувача
    friends = profile.get_friends()
    friend_ids = [f.user_id for f in friends]
    friend_ids.append(user.id)  # Додаємо власні історії
    
    # Отримуємо активні історії від друзів (не старше 24 годин)
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Q
    
    cutoff_time = timezone.now() - timedelta(hours=24)
    stories = (Story.objects
        .filter(user_id__in=friend_ids, created_at__gte=cutoff_time)
        .select_related('user', 'user__profile')
        .order_by('user_id', '-created_at'))
    
    # Групуємо по користувачам
    stories_by_user = {}
    for story in stories:
        if story.user_id not in stories_by_user:
            stories_by_user[story.user_id] = {
                'user': story.user,
                'profile': story.user.profile,
                'stories': [],
                'count': 0
            }
        stories_by_user[story.user_id]['stories'].append(story)
        stories_by_user[story.user_id]['count'] += 1
    
    context = {
        'stories_by_user': stories_by_user,
        'friends_count': len(friend_ids) - 1,  # Без себе
    }
    
    return render(request, 'gifts/stories_feed.html', context)


@login_required
def story_detail(request, story_id):
    """Деталь однієї історії з нав навігацією по історіям"""
    user = request.user
    story = get_object_or_404(Story, id=story_id)
    
    # Перевіряємо чи історія не вийшла з актуальності
    if story.is_expired():
        messages.error(request, "Ця історія вже неактуальна")
        return redirect('gifts:stories_feed')
    
    # Отримуємо всі активні історії цього користувача
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_time = timezone.now() - timedelta(hours=24)
    user_stories = (Story.objects
        .filter(user=story.user, created_at__gte=cutoff_time)
        .order_by('created_at')
        .values_list('id', flat=True))
    
    user_stories_list = list(user_stories)
    current_index = user_stories_list.index(story.id) if story.id in user_stories_list else 0
    
    # Поточна та наступна історія
    next_story = None
    prev_story = None
    
    if current_index < len(user_stories_list) - 1:
        next_story = user_stories_list[current_index + 1]
    if current_index > 0:
        prev_story = user_stories_list[current_index - 1]
    
    context = {
        'story': story,
        'next_story': next_story,
        'prev_story': prev_story,
        'current_index': current_index + 1,
        'total_stories': len(user_stories_list),
    }
    
    return render(request, 'gifts/story_detail.html', context)


@login_required
def create_story(request):
    """Форма для створення нової історії"""
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            story.save()
            messages.success(request, "Ваша історія успішно опублікована! 🎉")
            return redirect('gifts:stories_feed')
    else:
        form = StoryForm()
    
    context = {
        'form': form,
        'title': 'Створити нову історію'
    }
    return render(request, 'gifts/create_story.html', context)


@login_required
@require_http_methods(["DELETE"])
def delete_story(request, story_id):
    """Видалення власної історії"""
    story = get_object_or_404(Story, id=story_id)
    
    # Тільки власник може видалити
    if story.user != request.user:
        return JsonResponse({'error': 'Не можете видалити чужу історію'}, status=403)
    
    story.delete()
    return JsonResponse({'success': True})


@login_required
def story_api_list(request):
    """API для отримання списку активних історій"""
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Q
    
    user = request.user
    profile = user.profile
    
    friends = profile.get_friends()
    friend_ids = [f.user_id for f in friends]
    friend_ids.append(user.id)
    
    cutoff_time = timezone.now() - timedelta(hours=24)
    stories = (Story.objects
        .filter(user_id__in=friend_ids, created_at__gte=cutoff_time)
        .select_related('user', 'user__profile', 'gift')
        .order_by('-created_at')
        .values(
            'id', 'user__id', 'user__username', 
            'title', 'description', 'created_at',
            'image', 'background_color'
        ))
    
    return JsonResponse({
        'stories': list(stories),
        'count': len(stories)
    })
