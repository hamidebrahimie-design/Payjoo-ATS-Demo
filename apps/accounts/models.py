from django.db import models
from django.contrib.auth.models import User
from apps.core.models import SoftDeleteModel

class UserProfile(SoftDeleteModel):
    ROLE_RECRUITMENT_DIRECTOR = 'RECRUITMENT_DIRECTOR'
    ROLE_RECRUITMENT_SPECIALIST = 'RECRUITMENT_SPECIALIST'
    ROLE_DEPARTMENT_USER = 'DEPARTMENT_USER'
    ROLE_JOB_CLASSIFICATION_USER = 'JOB_CLASSIFICATION_USER'
    ROLE_INTERVIEWER = 'INTERVIEWER'
    ROLE_EXTERNAL_ASSESSOR = 'EXTERNAL_ASSESSOR'
    ROLE_READ_ONLY_AUDITOR = 'READ_ONLY_AUDITOR'
    ROLE_ADMIN = 'ADMIN'
    ROLE_CANDIDATE = 'CANDIDATE'

    ROLE_CHOICES = [
        (ROLE_RECRUITMENT_DIRECTOR, 'مدیر کل جذب و استخدام'),
        (ROLE_RECRUITMENT_SPECIALIST, 'کارشناس جذب و استخدام'),
        (ROLE_DEPARTMENT_USER, 'کاربر دپارتمان'),
        (ROLE_JOB_CLASSIFICATION_USER, 'کاربر طبقه‌بندی مشاغل'),
        (ROLE_INTERVIEWER, 'مصاحبه‌گر'),
        (ROLE_EXTERNAL_ASSESSOR, 'ارزیاب خارجی'),
        (ROLE_READ_ONLY_AUDITOR, 'حسابرس فقط‌خواندنی'),
        (ROLE_ADMIN, 'مدیر سیستم'),
        (ROLE_CANDIDATE, 'متقاضی'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="کاربر")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_INTERVIEWER, verbose_name="نقش")
    is_external = models.BooleanField(default=False, verbose_name="ارزیاب خارجی")
    phone_number = models.CharField(max_length=15, blank=True, verbose_name="شماره تماس")

    class Meta:
        verbose_name = "پروفایل کاربر"
        verbose_name_plural = "پروفایل‌های کاربران"

    def save(self, *args, **kwargs):
        if self.role == self.ROLE_EXTERNAL_ASSESSOR:
            self.is_external = True
        super().save(*args, **kwargs)

    @property
    def can_manage_jobs(self):
        return self.role in [
            self.ROLE_ADMIN,
            self.ROLE_RECRUITMENT_DIRECTOR,
            self.ROLE_RECRUITMENT_SPECIALIST,
            self.ROLE_JOB_CLASSIFICATION_USER
        ]

    @property
    def is_recruitment_staff(self):
        return self.role in [
            self.ROLE_ADMIN,
            self.ROLE_RECRUITMENT_DIRECTOR,
            self.ROLE_RECRUITMENT_SPECIALIST
        ]

    @property
    def can_enter_exam_scores(self):
        return self.role in [
            self.ROLE_ADMIN,
            self.ROLE_RECRUITMENT_SPECIALIST,
            self.ROLE_RECRUITMENT_DIRECTOR
        ]

    @property
    def can_view_interviews(self):
        return self.role in [
            self.ROLE_ADMIN,
            self.ROLE_INTERVIEWER,
            self.ROLE_EXTERNAL_ASSESSOR,
            self.ROLE_RECRUITMENT_SPECIALIST,
            self.ROLE_RECRUITMENT_DIRECTOR
        ]

    @property
    def can_view_audit_logs(self):
        return self.role in [
            self.ROLE_ADMIN,
            self.ROLE_READ_ONLY_AUDITOR
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"
