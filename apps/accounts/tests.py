from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from apps.accounts.models import UserProfile
from apps.core.models import AuditLog

class UserRoleAndPermissionTests(TestCase):
    def setUp(self):
        # Create standard test users for different roles
        self.admin_user = User.objects.create_user(
            username='admin_test',
            password='testpassword123',
            email='admin@test.com',
            first_name='Admin',
            last_name='User'
        )
        self.admin_user.profile.role = UserProfile.ROLE_ADMIN
        self.admin_user.profile.save()

        self.director_user = User.objects.create_user(
            username='director_test',
            password='testpassword123',
            email='director@test.com'
        )
        self.director_user.profile.role = UserProfile.ROLE_RECRUITMENT_DIRECTOR
        self.director_user.profile.save()

        self.interviewer_user = User.objects.create_user(
            username='interviewer_test',
            password='testpassword123',
            email='interviewer@test.com'
        )
        self.interviewer_user.profile.role = UserProfile.ROLE_INTERVIEWER
        self.interviewer_user.profile.save()

        self.external_assessor_user = User.objects.create_user(
            username='external_test',
            password='testpassword123',
            email='external@test.com'
        )
        self.external_assessor_user.profile.role = UserProfile.ROLE_EXTERNAL_ASSESSOR
        self.external_assessor_user.profile.save()

    def test_user_profile_creation_on_signal(self):
        """تست ایجاد خودکار پروفایل کاربر پس از ساخت اکانت کاربر جنگو"""
        new_user = User.objects.create_user(username='new_test_user', password='password123')
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertEqual(new_user.profile.role, UserProfile.ROLE_INTERVIEWER)  # نقش پیش‌فرض

    def test_external_assessor_is_external_flag(self):
        """تست اینکه ارزیاب‌های خارجی به طور خودکار فلگ is_external=True می‌گیرند"""
        # Test database model save level
        user = User.objects.create_user(username='ext_assessor_test', password='password123')
        profile = user.profile
        profile.role = UserProfile.ROLE_EXTERNAL_ASSESSOR
        profile.save()
        self.assertTrue(profile.is_external)

    def test_rbac_view_access(self):
        """تست کنترل دسترسی نقش‌ها (RBAC) به صفحات مدیریت کاربران"""
        # User list view only allowed for ADMIN
        user_list_url = reverse('user_list')
        
        # Test non-admin user
        self.client.login(username='director_test', password='testpassword123')
        response = self.client.get(user_list_url)
        self.assertEqual(response.status_code, 403)  # Permission Denied

        # Test admin user
        self.client.login(username='admin_test', password='testpassword123')
        response = self.client.get(user_list_url)
        self.assertEqual(response.status_code, 200)

    def test_candidate_exclusion_from_user_management(self):
        """تست عدم نمایش متقاضیان در لیست کاربران و فرم‌های ثبت‌نام/ویرایش"""
        # Create a user with candidate role
        candidate_user = User.objects.create_user(
            username='candidate_test',
            password='testpassword123',
            email='candidate@test.com'
        )
        candidate_user.profile.role = UserProfile.ROLE_CANDIDATE
        candidate_user.profile.save()

        # 1. Verify candidate is excluded from user list queryset
        self.client.login(username='admin_test', password='testpassword123')
        user_list_url = reverse('user_list')
        response = self.client.get(user_list_url)
        self.assertEqual(response.status_code, 200)
        users = response.context['users']
        self.assertNotIn(candidate_user, users)

        # 2. Verify candidate is excluded from UserCreationForm choices
        from apps.accounts.forms import UserCreationForm, UserUpdateForm
        creation_form = UserCreationForm()
        creation_roles = [choice[0] for choice in creation_form.fields['role'].choices]
        self.assertNotIn(UserProfile.ROLE_CANDIDATE, creation_roles)

        # 3. Verify candidate is excluded from UserUpdateForm choices
        update_form = UserUpdateForm(instance=self.admin_user)
        update_roles = [choice[0] for choice in update_form.fields['role'].choices]
        self.assertNotIn(UserProfile.ROLE_CANDIDATE, update_roles)

    def test_audit_log_immutability(self):
        """تست اینکه رکوردهای جدول AuditLog غیرقابل ویرایش و حذف هستند"""
        # Create an audit log entry
        log = AuditLog.objects.create(
            user=self.admin_user,
            action_type=AuditLog.ACTION_CREATE,
            model_name='userprofile',
            object_id=str(self.admin_user.profile.pk),
            changes={'role': 'ADMIN'}
        )
        self.assertIsNotNone(log.pk)

        # Try to modify log
        log.action_type = AuditLog.ACTION_UPDATE
        with self.assertRaises(PermissionDenied):
            log.save()

        # Try to delete log
        with self.assertRaises(PermissionDenied):
            log.delete()

    def test_management_dashboard_metrics(self):
        """تست محاسبات آماری، میانگین زمان مراحل و متقاضیان تاخیردار در داشبورد مدیریتی"""
        from apps.jobs.models import JobOpportunity, WorkflowTemplate, WorkflowStageTemplate
        from apps.candidates.models import Candidate, JobApplication, ApplicationStageState
        from django.utils import timezone
        from datetime import timedelta

        # ۱. ایجاد موقعیت شغلی و فرآیند ارزیابی
        workflow = WorkflowTemplate.objects.create(name='فرآیند ارزیابی تستی')
        stage1 = WorkflowStageTemplate.objects.create(workflow=workflow, name='آزمون کتبی تستی', default_weight=50, sequence=1)
        stage2 = WorkflowStageTemplate.objects.create(workflow=workflow, name='مصاحبه فنی تستی', default_weight=50, sequence=2)
        
        job = JobOpportunity.objects.create(
            request_number='REQ-TEST-100', title='برنامه‌نویس', code='DEV-100',
            department='فناوری', workflow=workflow, status=JobOpportunity.STATUS_PUBLISHED
        )

        # ۲. ایجاد متقاضی فعال
        cand1 = Candidate.objects.create(
            first_name='مهدی', last_name='حسینی', email='m.h@example.com',
            phone_number='09129999999', national_id='9999999999'
        )
        app1 = JobApplication.objects.create(job=job, candidate=cand1)
        
        # ۳. شبیه‌سازی متقاضی تاخیردار (بیش از ۷ روز توقف در مرحله اول)
        # برای تغییر فیلدهای created_at و updated_at که auto_now هستند، از متد update استفاده می‌کنیم
        JobApplication.objects.filter(id=app1.id).update(created_at=timezone.now() - timedelta(days=10))
        exam_state = app1.stage_states.filter(stage__name='آزمون کتبی تستی').first()
        ApplicationStageState.objects.filter(id=exam_state.id).update(
            created_at=timezone.now() - timedelta(days=10),
            updated_at=timezone.now() - timedelta(days=10)
        )

        # ۴. ایجاد متقاضی دوم که مرحله اول را با موفقیت پشت سر گذاشته
        cand2 = Candidate.objects.create(
            first_name='نیلوفر', last_name='کریمی', email='n.k@example.com',
            phone_number='09128888888', national_id='8888888888'
        )
        app2 = JobApplication.objects.create(job=job, candidate=cand2)
        
        # ثبت موفقیت‌آمیز آزمون کتبی برای کاندیدای دوم به صورت ۵ روز پیش
        exam_state2 = app2.stage_states.filter(stage__name='آزمون کتبی تستی').first()
        ApplicationStageState.objects.filter(id=exam_state2.id).update(
            status='COMPLETED',
            score=80.0,
            created_at=timezone.now() - timedelta(days=10),
            updated_at=timezone.now() - timedelta(days=5)
        )
        JobApplication.objects.filter(id=app2.id).update(created_at=timezone.now() - timedelta(days=10))

        # ۵. درخواست صفحه داشبورد توسط کاربر ادمین
        self.client.login(username='admin_test', password='testpassword123')
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # بررسی وجود متغیرهای آماری در کانتکست
        self.assertIn('total_jobs', response.context)
        self.assertIn('active_jobs_count', response.context)
        self.assertIn('total_candidates', response.context)
        self.assertIn('in_progress_apps', response.context)
        self.assertIn('selected_candidates', response.context)
        self.assertIn('active_stages', response.context)
        self.assertIn('dept_stats', response.context)
        self.assertIn('unit_stats', response.context)
        self.assertIn('category_stats', response.context)
        self.assertIn('avg_job_finalization_days', response.context)
        self.assertIn('avg_app_finalization_days', response.context)

        # ۶. تایید صحت شناسایی متقاضی تاخیردار (باید کاندیدای اول به عنوان تاخیردار حضور داشته باشد)
        delayed_list = response.context['delayed_candidates']
        self.assertTrue(any(item['candidate'].id == cand1.id for item in delayed_list))
        # کاندیدای دوم در مرحله دوم (مصاحبه فنی تستی) معلق است اما کمتر از ۷ روز پیش این مرحله برایش فعال شده، پس نباید جزو تاخیردارها باشد
        self.assertFalse(any(item['candidate'].id == cand2.id for item in delayed_list))

        # ۷. تایید محاسبه میانگین زمان سپری شده
        avg_days_list = response.context['avg_stage_days']
        self.assertTrue(any(item['stage_name'] == 'آزمون کتبی تستی' for item in avg_days_list))
        test_stage_avg = next(item for item in avg_days_list if item['stage_name'] == 'آزمون کتبی تستی')
        # کاندیدای دوم بعد از ۵ روز آزمونش ثبت شده (۱۰ روز پیش ثبت‌نام، ۵ روز پیش ثبت نمره)، پس میانگین حدود ۵ روز است
        self.assertEqual(test_stage_avg['avg_days'], 5.0)

    def test_role_based_stage_access_control(self):
        """تست کنترل دسترسی جامع نقش‌ها به مراحل ارزیابی و ثبت نمرات"""
        from apps.jobs.models import JobOpportunity, WorkflowTemplate, WorkflowStageTemplate, JobStageInterviewer
        from apps.candidates.models import Candidate, JobApplication, ApplicationStageState
        from apps.accounts.permissions import check_stage_access

        # ایجاد الگو با مراحل متنوع (مصاحبه و کانون ارزیابی)
        workflow = WorkflowTemplate.objects.create(name='فرآیند جامع تستی')
        stage_interview = WorkflowStageTemplate.objects.create(workflow=workflow, name='مصاحبه فنی تستی', default_weight=50, sequence=1)
        stage_assessment = WorkflowStageTemplate.objects.create(workflow=workflow, name='کانون ارزیابی تخصصی', default_weight=50, sequence=2)
        
        job = JobOpportunity.objects.create(
            request_number='REQ-ROLE-TEST', title='برنامه‌نویس ارشد', code='DEV-ROLE-TEST',
            department='فناوری', workflow=workflow, status=JobOpportunity.STATUS_PUBLISHED
        )

        # ایجاد متقاضی
        cand = Candidate.objects.create(
            first_name='علی', last_name='علوی', email='ali@example.com',
            phone_number='09127777777', national_id='7777777777'
        )
        app = JobApplication.objects.create(job=job, candidate=cand)
        
        # دریافت آبجکت‌های مراحل شغل
        job_stage_interview = job.stages.filter(name='مصاحبه فنی تستی').first()
        job_stage_assessment = job.stages.filter(name='کانون ارزیابی تخصصی').first()
        
        # ۱. بررسی تابع کمکی check_stage_access
        # مصاحبه‌گر (ROLE_INTERVIEWER) نباید به کانون ارزیابی دسترسی داشته باشد
        self.assertTrue(check_stage_access(self.interviewer_user, job_stage_interview))
        self.assertFalse(check_stage_access(self.interviewer_user, job_stage_assessment))
        
        # ارزیاب کانون (ROLE_EXTERNAL_ASSESSOR) نباید به مصاحبه فنی دسترسی داشته باشد
        self.assertTrue(check_stage_access(self.external_assessor_user, job_stage_assessment))
        self.assertFalse(check_stage_access(self.external_assessor_user, job_stage_interview))

        # ۲. بررسی فیلتر شدن پنل مصاحبه‌ها (InterviewsPanelView)
        # انتساب مصاحبه‌گر به هر دو مرحله در دیتابیس (هرچند که از لحاظ نقش نباید به کانون دسترسی داشته باشد)
        JobStageInterviewer.objects.create(job=job, stage=job_stage_interview, user=self.interviewer_user)
        JobStageInterviewer.objects.create(job=job, stage=job_stage_assessment, user=self.interviewer_user)
        
        # لاگین با مصاحبه‌گر
        self.client.login(username='interviewer_test', password='testpassword123')
        url_interviews = reverse('candidate_interviews')
        response = self.client.get(url_interviews)
        self.assertEqual(response.status_code, 200)
        
        # با اینکه مصاحبه‌گر به هر دو مرحله اساین شده، اما فقط باید مصاحبه فنی تستی را در لیست ببیند و کانون ارزیابی فیلتر شود
        stage_states = response.context['stage_states']
        self.assertTrue(any(state.stage.id == job_stage_interview.id for state in stage_states))
        self.assertFalse(any(state.stage.id == job_stage_assessment.id for state in stage_states))

        # ۳. بررسی بلاک کردن ثبت نمرات غیرمجاز (SubmitInterviewerScoreView)
        state_assessment = app.stage_states.filter(stage=job_stage_assessment).first()
        url_submit_score = reverse('candidate_submit_interviewer_score', kwargs={'pk': state_assessment.id})
        
        # ارسال نمره کانون ارزیابی توسط مصاحبه‌گر عادی باید با خطای ۴۰۳ (PermissionDenied) مواجه شود
        response = self.client.post(url_submit_score, {'score': '80', 'notes': 'تست'})
        self.assertEqual(response.status_code, 403)

    def test_audit_log_list_view_access_and_filtering(self):
        """تست دسترسی به لیست لاگ‌های ممیزی و فیلتر کردن آن‌ها"""
        # Create test audit logs
        log_create = AuditLog.objects.create(
            user=self.admin_user,
            action_type=AuditLog.ACTION_CREATE,
            model_name='jobopportunity',
            object_id='100',
            changes={'title': 'Developer'}
        )
        log_update = AuditLog.objects.create(
            user=self.director_user,
            action_type=AuditLog.ACTION_UPDATE,
            model_name='candidate',
            object_id='200',
            changes={'first_name': 'Ali'}
        )

        url = reverse('audit_log_list')

        # 1. Non-authorized user should get 403
        self.client.login(username='interviewer_test', password='testpassword123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # 2. Authorized user (ADMIN) should get 200 and see the logs
        self.client.login(username='admin_test', password='testpassword123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        logs = response.context['logs']
        # Note: the test setup creates other logs (like in signal profile creation, user profile saves, etc.),
        # so we assert that our logs exist in the returned list.
        log_ids = [l.id for l in logs]
        self.assertIn(log_create.id, log_ids)
        self.assertIn(log_update.id, log_ids)

        # 3. Filtering by action_type
        response = self.client.get(url, {'action_type': 'CREATE'})
        self.assertEqual(response.status_code, 200)
        logs = response.context['logs']
        for l in logs:
            self.assertEqual(l.action_type, 'CREATE')

        # 4. Searching by query q
        response = self.client.get(url, {'q': 'Ali'})
        self.assertEqual(response.status_code, 200)
        logs = response.context['logs']
        self.assertTrue(any(l.id == log_update.id for l in logs))
