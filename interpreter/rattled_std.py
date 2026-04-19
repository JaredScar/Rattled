#
# Rattled Standard Library — Python implementations of built-in algorithms.
#
# This string is prepended verbatim to the transpiled Python output whenever
# one or more of the standard-library symbols (binSer, mergSor, quikSor,
# heapSor, bubSor) are referenced in a Rattled program.
#
RATTLED_STD = '''# ── Rattled Standard Library ──────────────────────────────────────
def binSer(arr, val):
    """Binary search. Returns index of val in sorted arr, or -1 if not found."""
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == val:
            return mid
        elif arr[mid] < val:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

def mergSor(arr):
    """Merge sort. Returns a new sorted list."""
    if len(arr) <= 1:
        return arr[:]
    mid   = len(arr) // 2
    left  = mergSor(arr[:mid])
    right = mergSor(arr[mid:])
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def quikSor(arr):
    """Quick sort. Returns a new sorted list."""
    if len(arr) <= 1:
        return arr[:]
    pivot = arr[len(arr) // 2]
    left  = [x for x in arr if x < pivot]
    mid   = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quikSor(left) + mid + quikSor(right)

def heapSor(arr):
    """Heap sort. Returns a new sorted list."""
    import heapq
    h = arr[:]
    heapq.heapify(h)
    return [heapq.heappop(h) for _ in range(len(h))]

def bubSor(arr):
    """Bubble sort. Returns a new sorted list."""
    arr = arr[:]
    n   = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
# ── End Rattled Standard Library ──────────────────────────────────
'''
