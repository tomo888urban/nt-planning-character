"""
threshold_perturbation.py
V4 区分値（閾値）摂動の全指標を、乱数生成器を指定して算出する。

  --rng generator    : np.random.default_rng(42)  ISAIA 2026 公表時の設定
  --rng randomstate  : np.random.RandomState(42)  ストリーム互換が保証される設定

分類ロジックは ISAIA_verify_all.py から関数・定数の定義だけを取り出して使う
（検証本体は実行しない。ロジックを複製しない）。
乱数の引き方（呼び出し順・範囲）は ISAIA_verify_all.py S9 と同一。

出力指標:
  8類型維持(%) / 主類型維持(%) / 完全安定(%)          … 論文 87.2 / 89.5 / 61.1
  優先集合の類型維持(%)                                … 論文 82.9
  優先集合サイズ 5–95パーセンタイル                    … 論文 284–484
"""
import sys, io, ast, argparse, hashlib, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parents[1]   # 公開版：リポジトリの直下に data/ がある
SRC = BASE / "data" / "001257060_3.xls"
SRC_MD5 = "4c4126efc27e20a02b20d25cd5505a27"
VERIFY = Path(__file__).parent / "ISAIA_verify_all.py"
PRIORITY = ('T3b', 'T4b')

ap = argparse.ArgumentParser()
ap.add_argument("--rng", choices=["generator", "randomstate"], required=True)
ap.add_argument("--trials", type=int, default=500)
ap.add_argument("--seed", type=int, default=42, help="確定値は42。他の値はモンテカルロ誤差の評価用")
ap.add_argument("--json", help="結果をJSONで保存するパス")
args = ap.parse_args()

md5 = hashlib.md5(SRC.read_bytes()).hexdigest()
if md5 != SRC_MD5:
    sys.exit(f"[STOP] 一次資料のMD5不一致: {md5}")

# ---- ISAIA_verify_all.py から定義（import・関数・定数）だけを取り込む ----
tree = ast.parse(VERIFY.read_text(encoding="utf-8"))
keep = [n for n in tree.body
        if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))
        or (isinstance(n, ast.Assign) and all(isinstance(t, ast.Name) and t.id.isupper()
                                              for t in n.targets)
            and isinstance(n.value, (ast.List, ast.Tuple, ast.Constant)))]
ns = {}
exec(compile(ast.Module(body=keep, type_ignores=[]), str(VERIFY), "exec"), ns)
load, compute_axes, classify = ns['load'], ns['compute_axes'], ns['classify']
AX = ['rx1', 'rx2', 'rx3', 'rx4', 'rx5', 'rx6', 'rx7', 'rx8']

raw = load(str(SRC))
base = compute_axes(raw)
valid = base[AX].notna().all(axis=1)
dv, _, _ = classify(base[valid].copy())
IDX = dv.index
bt = dv['type'].values
n = len(bt)
bprio = np.isin(bt, PRIORITY)

rng = np.random.default_rng(args.seed) if args.rng == "generator" else np.random.RandomState(args.seed)
N = args.trials
match = np.zeros(n); mmatch = np.zeros(n)
prio_size = []
for _ in range(N):
    f = lambda tup: tuple(float(x) * (1 + rng.uniform(-0.10, 0.10)) for x in tup)
    e = tuple(sorted(int(round(x + rng.uniform(-2, 2))) for x in (1962, 1967, 1974, 1981, 1991)))
    dd = compute_axes(raw, dens_cuts=f((150, 80, 40)), scale_cuts=f((50000, 30000, 10000, 5000)),
                      dur_cuts=f((20, 15, 10, 5)), era_cuts=e)
    tt, _, _ = classify(dd.loc[IDX].copy())
    tp = tt['type'].values
    match += (tp == bt)
    mmatch += (np.array([x[:2] for x in tp]) == np.array([x[:2] for x in bt]))
    prio_size.append(int(np.isin(tp, PRIORITY).sum()))

prio_size = np.array(prio_size)
res = {
    "rng": args.rng, "seed": args.seed, "trials": N, "src_md5": md5,
    "numpy": np.__version__, "pandas": pd.__version__,
    "type8_retained_pct": float((match / N).mean() * 100),
    "main4_retained_pct": float((mmatch / N).mean() * 100),
    "fully_stable_pct": float((match / N == 1.0).mean() * 100),
    "priority_type_retained_pct": float((match[bprio] / N).mean() * 100),
    "priority_size_baseline": int(bprio.sum()),
    "priority_size_p05": float(np.percentile(prio_size, 5)),
    "priority_size_p95": float(np.percentile(prio_size, 95)),
    "priority_size_series": prio_size.tolist(),
}
for k, v in res.items():
    if k == "priority_size_series":
        continue
    print(f"  {k:28s} {v:.4f}" if isinstance(v, float) else f"  {k:28s} {v}")
if args.json:
    Path(args.json).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
