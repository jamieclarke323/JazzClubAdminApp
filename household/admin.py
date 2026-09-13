from django.contrib import admin

from .models import (
    CalendarIntegration,
    Category,
    DateIdea,
    DinnerIdea,
    Household,
    HolidayIdea,
    Idea,
    MealPlan,
    NotificationPreference,
    ShoppingItem,
    SubTask,
    Task,
    UserProfile,
    WatchItem,
)

admin.site.register(Household)
admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Task)
admin.site.register(SubTask)
admin.site.register(ShoppingItem)
admin.site.register(DateIdea)
admin.site.register(DinnerIdea)
admin.site.register(MealPlan)
admin.site.register(HolidayIdea)
admin.site.register(WatchItem)
admin.site.register(NotificationPreference)
admin.site.register(CalendarIntegration)
admin.site.register(Idea)
