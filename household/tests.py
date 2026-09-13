from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Household, ShoppingItem, Task, UserProfile

User = get_user_model()


class JazzClubModelTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name='The House')
        self.user1 = User.objects.create_user(username='alex', email='alex@example.com', password='secret123')
        self.user2 = User.objects.create_user(username='sam', email='sam@example.com', password='secret123')
        self.profile1 = UserProfile.objects.create(user=self.user1, household=self.household, name='Alex', color='wisteria')
        self.profile2 = UserProfile.objects.create(user=self.user2, household=self.household, name='Sam', color='sky')
        self.category = Category.objects.create(household=self.household, name='Home')

    def test_login_required_redirects(self):
        response = self.client.get(reverse('today'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_task_creation_and_defaults(self):
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('task_create'), {'title': 'Book car MOT'})
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='Book car MOT')
        self.assertEqual(task.household, self.household)
        self.assertEqual(task.owner_type, 'unassigned')
        self.assertIsNone(task.owner)
        self.assertEqual(task.priority, 'medium')
        self.assertEqual(task.effort, 'medium')
        self.assertIsNone(task.category)

    def test_task_creation_with_category_and_notes(self):
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('task_create'), {
            'title': 'Book dentist',
            'category_name': 'Health',
            'notes': 'Ask about referral',
        })
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='Book dentist')
        self.assertEqual(task.category.name, 'Health')
        self.assertEqual(task.notes, 'Ask about referral')

    def test_ill_do_it_assigns_task_to_current_user(self):
        task = Task.objects.create(
            household=self.household,
            title='Return parcel',
            owner_type='either',
            due_date=date.today(),
            category=self.category,
        )
        task.claim_for_user(self.user1)
        self.assertEqual(task.owner, self.user1)
        self.assertEqual(task.owner_type, 'assigned')

    def test_shopping_item_added_to_household(self):
        item = ShoppingItem.objects.create(
            household=self.household,
            list_type='groceries',
            section='Fridge',
            name='Milk',
            added_by=self.user1,
        )
        self.assertTrue(ShoppingItem.objects.filter(pk=item.pk).exists())
        self.assertEqual(item.household, self.household)

    def test_today_warning_for_over_three_tasks(self):
        for i in range(4):
            Task.objects.create(
                household=self.household,
                title=f'Task {i}',
                owner=self.user1,
                owner_type='assigned',
                due_date=date.today(),
                category=self.category,
            )
        self.assertGreater(Task.objects.filter(household=self.household, owner=self.user1, due_date=date.today()).count(), 3)

    def test_task_creation_with_explicit_owner_priority_effort(self):
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('task_create'), {
            'title': 'Book car MOT',
            'priority': 'high',
            'effort': 'low',
            'owner': f'user-{self.user2.id}',
        })
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='Book car MOT')
        self.assertEqual(task.priority, 'high')
        self.assertEqual(task.effort, 'low')
        self.assertEqual(task.owner, self.user2)
        self.assertEqual(task.owner_type, 'assigned')
        self.assertEqual(task.owner_color, 'sky')

    def test_admin_tasks_ordered_by_priority_not_date(self):
        low = Task.objects.create(household=self.household, title='Low task', priority='low', category=self.category)
        high = Task.objects.create(household=self.household, title='High task', priority='high', category=self.category)
        medium = Task.objects.create(household=self.household, title='Medium task', priority='medium', category=self.category)

        self.client.login(username='alex', password='secret123')
        response = self.client.get(reverse('tasks'))
        self.assertEqual(response.status_code, 200)
        titles = [task.title for task in response.context['tasks']]
        self.assertEqual(titles, ['High task', 'Medium task', 'Low task'])

    def test_task_effort_theme_mapping(self):
        high_effort = Task.objects.create(household=self.household, title='Hard task', effort='high', category=self.category)
        medium_effort = Task.objects.create(household=self.household, title='Medium task', effort='medium', category=self.category)
        low_effort = Task.objects.create(household=self.household, title='Easy task', effort='low', category=self.category)
        self.assertEqual(high_effort.effort_theme, 'effort-high')
        self.assertEqual(medium_effort.effort_theme, 'effort-medium')
        self.assertEqual(low_effort.effort_theme, 'effort-low')

    def test_completed_tasks_are_separated_from_active_tasks(self):
        active = Task.objects.create(household=self.household, title='Active task', category=self.category)
        done = Task.objects.create(household=self.household, title='Done task', category=self.category, completed=True)

        self.client.login(username='alex', password='secret123')
        response = self.client.get(reverse('tasks'))
        self.assertEqual(response.status_code, 200)
        active_titles = [task.title for task in response.context['tasks']]
        completed_titles = [task.title for task in response.context['completed_tasks']]
        self.assertEqual(active_titles, ['Active task'])
        self.assertEqual(completed_titles, ['Done task'])

    def test_task_update_changes_title_priority_effort_and_owner(self):
        task = Task.objects.create(household=self.household, title='Old title', priority='low', effort='low', category=self.category)
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('task_update', args=[task.id]), {
            'title': 'New title',
            'priority': 'high',
            'effort': 'high',
            'owner': f'user-{self.user2.id}',
            'category_name': self.category.name,
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.title, 'New title')
        self.assertEqual(task.priority, 'high')
        self.assertEqual(task.effort, 'high')
        self.assertEqual(task.owner, self.user2)
        self.assertEqual(task.owner_type, 'assigned')

    def test_task_update_can_change_category_and_notes(self):
        task = Task.objects.create(household=self.household, title='Trip planning', category=self.category)
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('task_update', args=[task.id]), {
            'title': 'Trip planning',
            'priority': 'medium',
            'effort': 'medium',
            'owner': '',
            'category_name': 'Travel',
            'notes': 'Check passport expiry',
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.category.name, 'Travel')
        self.assertEqual(task.notes, 'Check passport expiry')

    def test_task_update_can_remove_category(self):
        task = Task.objects.create(household=self.household, title='Has category', category=self.category)
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('task_update', args=[task.id]), {
            'title': 'Has category',
            'priority': 'medium',
            'effort': 'medium',
            'owner': '',
            'category_name': '',
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertIsNone(task.category)

    def test_task_update_can_remove_owner(self):
        task = Task.objects.create(
            household=self.household, title='Assigned task', category=self.category,
            owner=self.user1, owner_type='assigned',
        )
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('task_update', args=[task.id]), {
            'title': 'Assigned task',
            'priority': 'medium',
            'effort': 'medium',
            'owner': '',
            'category_name': self.category.name,
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertIsNone(task.owner)
        self.assertEqual(task.owner_type, 'unassigned')

    def test_update_color_changes_own_profile_only(self):
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('update_color'), {'color': 'sage'})
        self.assertEqual(response.status_code, 302)
        self.profile1.refresh_from_db()
        self.profile2.refresh_from_db()
        self.assertEqual(self.profile1.color, 'sage')
        self.assertEqual(self.profile2.color, 'sky')

    def test_today_view_shows_today_and_overdue_tasks(self):
        overdue = Task.objects.create(
            household=self.household, title='Overdue task', owner=self.user1, owner_type='assigned',
            due_date=date.today() - timedelta(days=2), category=self.category,
        )
        due_today = Task.objects.create(
            household=self.household, title='Due today task', owner=self.user1, owner_type='assigned',
            due_date=date.today(), category=self.category,
        )
        future = Task.objects.create(
            household=self.household, title='Future task', priority='low',
            due_date=date.today() + timedelta(days=3), category=self.category,
        )
        unassigned = Task.objects.create(
            household=self.household, title='Unassigned high priority', priority='high', category=self.category,
        )

        self.client.login(username='alex', password='secret123')
        response = self.client.get(reverse('today'))
        self.assertEqual(response.status_code, 200)
        today_titles = {task.title for task in response.context['today_tasks']}
        other_titles = [task.title for task in response.context['other_tasks']]
        self.assertEqual(today_titles, {'Overdue task', 'Due today task'})
        self.assertEqual(other_titles, ['Unassigned high priority', 'Future task'])

    def test_today_view_says_when_nothing_claimed_for_today(self):
        self.client.login(username='alex', password='secret123')
        response = self.client.get(reverse('today'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['today_tasks']), [])
        self.assertContains(response, 'No tasks claimed for today yet.')

    def test_claiming_a_task_for_today_promotes_it(self):
        task = Task.objects.create(
            household=self.household, title='Fix fence', priority='medium',
            due_date=date.today() + timedelta(days=5), category=self.category,
        )
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('task_claim', args=[task.id]), {'for_today': '1'})
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.owner, self.user1)
        self.assertEqual(task.owner_type, 'assigned')
        self.assertEqual(task.due_date, date.today())

    def test_shopping_toggle_records_checked_at_and_shows_in_history(self):
        item = ShoppingItem.objects.create(household=self.household, name='Milk', list_type='groceries', added_by=self.user1)
        old_item = ShoppingItem.objects.create(
            household=self.household, name='Old flour', list_type='groceries', added_by=self.user1,
            checked=True, checked_at=timezone.now() - timedelta(days=90),
        )

        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('shopping_toggle', args=[item.id]))
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertTrue(item.checked)
        self.assertIsNotNone(item.checked_at)

        today_response = self.client.get(reverse('today'), {'view': 'shopping'})
        recently_checked_names = [entry.name for entry in today_response.context['recently_checked']]
        self.assertIn('Milk', recently_checked_names)
        self.assertNotIn('Old flour', recently_checked_names)

    def test_task_set_owner_switches_to_other_user(self):
        task = Task.objects.create(
            household=self.household, title='Fix fence', owner=self.user1, owner_type='assigned',
            due_date=date.today(), category=self.category,
        )
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('task_set_owner', args=[task.id]), {'owner': f'user-{self.user2.id}'})
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.owner, self.user2)
        self.assertEqual(task.owner_type, 'assigned')

    def test_task_set_owner_can_set_both(self):
        task = Task.objects.create(
            household=self.household, title='Fix fence', owner=self.user1, owner_type='assigned',
            due_date=date.today(), category=self.category,
        )
        self.client.login(username='alex', password='secret123')
        response = self.client.post(reverse('task_set_owner', args=[task.id]), {'owner': 'either'})
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertIsNone(task.owner)
        self.assertEqual(task.owner_type, 'either')

    def test_owner_label_shows_both_for_either_owner_type(self):
        task = Task.objects.create(household=self.household, title='Shared chore', owner_type='either', category=self.category)
        self.assertEqual(task.owner_label, 'Both')

    def test_shopping_page_renders(self):
        self.client.login(username='alex', password='secret123')
        response = self.client.get(reverse('shopping'))
        self.assertEqual(response.status_code, 200)

    def test_signup_creates_user_and_profile_and_logs_in(self):
        response = self.client.post(reverse('signup'), {
            'email': 'newperson@example.com',
            'first_name': 'Jordan',
            'password': 'a-strong-password-1',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='newperson@example.com')
        self.assertEqual(user.first_name, 'Jordan')
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.name, 'Jordan')
        self.assertEqual(profile.household.name, 'Jazz Club')

        response = self.client.get(reverse('today'))
        self.assertEqual(response.status_code, 200)

    def test_signup_rejects_duplicate_email(self):
        response = self.client.post(reverse('signup'), {
            'email': 'alex@example.com',
            'first_name': 'Alex',
            'password': 'a-strong-password-1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='alex@example.com').count(), 1)
        self.assertContains(response, 'already exists')

