def inflate_box(box, margin):
    x, y, w, h = box
    return (x - margin, y - margin, w + 2 * margin, h + 2 * margin)


def box_iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2 = ax + aw
    ay2 = ay + ah
    bx2 = bx + bw
    by2 = by + bh

    ix1 = max(ax, bx)
    iy1 = max(ay, by)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    intersection = iw * ih
    union = aw * ah + bw * bh - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def filter_boxes_outside_occupied(candidate_boxes, occupied_boxes, max_iou=0.1):
    result = []
    for candidate in candidate_boxes:
        overlaps = any(box_iou(candidate, occupied) > max_iou for occupied in occupied_boxes)
        if not overlaps:
            result.append(candidate)
    return result
