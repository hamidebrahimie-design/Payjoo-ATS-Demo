import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd

main = r'D:\Payjoo-ATS-Demo\exam data\_main.xlsx'

df_status = pd.read_excel(main, sheet_name='جدول وضعیت')
print('Columns by index:')
for i, c in enumerate(df_status.columns):
    col_letter = chr(65+i) if i < 26 else 'A' + chr(65+i-26)
    print(f'  Col {col_letter} (index {i}): {c}')

col_k = df_status.columns[10] if len(df_status.columns) > 10 else None
print(f'\nColumn K = index 10 = "{col_k}"')

# Check values for all exam codes
print(f'\nValues in column K for all codes with data:')
non_null = df_status[df_status[col_k].notna()][['کد', col_k]]
print(non_null.to_string())

# For 4101 and 4108 specifically
print()
for code in [4101, 4108]:
    r = df_status[df_status['كد'] == code]
    if len(r) > 0:
        r = r.iloc[0]
        print(f'کد {code}:')
        print(f'  K = {r.get(col_k, "N/A")}')
        print()
