from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from apps.jobs.models import OrganizationSetting, JobOpportunity
from apps.candidates.models import Candidate
from apps.core.license import verify_license_key, get_system_license_limits, get_license_usage_stats, generate_license_key

class LicenseTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='Password123!'
        )

    def test_generate_and_verify_license(self):
        # 1. Generate license key
        key = generate_license_key(
            licensee="سازمان تست",
            expires_at="2030-01-01",
            max_jobs=15,
            max_candidates=200,
            max_posts=30,
            allowed_domains=["testserver"]
        )

        # 2. Verify license key with valid host
        limits = verify_license_key(key, current_host="testserver")
        self.assertTrue(limits['is_valid'])
        self.assertEqual(limits['licensee'], "سازمان تست")
        self.assertEqual(limits['max_jobs'], 15)
        self.assertEqual(limits['max_candidates'], 200)
        self.assertEqual(limits['max_posts'], 30)
        self.assertEqual(limits['error'], None)

        # 3. Verify license key with invalid host
        limits_invalid_host = verify_license_key(key, current_host="invalidhost.com")
        self.assertFalse(limits_invalid_host['is_valid'])
        self.assertIn("دامنه جاری", limits_invalid_host['error'])

    def test_free_limit_defaults(self):
        # Empty license key
        limits = verify_license_key("")
        self.assertFalse(limits['is_valid'])
        self.assertEqual(limits['max_jobs'], 5)
        self.assertEqual(limits['max_candidates'], 50)
        self.assertEqual(limits['max_posts'], 10)
