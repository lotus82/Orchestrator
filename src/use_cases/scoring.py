"""
Квадратичный спад очков относительно эталонного момента (Ground Truth).
"""

import math


def calculate_score(
    t_true: float,
    t_user: float,
    p_max: int = 1000,
    window: float = 3.0,
) -> tuple[int, float]:
    """
    Возвращает (очки, delta_t).

    score = p_max * (1 - (delta_t / window) ** 2), если delta_t <= window, иначе 0.
    Очки округляются вниз до целого.
    """
    delta_t = abs(t_user - t_true)
    if delta_t > window:
        return 0, delta_t
    raw = p_max * (1.0 - (delta_t / window) ** 2)
    return int(math.floor(raw)), delta_t
