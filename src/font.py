from typing import List, Tuple
import freetype as ft
import numpy as np


def contour_center(points):
    x = sum(p[0] for p in points) / len(points)
    y = sum(p[1] for p in points) / len(points)
    return (x, y)


def flat_lines_points(outline: ft.Outline):
    triangles = []
    start_idx = 0

    for contour_end in outline.contours:
        raw_points = outline.points[start_idx : contour_end + 1]
        raw_tags = outline.tags[start_idx : contour_end + 1]
        
        poly_points = [p for p, tag in zip(raw_points, raw_tags) if tag & 1]

        if len(poly_points) < 3:
            start_idx = contour_end + 1
            raise RuntimeError("Less that 3 points.")

        C = contour_center(poly_points)

        n = len(poly_points)
        for i in range(n):
            p_curr = poly_points[i]
            p_next = poly_points[(i + 1) % n]
            
            triangles.append((C, p_curr, p_next))

        start_idx = contour_end + 1

    return triangles
