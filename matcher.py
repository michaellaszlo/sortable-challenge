import json
import os.path
import random
import re
import string


class Matcher:

    def __init__(self, products, listings):
        self.products, self.listings = products, listings
        self.match_all_products()
        self.print_candidate_counts()
        self.disambiguate_matches()
        self.print_candidate_counts()

    def match_all_products(self):
        """Iterate over products first to match them with listings. This
        approach is faster than iterating over listings first, due to our use
        of token indexing to shrink the set of listings to consider for a
        product. It only makes sense to index the listings, not the products,
        because we deem a listing to match if it contains a sublist of product
        tokens. In other words, the product tokens act as a query and the
        listing tokens act as a document to which we apply the query. Thus,
        it is the listings (the documents) that must be indexed.
        """
        self.remove_duplicate_products()
        self.index_all_listings()
        for listing in self.listings:
            listing.candidates = []
        for product in self.products:
            self.match_product(product)

    def remove_duplicate_products(self):
        """Discard products that have the same manufacturer, family, and model
        values as a product that occurs earlier in the list. Text values are
        compared in lowercase after stripping non-alphanumeric characters.
        """
        products = []
        product_keys = set()
        reduce_regex = re.compile('[^a-z0-9]', re.IGNORECASE)
        reduce = lambda s: reduce_regex.sub('', s.lower())
        for product in self.products:
            values = [ product.manufacturer ]
            # Some products have no family value. The rascals!
            if hasattr(product, 'family'):
                values.append(product.family)
            values.append(product.model)
            # It's safe to join with a space--we stripped spaces from values.
            key = ' '.join(map(reduce, values))
            if key in product_keys:
                continue
            product_keys.add(key)
            products.append(product)
        self.products = products

    def index_all_listings(self):
        """Index the listings using their manufacturer and title tokens."""
        for field in [ 'manufacturer', 'title' ]:
            index = {}
            for listing in self.listings:
                for token in getattr(listing.tokens, field):
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
                # If the listings weren't indexed, the _index attribute
                #  doesn't exist and we bail out on the first iteration.
                break
            tokens = getattr(product.tokens, product_field)
            # For each product token, find the set of listings that include the
            #  token. Use the smallest such set. (Set intersection would yield
            #  a smaller set but increase the overall computational cost.)
            for token in tokens:
                if token.text not in index:
                    return
                try_listings = index[token.text]
                if len(try_listings) < len(listings):
                    listings = try_listings
        for listing in listings:
            if self.listing_may_match_product(listing, product):
                listing.candidates.append(product)

    def match_all_listings(self):
        """Iterate over listings first to match them with products. This
        produces the same results as iterating over products first, but
        it is slower because we can't take advantage of token indexing to
        quickly shrink the set of products. It is useful for verifying
        the correctness of match_all_products().
        """
        for listing in self.listings:
            self.match_listing(listing)

    def match_listing(self, listing):
        """Find products that may match the given listing."""
        listing.candidates = []
        for product in self.products:
            if self.listing_may_match_product(listing, product):
                listing.candidates.append(product)

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

    def disambiguate_matches(self):
        """Try to resolve cases where a listing has several match candidates."""
        for listing in self.listings:
            candidates = listing.candidates
            # If there are many candidates, assume that the listing does not
            #  describe any particular product.
            if len(candidates) == 0 or len(candidates) > 2:
                continue
            if len(candidates) == 1:
                listing.best_candidate = candidates[0]
                continue
            self.detail_sort(listing, candidates)
            if self.detail_compare(listing, candidates[0], candidates[1]) == 0:
                continue
            listing.best_candidate = candidates[0]

    def detail_sort(self, listing, products, start=0, length=None):
        """Sort products in place, calling detail_compare() on product pairs."""
        a = products
        if length == None:
            length = len(a)
        if length < 2:
            return
        # Use recursive quicksort with random pivot selection.
        pivot_pos = random.randrange(start, start + length)
        left = start
        right = start + length - 1
        pivot = a[pivot_pos]
        a[pivot_pos] = a[right]
        for pos in range(start, right):
            if self.detail_compare(listing, a[pos], pivot) == -1:
                a[left], a[pos] = a[pos], a[left]
                left += 1
        a[right] = a[left]
        a[left] = pivot
        self.detail_sort(listing, products, start, left - start)
        self.detail_sort(listing, products, left + 1, right - left)

    def print_candidate_counts(self):
        """Count each listing's candidates and show the count frequencies."""
        counts = {}
        for listing in self.listings:
            count = len(listing.candidates)
            if listing.best_candidate != None:
                count = 1
            counts[count] = counts.setdefault(count, 0) + 1
        print('candidate count frequencies:')
        for count, frequency in sorted(counts.items()):
            proportion = 100.0 * frequency / len(self.listings)
            print('%d: %d %.1f%%' % (count, frequency, proportion))
        print('')
    
    def output_json(self, file):
        """Convert products and listings into dictionaries, then print JSON."""
        product_items = len(self.products) * [ None ]
        for i, product in enumerate(self.products):
            item = product_items[i] = { 'id': product.id }
            for field in [ 'manufacturer', 'family', 'model' ]:
                # A product may not have the family attribute.
                if not hasattr(product, field):
                    continue
                # Make a dictionary containing text and tokens.
                web_tokens = item[field] = { 'text': getattr(product, field) }
                web_tokens['tokenSpans'] = [ token.span for
                        token in getattr(product.tokens, field) ]
        file.write('var products = %s;\n' % (json.dumps(product_items)))
                #sort_keys=True, indent=2)))
        listing_items = len(self.listings) * [ None ]
        for i, listing in enumerate(self.listings):
            item = listing_items[i] = { 'id': listing.id }
            for field in [ 'manufacturer', 'title' ]:
                # Make a dictionary containing text and tokens.
                web_tokens = item[field] = { 'text': getattr(listing, field) }
                web_tokens['tokenSpans'] = [ token.span for
                        token in getattr(listing.tokens, field) ]
            listing.candidates.sort(key=lambda p: p.id)
            item['candidateKeys'] = [ product.id for
                    product in listing.candidates ]
            if listing.best_candidate != None:
                item['bestCandidateKey'] = listing.best_candidate.id
        file.write('var listings = %s;\n' % (json.dumps(listing_items)))
                #sort_keys=True, indent=2)))


class LooseMatcher(Matcher):

    @staticmethod
    def listing_may_match_product(listing, product):
        """Decide whether a listing is potentially matched by a product."""
        # If a listing's manufacturer and title tokens include a product's
        #  manufacturer and model tokens, respectively, as sublists, we
        #  consider the product to be a potential match for the listing.
        if not Matcher.contains(listing.tokens.manufacturer,
                product.tokens.manufacturer):
            return False
        if not Matcher.contains(listing.tokens.title,
                product.tokens.model):
            return False
        return True

    @staticmethod 
    def detail_compare(listing, a, b):
        """Decide whether one match is more detailed than another."""
        a_family_match = hasattr(a.tokens, 'family') and \
                Matcher.contains(listing.tokens.title, a.tokens.family)
        b_family_match = hasattr(b.tokens, 'family') and \
                Matcher.contains(listing.tokens.title, b.tokens.family)
        if a_family_match and not b_family_match:
            return -1
        if not a_family_match and b_family_match:
            return 1
        a_num_tokens = len(a.tokens.model)
        b_num_tokens = len(b.tokens.model)
        if a_num_tokens > b_num_tokens:
            return -1
        if a_num_tokens < b_num_tokens:
            return 1
        a_total_length = sum(map(lambda t: len(t.text), a.tokens.model))
        b_total_length = sum(map(lambda t: len(t.text), b.tokens.model))
        if a_total_length > b_total_length:
            return -1
        if a_total_length < b_total_length:
            return 1
        return 0


class StrictMatcher(Matcher):

    @staticmethod
    def listing_may_match_product(listing, product):
        """Decide whether a listing is potentially matched by a product."""

    @staticmethod
    def detail_compare(listing, a, b):
        """Decide whether one match is more detailed than another."""


class Product:

    def __init__(self, data):
        set_data(self, data, 'id', 'manufacturer', 'family', 'model')
        tokenize_attributes(self, 'manufacturer', 'family', 'model')

    def __str__(self):
        family = self.family if hasattr(self, 'family') else '-'
        return str((self.id, self.manufacturer, family, self.model))


class Listing:

    def __init__(self, data):
        set_data(self, data, 'id', 'manufacturer', 'title')
        tokenize_attributes(self, 'manufacturer', 'title')
        self.best_candidate = None

    def __str__(self):
        return str((self.manufacturer, self.title))


class Token:

    def __init__(self, text, start):
        self.text, self.start = text, start
        self.span = [ start, start + len(text) ]


class Container:

    def __init__(self, data={}):
        for name, value in data.items():
            setattr(self, name, value)


def set_data(item, data, *names):
    """Set item attributes by getting named values from a data dictionary."""
    for name in names:
        if name in data:
            setattr(item, name, data[name])
    item.data = data

def tokenize_attributes(item, *names):
    """Convert the named attributes into lists of canonical tokens.""" 
    item.tokens = Container()
    for name in names:
        if hasattr(item, name):
            tokens = text_to_tokens(getattr(item, name))
            setattr(item.tokens, name, tokens)

letter_set = set(list(string.ascii_lowercase))
digit_set = set(list(string.digits))

def text_to_tokens(text):
    """Parse text into canonical tokens."""
    tokens = []
    text = text.lower()
    pos = 0
    while pos < len(text):
        ch = text[pos]
        made_token = False
        for char_set in [ letter_set, digit_set ]:
            if ch in char_set:
                pos, token = parse_token(char_set, text, pos)
                tokens.append(token)
                made_token = True
                break
        if not made_token:
            pos += 1
    return tokens

def parse_token(char_set, text, pos):
    """Extract a sequence of characters belonging to a character set."""
    chars = []
    start = pos
    while True:
        if pos == len(text) or text[pos] not in char_set:
            break
        chars.append(text[pos])
        pos += 1
    token = Token(''.join(chars), start)
    return pos, token

def load_items(Item, file_path):
    """Make a list of Item objects based on a file of JSON lines."""
    items = []
    with open(file_path) as file:
        for line_index, line in enumerate(file.readlines()):
            data = json.loads(line)
            # Allow for predefined IDs. Use the line number by default.
            if 'id' not in data:
                data['id'] = line_index + 1
            items.append(Item(data))
    return items

def main():
    data_dir = 'data/dev'
    products_name = 'products.txt'
    listings_name = 'listings_a.txt'
    products = load_items(Product, os.path.join(data_dir, products_name))
    listings = load_items(Listing, os.path.join(data_dir, listings_name))
    matcher = LooseMatcher(products, listings)
    with open('js/data.js', 'w') as file:
        matcher.output_json(file)


if __name__ == '__main__':
    main()

