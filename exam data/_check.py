import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np

main_file = r'D:\Payjoo-ATS-Demo\exam data\_main.xlsx'

# 1. Compare جدول وضعیت vs actual data
df_status = pd.read_excel(main_file, sheet_name='جدول وضعیت')
print('=== مقایسه جدول وضعیت vs داده واقعی ===')
mismatch_count = 0
for _, r in df_status.iterrows():
    code = r['کد']
    if pd.isna(code):
        continue
    code = int(code)

    df_reg = pd.read_excel(main_file, sheet_name='ثبت نام')
    actual_reg = len(df_reg[df_reg['ExamCode'] == code])
    
    df_kot = pd.read_excel(main_file, sheet_name='کتبی')
    actual_kot = len(df_kot[df_kot['ExamCode'] == code])
    
    df_mah = pd.read_excel(main_file, sheet_name='مهارتی')
    actual_mah = len(df_mah[df_mah['ExamCode'] == code])
    
    stated_reg = r['تعداد ثبت‌نام']
    stated_eligible = r['تعداد واجد شرایط']
    stated_skill_out = r['تعداد نفرات خروجی کتبی']
    
    issues = []
    if not pd.isna(stated_reg) and actual_reg != stated_reg:
        issues.append(f'ثبت‌نام: جدول={int(stated_reg)} واقعی={actual_reg}')
    if not pd.isna(stated_eligible) and actual_kot != stated_eligible:
        issues.append(f'واجدشرایط: جدول={int(stated_eligible)} واقعی={actual_kot}')
    if not pd.isna(stated_skill_out) and actual_mah != stated_skill_out:
        issues.append(f'خروجی کتبی: جدول={int(stated_skill_out)} واقعی={actual_mah}')
    
    if issues:
        mismatch_count += 1
        print(f'  کد {code}: {" | ".join(issues)}')

if mismatch_count == 0:
    print('  همه موارد مطابقت دارند.')
else:
    print(f'  مجموع مغایرتها: {mismatch_count}')
print()
