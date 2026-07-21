import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np

main = r'D:\Payjoo-ATS-Demo\exam data\_main.xlsx'
f = r'D:\Payjoo-ATS-Demo\exam data\4108.xlsx'
code = 4108

# ===== LOAD DATA =====
print(f'{"="*80}')
print(f'تحلیل کد آزمون {code}')
print(f'{"="*80}')

# Main file sheets
df_reg_m = pd.read_excel(main, sheet_name='ثبت نام')
df_reg_m = df_reg_m[df_reg_m['ExamCode'] == code].copy()
df_kot_m = pd.read_excel(main, sheet_name='کتبی')
df_kot_m = df_kot_m[df_kot_m['ExamCode'] == code].copy()
df_mah_m = pd.read_excel(main, sheet_name='مهارتی')
df_mah_m = df_mah_m[df_mah_m['ExamCode'] == code].copy()
df_int_m = pd.read_excel(main, sheet_name='مصاحبه')
df_int_m = df_int_m[df_int_m['ExamCode'] == code].copy()
df_ac_m = pd.read_excel(main, sheet_name='کانون')
df_ac_m = df_ac_m[df_ac_m['ExamCode'] == code].copy()

# Status table
df_status = pd.read_excel(main, sheet_name='جدول وضعیت')
r_status = df_status[df_status['کد'] == code].iloc[0]

# 4108.xlsx sheets
df_reg_d = pd.read_excel(f, sheet_name='ثبت نام')
df_screen_d = pd.read_excel(f, sheet_name='غربالگری')
df_kot_d = pd.read_excel(f, sheet_name='کتبی')
df_int_d = pd.read_excel(f, sheet_name='مصاحبه')
df_ac_d = pd.read_excel(f, sheet_name='کانون')

def nc_set(col):
    return set(col.dropna().astype('Int64').astype(str))

# ===== 1. STATUS TABLE =====
print(f'\n{"="*80}')
print('۱. جدول وضعیت (سطر 4108)')
print(f'{"="*80}')
for c in df_status.columns:
    v = r_status[c]
    if pd.notna(v):
        print(f'  {c}: {v}')

proposed_path = r_status['مسیر پیشنهادی (عنوان)']
print(f'\n  مسیر پیشنهادی: {proposed_path}')

# ===== 2. REGISTRATION =====
print(f'\n{"="*80}')
print('۲. ثبت نام — ساختار و تطابق')
print(f'{"="*80}')
print(f'فایل اصلی: {len(df_reg_m)} نفر')
print(f'4108.xlsx ثبت نام: {len(df_reg_d)} نفر')
print(f'4108.xlsx غربالگری: {len(df_screen_d)} نفر')

print(f'\nستون‌های 4108.xlsx ثبت نام: {list(df_reg_d.columns)}')
print(df_reg_d.to_string())

c_reg_m = nc_set(df_reg_m['NationCode'])
c_reg_d = nc_set(df_reg_d['کد ملی'])
print(f'\nکد ملی اصلی: {len(c_reg_m)}')
print(f'کد ملی 4108.xlsx: {len(c_reg_d)}')
print(f'اشتراک: {len(c_reg_m & c_reg_d)}')
print(f'فقط در اصلی: {len(c_reg_m - c_reg_d)}')
print(f'فقط در 4108.xlsx: {len(c_reg_d - c_reg_m)}')

print(f'\nResult در اصلی:')
print(df_reg_m['Result'].value_counts(dropna=False))

# ===== 3. WRITTEN EXAM =====
print(f'\n{"="*80}')
print('۳. آزمون کتبی')
print(f'{"="*80}')
print(f'فایل اصلی: {len(df_kot_m)} نفر')
print(f'4108.xlsx کتبی: {len(df_kot_d)} ردیف')

print(f'\nستون‌های 4108.xlsx کتبی: {list(df_kot_d.columns)}')
print(df_kot_d.to_string())

c_kot_m = nc_set(df_kot_m['NationCode'])

print(f'\nResult1 در اصلی:')
print(df_kot_m['Result1'].value_counts(dropna=False))
print(f'\nنمرات کتبی (اصلی): mean={df_kot_m["ScoreW"].mean():.2f}')

# Try to find nation code in the 4108 written sheet
# It seems to have unnamed columns - let's check each column
for col in df_kot_d.columns:
    print(f'  ستون "{col}" sample: {df_kot_d[col].head(3).tolist()}')

# ===== 4. SKILL EXAM =====
print(f'\n{"="*80}')
print('۴. آزمون مهارتی')
print(f'{"="*80}')
print(f'فایل اصلی: {len(df_mah_m)} نفر')
print(f'4108.xlsx: شیت مهارتی وجود ندارد')

# ===== 5. INTERVIEW =====
print(f'\n{"="*80}')
print('۵. مصاحبه')
print(f'{"="*80}')
print(f'فایل اصلی: {len(df_int_m)} نفر')
print(f'4108.xlsx مصاحبه: {len(df_int_d)} ردیف')

print(f'\nستون‌های 4108.xlsx مصاحبه: {list(df_int_d.columns)}')
print(df_int_d.to_string())

c_int_m = nc_set(df_int_m['NationCode'])

# Try to find nation code in interview sheet
print(f'\nداده‌های خام هر ستون:')
for col in df_int_d.columns:
    print(f'  "{col}": {df_int_d[col].tolist()[:6]}')

# ===== 6. ASSESSMENT CENTER =====
print(f'\n{"="*80}')
print('۶. کانون')
print(f'{"="*80}')
print(f'فایل اصلی: {len(df_ac_m)} نفر')
print(f'4108.xlsx کانون: {len(df_ac_d)} ردیف')

print(f'\nستون‌های 4108.xlsx کانون: {list(df_ac_d.columns)}')
print(df_ac_d.to_string())

c_ac_m = nc_set(df_ac_m['NationCode'])
c_ac_d = nc_set(df_ac_d['کد ملی'])
print(f'\nاشتراک کد ملی کانون: {len(c_ac_m & c_ac_d)}')

# ===== 7. PATH ANALYSIS =====
print(f'\n{"="*80}')
print('۷. مسیر استخدامی و تطابق')
print(f'{"="*80}')

stages = ['ثبت نام', 'کتبی', 'مهارتی', 'کانون', 'مصاحبه']
counts = [
    len(df_reg_m),
    len(df_kot_m),
    len(df_mah_m),
    len(df_ac_m),
    len(df_int_m)
]
for s, c in zip(stages, counts):
    print(f'  {s}: {c} نفر')

active = [(s, c) for s, c in zip(stages, counts) if c > 0]
path_parts = [s.split('+') for s in str(proposed_path).split('+')]
print(f'\nمراحل فعال: {" → ".join(s for s, _ in active)}')
print(f'مسیر پیشنهادی: {proposed_path}')

# ===== 8. DISCREPANCIES =====
print(f'\n{"="*80}')
print('۸. خلاصه مغایرت‌ها')
print(f'{"="*80}')

# Registration
if len(df_reg_m) != len(df_reg_d):
    print(f'⚠️ تعداد ثبت‌نام: اصلی={len(df_reg_m)} / 4108.xlsx={len(df_reg_d)}')

# Written
if len(df_kot_m) != len(df_kot_d):
    print(f'⚠️ تعداد کتبی: اصلی={len(df_kot_m)} / 4108.xlsx={len(df_kot_d)}')

# Skill - no skill sheet in 4108
print(f'ℹ️ 4108.xlsx شیت مهارتی ندارد.')
print(f'   فایل اصلی مهارتی={len(df_mah_m)} (منطقی است چون در این مسیر مهارتی وجود ندارد)')

# AC
if len(df_ac_m) != len(df_ac_d):
    print(f'⚠️ تعداد کانون: اصلی={len(df_ac_m)} / 4108.xlsx={len(df_ac_d)}')
else:
    print(f'✅ تعداد کانون تطابق: {len(df_ac_m)}')

# Interview
if len(df_int_m) != len(df_int_d):
    print(f'⚠️ تعداد مصاحبه: اصلی={len(df_int_m)} / 4108.xlsx={len(df_int_d)}')
else:
    print(f'✅ تعداد مصاحبه تطابق: {len(df_int_m)}')

# Check that National IDs are linked between registration and written
overlap_reg_kot = len(c_reg_m & c_kot_m)
print(f'\nکد ملی مشترک ثبت‌نام → کتبی: {overlap_reg_kot}/{len(c_kot_m)}')

print(f'\n{"="*80}')
print('پایان تحلیل 4108. آماده برای دستور بعدی.')
print(f'{"="*80}')
