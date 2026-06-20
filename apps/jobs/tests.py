from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from datetime import date, datetime
import jdatetime

from apps.jobs.models import WorkflowTemplate, WorkflowStageTemplate, JobOpportunity, JobOpportunityStage
from apps.jobs.forms import JobOpportunityFormSet, JobOpportunityForm
from apps.core.templatetags.jalali_tags import to_jalali

class JobOpportunityAndWorkflowTests(TestCase):
    def setUp(self):
        # Create a recruiter user
        self.recruiter = User.objects.create_user(username='recruiter_test', password='password123')
        self.recruiter.profile.role = 'RECRUITMENT_SPECIALIST'
        self.recruiter.profile.save()

        # Create a WorkflowTemplate with default stages
        self.workflow = WorkflowTemplate.objects.create(
            name='آزمون و مصاحبه استاندارد',
            description='شامل آزمون کتبی و مصاحبه تخصصی'
        )
        self.stage1 = WorkflowStageTemplate.objects.create(
            workflow=self.workflow,
            name='آزمون کتبی',
            default_weight=40,
            sequence=1
        )
        self.stage2 = WorkflowStageTemplate.objects.create(
            workflow=self.workflow,
            name='مصاحبه حضوری',
            default_weight=60,
            sequence=2
        )

    def test_workflow_template_creation(self):
        """تست ایجاد موفقیت‌آمیز قالب فرآیند کاری و مراحل پیش‌فرض آن"""
        self.assertEqual(self.workflow.stages.count(), 2)
        self.assertEqual(self.stage1.default_weight, 40)
        self.assertEqual(self.stage2.default_weight, 60)

    def test_job_list_filtering_and_sorting_state_preservation(self):
        """تست حفظ وضعیت فیلترها و مرتب‌سازی در لیست فرصت‌های شغلی با استفاده از سشن"""
        self.client.login(username='recruiter_test', password='password123')

        # 1. Initially request list view with query parameters
        url = reverse('job_list') + '?q=Python&sort=title&order=asc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verify that parameters are stored in session
        self.assertEqual(self.client.session.get('jobs_filter_params'), 'q=Python&sort=title&order=asc')

        # 2. Access the list view WITHOUT parameters (simulating going back to the page)
        response_back = self.client.get(reverse('job_list'))
        # Should redirect to preserve state
        self.assertEqual(response_back.status_code, 302)
        self.assertIn('q=Python&sort=title&order=asc', response_back.url)

        # 3. Request clear parameter to clear filters
        response_clear = self.client.get(reverse('job_list') + '?clear=1')
        self.assertEqual(response_clear.status_code, 302)
        self.assertEqual(response_clear.url, reverse('job_list'))

        # Verify session is cleared
        self.assertNotIn('jobs_filter_params', self.client.session)

    def test_job_opportunity_copies_workflow_stages(self):
        """تست اینکه با ایجاد فرصت شغلی جدید، مراحل پیش‌فرض از الگوی فرآیند کپی می‌شوند"""
        job = JobOpportunity.objects.create(
            request_number='REQ-1402-005',
            title='برنامه‌نویس پایتون',
            code='PY-1402',
            department='فناوری اطلاعات',
            assigned_recruiter=self.recruiter,
            workflow=self.workflow,
            status=JobOpportunity.STATUS_PLANNING,
            description='برنامه‌نویس مسلط به جنگو'
        )
        
        # Verify stages are copied
        job_stages = JobOpportunityStage.objects.filter(job=job).order_by('sequence')
        self.assertEqual(job_stages.count(), 2)
        self.assertEqual(job_stages[0].name, 'آزمون کتبی')
        self.assertEqual(job_stages[0].weight, 40)
        self.assertEqual(job_stages[1].name, 'مصاحبه حضوری')
        self.assertEqual(job_stages[1].weight, 60)

    def test_formset_validation_weight_sum(self):
        """تست اعتبارسنجی فرم‌ست به نحوی که مجموع وزن مراحل باید دقیقاً ۱۰۰٪ باشد"""
        job = JobOpportunity.objects.create(
            request_number='REQ-1402-006',
            title='طراح رابط کاربری',
            code='UI-1402',
            department='طراحی',
            description='طراح UI/UX'
        )
        
        # Scenario 1: Total weight is 90% (Invalid)
        data = {
            'stages-TOTAL_FORMS': '2',
            'stages-INITIAL_FORMS': '0',
            'stages-MIN_NUM_FORMS': '0',
            'stages-MAX_NUM_FORMS': '1000',
            'stages-0-name': 'آزمون عملی',
            'stages-0-weight': '40',
            'stages-0-sequence': '1',
            'stages-1-name': 'مصاحبه فنی',
            'stages-1-weight': '50',
            'stages-1-sequence': '2',
        }
        formset = JobOpportunityFormSet(data, instance=job)
        self.assertFalse(formset.is_valid())

        # Scenario 2: Total weight is 100% (Valid)
        data_valid = {
            'stages-TOTAL_FORMS': '2',
            'stages-INITIAL_FORMS': '0',
            'stages-MIN_NUM_FORMS': '0',
            'stages-MAX_NUM_FORMS': '1000',
            'stages-0-name': 'آزمون عملی',
            'stages-0-weight': '40',
            'stages-0-sequence': '1',
            'stages-1-name': 'مصاحبه فنی',
            'stages-1-weight': '60',
            'stages-1-sequence': '2',
        }
        formset_valid = JobOpportunityFormSet(data_valid, instance=job)
        self.assertTrue(formset_valid.is_valid())

    def test_soft_delete_job_opportunity(self):
        """تست حذف نرم فرصت‌های شغلی بدون حذف فیزیکی از دیتابیس"""
        job = JobOpportunity.objects.create(
            request_number='REQ-1402-007',
            title='مدیر پروژه',
            code='PM-1402',
            department='مدیریت',
            description='مدیر پروژه چابک'
        )
        
        job_pk = job.pk
        job.delete() # Soft delete
        
        # Verify not accessible via default objects manager
        self.assertFalse(JobOpportunity.objects.filter(pk=job_pk).exists())
        # Verify accessible via all_objects manager and is_deleted is True
        job_from_db = JobOpportunity.all_objects.get(pk=job_pk)
        self.assertTrue(job_from_db.is_deleted)
        self.assertIsNotNone(job_from_db.deleted_at)

    def test_jalali_date_template_filter(self):
        """تست عملکرد صحیح فیلتر تبدیل تاریخ به شمسی"""
        gregorian_date = date(2026, 6, 4)
        jalali_str = to_jalali(gregorian_date)
        self.assertEqual(jalali_str, '1405/03/14') # 2026-06-04 is 1405-03-14 in Jalali

        gregorian_datetime = datetime(2026, 6, 4, 15, 30)
        jalali_datetime_str = to_jalali(gregorian_datetime)
        self.assertEqual(jalali_datetime_str, '1405/03/14 - 15:30')

    def test_job_form_jalali_date_input_handling(self):
        """تست دریافت تاریخ شمسی از ورودی فرم و تبدیل صحیح آن به تاریخ میلادی برای ذخیره‌سازی"""
        form_data = {
            'request_number': 'REQ-1405-100',
            'title': 'کارشناس DevOps',
            'code': 'DEVOPS-01',
            'department': 'مهندسی زیرساخت',
            'unit': 'کلود',
            'headcount': '1',
            'recruitment_type': 'EXTERNAL',
            'status': 'PLANNING',
            'start_date': '1405/03/14',  # Jalali for 2026-06-04
            'end_date': '1405/04/14',    # Jalali for 2026-07-04
            'description': 'شرح وظایف کارشناس دیواپس',
        }
        form = JobOpportunityForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        job = form.save()

        # Check that stored date is Gregorian
        self.assertEqual(job.start_date, date(2026, 6, 4))
        self.assertEqual(job.end_date, date(2026, 7, 5))

    def test_workflow_template_crud_views(self):
        """تست ویوها و فرآیند ایجاد و مدیریت الگوهای فرآیند استخدام"""
        self.client.login(username='recruiter_test', password='password123')
        
        # Test List view
        response = self.client.get(reverse('workflow_list'))
        self.assertEqual(response.status_code, 200)
        
        # Test Create view
        data = {
            'name': 'الگوی برنامه‌نویس ارشد',
            'description': 'مراحل استاندارد جذب برنامه‌نویس ارشد',
            'stages-TOTAL_FORMS': '2',
            'stages-INITIAL_FORMS': '0',
            'stages-MIN_NUM_FORMS': '0',
            'stages-MAX_NUM_FORMS': '1000',
            'stages-0-name': 'مصاحبه فنی اولیه',
            'stages-0-default_weight': '50',
            'stages-0-sequence': '1',
            'stages-1-name': 'کانون ارزیابی تخصصی',
            'stages-1-default_weight': '50',
            'stages-1-sequence': '2',
        }
        response = self.client.post(reverse('workflow_add'), data)
        self.assertEqual(response.status_code, 302) # Redirects to list on success
        
        # Verify database
        wf = WorkflowTemplate.objects.get(name='الگوی برنامه‌نویس ارشد')
        self.assertEqual(wf.stages.count(), 2)

    def test_job_export_excel(self):
        """تست خروجی اکسل فرصت‌های شغلی"""
        # Create a job opportunity
        JobOpportunity.objects.create(
            request_number='REQ-1402-009',
            title='برنامه‌نویس فرانت‌اند',
            code='FE-1402',
            department='فناوری اطلاعات',
            assigned_recruiter=self.recruiter,
            workflow=self.workflow,
            status=JobOpportunity.STATUS_PLANNING,
            description='مسلط به ری‌اکت'
        )

        self.client.login(username='recruiter_test', password='password123')
        response = self.client.get(reverse('job_export_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertTrue(len(response.content) > 0)

    def test_job_category_saving(self):
        """تست ثبت و ویرایش فیلد رده شغلی در فرصت‌های شغلی"""
        job = JobOpportunity.objects.create(
            request_number='REQ-1402-999',
            title='مدیر فنی',
            code='PM-999',
            department='فناوری اطلاعات',
            job_category='کارشناس',
            description='مدیریت تیم توسعه'
        )
        self.assertEqual(job.job_category, 'کارشناس')

        # Test through form
        form_data = {
            'request_number': 'REQ-1405-101',
            'title': 'کارشناس هوش مصنوعی ارشد',
            'code': 'AI-02',
            'department': 'مهندسی داده',
            'unit': 'هوش مصنوعی',
            'job_category': 'کارشناس مسئول',
            'headcount': '1',
            'recruitment_type': 'EXTERNAL',
            'status': 'PLANNING',
            'description': 'مسلط به پایتون',
        }
        form = JobOpportunityForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        job_from_form = form.save()
        self.assertEqual(job_from_form.job_category, 'کارشناس مسئول')

    def test_job_print_doc_view(self):
        """تست نمایش صفحه چاپ سند آزمون به همراه جزئیات برنامه‌ریزی جذب"""
        job = JobOpportunity.objects.create(
            request_number='REQ-1402-991',
            title='مدیر مالی',
            code='FIN-991',
            department='مالی',
            description='مدیریت امور مالی'
        )
        stage = JobOpportunityStage.objects.create(
            job=job,
            name='غربالگری اولیه',
            weight=100,
            sequence=1,
            stage_type='SCREENING'
        )

        self.client.login(username='recruiter_test', password='password123')
        
        # Scenario 1: Without recruitment plan
        url = reverse('job_print_doc', kwargs={'pk': job.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'تاریخ شروع جذب (برنامه‌ریزی)')

        # Scenario 2: With recruitment plan
        from apps.recruitment_planning.models import JobRecruitmentPlan, JobStagePlan
        plan = JobRecruitmentPlan.objects.create(
            job=job,
            start_date=date(2026, 6, 8),
            predicted_end_date=date(2026, 6, 15),
            status=JobRecruitmentPlan.STATUS_ACTIVE
        )
        JobStagePlan.objects.create(
            plan=plan,
            stage=stage,
            stage_type='SCREENING',
            planned_start_date=date(2026, 6, 8),
            planned_end_date=date(2026, 6, 13),
            sla_days=5
        )

        response_with_plan = self.client.get(url)
        self.assertEqual(response_with_plan.status_code, 200)
        self.assertContains(response_with_plan, 'تاریخ شروع جذب (برنامه‌ریزی)')
        self.assertContains(response_with_plan, '1405/03/18') # 2026-06-08 is 1405-03-18
        self.assertContains(response_with_plan, '1405/03/23') # 2026-06-13 is 1405-03-23

    def test_job_opportunity_empty_stages_assigned_workflow(self):
        """تست اختصاص مراحل پیش‌فرض به فرصت شغلی ویرایش شده که فاقد مرحله بوده است"""
        # Create job opportunity with NO workflow template
        job = JobOpportunity.objects.create(
            request_number='REQ-TEST-001',
            title='برنامه‌نویس بک‌اند',
            code='BE-1402',
            department='فناوری',
            description='طراح وب'
        )
        self.assertEqual(job.stages.count(), 0)

        # Assign workflow template to the job and save
        job.workflow = self.workflow
        job.save()

        # Check if workflow stages are replicated
        self.assertEqual(job.stages.filter(is_deleted=False).count(), 2)

    def test_job_opportunity_update_workflow_template(self):
        """تست بروزرسانی الگوی فرآیند فرصت شغلی در نمای ویرایش و بازنشانی صحیح مراحل"""
        # Create standard workflow
        another_workflow = WorkflowTemplate.objects.create(
            name='فرآیند جایگزین',
            description='یک مرحله مصاحبه'
        )
        WorkflowStageTemplate.objects.create(
            workflow=another_workflow,
            name='مصاحبه مدیر عامل',
            default_weight=100,
            sequence=1
        )

        job = JobOpportunity.objects.create(
            request_number='REQ-TEST-002',
            title='کارشناس سیستم',
            code='SYS-1402',
            department='فناوری',
            workflow=self.workflow,
            description='ادمین شبکه'
        )
        self.assertEqual(job.stages.filter(is_deleted=False).count(), 2)

        self.client.login(username='recruiter_test', password='password123')
        
        # Post request to change workflow template to another_workflow
        url = reverse('job_edit', kwargs={'pk': job.pk})
        form_data = {
            'request_number': 'REQ-TEST-002',
            'title': 'کارشناس سیستم',
            'code': 'SYS-1402',
            'department': 'فناوری',
            'workflow': another_workflow.id,
            'headcount': 1,
            'recruitment_type': 'EXTERNAL',
            'status': 'PLANNING',
            'stages-TOTAL_FORMS': '2',
            'stages-INITIAL_FORMS': '2',
            'stages-MIN_NUM_FORMS': '0',
            'stages-MAX_NUM_FORMS': '1000',
            # Old stages in the formset (simulated from HTML rendering)
            'stages-0-id': job.stages.all()[0].id,
            'stages-0-name': 'آزمون کتبی',
            'stages-0-weight': '40',
            'stages-0-sequence': '1',
            'stages-1-id': job.stages.all()[1].id,
            'stages-1-name': 'مصاحبه حضوری',
            'stages-1-weight': '60',
            'stages-1-sequence': '2',
        }
        
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 302)

        # Verify stages are reset and updated to the new template's stage (مصاحبه مدیر عامل)
        job.refresh_from_db()
        self.assertEqual(job.workflow, another_workflow)
        active_stages = job.stages.filter(is_deleted=False)
        self.assertEqual(active_stages.count(), 1)
        self.assertEqual(active_stages[0].name, 'مصاحبه مدیر عامل')


class JobOpportunityReportTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='report_recruiter', password='password123')
        self.recruiter.profile.role = 'RECRUITMENT_SPECIALIST'
        self.recruiter.profile.save()

        self.job = JobOpportunity.objects.create(
            request_number='REQ-REPORT-01',
            title='مهندس صنایع',
            code='IND-01',
            department='تولید',
            assigned_recruiter=self.recruiter,
            status=JobOpportunity.STATUS_INTERVIEW,
            description='شرح مهندس صنایع'
        )
        self.stage = JobOpportunityStage.objects.create(
            job=self.job,
            name='مصاحبه عمومی',
            weight=100,
            sequence=1,
            stage_type='INTERVIEW'
        )

        # Create Candidates and Job Applications
        from apps.candidates.models import Candidate, JobApplication, ApplicationStageState
        
        self.cand1 = Candidate.objects.create(first_name='علی', last_name='علوی', national_id='1111111111', phone_number='09121111111')
        self.cand2 = Candidate.objects.create(first_name='رضا', last_name='رضایی', national_id='2222222222', phone_number='09122222222')

        self.app1 = JobApplication.objects.create(job=self.job, candidate=self.cand1, status='SELECTED', final_score=85.0)
        self.app2 = JobApplication.objects.create(job=self.job, candidate=self.cand2, status='IN_PROGRESS', final_score=60.0)

    def test_job_opportunity_report_anonymous_redirect(self):
        """تست اینکه کاربران وارد نشده به صفحه لاگین هدایت می‌شوند"""
        url = reverse('job_opportunity_report', kwargs={'pk': self.job.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_job_opportunity_report_authorized_user(self):
        """تست مشاهده شناسنامه فرصت شغلی توسط کاربر مجاز"""
        self.client.login(username='report_recruiter', password='password123')
        url = reverse('job_opportunity_report', kwargs={'pk': self.job.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_report.html')
        self.assertContains(response, 'مهندس صنایع')
        self.assertContains(response, 'IND-01')
        # Check context
        self.assertEqual(response.context['total_registered'], 2)
        self.assertEqual(response.context['status_counts']['selected'], 1)
        self.assertEqual(response.context['status_counts']['inprogress'], 1)

    def test_job_opportunity_report_no_assigned_recruiter(self):
        """تست مشاهده شناسنامه فرصت شغلی زمانی که کارشناس جذب مسئول مشخص نشده است (None)"""
        self.job.assigned_recruiter = None
        self.job.save()
        
        self.client.login(username='report_recruiter', password='password123')
        url = reverse('job_opportunity_report', kwargs={'pk': self.job.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_report.html')
        self.assertContains(response, 'مهندس صنایع')
        # Checks that the null recruiter is rendered as "-"
        self.assertContains(response, '-')


class JobOpportunityBulkStatusTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='bulk_admin', password='password123')
        self.admin_user.profile.role = 'ADMIN'
        self.admin_user.profile.save()
        
        self.normal_user = User.objects.create_user(username='bulk_normal', password='password123')
        self.normal_user.profile.role = 'INTERVIEWER'  # Not authorized to manage jobs
        self.normal_user.profile.save()

        self.job1 = JobOpportunity.objects.create(
            request_number='REQ-BULK-01', title='برنامه‌نویس', code='DEV-BULK-01',
            department='فناوری', status=JobOpportunity.STATUS_PUBLISHED
        )
        self.job2 = JobOpportunity.objects.create(
            request_number='REQ-BULK-02', title='مدیر پروژه', code='PM-BULK-02',
            department='فناوری', status=JobOpportunity.STATUS_PUBLISHED
        )

    def test_bulk_status_update_anonymous_redirect(self):
        url = reverse('job_bulk_status_update')
        response = self.client.post(url, {'job_codes': 'DEV-BULK-01', 'new_status': 'SUSPENDED'})
        self.assertEqual(response.status_code, 302)

    def test_bulk_status_update_unauthorized_user(self):
        self.client.login(username='bulk_normal', password='password123')
        url = reverse('job_bulk_status_update')
        response = self.client.post(url, {'job_codes': 'DEV-BULK-01', 'new_status': 'SUSPENDED'})
        self.assertEqual(response.status_code, 403)

    def test_bulk_status_update_success(self):
        self.client.login(username='bulk_admin', password='password123')
        url = reverse('job_bulk_status_update')
        response = self.client.post(url, {
            'job_codes': 'DEV-BULK-01, PM-BULK-02\nINVALID-CODE',
            'new_status': 'SUSPENDED'
        })
        self.assertEqual(response.status_code, 302)
        
        self.job1.refresh_from_db()
        self.job2.refresh_from_db()
        self.assertEqual(self.job1.status, JobOpportunity.STATUS_SUSPENDED)
        self.assertEqual(self.job2.status, JobOpportunity.STATUS_SUSPENDED)


class JobOpportunitySortingTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='sorting_recruiter', password='password123')
        self.recruiter.profile.role = 'RECRUITMENT_SPECIALIST'
        self.recruiter.profile.save()

        # Create opportunities with different attributes
        self.job_a = JobOpportunity.objects.create(
            request_number='REQ-SORT-A', title='A_Python Developer', code='DEV-A',
            department='Tech', headcount=5, status=JobOpportunity.STATUS_RECEIVED
        )
        self.job_b = JobOpportunity.objects.create(
            request_number='REQ-SORT-B', title='B_Project Manager', code='DEV-B',
            department='Biz', headcount=2, status=JobOpportunity.STATUS_PLANNING
        )
        self.job_c = JobOpportunity.objects.create(
            request_number='REQ-SORT-C', title='C_QA Engineer', code='DEV-C',
            department='Tech', headcount=1, status=JobOpportunity.STATUS_PUBLISHED
        )

    def test_sorting_by_code_asc(self):
        self.client.login(username='sorting_recruiter', password='password123')
        url = reverse('job_list') + '?sort=code&order=asc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        jobs = list(response.context['jobs'])
        self.assertEqual([j.code for j in jobs], ['DEV-A', 'DEV-B', 'DEV-C'])

    def test_sorting_by_title_desc(self):
        self.client.login(username='sorting_recruiter', password='password123')
        url = reverse('job_list') + '?sort=title&order=desc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        jobs = list(response.context['jobs'])
        self.assertEqual([j.title for j in jobs], ['C_QA Engineer', 'B_Project Manager', 'A_Python Developer'])

    def test_sorting_by_headcount_asc(self):
        self.client.login(username='sorting_recruiter', password='password123')
        url = reverse('job_list') + '?sort=headcount&order=asc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        jobs = list(response.context['jobs'])
        self.assertEqual([j.headcount for j in jobs], [1, 2, 5])


class JobOpportunityDeletionAndReuseTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='delete_recruiter', password='password123')
        self.recruiter.profile.role = 'RECRUITMENT_SPECIALIST'
        self.recruiter.profile.save()
        self.client.login(username='delete_recruiter', password='password123')

        from apps.candidates.models import Candidate, JobApplication
        self.Candidate = Candidate
        self.JobApplication = JobApplication

    def test_reusing_code_and_request_number_after_deletion(self):
        """تست استفاده مجدد از کد و شماره درخواست پس از حذف نرم"""
        job1 = JobOpportunity.objects.create(
            request_number='REQ-REUSE-01',
            title='شغل اول',
            code='CODE-REUSE-01',
            department='فناوری'
        )
        job1.delete()

        # Should be able to create a new one with same fields
        try:
            job2 = JobOpportunity.objects.create(
                request_number='REQ-REUSE-01',
                title='شغل دوم',
                code='CODE-REUSE-01',
                department='فناوری'
            )
        except Exception as e:
            self.fail(f"Could not create job with reused code/request_number: {e}")

        self.assertEqual(JobOpportunity.objects.filter(code='CODE-REUSE-01').count(), 1)
        self.assertEqual(JobOpportunity.all_objects.filter(code='CODE-REUSE-01').count(), 2)

    def test_active_jobs_cannot_have_duplicate_code_or_request_number(self):
        """تست عدم امکان ثبت دو فرصت شغلی فعال با کد یا شماره درخواست یکسان"""
        from django.db import IntegrityError, transaction

        JobOpportunity.objects.create(
            request_number='REQ-DUP-01',
            title='شغل فعال',
            code='CODE-DUP-01',
            department='فناوری'
        )

        # Test duplicate code
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobOpportunity.objects.create(
                    request_number='REQ-DUP-02',
                    title='شغل دیگر با همان کد',
                    code='CODE-DUP-01',
                    department='فناوری'
                )

        # Test duplicate request_number
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobOpportunity.objects.create(
                    request_number='REQ-DUP-01',
                    title='شغل دیگر با همان شماره درخواست',
                    code='CODE-DUP-02',
                    department='فناوری'
                )

    def test_delete_job_and_keep_exclusive_candidates(self):
        """تست حذف فرصت شغلی و حفظ متقاضیان اختصاصی در بانک استعدادها"""
        job = JobOpportunity.objects.create(
            request_number='REQ-DEL-K',
            title='تست حذف و حفظ',
            code='CODE-DEL-K',
            department='فناوری'
        )
        candidate = self.Candidate.objects.create(
            first_name='حسن',
            last_name='رضایی',
            national_id='1111111112',
            phone_number='09121111112'
        )
        app = self.JobApplication.objects.create(job=job, candidate=candidate)

        url = reverse('job_delete', kwargs={'pk': job.pk})
        response = self.client.post(url, {'cleanup_option': 'keep'})
        self.assertEqual(response.status_code, 200)

        # Job and Application should be soft-deleted
        self.assertTrue(JobOpportunity.all_objects.get(pk=job.pk).is_deleted)
        self.assertTrue(self.JobApplication.all_objects.get(pk=app.pk).is_deleted)
        # Candidate should NOT be deleted
        candidate.refresh_from_db()
        self.assertFalse(candidate.is_deleted)

    def test_delete_job_and_delete_exclusive_candidates(self):
        """تست حذف فرصت شغلی و حذف متقاضیان اختصاصی آن"""
        job = JobOpportunity.objects.create(
            request_number='REQ-DEL-D',
            title='تست حذف و حذف متقاضی',
            code='CODE-DEL-D',
            department='فناوری'
        )
        candidate = self.Candidate.objects.create(
            first_name='حسین',
            last_name='احمدی',
            national_id='1111111113',
            phone_number='09121111113'
        )
        app = self.JobApplication.objects.create(job=job, candidate=candidate)

        url = reverse('job_delete', kwargs={'pk': job.pk})
        response = self.client.post(url, {'cleanup_option': 'delete_exclusive'})
        self.assertEqual(response.status_code, 200)

        # Job, Application and Candidate should be soft-deleted
        self.assertTrue(JobOpportunity.all_objects.get(pk=job.pk).is_deleted)
        self.assertTrue(self.JobApplication.all_objects.get(pk=app.pk).is_deleted)
        
        # Candidate profile is soft-deleted
        candidate_from_db = self.Candidate.all_objects.get(pk=candidate.pk)
        self.assertTrue(candidate_from_db.is_deleted)

    def test_delete_job_does_not_delete_non_exclusive_candidates(self):
        """تست اینکه حذف فرصت شغلی با انتخاب حذف متقاضیان، متقاضیانی که درخواست دیگری دارند را حذف نمی‌کند"""
        job1 = JobOpportunity.objects.create(
            request_number='REQ-DEL-N1',
            title='تست حذف غیر اختصاصی ۱',
            code='CODE-DEL-N1',
            department='فناوری'
        )
        job2 = JobOpportunity.objects.create(
            request_number='REQ-DEL-N2',
            title='تست حذف غیر اختصاصی ۲',
            code='CODE-DEL-N2',
            department='فناوری'
        )
        candidate = self.Candidate.objects.create(
            first_name='جعفر',
            last_name='عباسی',
            national_id='1111111114',
            phone_number='09121111114'
        )
        app1 = self.JobApplication.objects.create(job=job1, candidate=candidate)
        app2 = self.JobApplication.objects.create(job=job2, candidate=candidate)

        url = reverse('job_delete', kwargs={'pk': job1.pk})
        response = self.client.post(url, {'cleanup_option': 'delete_exclusive'})
        self.assertEqual(response.status_code, 200)

        # Job1 and App1 should be soft-deleted
        self.assertTrue(JobOpportunity.all_objects.get(pk=job1.pk).is_deleted)
        self.assertTrue(self.JobApplication.all_objects.get(pk=app1.pk).is_deleted)

        # Job2 and App2 should NOT be deleted
        self.assertFalse(JobOpportunity.all_objects.get(pk=job2.pk).is_deleted)
        self.assertFalse(self.JobApplication.all_objects.get(pk=app2.pk).is_deleted)

        # Candidate should NOT be deleted because they have active application to Job2
        candidate.refresh_from_db()
        self.assertFalse(candidate.is_deleted)



