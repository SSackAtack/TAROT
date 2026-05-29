from tarotvision.roi_map import box_iou


def assign_boxes_to_cards(tracked_boxes, candidate_boxes, min_iou=0.5):
    assignments = {}
    used_candidates = set()

    for card_id, tracked_box in tracked_boxes.items():
        best_index = None
        best_iou = 0.0
        for index, candidate in enumerate(candidate_boxes):
            if index in used_candidates:
                continue
            overlap = box_iou(tracked_box, candidate)
            if overlap > best_iou:
                best_iou = overlap
                best_index = index

        if best_index is not None and best_iou >= min_iou:
            assignments[card_id] = candidate_boxes[best_index]
            used_candidates.add(best_index)

    return assignments
