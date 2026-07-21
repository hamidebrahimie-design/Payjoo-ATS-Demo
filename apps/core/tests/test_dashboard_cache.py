from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse

from apps.accounts.models import UserProfile


class DashboardCacheTests(TestCase):
    """Tests for dashboard caching mechanism"""

    def setUp(self):
        # Clear cache before each test
        cache.clear()

        # Create an admin user with access to dashboard
        self.user = User.objects.create_user(
            username='admin_test',
            password='testpass123',
            is_staff=True
        )
        self.user.profile.role = UserProfile.ROLE_ADMIN
        self.user.profile.save()

        self.client = Client()

    def test_dashboard_populates_cache(self):
        """پس از اولین درخواست به داشبورد، کش باید مقداردهی شود"""
        cache.delete('dashboard_stats_v1_active')
        cache.delete('dashboard_stats_v1_closed')
        self.client.login(username='admin_test', password='testpass123')

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        cached_active = cache.get('dashboard_stats_v1_active')
        self.assertIsNotNone(
            cached_active,
            "Cache key 'dashboard_stats_v1_active' should be populated after first dashboard request"
        )
        self.assertIn('total_jobs', cached_active)
        self.assertIn('active_jobs_count', cached_active)

    def test_dashboard_cache_hit_returns_fast(self):
        """درخواست دوم باید از کش استفاده کند و داده را برگرداند"""
        self.client.login(username='admin_test', password='testpass123')

        # First request: populate cache
        response1 = self.client.get(reverse('dashboard'))
        self.assertEqual(response1.status_code, 200)
        self.assertIsNotNone(cache.get('dashboard_stats_v1_active'))

        # Second request: should use cache
        response2 = self.client.get(reverse('dashboard'))
        self.assertEqual(response2.status_code, 200)

        # Context should have cached data
        self.assertIn('total_jobs', response2.context)
        self.assertIn('active_jobs_count', response2.context)

        # Cache should still be populated
        self.assertIsNotNone(
            cache.get('dashboard_stats_v1_active'),
            "Cache should still be populated after second dashboard request"
        )

    def test_cache_invalidation_on_model_change(self):
        """تغییر در JobApplication باید کش را پاک کند"""
        from apps.jobs.models import JobOpportunity, WorkflowTemplate
        from apps.candidates.models import Candidate, JobApplication

        self.client.login(username='admin_test', password='testpass123')

        # First: populate cache
        self.client.get(reverse('dashboard'))
        self.assertIsNotNone(cache.get('dashboard_stats_v1_active'))

        # Verify cache.delete works on locmem backend
        cache.delete('dashboard_stats_v1_active')
        self.assertIsNone(cache.get('dashboard_stats_v1_active'))

        # Re-populate cache
        self.client.get(reverse('dashboard'))
        self.assertIsNotNone(cache.get('dashboard_stats_v1_active'))

        # Create a job and candidate
        workflow = WorkflowTemplate.objects.create(name='test_workflow')
        job = JobOpportunity.objects.create(
            title='Test Job',
            code='TEST001',
            request_number='1404-TEST-001',
            workflow=workflow,
            status=JobOpportunity.STATUS_PUBLISHED
        )
        candidate = Candidate.objects.create(
            first_name='Test',
            last_name='Candidate',
            phone_number='09120000000',
            national_id='1234567890'
        )

        # Create an application — this should invalidate the cache via save()
        cache_key_active = 'dashboard_stats_v1_active'
        # Verify cache exists before create
        self.assertIsNotNone(cache.get(cache_key_active))
        
        app = JobApplication.objects.create(
            job=job,
            candidate=candidate,
            status=JobApplication.STATUS_IN_PROGRESS
        )

        # Cache should be cleared after JobApplication save
        cached_val = cache.get(cache_key_active)
        if cached_val is not None:
            print(f"DEBUG: cache still has {type(cached_val)} after create")
        self.assertIsNone(
            cached_val,
            "Cache should be invalidated after creating a new JobApplication"
        )
