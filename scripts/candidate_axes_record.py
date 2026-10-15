#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
candidate_axes_record.py
Record of the ten candidate axes evaluated in the ISAIA 2026 paper (Section 3): adopted or rejected, and the evidence,
recomputed from the primary source. Writes CANDIDATE_AXES.md next to the repository root.

  python scripts/candidate_axes_record.py            # uses data/001257060_3.xls

The classification logic is taken from ISAIA_verify_all.py (definitions only; the verification itself is not run).
"""
import sys, io, ast, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal

BASE = Path(__file__).parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "data" / "001257060_3.xls"
VERIFY = Path(__file__).parent / "ISAIA_verify_all.py"

tree = ast.parse(VERIFY.read_text(encoding="utf-8"))
keep = [n for n in tree.body
        if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))
        or (isinstance(n, ast.Assign) and all(isinstance(t, ast.Name) and t.id.isupper() for t in n.targets)
            and isinstance(n.value, (ast.List, ast.Tuple, ast.Constant)))]
ns = {}
exec(compile(ast.Module(body=keep, type_ignores=[]), str(VERIFY), "exec"), ns)
load, compute_axes, classify = ns["load"], ns["compute_axes"], ns["classify"]

AX = ["rx1", "rx2", "rx3", "rx4", "rx5", "rx6", "rx7", "rx8"]
raw_df = load(str(SRC))
base = compute_axes(raw_df)
valid = base[AX].notna().all(axis=1)
dv, _, _ = classify(base[valid].copy())
N_ALL, N_CL = len(base), len(dv)

# Adopted axes: computable cases among all NTs, and eight-type Kruskal–Wallis effect size r = sqrt(H / n)
NAMES = {"rx1": "Development period", "rx2": "Planned population density", "rx3": "Planned population scale",
         "rx4": "Developer type", "rx5": "Development method", "rx6": "Contiguity with adjacent NTs",
         "rx7": "Development duration", "rx8": "Geographic location"}
rows = []
for i, a in enumerate(AX, 1):
    H, p = kruskal(*[g[a].values for _, g in dv.groupby("type")])
    rows.append((f"{'①②③④⑤⑥⑦⑧'[i - 1]} {NAMES[a]}", "Adopted",
                 f"computable for {int(base[a].notna().sum()):,} of {N_ALL:,} NTs; eight-type Kruskal–Wallis r = {np.sqrt(H / N_CL):.3f} (p {'< 0.001' if p < 0.001 else f'= {p:.3g}'})",
                 "Meets the admissibility criteria; adopted by the researchers"))

# Rejected 1: expected household size = planned population / planned dwellings (needs the dwelling count)
hh = dv[dv["units"].notna() & (dv["units"] > 0)]
rows.append(("Expected household size (planned population ÷ planned dwellings)", "Rejected",
             f"computable for {len(hh):,} of {N_CL:,} classified NTs ({len(hh) / N_CL * 100:.1f}%), because planned dwelling counts are recorded far less completely than planned population",
             "Adopting it would have reduced the classifiable set by about 45%. Used instead as the external criterion in validity line V6, where its exclusion keeps the test non-circular"))

# Rejected 2: expected income stratum — look for any income-like field in the header of the primary source
raw = pd.read_excel(SRC, engine="xlrd", header=None)
header = " ".join(str(v) for r in range(0, 6) for v in raw.iloc[r].tolist() if str(v) != "nan")
income_terms = ["所得", "収入", "年収", "income"]
found = [t for t in income_terms if t in header]
rows.append(("Expected income stratum", "Rejected",
             "the primary source has no field on residents' income or livelihoods (header searched for: " + ", ".join(income_terms) + f"; found: {found if found else 'none'})",
             "Could not be determined at all from the planning record"))

md5 = hashlib.md5(SRC.read_bytes()).hexdigest()
L = ["# Candidate axes: adopted and rejected", "",
     "Record of the ten candidate axes proposed by the researchers and evaluated for statistical admissibility in the ISAIA 2026 paper (Section 3).",
     "Every candidate evaluated — adopted or not — is listed. All figures are recomputed from the primary source by `scripts/candidate_axes_record.py`.",
     f"Primary source: `{SRC.name}` (MD5 `{md5}`); {N_ALL:,} NTs, of which {N_CL:,} are classified.", "",
     "Admissibility was judged on validity rate, independence, discriminant strength, monotonicity and sensitivity stability; "
     "the eight adopted axes are evaluated in full in `scripts/ISAIA_verify_all.py` (sections S5–S9). "
     "Both rejections stem from the limits of the source record, not from statistical performance.", "",
     "| Candidate | Decision | Evidence | Reason |", "|---|---|---|---|"]
L += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
L += ["", "## 日本語", "",
      "研究者が提案した候補軸10案と、その採否の記録です（論文 第3節）。採用8案、却下2案です。却下はどちらも資料の記録の限界によるもので、統計的な成績によるものではありません。",
      "- 想定世帯人員（計画人口 ÷ 計画戸数）：計画戸数の記載が少なく、分類済みの地区の約55%でしか計算できない。採用すると分類できる地区が約45%減るため却下した。妥当性の検証 V6 の外部基準として用いた",
      "- 想定所得層：ニュータウンリストに住民の所得・生計の項目がなく、判定できない",
      "- 数値はすべて、このスクリプトが一次資料から計算し直したもの"]
out = BASE / "CANDIDATE_AXES.md"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
