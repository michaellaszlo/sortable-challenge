import json
import os.path
import string


class Matcher:

    def __init__(self, products, listings=[]):
        self.products = products
        self.listings = listings
        self.counts = {}
        self.match_all_listings()

    def match_all_listings(self):
        for listing in self.listings:
            self.match_listing(listing)
        print('candidate counts:')
        for count, frequency in sorted(self.counts.items()):
            proportion = 100.0 * frequency / len(self.listings)
            print('%d: %d %.1f%%' % (count, frequency, proportion))

    def match_listing(self, listing):
        candidates = []
        for product in self.products:
            if not self.contains(listing.canonical.manufacturer,
                    product.canonical.manufacturer):
                continue
            if not self.contains(listing.canonical.title,
                    product.canonical.model):
                continue
            candidates.append(product)
        count = len(candidates)
        self.counts[count] = self.counts.setdefault(count, 0) + 1
        listing.candidates = candidates

    def contains(self, sequence, sub):
        for start in range(0, len(sequence) - len(sub) + 1):
            okay = True
            for i, word in enumerate(sub):
                if sequence[start + i].text != word.text:
                    okay = False
                    break
            if okay:
                return True
        return False


class Product:

    def __init__(self, data):
        add_data(self, data, 'id', 'product_name', 'manufacturer', 'model')
        canonicalize_strings(self, 'manufacturer', 'model')

    def __str__(self):
        return str((self.manufacturer, self.model))


class Listing:

    def __init__(self, data):
        add_data(self, data, 'id', 'manufacturer', 'title')
        canonicalize_strings(self, 'manufacturer', 'title')

    def __str__(self):
        return str((self.manufacturer, self.title))


class Container:

    def __init__(self, data={}):
        for name, value in data.items():
            setattr(self, name, value)


letters = set(list(string.ascii_lowercase))
digits = set(list(string.digits))

def add_data(item, data, *names):
    """Set item attributes by getting named values from a data dictionary."""
    for name in names:
        value = data[name] if name in data else None
        setattr(item, name, value)
    item.data = data

def canonicalize_strings(item, *names):
    """Convert the named attributes into lists of canonical tokens.""" 
    item.canonical = Container()
    for name in names:
        text = getattr(item, name)
        tokens = make_canonical(text) if text != None else None
        setattr(item.canonical, name, tokens)

def make_canonical(text):
    """Parse text into canonical tokens."""
    tokens = []
    text = text.lower()
    pos = 0
    while pos < len(text):
        ch = text[pos]
        made_token = False
        for char_set in [ letters, digits ]:
            if ch in char_set:
                pos, token = make_token(char_set, text, pos)
                tokens.append(token)
                made_token = True
                break
        if not made_token:
            pos += 1
    return tokens

def make_token(char_set, text, pos):
    """Extract a sequence of characters belonging to the given set."""
    chars = []
    start = pos
    while True:
        if pos == len(text) or text[pos] not in char_set:
            break
        chars.append(text[pos])
        pos += 1
    token = Container()
    token.text = ''.join(chars)
    token.start = start
    return pos, token

def print_tokens(tokens):
    if tokens == None:
        print('None')
    else:
        print(' '.join(token.text for token in tokens))

def load_items(Item, file_path):
    """Make a list of Item objects loaded from a file of JSON lines."""
    items = []
    with open(file_path) as file:
        for ix, line in enumerate(file.readlines()):
            data = json.loads(line)
            # If the data has no ID, use the line number.
            if 'id' not in data:
                data['id'] = ix + 1
            items.append(Item(data))
    return items


if __name__ == '__main__':
    data_dir = 'data/dev'
    products_name = 'products.txt'
    listings_name = 'listings_a.txt'
    products = load_items(Product, os.path.join(data_dir, products_name))
    listings = load_items(Listing, os.path.join(data_dir, listings_name))
    matcher = Matcher(products, listings)

