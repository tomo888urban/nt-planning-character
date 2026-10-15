# Candidate axes: adopted and rejected

Record of the ten candidate axes proposed by the researchers and evaluated for statistical admissibility in the ISAIA 2026 paper (Section 3).
Every candidate evaluated — adopted or not — is listed. All figures are recomputed from the primary source by `scripts/candidate_axes_record.py`.
Primary source: `001257060_3.xls` (MD5 `4c4126efc27e20a02b20d25cd5505a27`); 2,022 NTs, of which 1,837 are classified.

Admissibility was judged on validity rate, independence, discriminant strength, monotonicity and sensitivity stability; the eight adopted axes are evaluated in full in `scripts/ISAIA_verify_all.py` (sections S5–S9). Both rejections stem from the limits of the source record, not from statistical performance.

| Candidate | Decision | Evidence | Reason |
|---|---|---|---|
| ① Development period | Adopted | computable for 2,013 of 2,022 NTs; eight-type Kruskal–Wallis r = 0.378 (p < 0.001) | Meets the admissibility criteria; adopted by the researchers |
| ② Planned population density | Adopted | computable for 1,854 of 2,022 NTs; eight-type Kruskal–Wallis r = 0.514 (p < 0.001) | Meets the admissibility criteria; adopted by the researchers |
| ③ Planned population scale | Adopted | computable for 1,854 of 2,022 NTs; eight-type Kruskal–Wallis r = 0.753 (p < 0.001) | Meets the admissibility criteria; adopted by the researchers |
| ④ Developer type | Adopted | computable for 2,022 of 2,022 NTs; eight-type Kruskal–Wallis r = 0.856 (p < 0.001) | Meets the admissibility criteria; adopted by the researchers |
| ⑤ Development method | Adopted | computable for 2,022 of 2,022 NTs; eight-type Kruskal–Wallis r = 0.423 (p < 0.001) | Meets the admissibility criteria; adopted by the researchers |
| ⑥ Contiguity with adjacent NTs | Adopted | computable for 2,022 of 2,022 NTs; eight-type Kruskal–Wallis r = 0.272 (p < 0.001) | Meets the admissibility criteria; adopted by the researchers |
| ⑦ Development duration | Adopted | computable for 1,987 of 2,022 NTs; eight-type Kruskal–Wallis r = 0.891 (p < 0.001) | Meets the admissibility criteria; adopted by the researchers |
| ⑧ Geographic location | Adopted | computable for 2,022 of 2,022 NTs; eight-type Kruskal–Wallis r = 0.445 (p < 0.001) | Meets the admissibility criteria; adopted by the researchers |
| Expected household size (planned population ÷ planned dwellings) | Rejected | computable for 1,013 of 1,837 classified NTs (55.1%), because planned dwelling counts are recorded far less completely than planned population | Adopting it would have reduced the classifiable set by about 45%. Used instead as the external criterion in validity line V6, where its exclusion keeps the test non-circular |
| Expected income stratum | Rejected | the primary source has no field on residents' income or livelihoods (header searched for: 所得, 収入, 年収, income; found: none) | Could not be determined at all from the planning record |

## 日本語

研究者が提案した候補軸10案と、その採否の記録です（論文 第3節）。採用8案、却下2案です。却下はどちらも資料の記録の限界によるもので、統計的な成績によるものではありません。
- 想定世帯人員（計画人口 ÷ 計画戸数）：計画戸数の記載が少なく、分類済みの地区の約55%でしか計算できない。採用すると分類できる地区が約45%減るため却下した。妥当性の検証 V6 の外部基準として用いた
- 想定所得層：ニュータウンリストに住民の所得・生計の項目がなく、判定できない
- 数値はすべて、このスクリプトが一次資料から計算し直したもの
