def should_reverify(frame_index, last_verified_frame, interval_frames, suspicious):
    if suspicious:
        return True
    return frame_index - last_verified_frame >= interval_frames
