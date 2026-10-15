#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
論文（v66）の記述のみから独立に実装したもの。
既存の step_all_v6.py / ISAIA_verify_all.py のロジックは参照せず、
表2の「Category boundaries」列と付録のスコア式・分類規則の文面だけを根拠とする。

目的：第三者が論文だけを読んで実装した場合に確定値と一致するかを検証する。
"""
import sys
import numpy as np, pandas as pd

SRC = sys.argv[1] if len(sys.argv)>1 else '001257060_3.xls'

# ---- 論文 表2 ⑧より：三大都市圏11府県 / 地方政令8道県 / その他28県 ----
METRO = ['東京','神奈川','千葉','埼玉','愛知','岐阜','三重','大阪','京都','兵庫','奈良']
ORDINANCE = ['北海道','宮城','福岡','広島','静岡','岡山','新潟','熊本']

raw = pd.read_excel(SRC, engine='xlrd', header=None)
df = raw.iloc[6:].copy()
df.columns = ['id','pref','citycode','address','name','nickname','rentan','area',
              'operator','method_code','method','start','c12','end','c14',
              'units','prepop','diff','pop','c19']
df = df[pd.to_numeric(df['id'],errors='coerce').notna()].copy()
for c in ['pop','area','start','end']:
    df[c]=pd.to_numeric(df[c],errors='coerce')

# ---- ① 6=≤1962; 5=1963–67; 4=1968–74; 3=1975–81; 2=1982–91; 1=1992– ----
def ax1(y):
    if pd.isna(y): return np.nan
    y=int(y)
    if y<=1962: return 6
    if y<=1967: return 5
    if y<=1974: return 4
    if y<=1981: return 3
    if y<=1991: return 2
    return 1

# ---- ② 1=≥150; 2=80–149; 3=40–79; 4=<40 persons/ha ----
def ax2(r):
    if pd.isna(r['pop']) or r['pop']==0 or pd.isna(r['area']) or r['area']==0: return np.nan
    v=r['pop']/r['area']
    if v>=150: return 1
    if v>=80: return 2
    if v>=40: return 3
    return 4

# ---- ③ 1=≥50,000; 2=30,000–49,999; 3=10,000–29,999; 4=5,000–9,999; 5=<5,000 ----
def ax3(p):
    if pd.isna(p) or p==0: return np.nan
    if p>=50000: return 1
    if p>=30000: return 2
    if p>=10000: return 3
    if p>=5000: return 4
    return 5

# ---- ④ 1=自治体; 2=公的法人; 3=民間; 4=組合; 5=個人。複合は最小値 ----
PREFS=['北海道','青森','岩手','宮城','秋田','山形','福島','茨城','栃木','群馬','埼玉','千葉','東京',
       '神奈川','新潟','富山','石川','福井','山梨','長野','岐阜','静岡','愛知','三重','滋賀','京都',
       '大阪','兵庫','奈良','和歌山','鳥取','島根','岡山','広島','山口','徳島','香川','愛媛','高知',
       '福岡','佐賀','長崎','熊本','大分','宮崎','鹿児島','沖縄']
def one_dev(s):
    s=s.strip()
    if s=='': return None
    if any(x in s for x in ['機構','公社','公団','住都','公的団体','都市再生','開発公社']): return 2
    if '組合' in s: return 4
    if '個人' in s: return 5
    if '都道府県' in s: return 1
    if any(p in s for p in PREFS): return 1
    if any(x in s for x in ['市','町','村','区']) and '会社' not in s: return 1
    return 3
def ax4(x):
    if pd.isna(x): return np.nan
    parts=str(x).replace('、',',').replace('，',',').replace('・',',').split(',')
    v=[one_dev(p) for p in parts]; v=[q for q in v if q is not None]
    return min(v) if v else np.nan   # 論文：the minimum (most public) value is used

# ---- ⑤ 1=新住法/一団地/旧住造法; 2=開発許可; 3=区画整理その他。複合は先頭 ----
def ax5(r):
    c=r['method_code']
    code=None
    try: code=int(float(str(c).replace('、',',').split(',')[0].strip()))
    except: pass
    if code is None:
        txt=str(c) if (pd.notna(c) and str(c).strip() not in ('','nan')) else str(r['method'])
        f=txt.replace('、',',').replace('，',',').split(',')[0].strip()   # 論文：the first listed
        if '区画整理' in f: code=6
        elif '新住' in f: code=1
        elif '一団地' in f: code=2
        elif '公的' in f: code=3
        elif '開発許可' in f: code=4
        elif '旧住' in f: code=5
        elif f in ('nan',''): return np.nan
        else: code=7
    # 論文の3段階：1=新住法(1)/一団地(2)/旧住造法(5)/公的(3)、2=開発許可(4)、3=区画整理(6)その他(7,8)
    if code in (1,2,3,5): return 1
    if code==4: return 2
    return 3

# ---- ⑥ 0=連たんあり; 1=孤立 ----
def ax6(x):
    return 0 if (pd.notna(x) and str(x).strip()!='') else 1

# ---- ⑦ 1=≥20; 2=15–19; 3=10–14; 4=5–9; 5=<5 years ----
def ax7(r):
    if pd.isna(r['start']) or pd.isna(r['end']): return np.nan
    v=int(r['end'])-int(r['start'])
    if v>=20: return 1
    if v>=15: return 2
    if v>=10: return 3
    if v>=5: return 4
    return 5

# ---- ⑧ 1=三大都市圏; 3=地方政令; 2=その他 ----
def ax8(p):
    p=str(p)
    if any(m in p for m in METRO): return 1
    if any(s in p for s in ORDINANCE): return 3
    return 2

df['a1']=df['start'].apply(ax1)
df['a2']=df.apply(ax2,axis=1)
df['a3']=df['pop'].apply(ax3)
df['a4']=df['operator'].apply(ax4)
df['a5']=df.apply(ax5,axis=1)
df['a6']=df['rentan'].apply(ax6)
df['a7']=df.apply(ax7,axis=1)
df['a8']=df['pref'].apply(ax8)

A_=['a1','a2','a3','a4','a5','a6','a7','a8']
valid=df[A_].notna().all(axis=1)
v=df[valid].copy()

# ---- 付録：A=(①+④×2+⑤−4)/15×6.67+1.89, B=(②+③×2+⑥+⑧−4)/14×8.14+1.86 ----
v['A']=(v['a1']+v['a4']*2+v['a5']-4)/15*6.67+1.89
v['B']=(v['a2']+v['a3']*2+v['a6']+v['a8']-4)/14*8.14+1.86
Am=v['A'].median(); Bm=v['B'].median()

# ---- T1 (A≤Am,B≤Bm) ... 同値は下側 / a-type for ⑦≤Cm(=3) ----
Cm=3
def typ(r):
    A,B=r['A'],r['B']
    m='T1' if (A<=Am and B<=Bm) else 'T2' if (A>Am and B<=Bm) else 'T3' if (A<=Am and B>Bm) else 'T4'
    return m+('a' if r['a7']<=Cm else 'b')
v['type']=v.apply(typ,axis=1)

print("=== 論文の記述のみから実装した結果 ===")
print(f"  総件数 {len(df)} / 欠損 {int((~valid).sum())} / 分類 {len(v)}")
print(f"  Am={Am:.4f}  Bm={Bm:.4f}")
c=v['type'].value_counts()
print("  8類型:", {t:int(c.get(t,0)) for t in ['T1a','T1b','T2a','T2b','T3a','T3b','T4a','T4b']})
print(f"  優先群 T4b+T3b = {int(v['type'].isin(['T4b','T3b']).sum())}")

EXP={'total':2022,'miss':185,'n':1837,'Am':5.0027,'Bm':7.0929,
     'T1a':369,'T1b':207,'T2a':184,'T2b':191,'T3a':254,'T3b':204,'T4a':205,'T4b':223,'prio':427}
ok=[]
ok.append(len(df)==EXP['total']); ok.append(int((~valid).sum())==EXP['miss']); ok.append(len(v)==EXP['n'])
ok.append(abs(Am-EXP['Am'])<0.001); ok.append(abs(Bm-EXP['Bm'])<0.001)
for t in ['T1a','T1b','T2a','T2b','T3a','T3b','T4a','T4b']:
    ok.append(int(c.get(t,0))==EXP[t])
ok.append(int(v['type'].isin(['T4b','T3b']).sum())==EXP['prio'])
print("\n" + "="*60)
print(f"確定値との一致: {sum(ok)}/{len(ok)}" + ("  ✅ 完全一致" if all(ok) else "  ❌ 不一致あり"))
print("="*60)
