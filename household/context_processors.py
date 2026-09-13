from .models import UndoEntry, UserProfile


def undo_context(request):
    if not request.user.is_authenticated:
        return {}
    profile = UserProfile.objects.filter(user=request.user).select_related('household').first()
    household = profile.household if profile else None
    if not household:
        return {}
    entries = UndoEntry.objects.filter(household=household).order_by('-created_at')
    latest = entries.first()
    return {
        'undo_count': entries.count(),
        'undo_description': latest.description if latest else '',
    }
