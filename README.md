# Planning-character typology of Japan's New Towns (ISAIA 2026) — classification and verification scripts

This repository contains the scripts that reproduce the classification of Japan's New Towns into eight planning-character types and all numbers reported in:

> Tomobuchi, T., Nakazawa, S., Miyazaki, Y. and Hayashi, K. (2026) Planning-Character Typology of Japan's New Towns: A Human–AI Approach. Paper presented at ISAIA 2026, 19–22 October 2026. [Proceedings reference to be added after publication]

日本語の説明は下にあります。

## Contents

| Path | Description |
|---|---|
| `data/001257060_3.xls` | Primary source: MLIT, *National list of New Towns* (FY2018). Unchanged copy of the file used in the paper (MD5 `4c4126efc27e20a02b20d25cd5505a27`) |
| `scripts/blind_reimpl.py` | Classification implemented only from the paper's text (Table 2 category boundaries, appendix score formulas and classification rule). Prints the counts by type and checks them against the published values |
| `scripts/ISAIA_verify_all.py` | Recomputes every number reported in the paper from the primary source and compares it with the published value (90 checks) |
| `scripts/threshold_perturbation.py` | Cut-point perturbation (validity line V4) with a selectable random-number generator |
| `scripts/candidate_axes_record.py` | Recomputes the record of all ten candidate axes (eight adopted, two rejected) and writes `CANDIDATE_AXES.md` |
| `CANDIDATE_AXES.md` | Record of the candidate axes: decision, evidence and reason for each (Section 3 of the paper) |
| `requirements.txt` | Library versions used |

## How to run

Python 3.12 with the versions in `requirements.txt` (`pip install -r requirements.txt`). On Windows, set `PYTHONIOENCODING=utf-8` so that the output can be printed.

```
python scripts/blind_reimpl.py data/001257060_3.xls        # 14/14 match with the published classification
python scripts/ISAIA_verify_all.py data/001257060_3.xls    # RESULT: 90/90 PASS
python scripts/threshold_perturbation.py --rng generator   # perturbation with the generator used for publication (seed 42)
python scripts/candidate_axes_record.py                    # record of the ten candidate axes -> CANDIDATE_AXES.md
```

Results: 2,022 New Towns, 185 excluded for missing attributes, 1,837 classified; types T1a 369, T1b 207, T2a 184, T2b 191, T3a 254, T3b 204, T4a 205, T4b 223; priority set (T3b + T4b) 427.

## Random numbers and a correction

The cut-point perturbation uses `numpy.random.default_rng(42)` (NumPy Generator), as at publication. NumPy does not guarantee that the Generator's stream stays the same across versions, so the perturbation figures are conditional on the library versions in `requirements.txt`. Repeating the analysis with 11 seeds and two generators (22 runs of 500 trials each) gave the following ranges, and the published values lie at their centre:

| Measure | Published | Range over 22 runs |
|---|---|---|
| Eight-type retention | 87.2% | 86.5–87.8% |
| Main-type retention | 89.5% | 88.8–89.9% |
| Fully stable | 61.1% | 61.0–61.7% |
| Priority-set type retention | 82.9% | 81.7–83.9% |
| Priority-set size, 5th–95th percentile | **281–482 (corrected)** | 276–285 / 476–486 |

**Correction**: the paper reported the 5th–95th percentile of the priority-set size as 284–484. This could not be reproduced with the published configuration; the reproducible value is **281–482**. The other perturbation figures are reproduced exactly.

## Source data and terms of use

`data/001257060_3.xls`: Ministry of Land, Infrastructure, Transport and Tourism (MLIT), 全国のニュータウンリスト（平成30年度作成）, https://www.mlit.go.jp/common/001257060.xls (listed on https://www.mlit.go.jp/totikensangyo/totikensangyo_tk2_000065.html). Redistributed unchanged under the Government of Japan Standard Terms of Use (Version 2.0), which are compatible with CC BY 4.0. The scripts derive classifications from this file; the derived classifications are not MLIT products.

The scripts are released under the MIT License (`LICENSE`).

---

## 日本語

国際会議 ISAIA 2026 の論文（Tomobuchi, Nakazawa, Miyazaki, Hayashi「Planning-Character Typology of Japan's New Towns: A Human–AI Approach」）で用いた、全国ニュータウンの計画性格類型（8類型）の分類と、論文中のすべての数値を一次資料から再現するスクリプトです。

- `scripts/blind_reimpl.py`：論文の記述（表2の区分境界、付録のスコア式と分類規則）だけから実装した分類。確定値と 14/14 で一致します
- `scripts/ISAIA_verify_all.py`：論文に記載したすべての数値を一次資料から再計算し、記載値と照合します（90項目、90/90 PASS）
- `scripts/threshold_perturbation.py`：区分値の摂動（妥当性の検証 V4）。乱数生成器を選べます
- `scripts/candidate_axes_record.py` と `CANDIDATE_AXES.md`：候補軸10案（採用8、却下2）の採否、根拠、理由の記録。数値は一次資料から計算し直したもの
- `data/001257060_3.xls`：国土交通省「全国のニュータウンリスト（平成30年度作成）」。論文で用いたファイルをそのまま収録しています。政府標準利用規約（第2.0版）に基づき、出典を明記して再配布しています

**訂正**：論文で優先集合サイズの5〜95パーセンタイルを 284–484 と記載しましたが、公表時の設定では再現できず、再現できる値は **281–482** です。そのほかの摂動の数値は、公表時の設定（Generator、seed 42）で正確に再現されます。
