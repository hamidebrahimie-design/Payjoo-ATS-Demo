"""Add official Iranian holidays for year 1405 to the database."""
import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'ats.settings'

import django
django.setup()

from apps.recruitment_planning.models import Holiday
from apps.recruitment_planning.utils import parse_jalali_to_gregorian

# Official holidays of Iran - year 1405
holidays = [
    # Fixed solar holidays
    ("1405/01/01", "Eid Nowruz (Day 1)"),
    ("1405/01/02", "Eid Nowruz (Day 2)"),
    ("1405/01/03", "Eid Nowruz (Day 3)"),
    ("1405/01/04", "Eid Nowruz (Day 4)"),
    ("1405/01/12", "Islamic Republic Day"),
    ("1405/01/13", "Nature Day (Sizdah Bedar)"),

    ("1405/03/14", "Demise of Imam Khomeini"),
    ("1405/03/15", "15 Khordad Uprising"),

    ("1405/11/22", "Islamic Revolution Victory (22 Bahman)"),

    ("1405/12/29", "Nationalization of Oil Industry"),

    # Religious holidays
    ("1405/01/10", "Eid al-Fitr"),
    ("1405/01/11", "Eid al-Fitr (Holiday)"),

    ("1405/03/15", "Eid al-Adha"),
    ("1405/03/23", "Eid al-Ghadir"),
    ("1405/04/14", "Tasua"),
    ("1405/04/15", "Ashura"),
    ("1405/05/24", "Arbaeen"),
    ("1405/06/01", "Prophet Demise & Imam Hassan (AS) Martyrdom"),
    ("1405/06/02", "Imam Reza (AS) Martyrdom"),
    ("1405/06/10", "Imam Hassan Askari (AS) Martyrdom"),
    ("1405/06/19", "Prophet Birth & Imam Sadeq (AS) Birth"),

    ("1405/08/10", "Fatima Zahra (SA) Martyrdom"),

    ("1405/10/20", "Imam Ali (AS) Birth & Father Day"),
    ("1405/11/03", "Mab'ath"),
    ("1405/11/21", "Imam Mahdi (AJ) Birth - Mid-Sha'ban"),
]

added = 0
skipped = 0
for date_str, title in holidays:
    g_date = parse_jalali_to_gregorian(date_str)
    if g_date:
        _, created = Holiday.objects.get_or_create(
            date=g_date,
            defaults={'title': title, 'is_deleted': False}
        )
        if created:
            added += 1
            print(f"✅ {date_str} - {title}")
        else:
            skipped += 1
    else:
        print(f"❌ Invalid date: {date_str} - {title}")

print(f"\n📊 نتیجه: {added} تعطیلی جدید اضافه شد، {skipped} تعطیلی از قبل وجود داشت.")
