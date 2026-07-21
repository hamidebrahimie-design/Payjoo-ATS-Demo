"""
Custom validators for file uploads and other fields.

Validators in this module raise django.core.exceptions.ValidationError
with user-friendly Persian messages.
"""

import os

from django.core.exceptions import ValidationError


def validate_resume_file_size(value):
    """حداکثر حجم فایل رزومه: ۵ مگابایت"""
    limit_mb = 5
    limit_bytes = limit_mb * 1024 * 1024
    if value.size > limit_bytes:
        raise ValidationError(
            f"حجم فایل رزومه نباید بیشتر از {limit_mb} مگابایت باشد. "
            f"حجم ارسالی شما: {value.size / (1024 * 1024):.1f} مگابایت"
        )


def validate_resume_file_extension(value):
    """فقط فرمت‌های PDF و Word مجاز است"""
    allowed_extensions = ['.pdf', '.doc', '.docx']
    _, ext = os.path.splitext(value.name.lower())
    if ext not in allowed_extensions:
        raise ValidationError(
            "فرمت فایل رزومه باید PDF یا Word (.pdf, .doc, .docx) باشد. "
            f"فرمت ارسالی شما: '{ext}' مجاز نیست."
        )
