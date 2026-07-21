import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np

main = r'D:\Payjoo-ATS-Demo\exam data\_main.xlsx'
f4101 = r'D:\Payjoo-ATS-Demo\exam data\4101.xlsx'

code = 4101

# Load main file sheets (filtered for exam 4101)
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

# Load 4101.xlsx sheets
df_reg_d = pd.read_excel(f4101, sheet_name='ثبت نام')
df_screen_d = pd.read_excel(f4101, sheet_name='غربالگری')
df_sent_d = pd.read_excel(f4101, sheet_name='ارسالی به مرکز آزمون')

df_written_d = pd.read_excel(f4101, sheet_name='نتایج کتبی')
# Filter out formula rows (first row with -1 values)
df_written_d = df_written_d[df_written_d['nacode'] > 0].copy()

df_skill_d = pd.read_excel(f4101, sheet_name='نتایج مهارتی')
df_skill_analysis_d = pd.read_excel(f4101, sheet_name='تحلیل مهارتی')

df_ac_d = pd.read_excel(f4101, sheet_name='نتایج کانون')
print('نتایج کانون columns:', list(df_ac_d.columns))
df_ac_analysis_d = pd.read_excel(f4101, sheet_name='تحلیل کانون')
print('تحلیل کانون columns:', list(df_ac_analysis_d.columns))

df_int_d = pd.read_excel(f4101, sheet_name='مصاحبه')

# Helper: normalize national code
def nc_set(series):
    return set(series.dropna().astype('Int64').astype(str))

def nc_map(df, col):
    return df.dropna(subset=[col]).set_index(df[col].astype('Int64').astype(str))

def nc_map_2(df, col1, col2):
    """Create a mapping dict from col1 -> col2"""
    d = {}
    for _, r in df.dropna(subset=[col1]).iterrows():
        key = str(int(float(r[col1])))
        d[key] = r[col2]
    return d

print('=' * 80)
print(f'ردیابی انتقال داده: کد آزمون {code}')
print('=' * 80)
print()

print('=' * 80)
print('بخش ۱: ثبت نام — مسیر ثبت نام تا ارسال به مرکز')
print('=' * 80)

c_reg = nc_set(df_reg_m['NationCode'])
c_sent = nc_set(df_sent_d['کد ملی'])
c_personnel = set(df_reg_d['شماره پرسنلي'].dropna().astype('Int64').astype(str))
c_screen = set(df_screen_d['شماره پرسنلي'].dropna().astype('Int64').astype(str))

print(f'فایل اصلی - ثبت نام: {len(c_reg)} نفر (کد ملی)')
print(f'4101.xlsx - ارسالی به مرکز: {len(c_sent)} نفر (کد ملی)')
print(f'4101.xlsx - ثبت نام (پرسنلی): {len(c_personnel)} نفر (شماره پرسنلی)')
print(f'4101.xlsx - غربالگری: {len(c_screen)} نفر (شماره پرسنلی)')

# Check if registration in main file matches sent-to-center
overlap_reg_sent = len(c_reg & c_sent)
only_reg = len(c_reg - c_sent)
only_sent = len(c_sent - c_reg)
print(f'\nاشتراک کد ملی بین ثبت نام اصلی و ارسالی به مرکز: {overlap_reg_sent}')
print(f'فقط در ثبت نام اصلی (غایبان احتمالی): {only_reg}')
print(f'فقط در ارسالی به مرکز: {only_sent}')

# Now check: do personnel IDs in 4101 registration match the ارسالی people?
# First, we need to link personnel IDs to national codes
personnel_to_nc = {}
for _, r in df_sent_d.iterrows():
    if pd.notna(r['شماره داوطلبی']) and pd.notna(r['کد ملی']):
        personnel_to_nc[str(int(r['شماره داوطلبی']))] = str(int(r['کد ملی']))

print(f'\nMapping در ارسالی به مرکز: {len(personnel_to_nc)} نفر')

# 4101 registration has personnel number (شماره پرسنلي), NOT the applicant number (شماره داوطلبی)
# We need to find the link

# Let's check if the 4101 registration has duplicate personnel IDs
personnel_counts = df_reg_d['شماره پرسنلي'].value_counts()
dups = personnel_counts[personnel_counts > 1]
print(f'شماره پرسنلی تکراری در ثبت نام 4101: {len(dups)}')
if len(dups) > 0:
    for pid, cnt in dups.head().items():
        print(f'  {int(pid)}: {cnt} بار')

print()

print('=' * 80)
print('بخش ۲: خروجی ثبت نام (Result / EXP)')
print('=' * 80)
# Main file registration has: Result and EXP columns
print('مقادیر Result در ثبت نام فایل اصلی:')
print(df_reg_m['Result'].value_counts(dropna=False))
print()

print('مقادیر EXP در ثبت نام فایل اصلی:')
print(df_reg_m['EXP'].value_counts(dropna=False))
print()

print('نمونه داده ثبت نام فایل اصلی (۵ ردیف):')
print(df_reg_m[['NationCode', 'Result', 'EXP']].head(10).to_string())
print()

print('=' * 80)
print('بخش ۳: آزمون کتبی — نتایج')
print('=' * 80)

c_kot_m = nc_set(df_kot_m['NationCode'])
c_written_d = nc_set(df_written_d['nacode'])

print(f'فایل اصلی - کتبی: {len(c_kot_m)} نفر')
print(f'4101.xlsx - نتایج کتبی: {len(c_written_d)} نفر')

overlap_w = len(c_kot_m & c_written_d)
only_kot_m = len(c_kot_m - c_written_d)
only_written_d = len(c_written_d - c_kot_m)
print(f'اشتراک: {overlap_w}')
print(f'فقط در اصلی (کتبی): {only_kot_m}')
print(f'فقط در 4101.xlsx (نتایج کتبی): {only_written_d}')

# Compare scores
scores_main = {}
for _, r in df_kot_m.iterrows():
    nc = str(int(float(r['NationCode'])))
    scores_main[nc] = {'ScoreW': r['ScoreW'], 'Result1': r['Result1']}

scores_detail = {}
for _, r in df_written_d.iterrows():
    nc = str(int(float(r['nacode'])))
    scores_detail[nc] = {
        'total': r['total'],
        'kalami': r['kalami'],
        'mantegi': r['mantegi'],
        'mohasebati': r['mohasebati'],
        'ai': r['ai'],
        'dist': r['dist']
    }

# Compare scores for common people
common_nc = c_kot_m & c_written_d
differences = 0
for nc in list(common_nc)[:]:
    s_m = scores_main.get(nc, {}).get('ScoreW', -1)
    s_d = scores_detail.get(nc, {}).get('total', -1)
    if abs(s_m - s_d) > 0.01:
        differences += 1
        if differences <= 10:
            print(f'  اختلاف: کدملی {nc} -> اصلی={s_m:.2f} / تفصیلی={s_d:.2f}')

print(f'تعداد اختلافات نمره کتبی: {differences}')
print()

# Check Results
print('مقادیر Result1 در کتبی فایل اصلی:')
print(df_kot_m['Result1'].value_counts(dropna=False))
print(f'تعداد مجاز: {len(df_kot_m[df_kot_m["Result1"]=="مجاز"])}')
print(f'تعداد غیرمجاز و NaN: {len(df_kot_m[df_kot_m["Result1"]!="مجاز"])}')
print()

print('=' * 80)
print('بخش ۴: آزمون مهارتی')
print('=' * 80)

c_mah_m = nc_set(df_mah_m['NationCode'])
c_skill_d = nc_set(df_skill_d['کد ملی'])

print(f'فایل اصلی - مهارتی: {len(c_mah_m)} نفر')
print(f'4101.xlsx - نتایج مهارتی: {len(c_skill_d)} نفر')

overlap_s = len(c_mah_m & c_skill_d)
print(f'اشتراک: {overlap_s}')
print(f'فقط در اصلی: {len(c_mah_m - c_skill_d)}')
print(f'فقط در 4101.xlsx: {len(c_skill_d - c_mah_m)}')

# Compare scores
print('\nمقایسه نمرات مهارتی:')
s_mah_main = {}
for _, r in df_mah_m.iterrows():
    nc = str(int(float(r['NationCode'])))
    s_mah_main[nc] = {'ScoreS': r['ScoreS'], 'CScoreS': r['CScoreS'], 'Result2': r['Result2']}

s_skill_d = {}
for _, r in df_skill_d.iterrows():
    nc = str(int(float(r['کد ملی'])))
    s_skill_d[nc] = {'Score': r.get('نمره مهارتی', r.get('total', 0))}

diff_s = 0
for nc in list(common_nc)[:]:
    pass

# Check the 'وضعیت آزمون تحلیل داده' column in skill results
print('مقادیر وضعیت آزمون تحلیل داده:')
col_names = df_skill_d.columns.tolist()
print(f'ستون‌ها: {col_names}')
for c in df_skill_d.columns:
    if 'وضعیت' in str(c):
        print(df_skill_d[c].value_counts(dropna=False).head(10))

print()

# Check تحلیل مهارتی
print('4101.xlsx - تحلیل مهارتی:')
print(f'تعداد ردیف: {len(df_skill_analysis_d)}')
print(f'ستون‌ها: {list(df_skill_analysis_d.columns)[:10]}...')

# Match with main file's skill sheet
c_sa_d = nc_set(df_skill_analysis_d['کد ملی'])
print(f'تعداد کد ملی یکتا در تحلیل مهارتی: {len(c_sa_d)}')
print(f'اشتراک با فایل اصلی (مهارتی): {len(c_mah_m & c_sa_d)}')

print()

print('=' * 80)
print('بخش ۵: کانون (مرکز ارزیابی)')
print('=' * 80)

c_ac_m = nc_set(df_ac_m['NationCode'])
# نتایج کانون has unnamed columns, find the right one
ac_cols = [c for c in df_ac_d.columns if 'کد ملی' in str(c) or 'ملی' in str(c)]
print(f'نتایج کانون - ستون کد ملی: {ac_cols}')
# The sheet seems to have merged cells; let's check the data
print(df_ac_d.head(3).to_string())
c_ac_d = set()
# skip
print('Skipping نتایج کانون comparison (merged cell layout)')
# Use تحلیل کانون instead
c_aca_d = nc_set(df_ac_analysis_d['کد ملی'])
c_aca_d = nc_set(df_ac_analysis_d['کد ملی'])
print(f'فایل اصلی - کانون: {len(c_ac_m)} نفر')
print(f'4101.xlsx - تحلیل کانون: {len(c_aca_d)} نفر')
print(f'اشتراک اصلی و تحلیل کانون: {len(c_ac_m & c_aca_d)}')

# The analysis sheet has more useful data - let's compare scores
print('\nمقایسه نمرات کانون:')
ac_scores_main = {}
for _, r in df_ac_m.iterrows():
    nc = str(int(float(r['NationCode'])))
    ac_scores_main[nc] = {'ScoreAC': r.get('ScoreAC', 0), 'CScoreAC': r.get('CScoreAC', 0)}

ac_scores_detail = {}
for _, r in df_ac_analysis_d.iterrows():
    nc = str(int(float(r['کد ملی'])))
    ac_scores_detail[nc] = {
        'نمره کانون': r.get('نمره کانون', 0),
        'نمره کل': r.get('نمره کل', 0),
        'رتبه کل': r.get('رتبه کل', 0),
        'وضعیت': r.get('وضعیت', '')
    }

match_count = 0
diff_count = 0
for nc in c_ac_m & c_aca_d:
    s1 = ac_scores_main.get(nc, {}).get('ScoreAC', 0)
    s2 = ac_scores_detail.get(nc, {}).get('نمره کانون', 0)
    if abs(s1 - s2) < 0.01:
        match_count += 1
    else:
        diff_count += 1
        if diff_count <= 5:
            print(f'  اختلاف: {nc} -> اصلی={s1:.2f} / کانون={s2:.2f}')

print(f'تطابق نمره کانون: {match_count} نفر')
print(f'اختلاف نمره کانون: {diff_count} نفر')

print()

print('=' * 80)
print('بخش ۶: مصاحبه')
print('=' * 80)

c_int_m = nc_set(df_int_m['NationCode'])
c_int_d = nc_set(df_int_d['کد ملی'])

print(f'فایل اصلی - مصاحبه: {len(c_int_m)} نفر')
print(f'4101.xlsx - مصاحبه: {len(c_int_d)} نفر')

overlap_i = len(c_int_m & c_int_d)
only_int_m = len(c_int_m - c_int_d)
only_int_d = len(c_int_d - c_int_m)
print(f'اشتراک: {overlap_i}')
print(f'فقط در اصلی: {only_int_m}')
print(f'فقط در 4101.xlsx: {only_int_d}')

# Compare scores
print('\nمقایسه نمرات مصاحبه:')
i_scores_m = {}
for _, r in df_int_m.iterrows():
    nc = str(int(float(r['NationCode'])))
    i_scores_m[nc] = {'ScoreI': r.get('ScoreI', 0), 'CScoreI': r.get('CScoreI', 0)}

i_scores_d = {}
for _, r in df_int_d.iterrows():
    nc = str(int(float(r['کد ملی'])))
    i_scores_d[nc] = {
        'نمره مصاحبه': r.get('نمره مصاحبه', 0),
        'نمره کل': r.get('نمره کل', 0),
        'رتبه': r.get('رتبه.1', r.get('رتبه', 0))
    }

for nc in c_int_m & c_int_d:
    s1 = i_scores_m.get(nc, {}).get('ScoreI', 0)
    s2 = i_scores_d.get(nc, {}).get('نمره مصاحبه', 0)
    c1 = i_scores_m.get(nc, {}).get('CScoreI', 0)
    c2 = i_scores_d.get(nc, {}).get('نمره کل', 0)
    stat_m = i_scores_m.get(nc, {}).get('CScoreI', 0)
    print(f'  کدملی {nc}:')
    print(f'    نمره مصاحبه: اصلی={s1} / تفصیلی={s2}')
    print(f'    نمره کل: اصلی={c1:.2f} / تفصیلی={c2:.2f}')

print()

print('=' * 80)
print('بخش ۷: الگوی انتقال داده')
print('=' * 80)

print('''بر اساس بررسی تطبیقی، الگوی انتقال داده از 4101.xlsx به فایل اصلی به این شرح است:

مرحله ۱ - ثبت نام:
  4101.xlsx.ثبت نام (شماره پرسنلی)
    → 4101.xlsx.غربالگری (فیلتر)
    → 4101.xlsx.ارسالی به مرکز آزمون (اختصاص شماره داوطلبی + کد ملی)
    → فایل اصلی.ثبت نام (کد ملی + نتیجه غربالگری)

مرحله ۲ - آزمون کتبی:
  4101.xlsx.نتایج کتبی (نمرات تفکیکی + نمره کل)
    → فایل اصلی.کتبی (نمره کل + نتیجه قبولی)

مرحله ۳ - آزمون مهارتی:
  4101.xlsx.نتایج مهارتی یا تحلیل مهارتی
    → فایل اصلی.مهارتی (نمره مهارتی + نمره تعدیل شده)

مرحله ۴ - کانون ارزیابی:
  4101.xlsx.تحلیل کانون
    → فایل اصلی.کانون (نمره کانون + نمره کل)

مرحله ۵ - مصاحبه:
  4101.xlsx.مصاحبه
    → فایل اصلی.مصاحبه (نمره مصاحبه + نمره کل)
''')

print('=' * 80)
print('بخش ۸: خلاصه مغایرت‌ها')
print('=' * 80)

discrepancies = []

# 1. Registration count
if len(c_reg) != len(df_reg_d):
    discrepancies.append(f'تعداد ثبت‌نام: اصلی={len(c_reg)} / 4101.xlsx={len(df_reg_d)}')

# 2. Written count
if len(c_kot_m) != len(c_written_d):
    discrepancies.append(f'تعداد کتبی: اصلی={len(c_kot_m)} / 4101.xlsx={len(c_written_d)}')

# 3. Skill count  
if len(c_mah_m) != len(c_skill_d):
    discrepancies.append(f'تعداد مهارتی: اصلی={len(c_mah_m)} / 4101.xlsx={len(c_skill_d)}')

# 4. AC count
if len(c_ac_m) != len(c_ac_d):
    discrepancies.append(f'تعداد کانون: اصلی={len(c_ac_m)} / 4101.xlsx={len(c_ac_d)}')

# 5. Interview count
if len(c_int_m) != len(c_int_d):
    discrepancies.append(f'تعداد مصاحبه: اصلی={len(c_int_m)} / 4101.xlsx={len(c_int_d)}')

# 6. Score differences in written
if differences > 0:
    discrepancies.append(f'اختلاف نمره کتبی در {differences} نفر')

# 7. Score differences in AC
if diff_count > 0:
    discrepancies.append(f'اختلاف نمره کانون در {diff_count} نفر')

if not discrepancies:
    discrepancies.append('مغایرتی یافت نشد')

for d in discrepancies:
    print(f'  ❌ {d}')

print()
print('=' * 80)
print('بخش ۹: مسیر استخدامی 4101 از ستون مسیر پیشنهادی')
print('=' * 80)

df_status = pd.read_excel(main, sheet_name='جدول وضعیت')
r = df_status[df_status['کد'] == code].iloc[0]
path = r['مسیر پیشنهادی (عنوان)']
print(f'مسیر ثبت شده در جدول وضعیت (ستون AH): {path}')
print()

# Verify the actual flow from the data
stages = ['ثبت نام', 'کتبی', 'مهارتی', 'کانون', 'مصاحبه']
actual_counts = []
for s in stages:
    df_s = pd.read_excel(main, sheet_name=s)
    cnt = len(df_s[df_s['ExamCode'] == code])
    actual_counts.append(cnt)

print('مسیر واقعی (بر اساس داده):')
for i, (s, c) in enumerate(zip(stages, actual_counts)):
    print(f'  {i+1}. {s}: {c} نفر')

# Check which stages actually happened
active = [s for s, c in zip(stages, actual_counts) if c > 0]
print(f'\nمراحل فعال: {" → ".join(active)}')

# Compare with proposed path
proposed = [s.strip() for s in str(path).split('+') if s.strip()]
print(f'مسیر پیشنهادی: {" → ".join(proposed)}')

# Check sequence integrity
print(f'\nتطابق مسیر پیشنهادی با واقعیت: {"✓" if active == proposed else "✗"}')

print()
print('آماده برای دستور بعدی.')
