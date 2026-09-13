from django.core.management.base import BaseCommand

from household.models import Category, Household, UserProfile


class Command(BaseCommand):
    help = 'Create the default two-user household with starter categories.'

    def handle(self, *args, **options):
        household, _ = Household.objects.get_or_create(name='Jazz Club')
        for name in ['Home', 'Money', 'Car', 'Appointments', 'Documents', 'Shopping', 'Travel', 'Relationship', 'Personal', 'Other']:
            Category.objects.get_or_create(household=household, name=name)
        profiles = UserProfile.objects.filter(household=household)
        self.stdout.write(self.style.SUCCESS(f'Household ready: {household} ({profiles.count()} profiles)'))
