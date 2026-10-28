def merge_intervals(intervals):
    items = [tuple(i) for i in intervals]
    for start, end in items:
        if start > end:
            raise ValueError(f"invalid interval: {(start, end)}")
    items.sort()
    merged = []
    for start, end in items:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
