import hmac
import hashlib
import json
import base64
from datetime import datetime, date
from django.conf import settings

LICENSE_SECRET_KEY = getattr(settings, 'PAYJOO_LICENSE_SECRET_KEY', 'payjoo_ats_licensing_sec_2026').encode('utf-8')

FREE_LIMIT_JOBS = 5
FREE_LIMIT_CANDIDATES = 50
FREE_LIMIT_POSTS = 10

def get_machine_id():
    """
    Generates a unique hardware identifier for the current machine based on MAC address.
    """
    import uuid
    import hashlib
    try:
        mac_num = uuid.getnode()
        mac_hash = hashlib.sha256(str(mac_num).encode('utf-8')).hexdigest()[:16].upper()
        formatted = "-".join([mac_hash[i:i+4] for i in range(0, 16, 4)])
        return formatted
    except Exception:
        return "UNKNOWN-MACHINE-ID"

def verify_license_key(license_key, current_host=None):
    """
    Verifies a base64 encoded license key.
    Returns a dict containing license state and limits.
    """
    default_limits = {
        'is_valid': False,
        'licensee': 'نسخه رایگان (Free Tier)',
        'expires_at': None,
        'expires_at_jalali': None,
        'max_jobs': FREE_LIMIT_JOBS,
        'max_candidates': FREE_LIMIT_CANDIDATES,
        'max_posts': FREE_LIMIT_POSTS,
        'allowed_domains': [],
        'error': 'لایسنس فعال یافت نشد.'
    }

    if not license_key:
        return default_limits

    try:
        # Decode base64
        decoded_bytes = base64.b64decode(license_key.strip().encode('utf-8'))
        license_data = json.loads(decoded_bytes.decode('utf-8'))
        
        payload = license_data.get('payload')
        signature = license_data.get('signature')
        
        if not payload or not signature:
            default_limits['error'] = 'ساختار لایسنس نامعتبر است.'
            return default_limits

        # Verify signature
        payload_str = json.dumps(payload, sort_keys=True)
        expected_signature = hmac.new(
            LICENSE_SECRET_KEY, 
            payload_str.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature):
            default_limits['error'] = 'امضای لایسنس نامعتبر است.'
            return default_limits

        # Extract values
        licensee = payload.get('licensee', 'نامشخص')
        expires_at_str = payload.get('expires_at')
        max_jobs = payload.get('max_jobs', FREE_LIMIT_JOBS)
        max_candidates = payload.get('max_candidates', FREE_LIMIT_CANDIDATES)
        max_posts = payload.get('max_posts', FREE_LIMIT_POSTS)
        allowed_domains = payload.get('allowed_domains', [])

        # Expiry check
        expires_at = None
        expires_at_jalali = None
        if expires_at_str and expires_at_str != 'never':
            try:
                expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d').date()
                if expires_at < date.today():
                    default_limits['error'] = f'لایسنس در تاریخ {expires_at_str} منقضی شده است.'
                    return default_limits
                
                # Convert Gregorian date to Jalali for display
                try:
                    import jdatetime
                    jd = jdatetime.date.fromgregorian(date=expires_at)
                    expires_at_jalali = jd.strftime('%Y/%m/%d')
                except Exception:
                    expires_at_jalali = expires_at_str
            except ValueError:
                default_limits['error'] = 'فرمت تاریخ انقضا نامعتبر است.'
                return default_limits
        else:
            expires_at_jalali = 'نامحدود (دائمی)'

        # Domain verification
        if current_host and allowed_domains:
            # Normalize host (strip port if present)
            clean_host = current_host.split(':')[0].lower()
            # Allow localhost / local IP by default to avoid breaking development/test/staging
            local_hosts = ['localhost', '127.0.0.1', '::1', 'testserver']
            
            if clean_host not in local_hosts:
                # Check if host is allowed
                host_allowed = False
                for domain in allowed_domains:
                    domain_clean = domain.strip().lower()
                    if clean_host == domain_clean or clean_host.endswith('.' + domain_clean):
                        host_allowed = True
                        break
                
                if not host_allowed:
                    default_limits['error'] = f'دامنه جاری ({clean_host}) در لیست دامنه‌های مجاز لایسنس قرار ندارد.'
                    return default_limits

        # Machine ID verification
        allowed_machine_id = payload.get('allowed_machine_id')
        if allowed_machine_id:
            current_machine_id = get_machine_id()
            if current_machine_id != allowed_machine_id:
                default_limits['error'] = 'شناسه سخت‌افزاری دستگاه با این لایسنس مطابقت ندارد.'
                return default_limits

        # If all checks pass
        return {
            'is_valid': True,
            'licensee': licensee,
            'expires_at': expires_at,
            'expires_at_jalali': expires_at_jalali,
            'max_jobs': max_jobs if max_jobs != -1 else float('inf'),
            'max_candidates': max_candidates if max_candidates != -1 else float('inf'),
            'max_posts': max_posts if max_posts != -1 else float('inf'),
            'allowed_domains': allowed_domains,
            'error': None
        }

    except Exception as e:
        default_limits['error'] = f'خطا در پردازش لایسنس: {str(e)}'
        return default_limits


def get_system_license_limits(request=None):
    """
    Fetches the active organization setting, verifies its license_key,
    and returns verified limits.
    """
    from apps.jobs.models import OrganizationSetting
    try:
        setting = OrganizationSetting.get_active_setting()
        license_key = setting.license_key
    except Exception:
        license_key = None

    current_host = None
    if request:
        current_host = request.get_host()

    return verify_license_key(license_key, current_host=current_host)


def get_license_usage_stats(request=None):
    """
    Gathers current DB statistics and compares them against limits.
    """
    from apps.jobs.models import JobOpportunity, CentralCompetency
    from apps.candidates.models import Candidate

    limits = get_system_license_limits(request)

    current_jobs = JobOpportunity.objects.filter(is_deleted=False).count()
    current_candidates = Candidate.objects.filter(is_deleted=False).count()
    current_posts = CentralCompetency.objects.filter(is_deleted=False).values('post_code').distinct().count()

    def get_percent(current, limit):
        if limit == float('inf'):
            return 0
        return min(int((current / limit) * 100), 100)

    return {
        'licensee': limits['licensee'],
        'is_valid': limits['is_valid'],
        'expires_at_jalali': limits['expires_at_jalali'],
        'error': limits['error'],
        
        'jobs_used': current_jobs,
        'jobs_limit': 'نامحدود' if limits['max_jobs'] == float('inf') else limits['max_jobs'],
        'jobs_percent': get_percent(current_jobs, limits['max_jobs']),
        'jobs_over_limit': current_jobs >= limits['max_jobs'],
        
        'candidates_used': current_candidates,
        'candidates_limit': 'نامحدود' if limits['max_candidates'] == float('inf') else limits['max_candidates'],
        'candidates_percent': get_percent(current_candidates, limits['max_candidates']),
        'candidates_over_limit': current_candidates >= limits['max_candidates'],
        
        'posts_used': current_posts,
        'posts_limit': 'نامحدود' if limits['max_posts'] == float('inf') else limits['max_posts'],
        'posts_percent': get_percent(current_posts, limits['max_posts']),
        'posts_over_limit': current_posts >= limits['max_posts'],
        'machine_id': get_machine_id(),
    }


def generate_license_key(licensee, expires_at, max_jobs, max_candidates, max_posts, allowed_domains):
    """
    Generates a cryptographically signed license key.
    """
    payload = {
        'licensee': licensee,
        'expires_at': expires_at,
        'max_jobs': max_jobs,
        'max_candidates': max_candidates,
        'max_posts': max_posts,
        'allowed_domains': allowed_domains
    }
    
    # Sort keys for deterministic JSON serialization
    payload_str = json.dumps(payload, sort_keys=True)
    
    # Compute signature
    signature = hmac.new(
        LICENSE_SECRET_KEY,
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Bundle payload & signature
    license_data = {
        'payload': payload,
        'signature': signature
    }
    
    # Encode as Base64
    serialized = json.dumps(license_data).encode('utf-8')
    encoded = base64.b64encode(serialized).decode('utf-8')
    return encoded
