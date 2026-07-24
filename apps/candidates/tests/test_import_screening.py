"""
تست‌های یکپارچگی ایمپورت نتایج غربالگری - Zero-Risk Protocol
"""
import tempfile, os
import openpyxl
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.jobs.models import JobOpportunity
from apps.candidates.models import Candidate, JobApplication
from apps.candidates.services import dry_run_import_screening, commit_import_screening


class ScreeningImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('testadmin', 'a@a.com', 'pass123')
        self.client = Client()
        self.client.force_login(self.user)

        # Create a job
        self.job = JobOpportunity.objects.create(
            code='9999', title='تست شغل', department='فنی',
            status='SCREENING', headcount=1
        )
        # Create a candidate
        self.candidate = Candidate.objects.create(
            first_name='تست', last_name='تستی', national_id='1111111111'
        )
        # Create application
        self.application = JobApplication.objects.create(
            job=self.job, candidate=self.candidate, status='IN_PROGRESS'
        )

    def _create_excel(self, rows):
        """Create a temp Excel file with given rows."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['Row', 'ExamCode', 'NationCode', 'Result', 'EXP'])
        for r in rows:
            ws.append(r)
        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        wb.save(tmp.name)
        wb.close()
        return tmp.name

    def test_dry_run_valid_data(self):
        """Test 1: Dry-Run with valid data"""
        path = self._create_excel([
            [1, '9999', '1111111111', 'مجاز', 'test reason'],
        ])
        result = dry_run_import_screening(path)
        os.unlink(path)

        self.assertEqual(result['summary']['valid_count'], 1)
        self.assertEqual(result['summary']['invalid_count'], 0)
        self.assertEqual(len(result['valid_rows']), 1)

    def test_dry_run_invalid_exam_code(self):
        """Test 2: Dry-Run with invalid ExamCode"""
        path = self._create_excel([
            [1, 'XXXX', '1111111111', 'مجاز', ''],
        ])
        result = dry_run_import_screening(path)
        os.unlink(path)

        self.assertEqual(result['summary']['valid_count'], 0)
        self.assertEqual(result['summary']['invalid_count'], 1)

    def test_dry_run_invalid_nation_code(self):
        """Test 3: Dry-Run with invalid NationCode"""
        path = self._create_excel([
            [1, '9999', '0000000000', 'غیرمجاز', ''],
        ])
        result = dry_run_import_screening(path)
        os.unlink(path)

        self.assertEqual(result['summary']['valid_count'], 0)
        self.assertEqual(result['summary']['invalid_count'], 1)

    def test_commit_updates_fields(self):
        """Test 4: Commit updates screening_result and screening_reason"""
        rows = [{
            'row': 2, 'exam_code': '9999', 'nation_code': '1111111111',
            'result': 'غیرمجاز', 'reason': 'عدم احراز',
            'application_id': self.application.id,
        }]
        result = commit_import_screening(rows)

        self.assertEqual(result['updated'], 1)
        self.application.refresh_from_db()
        self.assertEqual(self.application.screening_result, 'غیرمجاز')
        self.assertEqual(self.application.screening_reason, 'عدم احراز')

    def test_commit_rollback_on_error(self):
        """Test 5: Commit rollback on invalid application_id"""
        rows = [{
            'row': 2, 'exam_code': '9999', 'nation_code': '1111111111',
            'result': 'مجاز', 'reason': '',
            'application_id': 99999,  # invalid
        }]
        result = commit_import_screening(rows)

        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['failed'], 1)

    def test_view_page_loads(self):
        """Test 6: Import screening page loads"""
        resp = self.client.get('/candidates/import/screening/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'ایمپورت نتایج غربالگری')

    def test_view_dry_run_post(self):
        """Test 7: POST with valid Excel returns dry-run result"""
        path = self._create_excel([
            [1, '9999', '1111111111', 'مجاز', 'ok'],
        ])
        with open(path, 'rb') as f:
            resp = self.client.post('/candidates/import/screening/', {
                'phase': 'dry_run',
                'excel_file': f,
            })
        os.unlink(path)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'نتیجه اعتبارسنجی')
