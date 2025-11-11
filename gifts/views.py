from django.shortcuts import render, get_object_or_404, redirect
from .models import Gift, Category, Profile, SavedItem
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, ProfileForm
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
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
