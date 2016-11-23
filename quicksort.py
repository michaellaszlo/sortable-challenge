import random

def sort(a, start=0, length=None):
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

if __name__ == '__main__':
    okay = True
    for i in range(10**4):
        a = [ random.randrange(10) for i in range(20) ]
        b = sorted(a)
        c = a[:]
        sort(c)
        if c != b:
            print('original', a)
            print('expected', b)
            print('computed', c)
            okay = False
            break
    print('success' if okay else 'error')

