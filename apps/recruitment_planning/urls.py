from django.urls import path
from .views import PlanningDashboardView, JobPlanningView, PlanningConfigView

urlpatterns = [
    path('dashboard/', PlanningDashboardView.as_view(), name='planning_dashboard'),
    path('job/<int:job_id>/', JobPlanningView.as_view(), name='job_planning'),
    path('config/', PlanningConfigView.as_view(), name='planning_config'),
]
