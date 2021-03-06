"""Make random subsets of JSON lines for testing purposes."""

import json
import random
import re
import string

in_file_name = 'listings.txt'
subset_sizes = [100, 100, 200]

def main():
    """Read JSON lines from a file, add ID values, write out random subsets."""

    # Use line numbers as ID values
    items = [json.loads(line) for line in open(in_file_name).readlines()]
    for ix, item in enumerate(items):
        item['id'] = ix + 1

    # Perform an identical shuffle each time.
    random.seed(42)
    random.shuffle(items)

    # Extract components of the new file name.
    match = re.match('^(.*)[.](\w+)$', in_file_name)
    base_name = match.group(1) if match else in_file_name
    suffix = match.group(2) if match else ''

    offset = 0
    for i, size in enumerate(subset_sizes):
        # Make new file name.
        subset_id = string.ascii_lowercase[i]
        out_file_name = '%s_%s.%s' % (base_name, subset_id, suffix)
        # Get subset of items and sort by ID.
        subset = items[offset:offset+size]
        print(out_file_name, len(subset))
        subset.sort(key=lambda item: item['id'])
        # Write to file.
        with open(out_file_name, 'w') as out_f:
            out_f.write('\n'.join(json.dumps(item) for item in subset) + '\n')
        offset += size

if __name__ == '__main__':
    main()

