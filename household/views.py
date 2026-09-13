import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ShoppingForm, SignupForm
from .models import Category, DateIdea, DinnerIdea, Household, ImportantInfo, ShoppingItem, SubTask, Task, UndoEntry, UserProfile

User = get_user_model()

PRIORITY_ORDER = Case(
    When(priority='high', then=Value(0)),
    When(priority='medium', then=Value(1)),
    When(priority='low', then=Value(2)),
    output_field=IntegerField(),
)

UNDO_LIMIT = 6


def get_household_for_user(user):
    profile = UserProfile.objects.filter(user=user).first()
    if profile:
        return profile.household
    household = Household.objects.first()
    return household


def log_undo(household, model_name, action, description, object_id=None, snapshot=None):
    """Record a reversible action, keeping only the most recent UNDO_LIMIT entries per household."""
    if not household:
        return
    UndoEntry.objects.create(
        household=household,
        model_name=model_name,
        action=action,
        object_id=object_id,
        snapshot=snapshot,
        description=description,
    )
    stale_ids = list(
        UndoEntry.objects.filter(household=household).order_by('-created_at').values_list('id', flat=True)[UNDO_LIMIT:]
    )
    if stale_ids:
        UndoEntry.objects.filter(id__in=stale_ids).delete()


def tasks_url(open_subtasks=None):
    url = reverse('tasks')
    if open_subtasks:
        url = f'{url}?open_subtasks={open_subtasks}'
    return url


def resolve_owner_choice(owner_choice, household):
    """Turn an 'owner' form value ('', 'either', or 'user-<id>') into (owner, owner_type)."""
    if owner_choice == 'either':
        return None, 'either'
    if owner_choice.startswith('user-'):
        owner = User.objects.filter(id=owner_choice.split('-', 1)[1], household_profile__household=household).first()
        return (owner, 'assigned') if owner else (None, 'unassigned')
    return None, 'unassigned'


def resolve_category_choice(category_name, household):
    """Category is optional; blank means no category, otherwise get-or-create it."""
    category_name = category_name.strip()
    if not category_name:
        return None
    category, _ = Category.objects.get_or_create(household=household, name=category_name)
    return category


@login_required
def home_redirect(request):
    return redirect('today')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('today')

    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        first_name = form.cleaned_data['first_name'].strip()
        household, _ = Household.objects.get_or_create(name='Jazz Club')
        used_colors = set(household.profiles.values_list('color', flat=True))
        color = next((value for value, _ in UserProfile.COLOR_CHOICES if value not in used_colors), UserProfile.COLOR_CHOICES[0][0])

        user = User.objects.create_user(username=email, email=email, first_name=first_name, password=form.cleaned_data['password'])
        UserProfile.objects.create(user=user, household=household, name=first_name, color=color)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f'Welcome, {first_name}!')
        return redirect('today')

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def today_view(request):
    household = get_household_for_user(request.user)
    if not household:
        return render(request, 'household/empty_state.html', {'title': 'No household yet'})

    active_view = request.GET.get('view', 'todo')
    today = date.today()

    today_tasks = (
        Task.objects.filter(household=household, completed=False, due_date__lte=today)
        .select_related('owner', 'owner__household_profile', 'category')
        .prefetch_related('subtasks')
        .annotate(priority_rank=PRIORITY_ORDER)
        .order_by('priority_rank', '-created_at')
    )
    today_task_ids = list(today_tasks.values_list('id', flat=True))
    other_tasks = (
        Task.objects.filter(household=household, completed=False)
        .exclude(id__in=today_task_ids)
        .select_related('owner', 'owner__household_profile', 'category')
        .prefetch_related('subtasks')
        .annotate(priority_rank=PRIORITY_ORDER)
        .order_by('priority_rank', '-created_at')
    )
    completed_today_tasks = (
        Task.objects.filter(household=household, completed=True, completed_at__date=today)
        .select_related('owner', 'owner__household_profile', 'category')
        .order_by('-completed_at')
    )

    shopping_items = ShoppingItem.objects.filter(household=household, checked=False).order_by('section', 'name')
    recently_checked = ShoppingItem.objects.filter(
        household=household, checked=True, checked_at__gte=timezone.now() - timedelta(days=60),
    ).order_by('-checked_at', 'name')

    date_idea = DateIdea.objects.filter(household=household).order_by('-created_at').first()
    dinner_idea = DinnerIdea.objects.filter(household=household).order_by('-created_at').first()

    return render(request, 'household/today.html', {
        'household': household,
        'active_view': active_view,
        'today': today,
        'today_tasks': today_tasks,
        'other_tasks': other_tasks,
        'completed_today_tasks': completed_today_tasks,
        'shopping_items': shopping_items,
        'recently_checked': recently_checked,
        'date_idea': date_idea,
        'dinner_idea': dinner_idea,
        'today_label': today.strftime('%A %d %B'),
        'profiles': household.profiles.select_related('user'),
    })


@login_required
def admin_view(request):
    household = get_household_for_user(request.user)
    tasks = Task.objects.filter(household=household).select_related('owner', 'owner__household_profile', 'category').prefetch_related('subtasks')

    owner_filter = request.GET.get('owner', 'all')
    category_filter = request.GET.get('category')
    priority_filter = request.GET.get('priority')
    effort_filter = request.GET.get('effort')

    if owner_filter == 'me':
        tasks = tasks.filter(owner=request.user)
    elif owner_filter == 'partner':
        partner = household.profiles.exclude(user=request.user).first()
        if partner:
            tasks = tasks.filter(owner=partner.user)
        else:
            tasks = tasks.none()
    elif owner_filter == 'unassigned':
        tasks = tasks.filter(Q(owner__isnull=True) | Q(owner_type='unassigned') | Q(owner_type='either'))

    if category_filter:
        tasks = tasks.filter(category_id=category_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if effort_filter:
        tasks = tasks.filter(effort=effort_filter)

    tasks = tasks.annotate(priority_rank=PRIORITY_ORDER)
    active_tasks = tasks.filter(completed=False).order_by('priority_rank', '-created_at')
    completed_tasks = tasks.filter(completed=True).order_by('-completed_at')

    categories = Category.objects.filter(household=household)
    profiles = household.profiles.select_related('user') if household else UserProfile.objects.none()

    raw_open_subtasks = request.GET.get('open_subtasks')
    open_subtasks_id = int(raw_open_subtasks) if raw_open_subtasks and raw_open_subtasks.isdigit() else None

    return render(request, 'household/admin.html', {
        'tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'owner_filter': owner_filter,
        'categories': categories,
        'profiles': profiles,
        'open_subtasks_id': open_subtasks_id,
    })


@login_required
def shopping_view(request):
    household = get_household_for_user(request.user)
    groceries = ShoppingItem.objects.filter(household=household, list_type='groceries', checked=False).order_by('section', 'name')
    other = ShoppingItem.objects.filter(household=household, list_type='other', checked=False).order_by('name')
    recently_checked = ShoppingItem.objects.filter(
        household=household, checked=True, checked_at__gte=timezone.now() - timedelta(days=60),
    ).order_by('-checked_at', 'name')
    form = ShoppingForm()
    return render(request, 'household/shopping.html', {
        'groceries': groceries,
        'other_items': other,
        'recently_checked': recently_checked,
        'form': form,
        'household': household,
    })


@login_required
def settings_view(request):
    household = get_household_for_user(request.user)
    profiles = household.profiles.select_related('user').all()
    return render(request, 'household/settings.html', {
        'profiles': profiles,
        'color_choices': UserProfile.COLOR_CHOICES,
    })


@login_required
def important_info_view(request):
    household = get_household_for_user(request.user)
    items = ImportantInfo.objects.filter(household=household).order_by('order', 'created_at')
    return render(request, 'household/important_info.html', {'items': items})


@login_required
@require_POST
def important_info_create(request):
    household = get_household_for_user(request.user)
    text = request.POST.get('text', '').strip()
    if text:
        next_order = ImportantInfo.objects.filter(household=household).count()
        ImportantInfo.objects.create(household=household, text=text, order=next_order)
    return redirect('important_info')


@login_required
@require_POST
def important_info_delete(request, info_id):
    household = get_household_for_user(request.user)
    ImportantInfo.objects.filter(pk=info_id, household=household).delete()
    return redirect('important_info')


@login_required
@require_POST
def important_info_move(request, info_id):
    household = get_household_for_user(request.user)
    items = list(ImportantInfo.objects.filter(household=household).order_by('order', 'created_at'))
    ids = [item.id for item in items]
    if info_id not in ids:
        return redirect('important_info')

    index = ids.index(info_id)
    direction = request.POST.get('direction')
    swap_index = index - 1 if direction == 'up' else index + 1 if direction == 'down' else None

    if swap_index is not None and 0 <= swap_index < len(items):
        current, other = items[index], items[swap_index]
        current.order, other.order = other.order, current.order
        current.save(update_fields=['order'])
        other.save(update_fields=['order'])

    return redirect('important_info')


@login_required
@require_POST
def update_color(request):
    household = get_household_for_user(request.user)
    profile = UserProfile.objects.filter(user=request.user, household=household).first()
    color = request.POST.get('color')
    if profile and color in dict(UserProfile.COLOR_CHOICES):
        previous = {'color': profile.color}
        profile.color = color
        profile.save(update_fields=['color'])
        log_undo(household, 'UserProfile', 'update', f"Changed {profile.name}'s colour", object_id=profile.id, snapshot=previous)
        messages.success(request, 'Colour updated.')
    return redirect('settings')


@login_required
@require_POST
def task_create(request):
    household = get_household_for_user(request.user)
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, 'Please add a task title.')
        return redirect('tasks')

    owner, owner_type = resolve_owner_choice(request.POST.get('owner', ''), household)
    category = resolve_category_choice(request.POST.get('category_name', ''), household)

    task = Task.objects.create(
        household=household,
        title=title,
        description=request.POST.get('description', ''),
        notes=request.POST.get('notes', '').strip(),
        owner=owner,
        owner_type=owner_type,
        priority=request.POST.get('priority', 'medium'),
        effort=request.POST.get('effort', 'medium'),
        due_date=request.POST.get('due_date') or None,
        category=category,
    )
    log_undo(household, 'Task', 'create', f"Added task '{task.title}'", object_id=task.id)
    messages.success(request, 'Task added.')
    return redirect('tasks')


@login_required
@require_POST
def task_update(request, task_id):
    household = get_household_for_user(request.user)
    task = Task.objects.get(pk=task_id, household=household)

    previous = {
        'title': task.title,
        'priority': task.priority,
        'effort': task.effort,
        'category_id': task.category_id,
        'notes': task.notes,
        'owner_id': task.owner_id,
        'owner_type': task.owner_type,
    }

    title = request.POST.get('title', '').strip()
    if title:
        task.title = title
    if request.POST.get('priority') in dict(Task.PRIORITY_CHOICES):
        task.priority = request.POST.get('priority')
    if request.POST.get('effort') in dict(Task.EFFORT_CHOICES):
        task.effort = request.POST.get('effort')

    task.category = resolve_category_choice(request.POST.get('category_name', ''), household)
    task.notes = request.POST.get('notes', '').strip()
    task.owner, task.owner_type = resolve_owner_choice(request.POST.get('owner', ''), household)
    task.save()
    log_undo(household, 'Task', 'update', f"Edited task '{task.title}'", object_id=task.id, snapshot=previous)
    messages.success(request, 'Task updated.')
    return redirect('tasks')


@login_required
@require_POST
def task_toggle(request, task_id):
    household = get_household_for_user(request.user)
    task = Task.objects.get(pk=task_id, household=household)
    previous = {'completed': task.completed}
    task.completed = not task.completed
    task.save()
    verb = 'Completed' if task.completed else 'Reopened'
    log_undo(household, 'Task', 'update', f"{verb} task '{task.title}'", object_id=task.id, snapshot=previous)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'completed': task.completed})
    return redirect('tasks')


@login_required
@require_POST
def task_claim(request, task_id):
    household = get_household_for_user(request.user)
    task = Task.objects.get(pk=task_id, household=household)
    previous = {
        'owner_id': task.owner_id,
        'owner_type': task.owner_type,
        'completed': task.completed,
        'due_date': task.due_date,
    }
    task.owner = request.user
    task.owner_type = 'assigned'
    task.completed = False
    claim_for_today = request.POST.get('for_today') == '1'
    if claim_for_today:
        task.due_date = date.today()
    task.save(update_fields=['owner', 'owner_type', 'completed', 'due_date', 'updated_at'])
    description = f"Claimed '{task.title}' for today" if claim_for_today else f"Claimed '{task.title}'"
    log_undo(household, 'Task', 'update', description, object_id=task.id, snapshot=previous)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'owner': request.user.username})
    return redirect(request.POST.get('next') or 'today')


@login_required
@require_POST
def task_set_owner(request, task_id):
    household = get_household_for_user(request.user)
    task = Task.objects.get(pk=task_id, household=household)
    previous = {'owner_id': task.owner_id, 'owner_type': task.owner_type}
    task.owner, task.owner_type = resolve_owner_choice(request.POST.get('owner', ''), household)
    task.save(update_fields=['owner', 'owner_type', 'updated_at'])
    log_undo(household, 'Task', 'update', f"Reassigned '{task.title}'", object_id=task.id, snapshot=previous)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'owner': task.owner_value})
    return redirect(request.POST.get('next') or 'today')


@login_required
@require_POST
def subtask_create(request, task_id):
    household = get_household_for_user(request.user)
    task = Task.objects.get(pk=task_id, household=household)
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, 'Please add a sub-task title.')
        return redirect(tasks_url(task.id))

    owner, owner_type = resolve_owner_choice(request.POST.get('owner', ''), household)
    effort = request.POST.get('effort', 'medium')

    subtask = SubTask.objects.create(
        task=task,
        title=title,
        owner=owner,
        owner_type=owner_type,
        effort=effort if effort in dict(Task.EFFORT_CHOICES) else 'medium',
        order=task.subtasks.count(),
    )
    log_undo(household, 'SubTask', 'create', f"Added sub-task '{subtask.title}'", object_id=subtask.id)
    messages.success(request, 'Sub-task added.')
    return redirect(tasks_url(task.id))


@login_required
@require_POST
def subtask_toggle(request, subtask_id):
    household = get_household_for_user(request.user)
    subtask = SubTask.objects.get(pk=subtask_id, task__household=household)
    previous = {'completed': subtask.completed}
    subtask.completed = not subtask.completed
    subtask.save()
    log_undo(household, 'SubTask', 'update', f"Toggled sub-task '{subtask.title}'", object_id=subtask.id, snapshot=previous)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'completed': subtask.completed})
    return redirect(tasks_url(subtask.task_id))


@login_required
@require_POST
def subtask_delete(request, subtask_id):
    household = get_household_for_user(request.user)
    subtask = SubTask.objects.get(pk=subtask_id, task__household=household)
    task_id = subtask.task_id
    snapshot = {
        'task_id': subtask.task_id,
        'title': subtask.title,
        'owner_id': subtask.owner_id,
        'owner_type': subtask.owner_type,
        'priority': subtask.priority,
        'effort': subtask.effort,
        'completed': subtask.completed,
        'order': subtask.order,
    }
    description = f"Deleted sub-task '{subtask.title}'"
    subtask.delete()
    log_undo(household, 'SubTask', 'delete', description, snapshot=snapshot)
    return redirect(tasks_url(task_id))


@login_required
@require_POST
def shopping_add(request):
    household = get_household_for_user(request.user)
    name = request.POST.get('name', '').strip()
    if not name:
        return redirect(request.POST.get('next') or 'shopping')
    item = ShoppingItem.objects.create(
        household=household,
        name=name,
        list_type=request.POST.get('list_type', 'groceries'),
        section=request.POST.get('section', ''),
        note=request.POST.get('note', ''),
        added_by=request.user,
    )
    log_undo(household, 'ShoppingItem', 'create', f"Added shopping item '{item.name}'", object_id=item.id)
    return redirect(request.POST.get('next') or 'shopping')


@login_required
@require_POST
def shopping_toggle(request, item_id):
    household = get_household_for_user(request.user)
    item = ShoppingItem.objects.get(pk=item_id, household=household)
    previous = {'checked': item.checked, 'checked_at': item.checked_at}
    item.mark_checked(not item.checked)
    log_undo(household, 'ShoppingItem', 'update', f"Toggled '{item.name}'", object_id=item.id, snapshot=previous)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'checked': item.checked})
    return redirect(request.POST.get('next') or 'shopping')


@login_required
@require_POST
def shopping_delete(request, item_id):
    household = get_household_for_user(request.user)
    item = ShoppingItem.objects.get(pk=item_id, household=household)
    snapshot = {
        'name': item.name,
        'list_type': item.list_type,
        'section': item.section,
        'note': item.note,
        'checked': item.checked,
        'added_by_id': item.added_by_id,
    }
    description = f"Deleted shopping item '{item.name}'"
    item.delete()
    log_undo(household, 'ShoppingItem', 'delete', description, snapshot=snapshot)
    return redirect('shopping')


@login_required
@require_POST
def undo_action(request):
    household = get_household_for_user(request.user)
    entry = UndoEntry.objects.filter(household=household).order_by('-created_at').first()
    next_url = request.POST.get('next') or reverse('tasks')

    if not entry:
        messages.info(request, 'Nothing to undo.')
        return redirect(next_url)

    if entry.model_name == 'Task':
        if entry.action == 'create':
            Task.objects.filter(pk=entry.object_id, household=household).delete()
        else:
            task = Task.objects.filter(pk=entry.object_id, household=household).first()
            if task:
                for key, value in entry.snapshot.items():
                    setattr(task, key, value)
                task.save()
    elif entry.model_name == 'SubTask':
        if entry.action == 'create':
            subtask = SubTask.objects.filter(pk=entry.object_id, task__household=household).first()
            if subtask:
                subtask.delete()
        elif entry.action == 'update':
            subtask = SubTask.objects.filter(pk=entry.object_id, task__household=household).first()
            if subtask:
                for key, value in entry.snapshot.items():
                    setattr(subtask, key, value)
                subtask.save()
        elif entry.action == 'delete':
            SubTask.objects.create(**entry.snapshot)
    elif entry.model_name == 'ShoppingItem':
        if entry.action == 'create':
            ShoppingItem.objects.filter(pk=entry.object_id, household=household).delete()
        elif entry.action == 'update':
            item = ShoppingItem.objects.filter(pk=entry.object_id, household=household).first()
            if item:
                for key, value in entry.snapshot.items():
                    setattr(item, key, value)
                item.save()
        elif entry.action == 'delete':
            ShoppingItem.objects.create(household=household, **entry.snapshot)
    elif entry.model_name == 'UserProfile':
        profile = UserProfile.objects.filter(pk=entry.object_id, household=household).first()
        if profile:
            for key, value in entry.snapshot.items():
                setattr(profile, key, value)
            profile.save()

    messages.success(request, f'Undone: {entry.description}')
    entry.delete()
    return redirect(next_url)
