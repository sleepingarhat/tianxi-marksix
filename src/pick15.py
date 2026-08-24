# -*- coding: utf-8 -*-
"""五段 pick15：目標每段 3；不足則他段補 4。"""
from __future__ import annotations

from collections import defaultdict


def band(n: int) -> int:
    if n <= 9:
        return 0
    if n <= 19:
        return 1
    if n <= 29:
        return 2
    if n <= 39:
        return 3
    return 4


def pick15(scores: dict[int, float]) -> list[int]:
    """scores: 號碼 -> 分數；返回 15 個升序號碼。"""
    by_band: list[list[tuple[int, float]]] = [[] for _ in range(5)]
    for n, s in scores.items():
        if 1 <= n <= 49:
            by_band[band(n)].append((n, s))
    for b in by_band:
        b.sort(key=lambda x: (-x[1], x[0]))

    chosen: list[int] = []
    taken = [0] * 5
    # 先每段最多取 3
    for bi in range(5):
        for n, _ in by_band[bi][:3]:
            chosen.append(n)
            taken[bi] += 1

    # 不足 15：從剩餘高分補（允許某段到 4+）
    remain: list[tuple[int, float]] = []
    chosen_set = set(chosen)
    for bi in range(5):
        for n, s in by_band[bi]:
            if n not in chosen_set:
                remain.append((n, s))
    remain.sort(key=lambda x: (-x[1], x[0]))
    for n, _ in remain:
        if len(chosen) >= 15:
            break
        chosen.append(n)

    # 若仍不足（極端），按號碼補
    if len(chosen) < 15:
        for n in range(1, 50):
            if n not in chosen_set and n not in chosen:
                chosen.append(n)
            if len(chosen) >= 15:
                break

    return sorted(chosen[:15])
