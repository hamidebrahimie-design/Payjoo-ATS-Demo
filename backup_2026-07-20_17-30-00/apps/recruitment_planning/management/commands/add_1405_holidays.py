# -*- coding: utf-8 -*-
"""Management command to add 1405 holidays."""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from apps.recruitment_planning.models import Holiday
from apps.recruitment_planning.utils import parse_jalali_to_gregorian


class Command(BaseCommand):
    help = 'Add official Iranian holidays for year 1405'

    @transaction.atomic
    def handle(self, *args, **options):
        # Hard delete all existing holidays from DB
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM recruitment_planning_holiday")
        
        holidays = [
            (1405, 1, 1, "عید نوروز (روز اول)"),
            (1405, 1, 2, "عید نوروز (روز دوم)"),
            (1405, 1, 3, "عید نوروز (روز سوم)"),
            (1405, 1, 4, "عید نوروز (روز چهارم)"),
            (1405, 1, 10, "عید سعید فطر"),
            (1405, 1, 11, "عید سعید فطر (تعطیل)"),
            (1405, 1, 12, "روز جمهوری اسلامی ایران"),
            (1405, 1, 13, "روز طبیعت (سیزده به در)"),
            (1405, 3, 14, "رحلت امام خمینی (ره)"),
            (1405, 3, 15, "قیام ۱۵ خرداد و عید سعید قربان"),
            (1405, 3, 23, "عید سعید غدیر خم"),
            (1405, 4, 14, "تاسوعای حسینی"),
            (1405, 4, 15, "عاشورای حسینی"),
            (1405, 5, 24, "اربعین حسینی"),
            (1405, 6, 1, "رحلت پیامبر اکرم (ص) و شهادت امام حسن مجتبی (ع)"),
            (1405, 6, 2, "شهادت امام رضا (ع)"),
            (1405, 6, 10, "شهادت امام حسن عسکری (ع)"),
            (1405, 6, 19, "ولادت پیامبر اکرم (ص) و امام جعفر صادق (ع)"),
            (1405, 8, 10, "شهادت حضرت فاطمه زهرا (س)"),
            (1405, 10, 20, "ولادت حضرت علی (ع) و روز پدر"),
            (1405, 11, 3, "مبعث رسول اکرم (ص)"),
            (1405, 11, 21, "ولادت حضرت قائم (عج) - نیمه شعبان"),
            (1405, 11, 22, "پیروزی انقلاب اسلامی (۲۲ بهمن)"),
            (1405, 12, 29, "ملی شدن صنعت نفت ایران"),
        ]
        added = 0
        for year, month, day, title in holidays:
            date_str = f"{year:04d}/{month:02d}/{day:02d}"
            g_date = parse_jalali_to_gregorian(date_str)
            if g_date:
                Holiday.objects.update_or_create(date=g_date, defaults={'title': title, 'is_deleted': False})
                added += 1
                self.stdout.write(f"  {date_str} {title}")
        self.stdout.write(self.style.SUCCESS(f'{added} holidays added successfully'))
