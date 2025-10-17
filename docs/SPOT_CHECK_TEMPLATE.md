# 🧪 SPOT_CHECK_TEMPLATE.md
> Local Synthetic Data Factory – Education Edition (sdlg-edu)
> 英文法QA スポットチェックテンプレート（Phase 2-5）

---

## 🎯 目的
1,000件規模の試作生成データから **100件サンプル** を人手チェックし、
自動品質指標（language_match / dup_5gram / toxicity / pii）を補完的に検証する。

---

## 🧭 チェック対象ファイル
outputs/english_grammar_qa.jsonl

> 生成時：`python src/sdlg_edu/run_generate.py --recipe recipes/grammar.jsonl --seed 42 --deterministic --outdir outputs`

---

## ✅ チェック観点

| 項目 | 内容 | 判定例 |
|------|------|--------|
| **形式整合** | `question_en` / `answer_en` / `explanation_ja` の対応が明確か | ○／× |
| **文体統一** | 句読点・大文字小文字・記号が統一されているか | ○／△／× |
| **内容妥当** | 英文法説明が正しいか・誤りや曖昧さがないか | ○／× |
| **重複疑い** | 類似問題や表現の再出がないか（semantic dup 含む） | ○／△／× |
| **日本語品質** | explanation_ja が自然で簡潔か（過剰説明なし） | ○／△／× |

---

## 🧩 チェック表（100件抜粋）

| No | id | Topic | Question (EN) | Answer (EN) | Explanation (JA) | 形式整合 | 文体 | 内容 | 重複 | 備考 |
|----|----|--------|----------------|--------------|------------------|-----------|------|------|------|------|
| 001 | GRAM-000001 | present perfect | Explain the difference between 'I have gone' and 'I went'. | 'I have gone' emphasizes a present result; 'I went' states a past event without present relevance. | 現在完了は現在への結果を示す。一方過去形は過去の事実を述べる。 | ○ | ○ | ○ | ○ |  |
| 002 | GRAM-000002 | articles | Choose the correct article: "I bought __ umbrella because it was raining." | Answer: an | 「an」は母音音で始まる単語に使う。 | ○ | ○ | ○ | ○ |  |
| 003 | GRAM-000003 | present perfect | How does 'She has gone to Paris' differ from 'She went to Paris in 2019'? | Use present perfect for relevance to now; past simple for finished events. | 現在完了は現在との関連を強調。過去形は完了した出来事を述べる。 | ○ | ○ | ○ | ○ |  |
| … | … | … | … | … | … | … | … | … | … | … |

---

## 🗒 チェックログ記録方法
- 確認完了した行に `○` / `×` / `△` を入力。
- 気になる箇所には備考にコメントを残す（例：「過去完了混入」「冠詞ルール説明が曖昧」など）。
- 最終的に集計した結果は別ファイル `docs/SPOT_CHECK_LOG.md` にまとめる。

---

## 📊 集計テンプレ（SPOT_CHECK_LOG.md 用）

| 観点 | ○ | △ | × | 合格率 |
|------|----|----|----|--------|
| 形式整合 | 98 | 2 | 0 | 98% |
| 文体統一 | 95 | 5 | 0 | 95% |
| 内容妥当 | 94 | 4 | 2 | 94% |
| 重複疑い | 97 | 3 | 0 | 97% |
| 日本語品質 | 96 | 4 | 0 | 96% |

> Pass基準：全項目で 90%以上 合格。

---

## 🧾 備考
- チェックはランダム抽出（例：`shuf -n 100 outputs/english_grammar_qa.jsonl`）で行う。
- 明らかな誤りが10件以上あれば再生成（Phase 3-3 に戻る）。
- 完了後、`docs/SPOT_CHECK_LOG.md` をコミットして Phase 3 に進む。

---

_Last updated: 2025-10-17_
