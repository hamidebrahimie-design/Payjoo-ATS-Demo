from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from functools import wraps
from django.shortcuts import redirect

def role_required(roles):
    """
    دکوراتور برای اعتبارسنجی نقش کاربر در نماهای تابع‌محور.
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if not hasattr(request.user, 'profile') or request.user.profile.role not in roles:
                raise PermissionDenied("شما دسترسی لازم برای مشاهده این صفحه را ندارید.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

class RoleRequiredMixin(UserPassesTestMixin):
    """
    میکسین برای اعتبارسنجی نقش کاربر در نماهای کلاس‌محور.
    """
    allowed_roles = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if not hasattr(self.request.user, 'profile'):
            return False
        # If user is admin, allow bypass or strictly enforce role check
        # Let's enforce that they must have the role or be ADMIN
        from .models import UserProfile
        user_role = self.request.user.profile.role
        return user_role in self.allowed_roles or user_role == UserProfile.ROLE_ADMIN

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        raise PermissionDenied("شما دسترسی لازم برای مشاهده این صفحه را ندارید.")


def check_stage_access(user, stage):
    """
    بررسی دسترسی نقش کاربر به یک مرحله ارزیابی خاص بر اساس نام مرحله.
    - مدیران و کارکنان جذب دسترسی کامل دارند.
    - ارزیابان خارجی (کاربر کانون) فقط به مراحلی که شامل کلمات کلیدی کانون ارزیابی هستند دسترسی دارند.
    - مصاحبه‌گران فقط به مراحلی که شامل مصاحبه یا آزمون هستند و شامل کانون ارزیابی نیستند دسترسی دارند.
    """
    if not user.is_authenticated:
        return False
        
    from apps.accounts.models import UserProfile
    if not hasattr(user, 'profile'):
        return False
        
    profile = user.profile
    
    # ادمین و کادر جذب دسترسی کامل دارند
    if profile.is_recruitment_staff or profile.role == UserProfile.ROLE_ADMIN:
        return True
        
    stage_name_lower = stage.name.lower()
    
    # کلمات کلیدی کانون ارزیابی
    assessment_keywords = ["کانون", "ارزیابی", "assessment", "competency", "سنتر"]
    # کلمات کلیدی مصاحبه و آزمون
    interview_exam_keywords = ["مصاحبه", "آزمون", "امتحان", "کتبی", "screening", "exam", "interview", "test", "فنی", "مهارتی"]
    
    if profile.role == UserProfile.ROLE_EXTERNAL_ASSESSOR:
        # کاربر کانون فقط باید نمره کانون را ببیند/ثبت کند
        return any(kw in stage_name_lower for kw in assessment_keywords)
        
    if profile.role == UserProfile.ROLE_INTERVIEWER:
        # کاربر مصاحبه‌گر/مهارتی فقط مراحل مصاحبه و آزمون را ببیند و نباید کانون را ببیند
        has_intv_kw = any(kw in stage_name_lower for kw in interview_exam_keywords)
        has_asmt_kw = any(kw in stage_name_lower for kw in assessment_keywords)
        return has_intv_kw and not has_asmt_kw
        
    return False

