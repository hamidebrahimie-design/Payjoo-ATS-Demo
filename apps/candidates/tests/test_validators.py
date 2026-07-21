from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.validators import (
    validate_resume_file_size,
    validate_resume_file_extension,
)


class ResumeFileSizeValidatorTests(TestCase):
    """Tests for validate_resume_file_size"""

    def test_invalid_file_size(self):
        """فایل بزرگتر از ۵ مگابایت باید ValidationError بدهد"""
        # Create a dummy file > 5MB
        large_content = b'x' * (6 * 1024 * 1024)  # 6 MB
        fake_file = SimpleUploadedFile('resume.pdf', large_content, content_type='application/pdf')
        with self.assertRaises(ValidationError):
            validate_resume_file_size(fake_file)

    def test_valid_file_size(self):
        """فایل کوچکتر از ۵ مگابایت باید بدون خطا عبور کند"""
        small_content = b'x' * (1 * 1024 * 1024)  # 1 MB
        fake_file = SimpleUploadedFile('resume.pdf', small_content, content_type='application/pdf')
        try:
            validate_resume_file_size(fake_file)
        except ValidationError:
            self.fail("validate_resume_file_size raised ValidationError for a valid file (1MB).")


class ResumeFileExtensionValidatorTests(TestCase):
    """Tests for validate_resume_file_extension"""

    def test_invalid_file_extension(self):
        """فایل با پسوند .exe باید ValidationError بدهد"""
        fake_file = SimpleUploadedFile('virus.exe', b'small content', content_type='application/x-msdownload')
        with self.assertRaises(ValidationError):
            validate_resume_file_extension(fake_file)

    def test_valid_pdf_extension(self):
        """فایل با پسوند .pdf باید بدون خطا عبور کند"""
        fake_file = SimpleUploadedFile('resume.pdf', b'pdf content', content_type='application/pdf')
        try:
            validate_resume_file_extension(fake_file)
        except ValidationError:
            self.fail("validate_resume_file_extension raised ValidationError for a .pdf file.")

    def test_valid_doc_extension(self):
        """فایل با پسوند .doc باید بدون خطا عبور کند"""
        fake_file = SimpleUploadedFile('resume.doc', b'doc content', content_type='application/msword')
        try:
            validate_resume_file_extension(fake_file)
        except ValidationError:
            self.fail("validate_resume_file_extension raised ValidationError for a .doc file.")

    def test_valid_docx_extension(self):
        """فایل با پسوند .docx باید بدون خطا عبور کند"""
        fake_file = SimpleUploadedFile('resume.docx', b'docx content', content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        try:
            validate_resume_file_extension(fake_file)
        except ValidationError:
            self.fail("validate_resume_file_extension raised ValidationError for a .docx file.")

    def test_uppercase_extension(self):
        """فایل با پسوند .PDF (بزرگ) باید بدون خطا عبور کند"""
        fake_file = SimpleUploadedFile('RESUME.PDF', b'pdf content', content_type='application/pdf')
        try:
            validate_resume_file_extension(fake_file)
        except ValidationError:
            self.fail("validate_resume_file_extension raised ValidationError for .PDF (uppercase).")
