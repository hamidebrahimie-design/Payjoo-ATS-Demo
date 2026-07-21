import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import os

main = r'D:\Payjoo-ATS-Demo\exam data\_main.xlsx'
df_reg = pd.read_excel(main, sheet_name='ثبت نام')
df_kot = pd.read_excel(main, sheet_name='کتبی')
df_mah = pd.read_excel(main, sheet_name='مهارتی')
df_ac = pd.read_excel(main, sheet_name='کانون')
df_int = pd.read_excel(main, sheet_name='مصاحبه')
df_status = pd.read_excel(main, sheet_name='جدول وضعیت')

all_codes = sorted(df_reg['ExamCode'].dropna().unique())

total_rejected = 0
total_in_stages = 0
problem_codes = []

for code in all_codes:
    code = int(code)
    reg = df_reg[df_reg['ExamCode'] == code]
    rejected = reg[reg['Result'] == 'غیرمجاز']
    accepted = reg[reg['Result'] == 'مجاز']
    n_rejected = len(rejected)
    n_accepted = len(accepted)
    
    if n_rejected == 0:
        continue
    
    total_rejected += n_rejected
    rejected_codes = set(rejected['NationCode'].dropna().astype('Int64').astype(str))
    
    for s_name, df_s in [('کتبی', df_kot), ('مهارتی', df_mah), ('کانون', df_ac), ('مصاحبه', df_int)]:
        sc = df_s[df_s['ExamCode'] == code]
        sc_codes = set(sc['NationCode'].dropna().astype('Int64').astype(str))
        rejected_in = rejected_codes & sc_codes
        if len(rejected_in) > 0:
            total_in_stages += len(rejected_in)
            r_status = df_status[df_status[df_status.columns[2]] == code]
            title = ''
            if len(r_status) > 0:
                title = str(r_status.iloc[0].get('عنوان پست', ''))
            problem_codes.append({
                'code': code,
                'title': title[:40],
                'stage': s_name,
                'n_rejected': n_rejected + n_accepted,
                'n_rejected_in_stage': len(rejected_in),
                'n_stage_total': len(sc_codes),
                'all_nonzero_scores': False,
                'all_zero_scores': True
            })
            # Check if all have zero scores
            score_col = 'ScoreW'
            if s_name == 'مهارتی':
                score_col = 'ScoreS'
            elif s_name == 'مصاحبه':
                score_col = 'ScoreI'
            elif s_name == 'کانون':
                score_col = 'ScoreAC'
            
            scores = []
            for nc in rejected_in:
                row = sc[sc['NationCode'].astype('Int64').astype(str) == nc]
                if len(row) > 0:
                    v = row.iloc[0].get(score_col, 0)
                    if pd.notna(v) and v != 0:
                        problem_codes[-1]['all_zero_scores'] = False
                    if pd.notna(v) and v != 0:
                        pass

print('=' * 80)
print('گزارش کامل: مغایرت غربالگری برای همه کدهای آزمون')
print('=' * 80)

# Group by type
only_in_registration = []  # rejected people who appeared in later stages
reg_result_error = []  # ALL rejected but some in next stage

for pc in problem_codes:
    n_total_reg = pc['n_rejected']
    # Check if this code appears multiple times
    pass

# Reorganize
code_data = {}
for pc in problem_codes:
    c = pc['code']
    if c not in code_data:
        code_data[c] = {'title': pc['title'], 'stages': {}}
    code_data[c]['stages'][pc['stage']] = pc

print()
print(f'تعداد کل کدهای آزمون با رکورد ثبت نام: {len(all_codes)}')
print(f'تعداد کدهای دارای افراد رد شده (غیرمجاز): {len(set(pc["code"] for pc in problem_codes))}')
print(f'تعداد کدهایی که ردشدگان در مراحل بعدی ظاهر شده اند: {len(code_data)}')
print()

if len(code_data) == 0:
    print('هیچ مغایرتی یافت نشد.')
else:
    print('جزئیات کدهای مشکل دار:')
    print()
    for c in sorted(code_data.keys()):
        d = code_data[c]
        print(f'  کد {c} - {d["title"]}')
        # Get total registration
        reg_c = df_reg[df_reg['ExamCode'] == c]
        n_reg = len(reg_c)
        n_rej = len(reg_c[reg_c['Result'] == 'غیرمجاز'])
        n_acc = len(reg_c[reg_c['Result'] == 'مجاز'])
        print(f'    ثبت نام: {n_reg} (مجاز={n_acc}, غیرمجاز={n_rej})')
        
        for stage in sorted(d['stages'].keys()):
            pc = d['stages'][stage]
            print(f'    {stage}: {pc["n_stage_total"]} نفر (از این تعداد {pc["n_rejected_in_stage"]} ردشده در Result)')
        
        # Show status table comparison
        r = df_status[df_status[df_status.columns[2]] == c]
        if len(r) > 0:
            r = r.iloc[0]
            st_elg = r['تعداد واجد شرایط']
            print(f'    جدول وضعیت: تعداد واجد شرایط = {st_elg}')
            if pd.notna(st_elg):
                st_elg_n = int(st_elg)
                # Find first stage count
                first_stage = list(d['stages'].values())[0] if d['stages'] else None
                if first_stage and st_elg_n == first_stage['n_stage_total']:
                    print(f'    ✓ تطابق با اولین مرحله: {st_elg_n}')
                elif first_stage:
                    print(f'    ✗ عدم تطابق: واجد شرایط={st_elg_n} vs مرحله اول={first_stage["n_stage_total"]}')
        
        print()

print('=' * 80)
print('خلاصه:')
all_problems = sum(len(d['stages']) for d in code_data.values())
print(f'{len(code_data)} کد آزمون دارای مغایرت بین غربالگری و مراحل بعدی')
print(f'مجموع {all_problems} مورد ردشده در مراحل بعدی ظاهر شده اند')
print()

# Check for ALL ZERO pattern
zero_codes = []
for c in sorted(code_data.keys()):
    all_zero = True
    for stage, pc in code_data[c]['stages'].items():
        if not pc.get('all_zero_scores', True):
            all_zero = False
    if all_zero:
        zero_codes.append(c)

print(f'از {len(code_data)} کد مشکل دار:')
non_zero = [c for c in code_data if c not in zero_codes]
print(f'  {len(zero_codes)} کد: ردشدگان نمره صفر دارند (احتمالاً غایب محسوب شده اند)')
print(f'  {len(non_zero)} کد: ردشدگان نمره غیرصفر دارند (احتمالاً خطای به روزرسانی Result)')
