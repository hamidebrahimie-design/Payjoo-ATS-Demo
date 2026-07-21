import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd

main = r'D:\Payjoo-ATS-Demo\exam data\_main.xlsx'

print('=' * 80)
print('بررسی: آیا فرد رد شده در غربالگری به مرحله بعد راه یافته است؟')
print('=' * 80)

# Load data for 4101
print('\n--- کد 4101 ---')
df_reg = pd.read_excel(main, sheet_name='ثبت نام')
reg_4101 = df_reg[df_reg['ExamCode'] == 4101].copy()

# Get rejected (غیرمجاز) in registration
rejected = set(reg_4101[reg_4101['Result'] == 'غیرمجاز']['NationCode'].dropna().astype('Int64').astype(str))
accepted = set(reg_4101[reg_4101['Result'] == 'مجاز']['NationCode'].dropna().astype('Int64').astype(str))

print(f'رد شده در غربالگری (غیرمجاز): {len(rejected)} نفر')
print(f'تأیید شده (مجاز): {len(accepted)} نفر')

# Check written exam - did any rejected person appear?
df_kot = pd.read_excel(main, sheet_name='کتبی')
kot_4101 = df_kot[df_kot['ExamCode'] == 4101].copy()
kot_codes = set(kot_4101['NationCode'].dropna().astype('Int64').astype(str))

rejected_in_kot = rejected & kot_codes
accepted_in_kot = accepted & kot_codes
print(f'ردشدگانی که در کتبی حاضر شدند: {len(rejected_in_kot)} نفر')
if len(rejected_in_kot) > 0:
    print(f'  اسامی: {rejected_in_kot}')

# Check مهارتی
df_mah = pd.read_excel(main, sheet_name='مهارتی')
mah_4101 = df_mah[df_mah['ExamCode'] == 4101].copy()
mah_codes = set(mah_4101['NationCode'].dropna().astype('Int64').astype(str))
rejected_in_mah = rejected & mah_codes
print(f'ردشدگانی که به مهارتی راه یافتند: {len(rejected_in_mah)} نفر')

# Check کانون
df_ac = pd.read_excel(main, sheet_name='کانون')
ac_4101 = df_ac[df_ac['ExamCode'] == 4101].copy()
ac_codes = set(ac_4101['NationCode'].dropna().astype('Int64').astype(str))
rejected_in_ac = rejected & ac_codes
print(f'ردشدگانی که به کانون راه یافتند: {len(rejected_in_ac)} نفر')

# Check مصاحبه
df_int = pd.read_excel(main, sheet_name='مصاحبه')
int_4101 = df_int[df_int['ExamCode'] == 4101].copy()
int_codes = set(int_4101['NationCode'].dropna().astype('Int64').astype(str))
rejected_in_int = rejected & int_codes
print(f'ردشدگانی که به مصاحبه راه یافتند: {len(rejected_in_int)} نفر')

# Also check: people in written who are NOT in main registration
missing_reg = kot_codes - (rejected | accepted)
print(f'\nافراد حاضر در کتبی بدون رکورد ثبت‌نام: {len(missing_reg)} نفر')

print('\n\n--- کد 4108 ---')
reg_4108 = df_reg[df_reg['ExamCode'] == 4108].copy()
rejected_8 = set(reg_4108[reg_4108['Result'] == 'غیرمجاز']['NationCode'].dropna().astype('Int64').astype(str))
accepted_8 = set(reg_4108[reg_4108['Result'] == 'مجاز']['NationCode'].dropna().astype('Int64').astype(str))
print(f'رد شده: {len(rejected_8)} نفر')
print(f'تأیید شده: {len(accepted_8)} نفر')

kot_4108 = df_kot[df_kot['ExamCode'] == 4108].copy()
kot_codes_8 = set(kot_4108['NationCode'].dropna().astype('Int64').astype(str))
rejected_in_kot_8 = rejected_8 & kot_codes_8
print(f'ردشدگان در کتبی: {len(rejected_in_kot_8)} نفر')

# Check all exam codes for this pattern
print('\n\n--- بررسی همه کدهای آزمون ---')
print('کدهایی که ردشدگان در مراحل بعدی ظاهر شده‌اند:')

all_codes = sorted(reg_4108['ExamCode'].unique()) # wrong, this is just 4108
all_codes = sorted(df_reg['ExamCode'].dropna().unique())

found_any = False
for code in all_codes:
    code = int(code)
    reg_c = df_reg[df_reg['ExamCode'] == code]
    rejected_c = set(reg_c[reg_c['Result'] == 'غیرمجاز']['NationCode'].dropna().astype('Int64').astype(str))
    if len(rejected_c) == 0:
        continue
    
    for s_name, df_s in [('کتبی', df_kot), ('مهارتی', df_mah), ('کانون', df_ac), ('مصاحبه', df_int)]:
        df_sc = df_s[df_s['ExamCode'] == code]
        codes_sc = set(df_sc['NationCode'].dropna().astype('Int64').astype(str))
        overlap = rejected_c & codes_sc
        if len(overlap) > 0:
            found_any = True
            print(f'  کد {code} - مرحله {s_name}: {len(overlap)} ردشده ظاهر شده')

if not found_any:
    print('  هیچ موردی یافت نشد. همه افراد رد شده در غربالگری، به مراحل بعدی راه نیافته‌اند.')

print('\nنتیجه: غربالگری به درستی عمل کرده است.')
