import datetime
import jdatetime
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.accounts.permissions import RoleRequiredMixin
from apps.jobs.models import JobOpportunity, JobOpportunityStage
from .models import StageTypeConfiguration, Holiday, JobRecruitmentPlan, JobStagePlan
from .utils import (
    to_jalali_string, parse_jalali_to_gregorian, 
    calculate_recruitment_schedule, get_jalali_month_range
)
from apps.candidates.models import ApplicationStageState

class PlanningDashboardView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = [UserProfile.ROLE_ADMIN, UserProfile.ROLE_RECRUITMENT_DIRECTOR, UserProfile.ROLE_RECRUITMENT_SPECIALIST]

    def get(self, request):
        today = datetime.date.today()
        j_today = jdatetime.date.fromgregorian(date=today)
        current_month_name = j_today.strftime("%B %Y")
        month_key = f"{j_today.year:04d}/{j_today.month:02d}"
        
        # Get start/end dates of current Jalali month
        g_start, g_end = get_jalali_month_range(j_today.year, j_today.month)

        # Active plans
        active_plans = JobRecruitmentPlan.objects.filter(status=JobRecruitmentPlan.STATUS_ACTIVE, is_deleted=False)
        draft_plans = JobRecruitmentPlan.objects.filter(status=JobRecruitmentPlan.STATUS_DRAFT, is_deleted=False)
        
        # Find delayed plans (outside SLA)
        delayed_plans = []
        for plan in active_plans:
            is_delayed = False
            for stage_plan in plan.stage_plans.filter(is_deleted=False):
                # Check if this stage is completed in candidates evaluations
                # It is considered incomplete if any candidate application stage state is in PENDING
                pending_evals = ApplicationStageState.objects.filter(
                    stage=stage_plan.stage,
                    status=ApplicationStageState.STATUS_PENDING,
                    is_deleted=False
                )
                if pending_evals.exists() and stage_plan.planned_end_date < today:
                    is_delayed = True
                    break
            if is_delayed:
                delayed_plans.append(plan)

        # Capacity gauges for current month
        stage_types = ['SCREENING', 'EXAM', 'INTERVIEW', 'ASSESSMENT']
        capacity_stats = []
        configs = {c.stage_type: c for c in StageTypeConfiguration.objects.filter(is_deleted=False)}
        
        for stype in stage_types:
            config = configs.get(stype)
            capacity_limit = config.monthly_capacity if config else 100
            
            # Total headcount consuming this stage type in current month
            from django.db.models import Sum
            consumed = JobStagePlan.objects.filter(
                stage_type=stype,
                planned_end_date__range=(g_start, g_end),
                plan__status=JobRecruitmentPlan.STATUS_ACTIVE,
                plan__is_deleted=False,
                is_deleted=False
            ).aggregate(total=Sum('plan__job__headcount'))['total'] or 0
            
            remaining = max(0, capacity_limit - consumed)
            percentage = round((consumed / capacity_limit) * 100, 1) if capacity_limit > 0 else 0
            
            # Map type to Farsi label
            labels = {
                'SCREENING': 'غربالگری اولیه',
                'EXAM': 'آزمون کتبی/عملی',
                'INTERVIEW': 'مصاحبه حضوری',
                'ASSESSMENT': 'کانون ارزیابی'
            }
            
            capacity_stats.append({
                'type': stype,
                'label': labels.get(stype, stype),
                'limit': capacity_limit,
                'consumed': consumed,
                'remaining': remaining,
                'percentage': percentage
            })

        # List of active jobs that are NOT planned yet
        unplanned_jobs = JobOpportunity.objects.filter(
            is_deleted=False
        ).exclude(
            status__in=[JobOpportunity.STATUS_CLOSED, JobOpportunity.STATUS_CANCELLED]
        ).exclude(
            recruitment_plan__isnull=False
        )

        context = {
            'active_plans': active_plans,
            'draft_plans': draft_plans,
            'delayed_plans': delayed_plans,
            'delayed_count': len(delayed_plans),
            'capacity_stats': capacity_stats,
            'unplanned_jobs': unplanned_jobs,
            'current_month_name': current_month_name,
            'today_jalali': to_jalali_string(today)
        }
        return render(request, 'recruitment_planning/dashboard.html', context)


class JobPlanningView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = [UserProfile.ROLE_ADMIN, UserProfile.ROLE_RECRUITMENT_DIRECTOR, UserProfile.ROLE_RECRUITMENT_SPECIALIST]

    def get(self, request, job_id):
        job = get_object_or_404(JobOpportunity, pk=job_id, is_deleted=False)
        plan = getattr(job, 'recruitment_plan', None)
        
        stages = job.stages.filter(is_deleted=False).order_by('sequence')
        
        context = {
            'job': job,
            'plan': plan,
            'stages': stages,
            'today_jalali': to_jalali_string(datetime.date.today())
        }
        return render(request, 'recruitment_planning/job_planning.html', context)

    def post(self, request, job_id):
        job = get_object_or_404(JobOpportunity, pk=job_id, is_deleted=False)
        start_date_str = request.POST.get('start_date', '')
        start_date = parse_jalali_to_gregorian(start_date_str)
        
        if not start_date:
            return HttpResponse('<div class="alert alert-danger text-xs font-bold text-right mb-0">لطفا تاریخ شروع معتبری وارد کنید.</div>', status=400)

        # Generate schedule preview
        schedule = calculate_recruitment_schedule(job, start_date)
        
        # Check if it is a preview request
        action = request.POST.get('action', 'preview')
        if action == 'preview':
            context = {
                'schedule': schedule,
                'job': job,
                'start_date_str': start_date_str
            }
            return render(request, 'recruitment_planning/partials/schedule_preview.html', context)

        # Save Plan Action
        if not schedule:
            return HttpResponse('<div class="alert alert-danger text-xs font-bold text-right mb-0">خطا: این فرصت شغلی هیچ مرحله ارزیابی تعریف‌شده‌ای ندارد.</div>', status=400)

        with transaction.atomic():
            plan, created = JobRecruitmentPlan.objects.get_or_create(
                job=job,
                defaults={
                    'start_date': start_date,
                    'predicted_end_date': schedule[-1]['planned_end_date'],
                    'status': JobRecruitmentPlan.STATUS_ACTIVE
                }
            )
            if not created:
                plan.start_date = start_date
                plan.predicted_end_date = schedule[-1]['planned_end_date']
                plan.status = JobRecruitmentPlan.STATUS_ACTIVE
                plan.is_deleted = False
                plan.save()

            # Clean and rebuild stage plans
            plan.stage_plans.all().delete()
            for s in schedule:
                JobStagePlan.objects.create(
                    plan=plan,
                    stage=s['stage'],
                    stage_type=s['stage_type'],
                    planned_start_date=s['planned_start_date'],
                    planned_end_date=s['planned_end_date'],
                    sla_days=s['sla_days'],
                    capacity_shifted=s['capacity_shifted']
                )

        return HttpResponse(
            f'<script>window.location.href = "{reverse("planning_dashboard")}";</script>'
        )


class PlanningConfigView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = [UserProfile.ROLE_ADMIN, UserProfile.ROLE_RECRUITMENT_DIRECTOR]

    def get(self, request):
        configs = StageTypeConfiguration.objects.filter(is_deleted=False)
        holidays = Holiday.objects.filter(is_deleted=False).order_by('date')
        
        # Initialize default configs if they do not exist
        defaults = [
            ('SCREENING', 'غربالگری اولیه', 5, 200),
            ('EXAM', 'آزمون کتبی/عملی', 15, 300),
            ('INTERVIEW', 'مصاحبه حضوری', 10, 80),
            ('ASSESSMENT', 'کانون ارزیابی', 15, 20),
            ('OTHER', 'سایر مراحل', 5, 100)
        ]
        
        with transaction.atomic():
            for code, name, sla, cap in defaults:
                StageTypeConfiguration.objects.get_or_create(
                    stage_type=code,
                    defaults={'default_sla_days': sla, 'monthly_capacity': cap}
                )
        
        context = {
            'configs': configs,
            'holidays': holidays,
            'today_jalali': to_jalali_string(datetime.date.today())
        }
        return render(request, 'recruitment_planning/config.html', context)

    def post(self, request):
        action = request.POST.get('action')
        
        # 1. Update SLA/Capacity Configs
        if action == 'save_configs':
            configs = StageTypeConfiguration.objects.filter(is_deleted=False)
            with transaction.atomic():
                for c in configs:
                    sla_val = request.POST.get(f'sla_{c.stage_type}')
                    cap_val = request.POST.get(f'capacity_{c.stage_type}')
                    if sla_val:
                        c.default_sla_days = int(sla_val)
                    if cap_val:
                        c.monthly_capacity = int(cap_val)
                    c.save()
            return redirect('planning_config')

        # 2. Add Holiday
        elif action == 'add_holiday':
            title = request.POST.get('title', '').strip()
            date_str = request.POST.get('date', '').strip()
            g_date = parse_jalali_to_gregorian(date_str)
            
            if title and g_date:
                Holiday.objects.get_or_create(
                    date=g_date,
                    defaults={'title': title, 'is_deleted': False}
                )
            return redirect('planning_config')

        # 3. Delete Holiday
        elif action == 'delete_holiday':
            holiday_id = request.POST.get('holiday_id')
            if holiday_id:
                Holiday.objects.filter(pk=holiday_id).update(is_deleted=True)
            return redirect('planning_config')

        return redirect('planning_config')
