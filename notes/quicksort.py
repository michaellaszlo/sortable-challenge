"""An in-place implementation of quicksort."""

import random

def sort(a, start=0, length=None):
    """Recursively sort part of a list."""
    if length == None:
        length = len(a)
    if length < 2:
        return
    pivot_pos = random.randrange(start, start + length)
    left = start
    right = start + length - 1
    pivot = a[pivot_pos]
    a[pivot_pos] = a[right]
    for pos in range(start, right):
        if a[pos] < pivot:
            a[left], a[pos] = a[pos], a[left]
            left += 1
    a[right] = a[left]
    a[left] = pivot
    sort(a, start, left - start)
    sort(a, left + 1, right - left)

def test():
    """Generate random lists and test our sorting against Python's sorting."""
    okay = True
    for i in range(10**4):
        original = [random.randrange(10) for i in range(20)]
        computed = original[:]
        sort(computed)
        expected = sorted(original)
        if computed != expected:
            print('original', original)
            print('expected', expected)
            print('computed', computed)
            okay = False
            break
    print('success' if okay else 'error')


if __name__ == '__main__':
    test()

