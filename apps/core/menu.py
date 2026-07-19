"""
Centralized menu configuration for Payjoo ATS.
Each item defines label, icon, url_name, allowed_roles, and optional children.
"""
from dataclasses import dataclass, field
from typing import Optional
from apps.accounts.models import UserProfile


@dataclass
class MenuItem:
    label: str
    icon: str
    url_name: Optional[str] = None
    url_params: Optional[dict] = None
    allowed_roles: list = field(default_factory=list)  # empty = all roles
    children: list = field(default_factory=list)
    badge: Optional[str] = None
    divider: bool = False
    parent_key: Optional[str] = None


# ─── Menu Structure ──────────────────────────────────────────────

DASHBOARD = MenuItem(label="داشبورد", icon="📊", url_name="dashboard")

JOBS = MenuItem(label="فرصت‌های شغلی", icon="💼", url_name="job_list")
WORKFLOWS = MenuItem(label="الگوهای فرآیند استخدام", icon="🔄", url_name="workflow_list")

CANDIDATES = MenuItem(label="متقاضیان", icon="👥", url_name="candidate_list",
                      url_params={'view': 'candidates'})
CANDIDATES_BY_STAGE = MenuItem(label="پایش به تفکیک مراحل", icon="📋", url_name="candidates_by_stage_list")

PLANNING = MenuItem(label="برنامه‌ریزی جذب", icon="📅", url_name="planning_dashboard")
ANALYTICS = MenuItem(label="داشبورد تحلیلی", icon="📈", url_name="analytics_dashboard")

# ─── Competency Submenu ──────────────────────────────────────────
COMPETENCY_BANK = MenuItem(label="بانک شایستگی‌ها", icon="", url_name="competency_list",
    allowed_roles=[UserProfile.ROLE_ADMIN, UserProfile.ROLE_RECRUITMENT_SPECIALIST])
COMPETENCY_MODELS = MenuItem(label="مدل‌های شایستگی", icon="", url_name="competency_model_list")
COMPETENCY_CUSTOM = MenuItem(label="شایستگی‌های دستی", icon="", url_name="custom_competencies_report")
COMPETENCY_PATTERNS = MenuItem(label="الگوهای شایستگی", icon="", url_name="recruitment_patterns")
COMPETENCY_UPLOAD = MenuItem(label="بارگذاری اکسل", icon="", url_name="competency_upload")

COMPETENCIES = MenuItem(label="شایستگی‌ها", icon="⭐", children=[
    COMPETENCY_BANK, COMPETENCY_MODELS, COMPETENCY_CUSTOM,
    COMPETENCY_PATTERNS, COMPETENCY_UPLOAD,
])

SCORE_ENTRY = MenuItem(label="ثبت و ورود نمرات", icon="📝", url_name="candidate_score_entry")
INTERVIEWS = MenuItem(label="پنل مصاحبه‌ها", icon="🎤", url_name="candidate_interviews")
ASSESSMENT_CENTER = MenuItem(label="کانون ارزیابی (PDF)", icon="📄", url_name="assessment_center_report")

TALENT_POOL = MenuItem(label="بانک استعدادها", icon="🏆", url_name="candidate_list")

# ─── Settings Submenu ────────────────────────────────────────────
PREFERENCES = MenuItem(label="تنظیمات حساب", icon="", url_name="user_preferences")
USERS = MenuItem(label="مدیریت کاربران", icon="", url_name="user_list")
IMPORT = MenuItem(label="ورود اطلاعات قدیمی", icon="", url_name="import_upload")
BACKUP = MenuItem(label="پشتیبان‌گیری", icon="", url_name="system_backup")
DATA_INTEGRITY = MenuItem(label="یکپارچگی داده‌ها", icon="", url_name="data_integrity_dashboard")
AI_SETTING = MenuItem(label="تنظیمات هوش مصنوعی", icon="", url_name="ai_setting")
ORG_SETTING = MenuItem(label="تنظیمات سازمان", icon="", url_name="organization_setting")
AUDIT_LOGS = MenuItem(label="لاگ ممیزی", icon="", url_name="audit_log_list")

SETTINGS = MenuItem(label="تنظیمات سیستم", icon="⚙️", children=[
    PREFERENCES, IMPORT, USERS, BACKUP, DATA_INTEGRITY,
    AI_SETTING, ORG_SETTING, AUDIT_LOGS,
])

# ─── Full Menu ───────────────────────────────────────────────────
MAIN_MENU = [
    DASHBOARD,
    JOBS,
    WORKFLOWS,
    CANDIDATES,
    CANDIDATES_BY_STAGE,
    PLANNING,
    ANALYTICS,
    COMPETENCIES,
    SCORE_ENTRY,
    INTERVIEWS,
    ASSESSMENT_CENTER,
    TALENT_POOL,
    SETTINGS,
]


def get_menu_for_user(user):
    """Return menu items accessible to the given user's role."""
    if not user or not user.is_authenticated:
        return []
    
    role = getattr(user.profile, 'role', None) if hasattr(user, 'profile') else None
    
    def is_allowed(item):
        return not item.allowed_roles or role in item.allowed_roles
    
    menu = []
    for item in MAIN_MENU:
        if not is_allowed(item):
            continue
        if item.children:
            filtered_children = [c for c in item.children if is_allowed(c)]
            if filtered_children:
                menu.append(MenuItem(
                    label=item.label, icon=item.icon,
                    children=filtered_children
                ))
        else:
            menu.append(item)
    return menu


def is_item_active(item, request):
    """Check if a menu item corresponds to the current request path."""
    if not item.url_name:
        return False
    from django.urls import resolve, reverse
    try:
        match = resolve(request.path)
        if match.url_name == item.url_name:
            if item.url_params:
                return all(match.kwargs.get(k) == v for k, v in item.url_params.items())
            return True
    except Exception:
        pass
    return False


def is_any_child_active(items, request):
    """Check if any item in a list matches the current path."""
    for item in items:
        if is_item_active(item, request):
            return True
        if item.children:
            if is_any_child_active(item.children, request):
                return True
    return False
