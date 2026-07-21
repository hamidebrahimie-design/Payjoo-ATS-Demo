import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd

main = r'D:\Payjoo-ATS-Demo\exam data\_main.xlsx'

# Check جدول وضعیت columns
df_status = pd.read_excel(main, sheet_name='جدول وضعیت')
print('=== جدول وضعیت - همه ستونها (A..) ===')
for i, c in enumerate(df_status.columns):
    letter = chr(65+i) if i < 26 else 'A' + chr(65+i-26)
    sample = df_status[c].dropna().iloc[0] if len(df_status[c].dropna()) > 0 else '(empty)'
    print(f'  {letter} (idx {i}): {c}  -> sample: {sample}')

print()

# Check defList columns
df_def = pd.read_excel(main, sheet_name='defList')
print('=== defList - همه ستونها ===')
for i, c in enumerate(df_def.columns):
    letter = chr(65+i) if i < 26 else 'A' + chr(65+i-26)
    sample = df_def[c].dropna().iloc[0] if len(df_def[c].dropna()) > 0 else '(empty)'
    print(f'  {letter} (idx {i}): {c}  -> sample: {sample}')
print()

# Check 4101.xlsx registration columns
f4101 = r'D:\Payjoo-ATS-Demo\exam data\4101.xlsx'
df_r = pd.read_excel(f4101, sheet_name='ثبت نام')
print('=== 4101.xlsx ثبت نام - همه ستونها ===')
for i, c in enumerate(df_r.columns):
    letter = chr(65+i) if i < 26 else 'A' + chr(65+i-26)
    print(f'  {letter} (idx {i}): {c}')
print()

# Check 4108.xlsx registration columns  
f4108 = r'D:\Payjoo-ATS-Demo\exam data\4108.xlsx'
df_r8 = pd.read_excel(f4108, sheet_name='ثبت نام')
print('=== 4108.xlsx ثبت نام - همه ستونها ===')
for i, c in enumerate(df_r8.columns):
    letter = chr(65+i) if i < 26 else 'A' + chr(65+i-26)
    print(f'  {letter} (idx {i}): {c}')
