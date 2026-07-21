import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd

main = r'D:\Payjoo-ATS-Demo\exam data\_main.xlsx'
df_reg = pd.read_excel(main, sheet_name='ثبت نام')
df_kot = pd.read_excel(main, sheet_name='کتبی')
df_mah = pd.read_excel(main, sheet_name='مهارتی')
df_ac = pd.read_excel(main, sheet_name='کانون')
df_int = pd.read_excel(main, sheet_name='مصاحبه')
df_status = pd.read_excel(main, sheet_name='جدول وضعیت')

for code in [4155, 4166, 4167, 4178]:
    print('='*70)
    print(f'کد آزمون {code}')
    print('='*70)
    
    r = df_status[df_status['کد'] == code]
    if len(r) > 0:
        r = r.iloc[0]
        print(f'  عنوان: {r["عنوان پست"]}')
        print(f'  واحد: {r["واحد متقاضی"]}')
        print(f'  مسیر: {r["مسیر پیشنهادی (عنوان)"]}')
        cnt_reg = r['تعداد ثبت\u200cنام']
        cnt_elg = r['تعداد واجد شرایط']
        print(f'  تعداد ثبت: {cnt_reg}')
        print(f'  واجد شرایط: {cnt_elg}')
    
    reg = df_reg[df_reg['ExamCode'] == code]
    rejected = set(reg[reg['Result'] == 'غیرمجاز']['NationCode'].dropna().astype('Int64').astype(str))
    accepted = set(reg[reg['Result'] == 'مجاز']['NationCode'].dropna().astype('Int64').astype(str))
    print(f'  کل ثبت نام: {len(reg)} نفر')
    print(f'  رد شده (غیرمجاز): {len(rejected)} نفر')
    print(f'  تایید شده (مجاز): {len(accepted)} نفر')
    
    for s_name, df_s in [('کتبی', df_kot), ('مهارتی', df_mah), ('کانون', df_ac), ('مصاحبه', df_int)]:
        sc = df_s[df_s['ExamCode'] == code]
        sc_codes = set(sc['NationCode'].dropna().astype('Int64').astype(str))
        rejected_in = rejected & sc_codes
        accepted_in = accepted & sc_codes
        unknown = sc_codes - (rejected | accepted)
        
        details = []
        if len(rejected_in) > 0:
            details.append(f'{len(rejected_in)} ردشده')
        if len(accepted_in) > 0:
            details.append(f'{len(accepted_in)} تاییدشده')
        if len(unknown) > 0:
            details.append(f'{len(unknown)} بدون رکورد ثبت')
        
        detail_str = ', '.join(details) if details else '0 نفر'
        print(f'  {s_name} ({len(sc_codes)}): {detail_str}')
        
        if len(rejected_in) > 0:
            print('    ردشدگان حاضر:')
            for nc in list(rejected_in)[:5]:
                row = sc[sc['NationCode'].astype('Int64').astype(str) == nc].iloc[0]
                score = row.get('ScoreW', row.get('ScoreS', row.get('ScoreI', row.get('ScoreAC', '?'))))
                print(f'       کد ملی {nc} - نمره: {score}')
            if len(rejected_in) > 5:
                print(f'       ... و {len(rejected_in)-5} نفر دیگر')
    
    import os
    detail_path = f'D:\\Payjoo-ATS-Demo\\exam data\\{code}.xlsx'
    if os.path.exists(detail_path):
        f_detail = pd.ExcelFile(detail_path)
        print(f'  فایل {code}.xlsx شیت ها: {f_detail.sheet_names}')
        if 'ثبت نام' in f_detail.sheet_names:
            dr = pd.read_excel(detail_path, sheet_name='ثبت نام')
            print(f'  ثبت نام: {len(dr)} ردیف, {len(dr.columns)} ستون')
            for i, c in enumerate(dr.columns):
                letter = chr(65+i) if i < 26 else 'A'+chr(65+i-26)
                s = str(c)[:40]
                print(f'    {letter}: {s}')
    else:
        print(f'  فایل {code}.xlsx وجود ندارد')
    
    print()
