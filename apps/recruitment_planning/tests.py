import datetime
import jdatetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.jobs.models import JobOpportunity, JobOpportunityStage, WorkflowTemplate, WorkflowStageTemplate
from .models import StageTypeConfiguration, Holiday, JobRecruitmentPlan, JobStagePlan
from .utils import (
    add_working_days, get_next_working_day, 
    parse_jalali_to_gregorian, to_jalali_string,
    calculate_recruitment_schedule, get_jalali_month_range
)

class RecruitmentPlanningTests(TestCase):

    def setUp(self):
        # Create administrative users
        self.admin_user = User.objects.create_user(username='admin_planning', password='testpassword123')
        self.admin_user.profile.role = UserProfile.ROLE_ADMIN
        self.admin_user.profile.save()

        # Create stages type config
        self.config_screening = StageTypeConfiguration.objects.create(
            stage_type='SCREENING',
            default_sla_days=5,
            monthly_capacity=50
        )
        self.config_exam = StageTypeConfiguration.objects.create(
            stage_type='EXAM',
            default_sla_days=10,
            monthly_capacity=20
        )

        # Create workflow template
        self.workflow = WorkflowTemplate.objects.create(name='Planning Workflow')
        self.stage_template_1 = WorkflowStageTemplate.objects.create(
            workflow=self.workflow,
            name='غربالگری اولیه',
            sequence=1,
            stage_type='SCREENING'
        )
        self.stage_template_2 = WorkflowStageTemplate.objects.create(
            workflow=self.workflow,
            name='آزمون کتبی',
            sequence=2,
            stage_type='EXAM'
        )

        # Create Job Opportunities
        self.job1 = JobOpportunity.objects.create(
            title='برنامه‌نویس پایتون',
            code='PYTHON-01',
            request_number='REQ-PLAN-01',
            department='فنی',
            headcount=15,
            workflow=self.workflow
        )
        self.job2 = JobOpportunity.objects.create(
            title='طراح رابط کاربری',
            code='UI-01',
            request_number='REQ-PLAN-02',
            department='هنری',
            headcount=10,
            workflow=self.workflow
        )

    def test_working_days_and_holidays_calculation(self):
        """تست عبور از جمعه‌ها و روزهای تعطیل ثبت‌شده در دیتابیس"""
        # 1405/03/16 is Friday (2026-06-06)
        # 1405/03/17 is Saturday (2026-06-07)
        # 1405/03/18 is Sunday (2026-06-08)
        
        start_date = datetime.date(2026, 6, 5) # Friday (1405/03/15)
        
        # Define a custom holiday on Sunday 2026-06-07 (1405/03/17)
        Holiday.objects.create(date=datetime.date(2026, 6, 7), title='تست تعطیلی')
        
        # Add 2 working days starting from Friday:
        # Day 1: Saturday (2026-06-06) is a working day
        # Sunday (2026-06-07) is a holiday -> skipped
        # Day 2: Monday (2026-06-08) is a working day
        # Result should be Monday (2026-06-08)
        end_date = add_working_days(start_date, 2)
        self.assertEqual(end_date, datetime.date(2026, 6, 8))

    def test_capacity_overflow_triggers_monthly_shift(self):
        """تست انتقال خودکار برنامه به ماه بعد در صورت تکمیل ظرفیت ماه جاری"""
        # Set monthly capacity limit of EXAM to 20
        # Job 1 has headcount 15 (occupies 15 slots of EXAM capacity in Mehr 1405)
        # Job 2 has headcount 10 (needs 10 slots of EXAM. 15 + 10 = 25 > 20 -> should trigger shift!)
        
        start_date = datetime.date(2026, 9, 23) # 1405/07/01 (Mehr start)
        
        # 1. Schedule Job 1
        schedule1 = calculate_recruitment_schedule(self.job1, start_date)
        # Save Job 1 plan to DB so it consumes capacity
        plan1 = JobRecruitmentPlan.objects.create(
            job=self.job1,
            start_date=start_date,
            predicted_end_date=schedule1[-1]['planned_end_date'],
            status=JobRecruitmentPlan.STATUS_ACTIVE
        )
        for s in schedule1:
            JobStagePlan.objects.create(
                plan=plan1,
                stage=s['stage'],
                stage_type=s['stage_type'],
                planned_start_date=s['planned_start_date'],
                planned_end_date=s['planned_end_date'],
                sla_days=s['sla_days'],
                capacity_shifted=s['capacity_shifted']
            )
            
        # 2. Schedule Job 2 starting at same date
        schedule2 = calculate_recruitment_schedule(self.job2, start_date)
        
        # The screening stage for Job 2 is OK (capacity screening is 50, consumes 10 + 15 = 25 <= 50)
        # The exam stage for Job 2 has capacity limit 20. Consumed is 15. Adding 10 exceeds 20.
        # So Job 2's exam stage should have capacity_shifted=True and be moved to Aban month (1405/08/01 onwards)
        exam_stage_plan = next(s for s in schedule2 if s['stage_type'] == 'EXAM')
        self.assertTrue(exam_stage_plan['capacity_shifted'])
        
        # Check that its planned_start_date is in Aban 1405 (Gregorian after 2026-10-23)
        j_planned_start = jdatetime.date.fromgregorian(date=exam_stage_plan['planned_start_date'])
        self.assertEqual(j_planned_start.month, 8) # Aban (month 8)

    def test_planning_views_and_dashboards(self):
        """تست عملکرد صفحات و ارسال فرم‌ها در ماژول برنامه‌ریزی"""
        self.client.login(username='admin_planning', password='testpassword123')

        # 1. Access Dashboard
        response = self.client.get(reverse('planning_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'برنامه‌ریزی و ظرفیت‌سنجی جذب')

        # 2. Preview schedule for Job 1 via HTMX
        url = reverse('job_planning', kwargs={'job_id': self.job1.id})
        post_data = {
            'action': 'preview',
            'start_date': '1405/02/01'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'پیش‌بینی اتمام فرآیند جذب')

        # 3. Save schedule plan
        post_data['action'] = 'save'
        response = self.client.post(url, post_data)
        # Should redirect to dashboard (or return JS script redirecting)
        self.assertEqual(response.status_code, 200)
        self.assertIn('window.location.href', response.content.decode('utf-8'))

        # Check plan is saved in DB
        self.assertTrue(JobRecruitmentPlan.objects.filter(job=self.job1, status='ACTIVE').exists())

        # 4. Access and Save configs view
        config_url = reverse('planning_config')
        response = self.client.get(config_url)
        self.assertEqual(response.status_code, 200)

        # Save config update post
        post_config = {
            'action': 'save_configs',
            'sla_SCREENING': '6',
            'capacity_SCREENING': '60'
        }
        response = self.client.post(config_url, post_config)
        self.assertEqual(response.status_code, 302) # Redirects back to config view
        
        self.config_screening.refresh_from_db()
        self.assertEqual(self.config_screening.default_sla_days, 6)
        self.assertEqual(self.config_screening.monthly_capacity, 60)
