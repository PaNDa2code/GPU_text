from typing import List, Tuple
import freetype as ft
import numpy as np


def generate_glyph_geometry(outline: ft.Outline):
    # Each vertex needs: [x, y, u, v]
    # u,v = (0,1) for solid interior
    # u,v = (0,0), (0.5, 0), (1,1) for curve triangles
    vertices = []

    start_idx = 0
    for contour_end in outline.contours:
        raw_points = outline.points[start_idx : contour_end + 1]
        raw_tags = outline.tags[start_idx : contour_end + 1]
        start_idx = contour_end + 1

        if not raw_points:
            continue

        # --- 1. EXPAND IMPLIED POINTS ---
        # We rewrite the contour into a clean list of segments:
        # [(p0, p1, p2), (p2, p3, p4)...] where middle is control, ends are on-curve.
        # For lines, we can treat them as flat curves or handle separately.
        
        # Helper to get point/tag with wrap-around
        def get_pt(i): return raw_points[i % len(raw_points)]
        def get_tag(i): return raw_tags[i % len(raw_tags)]
        
        # Find a safe starting index (first on-curve point)
        # If all are off-curve, it's a special case, but rare in fonts.
        first_on_curve = -1
        for i in range(len(raw_tags)):
            if raw_tags[i] & 1:
                first_on_curve = i
                break
        
        if first_on_curve == -1:
            continue # Skip invalid contour

        # Reorder/Rotate lists so we start with an on-curve point
        curr_points = raw_points[first_on_curve:] + raw_points[:first_on_curve]
        curr_tags = raw_tags[first_on_curve:] + raw_tags[:first_on_curve]

        hull_points = [] # The polygon of on-curve points for the solid fill
        
        # Process the contour
        i = 0
        n = len(curr_points)
        
        # Start point is definitely on-curve due to rotation
        hull_points.append(curr_points[0])
        
        while i < n:
            curr = curr_points[i]
            # Look ahead
            next_i = (i + 1) % n
            next_pt = curr_points[next_i]
            next_tag = curr_tags[next_i]
            
            if next_tag & 1:
                # On -> On (Line)
                # Just add the point to hull, no curve triangle needed
                if i + 1 < n: # Don't duplicate start point if wrapping
                    hull_points.append(next_pt)
                i += 1
            else:
                # On -> Off ...
                # We need to check the point AFTER the off-curve point
                next_next_i = (i + 2) % n
                next_next_pt = curr_points[next_next_i]
                next_next_tag = curr_tags[next_next_i]
                
                if next_next_tag & 1:
                    # On -> Off -> On (Standard Quadratic Bezier)
                    p0 = curr
                    p1 = next_pt
                    p2 = next_next_pt
                    
                    # Add curve geometry
                    vertices.extend([
                        p0[0], p0[1], 0.0, 0.0,
                        p1[0], p1[1], 0.5, 0.0,
                        p2[0], p2[1], 1.0, 1.0
                    ])
                    
                    # Add end point to hull
                    if i + 2 < n:
                        hull_points.append(p2)
                        
                    i += 2
                else:
                    # On -> Off -> Off (Implicit On-Curve Point)
                    # The "real" on-curve point is the midpoint of the two off-curve points
                    p0 = curr
                    p1 = next_pt
                    mid_x = (next_pt[0] + next_next_pt[0]) / 2
                    mid_y = (next_pt[1] + next_next_pt[1]) / 2
                    p2 = (mid_x, mid_y)
                    
                    # Add curve geometry (p0 -> p1 -> Implicit Midpoint)
                    vertices.extend([
                        p0[0], p0[1], 0.0, 0.0,
                        p1[0], p1[1], 0.5, 0.0,
                        p2[0], p2[1], 1.0, 1.0
                    ])
                    
                    # Add the virtual point to the hull
                    hull_points.append(p2)
                    
                    # IMPORTANT: Do NOT advance i by 2. 
                    # The next iteration must start from the virtual midpoint.
                    # We synthesize the list to insert the midpoint for the next loop logic
                    # Or simpler: Update the current point in our localized list logic?
                    # Since we can't easily modify the list we are iterating, 
                    # we hack it: logic treats p2 as the start of next iter.
                    
                    # Because our loop logic relies on `curr_points`, we can't just 'pause'.
                    # Simplest fix: Insert the midpoint into the list for the next iteration to pick up.
                    curr_points.insert(i + 2, p2)
                    curr_tags.insert(i + 2, 1) # Mark as On-Curve
                    n += 1 # List grew
                    
                    # Now we processed p0->p1->p2. 
                    # Next iteration should start at p2. 
                    # p2 is now at index i+2.
                    i += 2 

        # --- 2. TRIANGULATE SOLID HULL ---
        # Use a simple Triangle Fan from the first vertex (hull_points[0]).
        # For Even-Odd filling (parity check), this works even for concave shapes
        # as long as the stencil/accumulation logic is correct.
        
        if len(hull_points) >= 3:
            p0 = hull_points[0]
            for j in range(1, len(hull_points) - 1):
                p1 = hull_points[j]
                p2 = hull_points[j+1]
                
                vertices.extend([
                    p0[0], p0[1], 0.0, 1.0,
                    p1[0], p1[1], 0.0, 1.0,
                    p2[0], p2[1], 0.0, 1.0
                ])

    return np.array(vertices, dtype="float32").reshape((-1,4))
