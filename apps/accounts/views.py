from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponse

from .forms import PersianLoginForm, UserCreationForm, UserUpdateForm
from .models import UserProfile
from .permissions import RoleRequiredMixin

class CustomLoginView(DjangoLoginView):
    form_class = PersianLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == UserProfile.ROLE_CANDIDATE:
            return reverse('candidate_dashboard')
        return reverse('dashboard')


class CustomLogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('login')

    def get(self, request):
        logout(request)
        return redirect('login')


class UserListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    allowed_roles = [UserProfile.ROLE_ADMIN]

    def get_queryset(self):
        # فقط کاربرانی که پروفایل آن‌ها حذف نرم نشده و نقش متقاضی ندارند بازگردانده شوند
        return User.objects.filter(
            profile__is_deleted=False
        ).exclude(
            profile__role=UserProfile.ROLE_CANDIDATE
        ).select_related('profile')


class UserCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')
    allowed_roles = [UserProfile.ROLE_ADMIN]

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('HX-Request'):
            # در صورتی که درخواست از طریق HTMX باشد، ردیف جدول جدید را بازمی‌گردانیم
            user = self.object
            edit_url = reverse('user_edit', kwargs={'pk': user.pk})
            delete_url = reverse('user_delete', kwargs={'pk': user.pk})
            external_text = "خارجی" if user.profile.is_external else "داخلی"
            return HttpResponse(
                f'<tr id="user-{user.id}">'
                f'<td>{user.username}</td>'
                f'<td>{user.get_full_name() or user.username}</td>'
                f'<td>{user.email}</td>'
                f'<td>{user.profile.get_role_display()}</td>'
                f'<td>{external_text}</td>'
                f'<td>'
                f'<a href="{edit_url}" class="btn btn-sm btn-outline-primary me-1">ویرایش</a>'
                f'<button hx-delete="{delete_url}" hx-target="#user-{user.id}" hx-confirm="آیا از حذف این کاربر مطمئن هستید؟" class="btn btn-sm btn-outline-danger">حذف</button>'
                f'</td>'
                f'</tr>'
            )
        return response


class UserUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')
    allowed_roles = [UserProfile.ROLE_ADMIN]

    def get_initial(self):
        initial = super().get_initial()
        profile = self.object.profile
        initial['role'] = profile.role
        initial['is_external'] = profile.is_external
        initial['phone_number'] = profile.phone_number
        return initial


class UserDeleteView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = [UserProfile.ROLE_ADMIN]

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        
        # غیرفعال کردن اکانت جنگو
        user.is_active = False
        user.save()

        # حذف نرم پروفایل کاربر
        profile = user.profile
        profile.delete()

        # بازگرداندن پاسخ خالی جهت حذف ردیف توسط HTMX
        return HttpResponse("")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if hasattr(request.user, 'profile') and request.user.profile.role == UserProfile.ROLE_CANDIDATE:
            return redirect('candidate_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        from apps.jobs.models import JobOpportunity
        from apps.candidates.models import Candidate, JobApplication, ApplicationStageState
        from apps.core.models import AuditLog
        from django.utils import timezone
        from datetime import timedelta
        
        # ۱. آمارهای کلی
        total_jobs = JobOpportunity.objects.filter(is_deleted=False).count()
        active_jobs = JobOpportunity.objects.filter(is_deleted=False).exclude(status__in=['CLOSED', 'CANCELLED']).count()
        total_candidates = Candidate.objects.filter(is_deleted=False).count()
        in_progress_apps = JobApplication.objects.filter(status='IN_PROGRESS', is_deleted=False).count()
        selected_candidates = JobApplication.objects.filter(status='SELECTED', is_deleted=False).count()
        
        data.update({
            'total_jobs': total_jobs,
            'active_jobs_count': active_jobs,
            'total_candidates': total_candidates,
            'in_progress_apps': in_progress_apps,
            'selected_candidates': selected_candidates,
        })
        
        # ۲. توزیع وضعیت فرصت‌های شغلی
        job_status_distribution = []
        for status_key, status_label in JobOpportunity.STATUS_CHOICES:
            count = JobOpportunity.objects.filter(status=status_key, is_deleted=False).count()
            if count > 0:
                job_status_distribution.append({
                    'label': status_label,
                    'count': count,
                    'percentage': round((count / total_jobs) * 100, 1) if total_jobs > 0 else 0
                })
        data['job_status_distribution'] = job_status_distribution

        # ۳. توزیع متقاضیان در مراحل ارزیابی فعال
        from django.db.models import Count
        people_in_stages = JobApplication.objects.filter(
            status='IN_PROGRESS', is_deleted=False
        ).values('current_stage__name').annotate(count=Count('id')).order_by('-count')
        
        stage_people_stats = []
        for item in people_in_stages:
            if item['current_stage__name']:
                stage_people_stats.append({
                    'stage_name': item['current_stage__name'],
                    'count': item['count']
                })
        data['stage_people_stats'] = stage_people_stats

        # ۴. محاسبه میانگین زمان حضور در هر مرحله (روز)
        completed_states = ApplicationStageState.objects.filter(
            status__in=['COMPLETED', 'FAILED'],
            is_deleted=False
        ).select_related('application', 'stage')
        
        stage_times = {}
        for state in completed_states:
            app = state.application
            stage = state.stage
            duration = None
            
            if stage.sequence == 1:
                duration = state.updated_at - app.created_at
            else:
                prev_state = app.stage_states.filter(
                    stage__sequence__lt=stage.sequence,
                    is_deleted=False
                ).order_by('-stage__sequence').first()
                if prev_state and prev_state.status in ['COMPLETED', 'FAILED']:
                    duration = state.updated_at - prev_state.updated_at
            
            if duration is not None:
                days = duration.total_seconds() / (24 * 3600)
                days = max(days, 0.1)
                stage_name = stage.name
                if stage_name not in stage_times:
                    stage_times[stage_name] = []
                stage_times[stage_name].append(days)
                
        avg_stage_days = []
        for stage_name, durations in stage_times.items():
            avg_stage_days.append({
                'stage_name': stage_name,
                'avg_days': round(sum(durations) / len(durations), 1),
                'count': len(durations)
            })
        avg_stage_days.sort(key=lambda x: x['avg_days'], reverse=True)
        data['avg_stage_days'] = avg_stage_days

        # ۵. شناسایی متقاضیان تاخیردار (بیش از ۷ روز توقف در وضعیت PENDING)
        seven_days_ago = timezone.now() - timedelta(days=7)
        delayed_candidates = []
        pending_states = ApplicationStageState.objects.filter(
            status='PENDING',
            application__status='IN_PROGRESS',
            application__is_deleted=False,
            is_deleted=False
        ).select_related('application__candidate', 'application__job', 'stage')
        
        for state in pending_states:
            app = state.application
            stage = state.stage
            active_since = None
            if stage.sequence == 1:
                active_since = app.created_at
            else:
                prev_state = app.stage_states.filter(
                    stage__sequence__lt=stage.sequence,
                    is_deleted=False
                ).order_by('-stage__sequence').first()
                if prev_state and prev_state.status in ['COMPLETED', 'FAILED']:
                    active_since = prev_state.updated_at
                    
            if active_since and active_since < seven_days_ago:
                days_waiting = (timezone.now() - active_since).days
                delayed_candidates.append({
                    'candidate': app.candidate,
                    'job': app.job,
                    'stage_name': stage.name,
                    'days_waiting': days_waiting
                })
        delayed_candidates.sort(key=lambda x: x['days_waiting'], reverse=True)
        data['delayed_candidates'] = delayed_candidates[:5] # نمایش حداکثر ۵ مورد بحرانی

        # ۶. لاگ فعالیت‌های اخیر سیستم
        data['recent_activities'] = AuditLog.objects.all().select_related('user').order_by('-timestamp')[:5]

        # ۷. آمارهای تکمیلی برای داشبورد (توزیع کاندیداها و دپارتمان‌ها و واحدها)
        # دریافت تمام نام مراحل فعال در سیستم برای نمایش در ستون‌های جدول
        active_stages_qs = JobApplication.objects.filter(
            status='IN_PROGRESS', is_deleted=False
        ).exclude(current_stage=None).values_list('current_stage__name', flat=True).distinct()
        active_stages = sorted(list(set(active_stages_qs)))
        data['active_stages'] = active_stages

        # آمار دپارتمان‌ها
        departments = list(JobOpportunity.objects.filter(is_deleted=False).values_list('department', flat=True).distinct())
        dept_stats = []
        for dept in departments:
            if not dept:
                continue
            # تعداد فرصت‌های شغلی
            total_jobs_dept = JobOpportunity.objects.filter(department=dept, is_deleted=False).count()
            active_jobs_dept = JobOpportunity.objects.filter(department=dept, is_deleted=False).exclude(status__in=['CLOSED', 'CANCELLED']).count()
            
            dept_row = {
                'department': dept,
                'total_jobs': total_jobs_dept,
                'active_jobs': active_jobs_dept,
                'stages': {},
                'total_candidates': 0
            }
            # متقاضیان فعال در این دپارتمان
            apps = JobApplication.objects.filter(
                job__department=dept,
                status='IN_PROGRESS',
                is_deleted=False
            )
            for stage_name in active_stages:
                count = apps.filter(current_stage__name=stage_name).count()
                dept_row['stages'][stage_name] = count
                dept_row['total_candidates'] += count
            
            dept_stats.append(dept_row)
        data['dept_stats'] = dept_stats

        # آمار واحدها
        units = list(JobOpportunity.objects.filter(is_deleted=False).exclude(unit='').exclude(unit=None).values_list('unit', flat=True).distinct())
        unit_stats = []
        for unit in units:
            if not unit:
                continue
            total_jobs_unit = JobOpportunity.objects.filter(unit=unit, is_deleted=False).count()
            active_jobs_unit = JobOpportunity.objects.filter(unit=unit, is_deleted=False).exclude(status__in=['CLOSED', 'CANCELLED']).count()
            
            unit_row = {
                'unit': unit,
                'total_jobs': total_jobs_unit,
                'active_jobs': active_jobs_unit,
                'stages': {},
                'total_candidates': 0
            }
            apps = JobApplication.objects.filter(
                job__unit=unit,
                status='IN_PROGRESS',
                is_deleted=False
            )
            for stage_name in active_stages:
                count = apps.filter(current_stage__name=stage_name).count()
                unit_row['stages'][stage_name] = count
                unit_row['total_candidates'] += count
            
            unit_stats.append(unit_row)
        data['unit_stats'] = unit_stats

        # آمار رده‌های شغلی (رده شغلی)
        categories = list(JobOpportunity.objects.filter(is_deleted=False).exclude(job_category='').exclude(job_category=None).values_list('job_category', flat=True).distinct())
        category_stats = []
        for cat in categories:
            if not cat:
                continue
            total_jobs_cat = JobOpportunity.objects.filter(job_category=cat, is_deleted=False).count()
            active_jobs_cat = JobOpportunity.objects.filter(job_category=cat, is_deleted=False).exclude(status__in=['CLOSED', 'CANCELLED']).count()
            
            cat_row = {
                'job_category': cat,
                'total_jobs': total_jobs_cat,
                'active_jobs': active_jobs_cat,
                'stages': {},
                'total_candidates': 0
            }
            apps = JobApplication.objects.filter(
                job__job_category=cat,
                status='IN_PROGRESS',
                is_deleted=False
            )
            for stage_name in active_stages:
                count = apps.filter(current_stage__name=stage_name).count()
                cat_row['stages'][stage_name] = count
                cat_row['total_candidates'] += count
            
            category_stats.append(cat_row)
        data['category_stats'] = category_stats

        # ۸. میانگین زمان تعیین تکلیف فرصت شغلی و درخواست‌ها
        # میانگین زمان بستن فرصت شغلی (از تاریخ شروع/ایجاد تا انتخاب نهایی کاندیدا یا بسته‌شدن فرصت)
        closed_jobs = JobOpportunity.objects.filter(status='CLOSED', is_deleted=False)
        job_durations = []
        for job in closed_jobs:
            pub_date = job.start_date or job.created_at.date()
            # پیدا کردن اولین اپلیکیشن قبول نهایی شده برای این موقعیت شغلی
            selected_app = job.applications.filter(status='SELECTED', is_deleted=False).order_by('updated_at').first()
            if selected_app:
                close_date = selected_app.updated_at.date()
            else:
                close_date = job.updated_at.date()
            duration = (close_date - pub_date).days
            job_durations.append(max(duration, 0))
        
        data['avg_job_finalization_days'] = round(sum(job_durations) / len(job_durations), 1) if job_durations else 0

        # میانگین زمان تعیین تکلیف درخواست‌های متقاضیان (SELECTED یا REJECTED)
        finalized_apps = JobApplication.objects.filter(status__in=['SELECTED', 'REJECTED'], is_deleted=False)
        app_durations = []
        for app in finalized_apps:
            duration = (app.updated_at.date() - app.created_at.date()).days
            app_durations.append(max(duration, 0))
            
        data['avg_app_finalization_days'] = round(sum(app_durations) / len(app_durations), 1) if app_durations else 0

        return data


from django.core.exceptions import PermissionDenied
from django.db.models import Q
from apps.core.models import AuditLog

class AuditLogListView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = 'accounts/audit_log_list.html'
    context_object_name = 'logs'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, 'profile') or not request.user.profile.can_view_audit_logs:
            raise PermissionDenied("شما دسترسی به مشاهده لاگ‌های ممیزی ندارید.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = AuditLog.objects.all().select_related('user').order_by('-timestamp')
        
        # Action type filter
        action_type = self.request.GET.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
            
        # Search query
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(user__username__icontains=q) |
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(model_name__icontains=q) |
                Q(object_id__icontains=q) |
                Q(changes__icontains=q)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_action_type'] = self.request.GET.get('action_type', '')
        context['search_q'] = self.request.GET.get('q', '')
        context['action_choices'] = AuditLog.ACTION_CHOICES
        return context


