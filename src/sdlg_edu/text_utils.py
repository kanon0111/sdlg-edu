"""
Utility helpers for text normalization / template cleanup.
This module intentionally keeps deps minimal and deterministic.
"""

from __future__ import annotations
import re
import unicodedata

_ws_re = re.compile(r"\s+")
_tag_re = re.compile(r"[<\[{](.*?)[>\]}]")
_tpl_re = re.compile(r"\{\{.*?\}\}|\(\(.*?\)\)")
_quote_pairs = [
    ("“", '"'), ("”", '"'), ("„", '"'), ("‟", '"'),
    ("’", "'"), ("‘", "'"),
    ("＂", '"'), ("＇", "'"),
]
_punct_map = {
    "：": ":", "；": ";", "，": ",", "．": ".",
    "！": "!", "？": "?", "（": "(", "）": ")",
    "「": "「", "」": "」", "『": "『", "』": "』",
}

def _normalize_unicode(s: str) -> str:
    # NFCで統一、よくある全角記号を半角へ（和文引用符は維持）
    s = unicodedata.normalize("NFC", s)
    for k, v in _punct_map.items():
        s = s.replace(k, v)
    for k, v in _quote_pairs:
        s = s.replace(k, v)
    return s

def _cleanup_templates(s: str) -> str:
    # {{TEMPLATE}} / ((TEMPLATE)) を削除、<placeholder> や [placeholder] を中身のみに
    s = _tpl_re.sub("", s)
    s = _tag_re.sub(lambda m: m.group(1), s)
    return s

def _squeeze_ws(s: str) -> str:
    # 連続スペース・改行を1個に
    s = _ws_re.sub(" ", s).strip()
    return s

def _clamp_ja_sentences(s: str, max_sentences: int = 3) -> str:
    """
    日本語説明を2〜3文に抑える簡易分割（。！？）で判定。
    """
    # 文区切りの目安：「。」「！」「？」＋改行など
    parts = re.split(r"(。|！|!|？|\?)", s)
    # parts は [text, delim, text, delim, ...] 構造になることが多い
    out = []
    sentence = ""
    for chunk in parts:
        sentence += chunk
        if chunk in ("。", "！", "!", "？", "?"):
            out.append(sentence.strip())
            sentence = ""
        if len(out) >= max_sentences:
            break
    # 区切れずに残った場合は追加（ただし長すぎるとdupに寄与するので控えめに）
    if len(out) < max_sentences and sentence.strip():
        out.append(sentence.strip())
    # 末尾の句点体裁
    text = " ".join(out).strip()
    if text and text[-1] not in ("。", "！", "!", "？", "?"):
        text += "。"
    return text

def de_template_explanation(s: str, max_sentences: int = 3) -> str:
    """
    英文法の日本語解説用に、テンプレ臭・不要なマーカーや余分な空白を除去して
    2〜3文に収める軽量クリーナー。冗長化や5-gram重複の温床を抑える。
    """
    if not isinstance(s, str):
        return s
    s = _normalize_unicode(s)
    s = _cleanup_templates(s)
    s = _squeeze_ws(s)
    s = _clamp_ja_sentences(s, max_sentences=max_sentences)
    return s
