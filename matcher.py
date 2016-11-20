import json
import os.path
import string


class Matcher:

    def __init__(self, products, listings=[]):
        self.products, self.listings = products, listings
        self.match_all_products()
        self.print_candidate_counts()
        #self.output_json()

    def match_all_products(self):
        """Iterate over products first to match them with listings. This
        approach is faster than iterating over listings first, due to our use
        of token indexing to shrink the set of listings to consider for a
        product. It only makes sense to index the listings, not the products,
        because we recognize a match when a listing contains a list of product
        tokens. In other words, the product tokens act as a query and the
        listing tokens act as a document to which we apply the query. Thus,
        it is the listings (the documents) that must be indexed.
        """
        self.index_all_listings()
        for listing in self.listings:
            listing.candidates = []
        for product in self.products:
            self.match_product(product)

    def index_all_listings(self):
        """Index the listings using their manufacturer and title tokens."""
        for field in [ 'manufacturer', 'title' ]:
            index = {}
            for listing in self.listings:
                for token in getattr(listing.canonical, field):
                    index.setdefault(token.text, set()).add(listing)
            setattr(self, field + '_index', index)

    def match_product(self, product):
        """Consider the given product as a match candidate for each listing."""
        listings = self.listings
        # Use token indices to get a smaller set of listings.
        for listing_field, product_field in [
                ('manufacturer', 'manufacturer'),
                ('title', 'model') ]:
            try:
                index = getattr(self, listing_field + '_index')
            except AttributeError:
                break
            tokens = getattr(product.canonical, product_field)
            # For each product token, find the set of listings that include the
            #  token. Use the smallest such set. (Set intersection would yield
            #  a smaller set but increase the overall computational cost.)
            for token in tokens:
                if token.text not in index:
                    return
                try_listings = index[token.text]
                if len(try_listings) < len(listings):
                    listings = try_listings
        for listing in self.listings:
            if self.listing_may_match_product(listing, product):
                listing.candidates.append(product)

    def match_all_listings(self):
        """Iterate over listings first to match them with products. This
        produces the same results as iterating over products first, but it
        is slower because we can't take advantage of token indexing to
        quickly shrink the set of products.
        """
        for listing in self.listings:
            self.match_listing(listing)

    def match_listing(self, listing):
        """Find products that may match the given listing."""
        listing.candidates = []
        for product in self.products:
            if Matcher.listing_may_match_product(listing, product):
                listing.candidates.append(product)

    @staticmethod
    def listing_may_match_product(listing, product):
        """Decide whether a listing is potentially matched by a product.
        If a listing's manufacturer and title tokens include a product's
        manufacturer and model tokens, respectively, as sublists, we consider
        the product to be a potential match for the listing.
        """
        if not Matcher.contains(listing.canonical.manufacturer,
                product.canonical.manufacturer):
            return False
        if not Matcher.contains(listing.canonical.title,
                product.canonical.model):
            return False
        return True

    @staticmethod
    def contains(tokens, sublist):
        """Determine whether a token list contains a given sublist."""
        for start in range(0, len(tokens) - len(sublist) + 1):
            okay = True
            for i, word in enumerate(sublist):
                if tokens[start + i].text != word.text:
                    okay = False
                    break
            if okay:
                return True
        return False

    def print_candidate_counts(self):
        """Count each listing's candidates and show the count frequencies."""
        counts = {}
        for listing in self.listings:
            count = len(listing.candidates)
            counts[count] = counts.setdefault(count, 0) + 1
        print('candidate count frequencies:')
        for count, frequency in sorted(counts.items()):
            proportion = 100.0 * frequency / len(self.listings)
            print('%d: %d %.1f%%' % (count, frequency, proportion))
    
    def output_json(self):
        """Display the listings together with their candidate products."""
        json_listings = []
        for listing in self.listings:
            data_plus = listing.data.copy()
            data_plus['candidates'] = [ product.data for
                    product in listing.candidates ]
            json_listings.append(data_plus)
        print('var listings = %s;' % json.dumps(json_listings))


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

letters = set(list(string.ascii_lowercase))
digits = set(list(string.digits))

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
    """Extract a sequence of characters belonging to a character set."""
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
    """Make a list of Item objects based on a file of JSON lines."""
    items = []
    with open(file_path) as file:
        for ix, line in enumerate(file.readlines()):
            data = json.loads(line)
            # If the data has no ID, use the line number.
            if 'id' not in data:
                data['id'] = ix + 1
            items.append(Item(data))
    return items

def main():
    data_dir = 'data/dev'
    products_name = 'products.txt'
    listings_name = 'listings_a.txt'
    products = load_items(Product, os.path.join(data_dir, products_name))
    listings = load_items(Listing, os.path.join(data_dir, listings_name))
    matcher = Matcher(products, listings)


if __name__ == '__main__':
    main()

