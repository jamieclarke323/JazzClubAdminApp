from __future__ import annotations

from datetime import date

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone


class Household(models.Model):
    name = models.CharField(max_length=120, default='Shared home')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    COLOR_CHOICES = [
        ('wisteria', 'Wisteria'),
        ('sage', 'Sage'),
        ('sky', 'Sky'),
        ('peach', 'Peach'),
        ('butter', 'Butter'),
        ('coral', 'Coral'),
        ('slate', 'Slate'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='household_profile')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='profiles')
    name = models.CharField(max_length=80)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='wisteria')
    avatar = models.CharField(max_length=2, default='A', blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=80)
    icon = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['name']
        unique_together = ('household', 'name')

    def __str__(self):
        return self.name


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    EFFORT_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    OWNER_TYPE_CHOICES = [
        ('unassigned', 'Unassigned'),
        ('either', 'Either'),
        ('assigned', 'Assigned'),
    ]
    RECURRENCE_CHOICES = [
        ('none', 'No recurrence'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('fortnightly', 'Fortnightly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_tasks')
    owner_type = models.CharField(max_length=20, choices=OWNER_TYPE_CHOICES, default='unassigned')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    effort = models.CharField(max_length=20, choices=EFFORT_CHOICES, default='medium')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    due_date = models.DateField(null=True, blank=True)
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='none')
    notes = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['priority', '-created_at']
        indexes = [models.Index(fields=['household', 'due_date']), models.Index(fields=['owner', 'due_date'])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.completed and self.completed_at is None:
            self.completed_at = timezone.now()
        elif not self.completed:
            self.completed_at = None
        super().save(*args, **kwargs)

    @property
    def progress(self):
        subtasks = self.subtasks.all()
        if not subtasks:
            return {'done': 0, 'total': 0, 'percent': 0}
        done = subtasks.filter(completed=True).count()
        total = subtasks.count()
        return {'done': done, 'total': total, 'percent': int((done / total) * 100) if total else 0}

    def update_completion_from_subtasks(self):
        if self.subtasks.exists():
            total = self.subtasks.count()
            done = self.subtasks.filter(completed=True).count()
            self.completed = total > 0 and done == total
            self.save(update_fields=['completed', 'completed_at'])

    def claim_for_user(self, user):
        self.owner = user
        self.owner_type = 'assigned'
        self.completed = False
        self.save(update_fields=['owner', 'owner_type', 'completed', 'updated_at'])

    def due_today(self):
        return self.due_date == date.today()

    @property
    def owner_profile(self):
        return getattr(self.owner, 'household_profile', None) if self.owner_id else None

    @property
    def owner_label(self):
        if self.owner_type == 'either':
            return 'Both'
        profile = self.owner_profile
        return profile.name if profile else 'Unassigned'

    @property
    def owner_color(self):
        profile = self.owner_profile
        return profile.color if profile else 'neutral'

    @property
    def owner_value(self):
        if self.owner_type == 'either':
            return 'either'
        if self.owner_id:
            return f'user-{self.owner_id}'
        return ''

    @property
    def effort_theme(self):
        return {'high': 'effort-high', 'medium': 'effort-medium', 'low': 'effort-low'}.get(self.effort, 'effort-medium')


class SubTask(models.Model):
    task = models.ForeignKey(Task, related_name='subtasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=220)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_subtasks')
    owner_type = models.CharField(max_length=20, choices=Task.OWNER_TYPE_CHOICES, default='unassigned')
    priority = models.CharField(max_length=20, choices=Task.PRIORITY_CHOICES, default='medium')
    effort = models.CharField(max_length=20, choices=Task.EFFORT_CHOICES, default='medium')
    completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.task.update_completion_from_subtasks()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.task.update_completion_from_subtasks()

    @property
    def owner_profile(self):
        return getattr(self.owner, 'household_profile', None) if self.owner_id else None

    @property
    def owner_label(self):
        if self.owner_type == 'either':
            return 'Both'
        profile = self.owner_profile
        return profile.name if profile else 'Unassigned'

    @property
    def owner_color(self):
        profile = self.owner_profile
        return profile.color if profile else 'neutral'

    @property
    def owner_value(self):
        if self.owner_type == 'either':
            return 'either'
        if self.owner_id:
            return f'user-{self.owner_id}'
        return ''

    @property
    def effort_theme(self):
        return {'high': 'effort-high', 'medium': 'effort-medium', 'low': 'effort-low'}.get(self.effort, 'effort-medium')


class ShoppingItem(models.Model):
    LIST_TYPE_CHOICES = [
        ('groceries', 'Groceries'),
        ('other', 'Other shopping'),
    ]

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='shopping_items')
    name = models.CharField(max_length=200)
    list_type = models.CharField(max_length=20, choices=LIST_TYPE_CHOICES, default='groceries')
    section = models.CharField(max_length=80, blank=True)
    note = models.CharField(max_length=260, blank=True)
    checked = models.BooleanField(default=False)
    checked_at = models.DateTimeField(null=True, blank=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-checked', 'section', 'name']
        indexes = [models.Index(fields=['household', 'list_type', 'checked'])]

    def __str__(self):
        return self.name

    def mark_checked(self, checked):
        self.checked = checked
        self.checked_at = timezone.now() if checked else None
        self.save(update_fields=['checked', 'checked_at'])


class DateIdea(models.Model):
    STATUS_CHOICES = [
        ('idea', 'Idea'),
        ('planned', 'Planned'),
        ('done', 'Done'),
    ]
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='date_ideas')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    suggested_by = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=200, blank=True)
    approx_cost = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idea')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class DinnerIdea(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='dinner_ideas')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class MealPlan(models.Model):
    DAYS = [
        ('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'), ('thursday', 'Thursday'),
        ('friday', 'Friday'), ('saturday', 'Saturday'), ('sunday', 'Sunday'),
    ]
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='meal_plan')
    day = models.CharField(max_length=20, choices=DAYS)
    dinner = models.ForeignKey(DinnerIdea, null=True, blank=True, on_delete=models.SET_NULL, related_name='meal_entries')

    class Meta:
        unique_together = ('household', 'day')

    def __str__(self):
        return f'{self.day}: {self.dinner}'


class HolidayIdea(models.Model):
    STATUS_CHOICES = [
        ('idea', 'Idea'),
        ('planning', 'Planning'),
        ('booked', 'Booked'),
    ]
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='holiday_ideas')
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    places = models.TextField(blank=True)
    activities = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    suggested_by = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idea')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class WatchItem(models.Model):
    KIND_CHOICES = [('film', 'Film'), ('tv', 'TV')]
    STATUS_CHOICES = [('want', 'Want to watch'), ('watching', 'Watching'), ('watched', 'Watched')]
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='watch_items')
    title = models.CharField(max_length=220)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='film')
    genre = models.CharField(max_length=80, blank=True)
    recommended_by = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='want')
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class NotificationPreference(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='notification_preferences')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    task_due = models.BooleanField(default=True)
    shopping_updates = models.BooleanField(default=True)
    partner_claimed_task = models.BooleanField(default=True)

    class Meta:
        unique_together = ('household', 'user')


class CalendarIntegration(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='calendar_integrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_integrations')
    google_calendar_id = models.CharField(max_length=200, blank=True)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('household', 'user')


class UndoEntry(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='undo_entries')
    model_name = models.CharField(max_length=40)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    snapshot = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.description


class ImportantInfo(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='important_info')
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.text[:50]


class Idea(models.Model):
    CATEGORY_CHOICES = [
        ('holiday', 'Holiday'),
        ('recipe', 'Recipe'),
        ('place', 'Place'),
        ('other', 'Other'),
    ]
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='ideas')
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
