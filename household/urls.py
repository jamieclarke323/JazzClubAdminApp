from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('today/', views.today_view, name='today'),
    path('tasks/', views.admin_view, name='tasks'),
    path('shopping/', views.shopping_view, name='shopping'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/color/', views.update_color, name='update_color'),
    path('ideas/<str:kind>/', views.idea_list_view, name='idea_list'),
    path('ideas/<str:kind>/create/', views.idea_create, name='idea_create'),
    path('ideas/<str:kind>/<int:item_id>/toggle/', views.idea_toggle, name='idea_toggle'),
    path('ideas/<str:kind>/<int:item_id>/delete/', views.idea_delete, name='idea_delete'),
    path('ideas/<str:kind>/categories/create/', views.category_create, name='category_create'),
    path('ideas/<str:kind>/categories/<int:category_id>/update/', views.category_update, name='category_update'),
    path('ideas/<str:kind>/categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/update/', views.task_update, name='task_update'),
    path('tasks/<int:task_id>/toggle/', views.task_toggle, name='task_toggle'),
    path('tasks/<int:task_id>/claim/', views.task_claim, name='task_claim'),
    path('tasks/<int:task_id>/set-owner/', views.task_set_owner, name='task_set_owner'),
    path('tasks/<int:task_id>/subtasks/create/', views.subtask_create, name='subtask_create'),
    path('subtasks/<int:subtask_id>/toggle/', views.subtask_toggle, name='subtask_toggle'),
    path('subtasks/<int:subtask_id>/delete/', views.subtask_delete, name='subtask_delete'),
    path('shopping/add/', views.shopping_add, name='shopping_add'),
    path('shopping/<int:item_id>/toggle/', views.shopping_toggle, name='shopping_toggle'),
    path('shopping/<int:item_id>/delete/', views.shopping_delete, name='shopping_delete'),
    path('undo/', views.undo_action, name='undo_action'),
]
