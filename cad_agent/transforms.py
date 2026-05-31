from __future__ import annotations

import math


def mm(value: float) -> float:
    return value / 1000.0


def mat_mul(a: list[float], b: list[float]) -> list[float]:
    return [sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4)) for r in range(4) for c in range(4)]


def rz(rad: float) -> list[float]:
    c, s = math.cos(rad), math.sin(rad)
    return [c, -s, 0, 0, s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def translate(tx: float, ty: float, tz: float = 0.0) -> list[float]:
    return [1, 0, 0, tx, 0, 1, 0, ty, 0, 0, 1, tz, 0, 0, 0, 1]


def rotate_about_point_z(theta: float, x_mm: float, y_mm: float, local_spin: float = 0.0) -> list[float]:
    return mat_mul(
        rz(theta),
        mat_mul(translate(mm(x_mm), mm(y_mm)), mat_mul(rz(local_spin), translate(mm(-x_mm), mm(-y_mm)))),
    )


def spin_about_fixed_point_z(theta: float, x_mm: float, y_mm: float) -> list[float]:
    return mat_mul(translate(mm(x_mm), mm(y_mm)), mat_mul(rz(theta), translate(mm(-x_mm), mm(-y_mm))))


def orbit_with_absolute_spin_z(orbit: float, x_mm: float, y_mm: float, absolute_spin: float) -> list[float]:
    c, s = math.cos(orbit), math.sin(orbit)
    x_rot = x_mm * c - y_mm * s
    y_rot = x_mm * s + y_mm * c
    return mat_mul(translate(mm(x_rot), mm(y_rot)), mat_mul(rz(absolute_spin), translate(mm(-x_mm), mm(-y_mm))))
