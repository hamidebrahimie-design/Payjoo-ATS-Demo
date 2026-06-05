from django.urls import path
from .views import CustomLoginView, CustomLogoutView, UserListView, UserCreateView, UserUpdateView, UserDeleteView, AuditLogListView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/add/', UserCreateView.as_view(), name='user_add'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('audit-logs/', AuditLogListView.as_view(), name='audit_log_list'),
]
