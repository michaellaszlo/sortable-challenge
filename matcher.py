import json
import os.path
import random
import re
import string


class Matcher:

    def __init__(self, products, listings):
        self.products, self.listings = products, listings
        self.match_all_products()
        self.disambiguate_matches()
        self.print_candidate_counts()

    def match_all_products(self):
        """Iterate over products first to match them with listings."""
        # This approach is faster than iterating over listings first, due to
        #  our use of token indexing to shrink the set of listings to consider
        #  for a product. It only makes sense to index the listings, not the
        #  products, because we deem a listing to match if it contains a
        #  sublist of product tokens. The product tokens act as a query and
        #  the listing tokens act as a document to which we apply the query.
        #  Thus, it is the listings -- the documents, as it were -- that must
        #  be indexed.
        self.remove_duplicate_products()
        self.index_all_listings()
        for listing in self.listings:
            listing.candidates = []
            listing.best_candidate = None
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
            # It's safe to join with a space -- values were stripped of spaces.
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
            if self.is_candidate_match(listing, product):
                listing.candidates.append(product)

    def match_all_listings(self):
        """Iterate over listings first to match them with products."""
        # This produces the same results as iterating over products first, but
        #  it is slower because we can't take advantage of token indexing to
        #  quickly shrink the set of products. It is useful for verifying
        #  the correctness of match_all_products().
        for listing in self.listings:
            self.match_listing(listing)

    def match_listing(self, listing):
        """Find products that may match the given listing."""
        listing.candidates = []
        for product in self.products:
            if self.is_candidate_match(listing, product):
                listing.candidates.append(product)

    @staticmethod
    def find(tokens, sublist):
        """Search a token list for a sublist. Return the start index or -1."""
        for start in range(0, len(tokens) - len(sublist) + 1):
            okay = True
            for i, word in enumerate(sublist):
                if tokens[start + i].text != word.text:
                    okay = False
                    break
            if okay:
                return start
        return -1

    @staticmethod
    def find_all(tokens, sublist):
        """Search a token list for a sublist. Return a list of start indices."""
        result = []
        for start in range(0, len(tokens) - len(sublist) + 1):
            okay = True
            for i, word in enumerate(sublist):
                if tokens[start + i].text != word.text:
                    okay = False
                    break
            if okay:
                result.append(start)
        return result

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
            if self.compare_details(listing, candidates[0], candidates[1]) == 0:
                continue
            listing.best_candidate = candidates[0]

    def detail_sort(self, listing, products, start=0, length=None):
        """Sort products in place, using compare_details() for product pairs."""
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
            if self.compare_details(listing, a[pos], pivot) == -1:
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
            # If a multiple-candidate case was successfully resolved, count
            #  it as a single-candidate case.
            if listing.best_candidate != None:
                count = 1
            counts[count] = counts.setdefault(count, 0) + 1
        print('candidate count frequencies:')
        for count, frequency in sorted(counts.items()):
            proportion = 100.0 * frequency / len(self.listings)
            print('%d: %d %.1f%%' % (count, frequency, proportion))
        print('')
    
    def write_js(self, file):
        """Convert products and listings into dictionaries. Write a JS file."""
        product_items = len(self.products) * [ None ]
        for i, product in enumerate(self.products):
            item = product_items[i] = { 'id': product.id }
            for field in [ 'manufacturer', 'family', 'model' ]:
                # A product may not have the family attribute.
                if not hasattr(product, field):
                    continue
                # Make a dictionary containing text and tokens.
                item[field] = { 'text': getattr(product, field),
                        'tokenSpans': [ token.span for
                                token in getattr(product.tokens, field) ] }
        file.write('var products = %s;\n' % (json.dumps(product_items)))
                #sort_keys=True, indent=2)))
        listing_items = len(self.listings) * [ None ]
        for i, listing in enumerate(self.listings):
            item = listing_items[i] = { 'id': listing.id }
            for field in [ 'manufacturer', 'title' ]:
                # Make a dictionary containing text and tokens.
                item[field] = { 'text': getattr(listing, field),
                        'tokenSpans': [ token.span for
                                token in getattr(listing.tokens, field) ] }
            listing.candidates.sort(key=lambda p: p.id)
            item['candidateKeys'] = [ product.id for
                    product in listing.candidates ]
            if listing.best_candidate != None:
                item['bestCandidateKey'] = listing.best_candidate.id
        file.write('var listings = %s;\n' % (json.dumps(listing_items)))
                #sort_keys=True, indent=2)))

    def write_results(self, file):
        """Write out final matches in the format specified for the challenge."""
        result_map = {}
        for listing in self.listings:
            product = listing.best_candidate
            if product == None:
                continue
            result_map.setdefault(product.product_name, []).append(listing)
        file.write('\n'.join(json.dumps(
                { 'product_name': product_name,
                  'listings': [ listing.data for listing in listings ] },
                ensure_ascii=False) for product_name, listings in
                sorted(result_map.items())) + '\n')

    def write_html(self, file, header, footer):
        """Generate a static HTML file displaying listings with candidates."""
        # Make nodes to contain listings grouped by candidate count.
        multiple_unresolved = self.make_group_node('Unresolved multiple', 's')
        multiple_resolved = self.make_group_node('Resolved multiple', 's')
        one = self.make_group_node('Single')
        zero = self.make_group_node('No')
        for listing in sorted(self.listings, key=lambda x: x.id):
            count = len(listing.candidates)
            best_candidate = listing.best_candidate
            # Select the appropriate group for this listing.
            if count == 0:
                group = zero
            elif count == 1:
                group = one
            elif best_candidate != None:
                group = multiple_resolved
            else:
                group = multiple_unresolved
            # Make a node to contain the listing and its candidate products.
            container = HTMLNode('div', { 'class': 'listingContainer' })
            group.add(container)
            # Make a node for the listing itself.
            listing_node = HTMLNode('div', { 'class': 'listing' },
                    [ self.make_pair_node('listing', listing.id, 'id') ])
            container.add(listing_node)
            # Store text fragments for later use in highlighting the listing.
            highlight_maps = Container({ 'manufacturer': {}, 'title': {} })
            for product in sorted(listing.candidates, key=lambda x: x.id):
                # Make a node for the product.
                class_text = 'product'
                if product == best_candidate:
                    class_text += ' selected'
                group_node = HTMLNode('div', { 'class': class_text },
                        [ self.make_pair_node('product', product.id, 'id') ])
                container.add(group_node)
                # Add the product fields.
                for name in [ 'manufacturer', 'family', 'model' ]:
                    # There may be no family.
                    if not hasattr(product, name):
                        continue
                    text = getattr(product, name)
                    text_lower = text.lower()
                    if name == 'manufacturer':
                        highlight_map = highlight_maps.manufacturer
                    else:
                        highlight_map = highlight_maps.title
                    for token in reversed(getattr(product.tokens, name)):
                        a, b = token.span
                        highlight_map[text_lower[a:b]] = name
                        text = text[:a] + ''.join([ '<span class="match ',
                                name, '">', text[a:b], '</span>', text[b:] ])
                    group_node.add(self.make_pair_node(name, text, name))
        wrapper = HTMLNode('div', { 'id': 'wrapper' })
        # Alter each group header to show the number of listings it contains.
        total_count = len(self.listings)
        for group in [ multiple_unresolved, multiple_resolved, one, zero ]:
            count = len(group.children) - 1
            count_text = ': %d listing%s (%.1f%%)' % (count,
                    '' if count == 1 else 's', 100.0 * count / total_count)
            group.children[0].children[0] += count_text
            wrapper.add(group)
        file.write(header)
        file.write(wrapper.to_text(indent_to_depth=3))
        file.write(footer)

    @staticmethod
    def make_group_node(header_text, plural=''):
        return HTMLNode('div', { 'class': 'group' },
                [ HTMLNode('h2', { 'class': 'header' },
                        [ header_text + ' candidate' + plural ]) ])

    @staticmethod
    def make_pair_node(key, value, class_extra=None):
        class_name = 'pair' if class_extra == None else 'pair %s' % class_extra
        return HTMLNode('div', { 'class': class_name },
                [ HTMLNode('span', { 'class': 'key' }, [ key ]),
                  HTMLNode('span', { 'class': 'value' }, [ value ]) ])


class HTMLNode:

    indent_unit = '  '

    def __init__(self, name, attributes=None, children=None):
        self.name = name
        self.attributes = attributes or {}
        self.children = children or []

    def add(self, node):
        self.children.append(node)

    def to_text(self, depth=0, indent_to_depth=0):
        parts = []
        # Opening tag.
        if depth < indent_to_depth:
            parts.extend(depth * [ self.indent_unit ])
        parts.extend([ '<', self.name ])
        for key, value in self.attributes.items():
            parts.extend([ ' ', key, '="', value, '"' ])
        parts.append('>')
        if depth < indent_to_depth:
            parts.append('\n')
        # Children.
        for child in self.children:
            if type(child) == HTMLNode:
                parts.append(child.to_text(depth + 1, indent_to_depth))
            else:
                if depth < indent_to_depth:
                    parts.extend((depth + 1) * [ self.indent_unit ])
                parts.append(str(child))
                if depth < indent_to_depth:
                    parts.append('\n')
        # Closing tag.
        if depth < indent_to_depth:
            parts.extend(depth * [ self.indent_unit ])
        parts.extend([ '</', self.name, '>' ])
        if depth < indent_to_depth:
            parts.append('\n')
        # Done.
        return ''.join(parts)


class LooseMatcher(Matcher):

    @staticmethod
    def is_candidate_match(listing, product):
        """Decide whether a listing is potentially matched by a product."""
        # If a listing's manufacturer and title tokens include a product's
        #  manufacturer and model tokens, respectively, as sublists, we
        #  consider the product to be a potential match for the listing.
        if Matcher.find(listing.tokens.manufacturer,
                product.tokens.manufacturer) == -1:
            return False
        return Matcher.find(listing.tokens.title, product.tokens.model) != -1

    @staticmethod 
    def compare_details(listing, a, b):
        """Decide whether one product is a closer match than another."""
        # Does one product have a family match whereas the other does not?
        a_family_match = hasattr(a.tokens, 'family') and \
                Matcher.find(listing.tokens.title, a.tokens.family) >= 0
        b_family_match = hasattr(b.tokens, 'family') and \
                Matcher.find(listing.tokens.title, b.tokens.family) >= 0
        if a_family_match and not b_family_match:
            return -1
        if not a_family_match and b_family_match:
            return 1
        # Does one product have more tokens than the other?
        a_num_tokens = len(a.tokens.model)
        b_num_tokens = len(b.tokens.model)
        if a_num_tokens > b_num_tokens:
            return -1
        if a_num_tokens < b_num_tokens:
            return 1
        # Does one product have a longer model name than the other?
        a_total_length = sum(map(lambda t: len(t.text), a.tokens.model))
        b_total_length = sum(map(lambda t: len(t.text), b.tokens.model))
        if a_total_length > b_total_length:
            return -1
        if a_total_length < b_total_length:
            return 1
        return 0


class TightMatcher(Matcher):

    @staticmethod
    def is_candidate_match(listing, product):
        """Decide whether a listing is potentially matched by a product."""
        # If the product has a family value, we require that it be present
        #  in the listing and that it occur immediately before or after the
        #  model value. The other criteria are the same as in loose matching.
        title_tokens = listing.tokens.title
        model_tokens = product.tokens.model
        model_starts = Matcher.find_all(title_tokens, model_tokens)
        if len(model_starts) == 0:
            return False
        if hasattr(product, 'family'):
            family_tokens = product.tokens.family
            family_starts = Matcher.find_all(title_tokens, family_tokens)
            if len(family_starts) == 0:
                return False
            # Check every family occurrence to see if it immediately precedes
            #  or succeeds any of the model occurrences.
            found = False
            model_start_set = set(model_starts)
            num_family_tokens = len(family_tokens)
            num_model_tokens = len(model_tokens)
            for family_start in family_starts:
                if family_start + num_family_tokens in model_start_set or \
                   family_start - num_model_tokens in model_start_set:
                    found = True
                    break
            if not found:
                return False
        return Matcher.find(listing.tokens.manufacturer,
                product.tokens.manufacturer) != -1

    @staticmethod
    def compare_details(listing, a, b):
        """Decide whether one product is a closer match than another."""
        # Does one have a family match whereas the other does not?
        a_family_match = hasattr(a.tokens, 'family') and \
                Matcher.find(listing.tokens.title, a.tokens.family) >= 0
        b_family_match = hasattr(b.tokens, 'family') and \
                Matcher.find(listing.tokens.title, b.tokens.family) >= 0
        if a_family_match and not b_family_match:
            return -1
        if not a_family_match and b_family_match:
            return 1
        # Is one model a strict superlist of the other model?
        if Matcher.find(a.tokens.model, b.tokens.model) >= 0:
            return -1
        if Matcher.find(b.tokens.model, a.tokens.model) >= 0:
            return 1
        return 0


class Product:

    def __init__(self, data):
        set_data(self, data)
        tokenize_attributes(self, 'manufacturer', 'family', 'model')

    def __str__(self):
        family = self.family if hasattr(self, 'family') else '-'
        return ' '.join([ self.id, self.manufacturer, family, self.model ])


class Listing:

    def __init__(self, data):
        set_data(self, data)
        tokenize_attributes(self, 'manufacturer', 'title')

    def __str__(self):
        return ' '.join([ self.id, self.manufacturer, self.title ])


class Token:

    def __init__(self, text, start):
        self.text, self.start = text, start
        self.span = [ start, start + len(text) ]


class Container:

    def __init__(self, data={}):
        for name, value in data.items():
            setattr(self, name, value)


def set_data(item, data, copy_id=False):
    """Set item attributes using values from a data dictionary."""
    for key, value in data.items():
        setattr(item, key, value)
    # Save a copy of the data for later use in logging and reporting.
    item.data = data.copy()
    if not copy_id:
        del item.data['id']

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
    """Make a list of Item objects from a file of JSON lines."""
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
    listings_name = 'listings.txt'
    products = load_items(Product, os.path.join(data_dir, products_name))
    listings = load_items(Listing, os.path.join(data_dir, listings_name))
    matcher = TightMatcher(products, listings)
    #with open('js/data.js', 'w') as file:
    #    matcher.write_js(file)
    fragment_dir = 'fragments'
    header = open(os.path.join(fragment_dir, 'header.html')).read()
    footer = open(os.path.join(fragment_dir, 'footer.html')).read()
    with open('view_listings.html', 'w') as file:
        matcher.write_html(file, header, footer)
    #with open('results.txt', 'w') as file:
    #    matcher.write_results(file)


if __name__ == '__main__':
    main()

