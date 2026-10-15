#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ISAIA 2026 fullpaper — 全数値の再現・検証スクリプト
=====================================================
本稿に記載したすべての数値を一次資料 001257060_3.xls から再計算し、
論文中の記載値と突合する。逆算は行わない（記載値は expected として比較のみ）。

実行:  python3 ISAIA_verify_all.py 001257060_3.xls
依存:  pandas, numpy, scipy, xlrd
出力:  各項目の PASS/FAIL と総合判定

対応関係（論文の記載箇所 → 本スクリプトの Section）
  §4 表2・付録  → S1 基本分類・密度区分
  §4 閾値設定    → S2 分位点 / S3 密度と住宅形態 / S4 上限境界の比較
  §5 V2         → S5 効果量（8群・4群）/ S6 軸の必要性
  §5 V3         → S7 軸間独立性
  §5 V4         → S8 感度分析（重み）/ S9 感度分析（閾値）
  §6            → S10 欠損の偏り / S11 地理と単調性
"""
import sys, hashlib
import numpy as np, pandas as pd
from scipy.stats import kruskal, spearmanr, chi2_contingency

SRC = sys.argv[1] if len(sys.argv) > 1 else '001257060_3.xls'
RESULTS = []

def check(label, got, exp, tol=0.05):
    if isinstance(exp, (int, np.integer)) and not isinstance(exp, bool):
        ok = (int(round(got)) == int(exp))
    else:
        ok = abs(float(got) - float(exp)) <= tol
    RESULTS.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:52s} got={got}  paper={exp}")

# ---------- 一次資料の読み込みと8軸の算出（step_all_v6 と同一定義） ----------
PREFS=['北海道','青森','岩手','宮城','秋田','山形','福島','茨城','栃木','群馬','埼玉','千葉','東京',
       '神奈川','新潟','富山','石川','福井','山梨','長野','岐阜','静岡','愛知','三重','滋賀','京都',
       '大阪','兵庫','奈良','和歌山','鳥取','島根','岡山','広島','山口','徳島','香川','愛媛','高知',
       '福岡','佐賀','長崎','熊本','大分','宮崎','鹿児島','沖縄']
METRO=['三重','京都','兵庫','千葉','埼玉','大阪','奈良','岐阜','愛知','東京','神奈川']
SEIREI=['北海道','宮城','岡山','広島','新潟','熊本','福岡','静岡']

def load(src):
    raw = pd.read_excel(src, engine='xlrd', header=None)
    df = raw.iloc[6:].copy()
    df.columns = ['id','pref','citycode','address','name','nickname','rentan','area',
                  'operator','method_code','method','start','c12','end','c14',
                  'units','prepop','diff','pop','c19']
    df = df[pd.to_numeric(df['id'],errors='coerce').notna()].copy()
    df['id']=df['id'].astype(int)
    for c in ['pop','area','start','end','units']:
        df[c]=pd.to_numeric(df[c],errors='coerce')
    return df

def subj(p):
    p=p.strip()
    if p=='': return None
    if any(x in p for x in ['機構','公社','公団','住都','公的団体','都市再生','開発公社']): return 2
    if '組合' in p: return 4
    if '個人' in p: return 5
    if '都道府県' in p: return 1
    if any(pr in p for pr in PREFS): return 1
    if any(x in p for x in ['市','町','村','区']) and '会社' not in p: return 1
    return 3

def compute_axes(df, dens_cuts=(150,80,40), scale_cuts=(50000,30000,10000,5000),
                 dur_cuts=(20,15,10,5), era_cuts=(1962,1967,1974,1981,1991)):
    d=df.copy()
    e=era_cuts
    d['rx1']=d['start'].apply(lambda y: np.nan if pd.isna(y) else
        (6 if y<=e[0] else 5 if y<=e[1] else 4 if y<=e[2] else 3 if y<=e[3] else 2 if y<=e[4] else 1))
    c=dens_cuts
    d['rx2']=d.apply(lambda r: np.nan if (pd.isna(r['pop']) or r['pop']==0 or pd.isna(r['area']) or r['area']==0)
        else (1 if r['pop']/r['area']>=c[0] else 2 if r['pop']/r['area']>=c[1] else 3 if r['pop']/r['area']>=c[2] else 4), axis=1)
    s=scale_cuts
    d['rx3']=d['pop'].apply(lambda p: np.nan if (pd.isna(p) or p==0) else
        (1 if p>=s[0] else 2 if p>=s[1] else 3 if p>=s[2] else 4 if p>=s[3] else 5))
    def rx4(x):
        if pd.isna(x): return np.nan
        parts=str(x).replace('、',',').replace('，',',').replace('・',',').split(',')
        v=[subj(p) for p in parts]; v=[q for q in v if q is not None]
        return min(v) if v else np.nan
    d['rx4']=d['operator'].apply(rx4)
    def code(r):
        cc=r['method_code']
        try: return int(float(str(cc).replace('、',',').split(',')[0].strip()))
        except: pass
        t=str(cc) if (pd.notna(cc) and str(cc).strip() not in ('','nan')) else str(r['method'])
        f=t.replace('、',',').replace('，',',').split(',')[0].strip()
        if '区画整理' in f: return 6
        if '新住' in f: return 1
        if '一団地' in f: return 2
        if '公的' in f: return 3
        if '開発許可' in f: return 4
        if '旧住' in f: return 5
        if f in ('nan',''): return np.nan
        return 7
    m={1:1,2:1,3:1,4:2,5:1,6:3,7:3,8:3}
    d['rx5']=d.apply(code,axis=1).map(lambda x: m.get(int(x),np.nan) if pd.notna(x) else np.nan)
    d['rx6']=d['rentan'].apply(lambda x:0 if (pd.notna(x) and str(x).strip()!='') else 1)
    u=dur_cuts
    def rx7(r):
        if pd.isna(r['start']) or pd.isna(r['end']): return np.nan
        v=int(r['end'])-int(r['start'])
        return 1 if v>=u[0] else 2 if v>=u[1] else 3 if v>=u[2] else 4 if v>=u[3] else 5
    d['rx7']=d.apply(rx7,axis=1)
    def rx8(p):
        p=str(p)
        if any(x in p for x in METRO): return 1
        if any(x in p for x in SEIREI): return 3
        return 2
    d['rx8']=d['pref'].apply(rx8)
    return d

def classify(dv):
    dv=dv.copy()
    dv['A_score']=(dv['rx1']+dv['rx4']*2+dv['rx5']-4)/15*6.67+1.89
    dv['B_score']=(dv['rx2']+dv['rx3']*2+dv['rx6']+dv['rx8']-4)/14*8.14+1.86
    dv['C_score']=dv['rx7']*2
    Am=dv['A_score'].median(); Bm=dv['B_score'].median()
    def cl(r):
        A,B,r7=r['A_score'],r['B_score'],r['rx7']
        m='T1' if(A<=Am and B<=Bm) else 'T2' if(A>Am and B<=Bm) else 'T3' if(A<=Am and B>Bm) else 'T4'
        return m+('a' if r7<=3 else 'b')
    dv['type']=dv.apply(cl,axis=1)
    return dv,Am,Bm

AX=['rx1','rx2','rx3','rx4','rx5','rx6','rx7','rx8']
raw=load(SRC); base=compute_axes(raw)
valid=base[AX].notna().all(axis=1)
dv,Am,Bm=classify(base[valid].copy())
n=len(dv); IDX=dv.index
print(f"MD5(input)={hashlib.md5(open(SRC,'rb').read()).hexdigest()}\n")

# ---------- S1 基本分類 ----------
print("== S1 基本分類（§6・表5）==")
check("総件数", len(base), 2022); check("欠損", int((~valid).sum()), 185)
check("分類", n, 1837); check("欠損率(%)", (~valid).sum()/len(base)*100, 9.1)
check("Am", Am, 5.003, 0.001); check("Bm", Bm, 7.093, 0.001)
for t,e in [('T1a',369),('T1b',207),('T2a',184),('T2b',191),('T3a',254),('T3b',204),('T4a',205),('T4b',223)]:
    check(f"{t}", int((dv['type']==t).sum()), e)
check("高リスク群 T4b+T3b", int(dv['type'].isin(['T4b','T3b']).sum()), 427)
check("高リスク群(%)", dv['type'].isin(['T4b','T3b']).mean()*100, 23.2)

# ---------- S2 密度区分と分位点 ----------
print("\n== S2 密度区分・分位点（§4・付録）==")
dv['dens']=dv['pop']/dv['area']
for lab,m,e in [('α<40',dv['dens']<40,66),('β40-79',(dv['dens']>=40)&(dv['dens']<80),584),
                ('γ80-149',(dv['dens']>=80)&(dv['dens']<150),1024),('δ≥150',dv['dens']>=150,163)]:
    check(f"密度 {lab}", int(m.sum()), e)
check("δ構成比(%)", (dv['dens']>=150).mean()*100, 8.9, 0.1)
check("密度中央値", dv['dens'].median(), 90.2, 0.1)
for cut,e in [(40,3.6),(80,35.4),(150,91.1)]:
    check(f"{cut}人/ha の分位点(%)", (dv['dens']<cut).mean()*100, e, 0.1)

# ---------- S3 密度帯と住宅形態 ----------
print("\n== S3 密度と住宅形態（§4）==")
ok=dv[dv['units'].notna()&(dv['units']>0)].copy()
ok['udens']=ok['units']/ok['area']
check("戸数データ有効", len(ok), 1013)
check("戸数データ有効率(%)", len(ok)/n*100, 55.1, 0.1)
for lab,m,eu,ea in [('80-149',(ok['dens']>=80)&(ok['dens']<150),27.2,367),
                    ('≥150',ok['dens']>=150,47.0,213)]:
    s=ok[m]
    check(f"{lab} 戸/ha中央値", s['udens'].median(), eu, 0.1)
    check(f"{lab} 粗面積㎡/戸", 10000/s['udens'].median(), ea, 1.5)

# ---------- S4 上限境界の比較 ----------
print("\n== S4 密度上限境界の比較（§4）==")
bt=dv['type'].values
def alt_top(top):
    d2=compute_axes(raw, dens_cuts=(top,80,40))
    t2,_,_=classify(d2.loc[IDX].copy()); return t2['type'].values
for top,e in [(100,93.5),(120,98.3),(200,99.5)]:
    check(f"上限{top} 一致率(%)", (alt_top(top)==bt).mean()*100, e, 0.2)
H,_=kruskal(*[g['rx2'].values for _,g in dv.groupby('type')])
check("rx2 効果量(境界150)", np.sqrt(H/n), 0.514, 0.002)
d100=compute_axes(raw, dens_cuts=(100,80,40)); t100,_,_=classify(d100.loc[IDX].copy())
H2,_=kruskal(*[g['rx2'].values for _,g in t100.groupby('type')])
check("rx2 効果量(境界100)", np.sqrt(H2/n), 0.628, 0.002)
check("境界100の最上位区分(%)", (t100['rx2']==1).mean()*100, 35.3, 0.2)
# δ帯を統合（境界廃止）
dmg=base.copy()
dmg['rx2']=dmg.apply(lambda r: np.nan if (pd.isna(r['pop']) or r['pop']==0 or pd.isna(r['area']) or r['area']==0)
    else (2 if r['pop']/r['area']>=80 else 3 if r['pop']/r['area']>=40 else 4),axis=1)
tmg,Am2,Bm2=classify(dmg.loc[IDX].copy())
check("境界廃止 類型変化件数", int((tmg['type'].values!=bt).sum()), 12)
check("境界廃止 変化率(%)", (tmg['type'].values!=bt).mean()*100, 0.65, 0.02)
check("境界廃止でも Am 不変", abs(Am2-Am)<1e-9, True, 0)
check("境界廃止でも優先群維持", int((np.isin(bt,['T4b','T3b']) & np.isin(tmg['type'].values,['T4b','T3b'])).sum()), 427)

# ---------- S5 効果量 ----------
print("\n== S5 効果量（§5 V2・表4）==")
EXP8={'rx1':0.378,'rx2':0.514,'rx3':0.753,'rx4':0.856,'rx5':0.423,'rx6':0.272,'rx7':0.891,'rx8':0.445}
for a,e in EXP8.items():
    H,p=kruskal(*[g[a].values for _,g in dv.groupby('type')])
    check(f"8群KW {a}", np.sqrt(H/n), e, 0.002)
    RESULTS.append(p<0.001)
dv['main']=dv['type'].str[:2]
for a,e in [('rx3',0.747),('rx4',0.834),('rx7',0.180)]:
    H,_=kruskal(*[g[a].values for _,g in dv.groupby('main')])
    check(f"4群KW {a}", np.sqrt(H/n), e, 0.002)

# ---------- S6 軸の必要性 ----------
print("\n== S6 軸の必要性（§5 V2）==")
EXPN={'rx7':55.1,'rx4':61.0,'rx3':76.3,'rx6':80.8,'rx5':89.0,'rx8':90.8,'rx2':92.6,'rx1':93.7}
for a,e in EXPN.items():
    tmp=dv.copy(); tmp[a]=dv[a].median()
    tt,_,_=classify(tmp)
    check(f"{a} 無効化 一致率(%)", (tt['type'].values==bt).mean()*100, e, 0.2)

# ---------- S7 軸間独立性 ----------
print("\n== S7 軸間独立性（§5 V3）==")
check("A×B ρ", spearmanr(dv['A_score'],dv['B_score'])[0], 0.019, 0.002)
check("A×C ρ", spearmanr(dv['A_score'],dv['C_score'])[0], 0.309, 0.002)
mx=0; pair=None
for i in range(8):
    for j in range(i+1,8):
        r=abs(spearmanr(dv[AX[i]],dv[AX[j]])[0])
        if r>mx: mx, pair = r, (AX[i],AX[j])
check(f"28ペア最大|ρ| {pair}", mx, 0.339, 0.002)
check("全28ペア ≤0.40", mx<=0.40, True, 0)

# ---------- S8 感度分析（重み） ----------
print("\n== S8 感度分析・重み（§5 V4）==")
np.random.seed(42)
vals={c:dv[c].values for c in AX}
res=[]
for _ in range(2000):
    wA=np.random.uniform(0.9,1.1,3); wB=np.random.uniform(0.9,1.1,4)
    A=((vals['rx1']*wA[0]+vals['rx4']*2*wA[1]+vals['rx5']*wA[2]-4)/15*6.67+1.89)
    B=((vals['rx2']*wB[0]+vals['rx3']*2*wB[1]+vals['rx6']*wB[2]+vals['rx8']*wB[3]-4)/14*8.14+1.86)
    am,bm=np.median(A),np.median(B)
    lab=np.where((A<=am)&(B<=bm),'T1',np.where((A>am)&(B<=bm),'T2',np.where((A<=am)&(B>bm),'T3','T4')))
    res.append(np.char.add(lab, np.where(vals['rx7']<=3,'a','b')))
arr=np.array(res)
stab=np.array([np.unique(arr[:,i],return_counts=True)[1].max()/2000 for i in range(n)])
check("確定型(>0.70)", int((stab>0.70).sum()), 1609)
check("確定型(%)", (stab>0.70).mean()*100, 87.6, 0.1)
check("完全確定(=1.0)", int((stab==1.0).sum()), 1575)
check("完全確定(%)", (stab==1.0).mean()*100, 85.7, 0.1)
check("境界型(≤0.70)", int((stab<=0.70).sum()), 228)
adj=0
for i in np.where(stab<=0.70)[0]:
    u=np.unique(arr[:,i])
    mains={x[:2] for x in u}
    if len(mains)<=2 and not ({'T1','T4'}<=mains or {'T2','T3'}<=mains): adj+=1
check("境界型のうち隣接移動", adj, 222, 3)

# ---------- S9 感度分析（閾値） ----------
print("\n== S9 感度分析・閾値（§5 V4）==")
# 公表時の設定（Generator）を維持する。再現は requirements-lock.txt の固定環境で保証する。
# 2026-09-30: 許容誤差を0.05に縮め、優先集合の検査を追加。
#   優先集合サイズの公表値 284–484 は再現不能のため、同じ計算で再現できる 281–482 に訂正。
#   シード間のモンテカルロ誤差（10シード）は記録を参照。
#   記録: docs/確定値変更記録_乱数統一_20260930.md
rng=np.random.default_rng(42); match=np.zeros(n); mmatch=np.zeros(n); N=500
psize=[]; bprio=np.isin(bt,['T3b','T4b'])
for _ in range(N):
    f=lambda tup: tuple(float(x)*(1+rng.uniform(-0.10,0.10)) for x in tup)
    e=tuple(sorted(int(round(x+rng.uniform(-2,2))) for x in (1962,1967,1974,1981,1991)))
    dd=compute_axes(raw, dens_cuts=f((150,80,40)), scale_cuts=f((50000,30000,10000,5000)),
                    dur_cuts=f((20,15,10,5)), era_cuts=e)
    tt,_,_=classify(dd.loc[IDX].copy())
    tp=tt['type'].values
    match += (tp==bt)
    mmatch += (np.array([x[:2] for x in tp])==np.array([x[:2] for x in bt]))
    psize.append(int(np.isin(tp,['T3b','T4b']).sum()))
check("閾値摂動 8類型維持(%)", (match/N).mean()*100, 87.2, 0.05)
check("閾値摂動 主類型維持(%)", (mmatch/N).mean()*100, 89.5, 0.05)
check("閾値摂動 完全安定(%)", (match/N==1.0).mean()*100, 61.1, 0.05)
check("閾値摂動 優先集合の類型維持(%)", (match[bprio]/N).mean()*100, 82.9, 0.05)
check("閾値摂動 優先集合サイズ P5（公表284→訂正281）", int(round(np.percentile(psize,5))), 281)
check("閾値摂動 優先集合サイズ P95（公表484→訂正482）", int(round(np.percentile(psize,95))), 482)

# ---------- S10 欠損 ----------
print("\n== S10 欠損の偏り（§6）==")
b2=base.copy(); b2['miss']=~valid
chi2,p,dof,_=chi2_contingency(pd.crosstab(b2['rx1'],b2['miss']))
check("欠損×rx1 χ²", chi2, 141.85, 0.5); check("df", dof, 5); RESULTS.append(p<0.001)

# ---------- S11 地理・単調性 ----------
print("\n== S11 地理と単調性（表2）==")
for g,e in [(1,6.8),(2,9.9),(3,27.5)]:
    s=dv[dv['rx8']==g]
    check(f"rx8={g} T4b出現率(%)", (s['type']=='T4b').mean()*100, e, 0.1)

print("\n"+"="*66)
print(f"RESULT: {sum(RESULTS)}/{len(RESULTS)} PASS" + ("  ✅ ALL PASS" if all(RESULTS) else "  ❌ FAIL あり"))
print("="*66)
