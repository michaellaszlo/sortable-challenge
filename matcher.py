"""A solution to the Sortable coding challenge."""

import argparse
import inspect
import json
import os.path
import random
import re
import string
import sys
import time


class Matcher:
    """Implements the general matching process. Supports output generation in
    JSON, JavaScript, and HTML. Specific matching rules must be implemented by
    a subclass that defines may_match() and compare_details().
    """

    def __init__(self, products, listings):
        """Run the matching process."""
        self.products, self.listings = products, listings
        print('matching')
        start_time = time.time()
        self.match_all_products()
        self.disambiguate_matches()
        print('  %.3f s' % (time.time() - start_time))

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
        strip_regex = re.compile('[^a-z0-9]', re.IGNORECASE)
        strip = lambda s: strip_regex.sub('', s.lower())
        for product in self.products:
            values = [product.manufacturer]
            # Some products have no family value. The rascals!
            if hasattr(product, 'family'):
                values.append(product.family)
            values.append(product.model)
            # It's safe to join with a space -- values were stripped of spaces.
            key = ' '.join(map(strip, values))
            if key in product_keys:
                continue
            product_keys.add(key)
            products.append(product)
        self.products = products

    def index_all_listings(self):
        """Index the listings using their manufacturer and title tokens."""
        for field in ['manufacturer', 'title']:
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
                ('title', 'model')]:
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
            if self.may_match(listing, product):
                listing.candidates.append(product)

    def match_all_listings(self):
        """Iterate over listings first and match them with products."""
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
            if self.may_match(listing, product):
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
        """Search for a sublist of tokens. Return a list of start indices."""
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
        """Try to resolve cases of listings with several match candidates."""
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
            if self.compare_details(listing,
                    candidates[0], candidates[1]) == 0:
                continue
            listing.best_candidate = candidates[0]

    def detail_sort(self, listing, products, start=0, length=None):
        """Sort products in place, using compare_details() on product pairs."""
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
        print('candidate-count frequencies:')
        for count, frequency in sorted(counts.items()):
            proportion = 100.0 * frequency / len(self.listings)
            print('%3d: %d %.1f%%' % (count, frequency, proportion))

    def write_results(self, out_file):
        """Write out final matches in the required challenge format."""
        result_map = {}
        for listing in self.listings:
            product = listing.best_candidate
            if product == None:
                continue
            result_map.setdefault(product.product_name, []).append(listing)
        out_file.write('\n'.join(json.dumps(
                {'product_name': product_name,
                 'listings': [listing.result_data for listing in listings]},
                ensure_ascii=False) for product_name, listings in
                sorted(result_map.items())) + '\n')

    def write_data_js(self, out_file):
        """Convert products and listings into dictionaries. Write them to a
        JavaScript file that can be used to dynamically build a web page
        that displays listings with candidates.
        """
        product_items = len(self.products) * [None]
        for i, product in enumerate(self.products):
            item = product_items[i] = {'id': product.id}
            for field in ['manufacturer', 'family', 'model']:
                # A product may not have the family attribute.
                if not hasattr(product, field):
                    continue
                # Make a dictionary containing text and tokens.
                item[field] = {'text': getattr(product, field),
                        'tokenSpans': [token.span for token in
                                getattr(product.tokens, field)]}
        out_file.write('var products = %s;\n' % (json.dumps(product_items,
                ensure_ascii=False)))
        listing_items = len(self.listings) * [None]
        for i, listing in enumerate(self.listings):
            item = listing_items[i] = {'id': listing.id}
            for field in ['manufacturer', 'title']:
                # Make a dictionary containing text and tokens.
                item[field] = {'text': getattr(listing, field),
                        'tokenSpans': [token.span for token in
                                getattr(listing.tokens, field)]}
            listing.candidates.sort(key=lambda p: p.id)
            item['candidateKeys'] = [product.id for
                    product in listing.candidates]
            if listing.best_candidate != None:
                item['bestCandidateKey'] = listing.best_candidate.id
        out_file.write('var listings = %s;\n' % (json.dumps(listing_items,
                ensure_ascii=False)))

    def write_viewer_html(self, out_file, header, footer):
        """Generate a static HTML file displaying listings with candidates."""
        # Make a wrapper for everything.
        wrapper = HTMLNode('div', {'id': 'wrapper'})
        # Add a spinner to bide the time while the listings load.
        spinner = HTMLNode('div', {'id': 'spinner'})
        wrapper.add(spinner)
        # Make nodes to contain listings grouped by candidate count.
        multiple_unresolved = self.make_group_node('Unresolved multiple', 's')
        multiple_resolved = self.make_group_node('Resolved multiple', 's')
        one = self.make_group_node('Single')
        zero = self.make_group_node('No')
        for listing in sorted(self.listings, key=lambda x: x.id):
            # Select the appropriate group for this listing.
            count = len(listing.candidates)
            if count == 0:
                group = zero
            elif count == 1:
                group = one
            elif listing.best_candidate != None:
                group = multiple_resolved
            else:
                group = multiple_unresolved
            # Make a node to contain the listing and its candidate products.
            container = HTMLNode('div', {'class': 'listingContainer'})
            group.add(container)
            # Make a node for the listing itself.
            listing_node = HTMLNode('div', {'class': 'listing'},
                    [self.make_pair_node('listing', listing.id, 'id')])
            container.add(listing_node)
            # Store text fragments for later use in highlighting the listing.
            highlight_maps = Container({'manufacturer': {}, 'title': {}})
            for product in sorted(listing.candidates, key=lambda x: x.id):
                # Make a node for the product.
                class_text = 'product'
                if product == listing.best_candidate:
                    class_text += ' selected'
                group_node = HTMLNode('div', {'class': class_text},
                        [self.make_pair_node('product', product.id, 'id')])
                container.add(group_node)
                # Add the product fields.
                for name in ['manufacturer', 'family', 'model']:
                    # There may be no family.
                    if not hasattr(product, name):
                        continue
                    text = getattr(product, name)
                    text_lower = text.lower()
                    # Highlight text fragments and save for later use.
                    if name == 'manufacturer':
                        highlight_map = highlight_maps.manufacturer
                    else:
                        highlight_map = highlight_maps.title
                    for token in reversed(getattr(product.tokens, name)):
                        a, b = token.span
                        highlight_map[text_lower[a:b]] = name
                        text = self.insert_highlighting(text, a, b, name)
                    group_node.add(self.make_pair_node(name, text, name))
            # Highlight listing fields and turn them into nodes.
            for name in ['manufacturer', 'title']:
                highlight_map = getattr(highlight_maps, name)
                text = getattr(listing, name)
                text_lower = text.lower()
                for token in reversed(getattr(listing.tokens, name)):
                    a, b = token.span
                    key = text_lower[a:b]
                    if key in highlight_map:
                        field_name = highlight_map[key]
                        text = self.insert_highlighting(text, a, b, field_name)
                if name == 'title':
                    listing_node.add('<br>')
                listing_node.add(self.make_pair_node(name, text, name))
        # Alter each group header to show the number of listings it contains.
        total_count = len(self.listings)
        for group in [multiple_unresolved, multiple_resolved, one, zero]:
            count = len(group.children) - 1
            count_text = ': %d listing%s (%.1f%%)' % (count,
                    '' if count == 1 else 's', 100.0 * count / total_count)
            group.children[0].children[0] += count_text
            wrapper.add(group)
        out_file.write(header)
        out_file.write(wrapper.to_text(indent_to_depth=3))
        out_file.write(footer)

    @staticmethod
    def make_group_node(header_text, plural=''):
        """Represent a group of listings in HTML."""
        return HTMLNode('div', {'class': 'group'},
                [HTMLNode('h2', {'class': 'header'},
                        [header_text + ' candidate' + plural])])

    @staticmethod
    def make_pair_node(key, value, class_extra=None):
        """Represent a key-value pair in HTML."""
        class_name = 'pair' if class_extra == None else 'pair %s' % class_extra
        return HTMLNode('div', {'class': class_name},
                [HTMLNode('span', {'class': 'key'}, [key]),
                 HTMLNode('span', {'class': 'value'}, [value])])

    @staticmethod
    def insert_highlighting(text, a, b, field_name):
        """Insert span tags that will activate highlight styling."""
        return ''.join([text[:a], '<span class="match ',
                field_name, '">', text[a:b], '</span>', text[b:]])


class LooseMatcher(Matcher):
    """Implements matching rules that prefer recall to precision."""

    @staticmethod
    def may_match(listing, product):
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
        a_family_match = (hasattr(a.tokens, 'family') and
                Matcher.find(listing.tokens.title, a.tokens.family) >= 0)
        b_family_match = (hasattr(b.tokens, 'family') and
                Matcher.find(listing.tokens.title, b.tokens.family) >= 0)
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
        a_total_length = sum(len(token.text) for token in a.tokens.model)
        b_total_length = sum(len(token.text) for token in b.tokens.model)
        if a_total_length > b_total_length:
            return -1
        if a_total_length < b_total_length:
            return 1
        return 0


class TightMatcher(Matcher):
    """Implements matching rules that prefer precision to recall."""

    @staticmethod
    def may_match(listing, product):
        """Decide whether a listing is potentially matched by a product."""
        # If the product has a family value, we require that it be present
        #  in the listing and that it occur immediately before or after the
        #  model value. The other criteria are the same as for loose matching.
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
                if (family_start + num_family_tokens in model_start_set or
                        family_start - num_model_tokens in model_start_set):
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
        a_family_match = (hasattr(a.tokens, 'family') and
                Matcher.find(listing.tokens.title, a.tokens.family) >= 0)
        b_family_match = (hasattr(b.tokens, 'family') and
                Matcher.find(listing.tokens.title, b.tokens.family) >= 0)
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


class HTMLNode:
    """A simple representation of an HTML element, containing just enough
    information to print out static HTML.
    """

    one_indent = '  '  # The unit of indentation.

    def __init__(self, name, attributes=None, children=None):
        """Make a specified type of HTML element. Optionally set its
        dictionary of attribute strings and list of child elements.
        """
        self.name = name
        self.attributes = attributes or {}
        self.children = children or []

    def add(self, node):
        """Add a given HTML node as a child of this one."""
        self.children.append(node)

    def to_text(self, depth=0, indent_to_depth=0):
        """Recursively generate a text representation of this HTML node.
        Indentation is done to the maximum depth specified by the optional
        argument indent_to_depth. Upon reaching this depth, indentation ceases.
        If indent_to_depth is omitted, there is no indentation at all.
        """
        parts = []
        # Opening tag.
        if depth < indent_to_depth:
            parts.extend(depth * [self.one_indent])
        parts.extend(['<', self.name])
        for key, value in self.attributes.items():
            parts.extend([' ', key, '="', value, '"'])
        parts.append('>')
        if depth < indent_to_depth:
            parts.append('\n')
        # Children.
        for child in self.children:
            if type(child) == HTMLNode:
                parts.append(child.to_text(depth + 1, indent_to_depth))
            else:
                if depth < indent_to_depth:
                    parts.extend((depth + 1) * [self.one_indent])
                parts.append(str(child))
                if depth < indent_to_depth:
                    parts.append('\n')
        # Closing tag.
        if depth < indent_to_depth:
            parts.extend(depth * [self.one_indent])
        parts.extend(['</', self.name, '>'])
        if depth < indent_to_depth:
            parts.append('\n')
        # Done.
        return ''.join(parts)


class Container:
    """A bag of unspecified attributes. Convenient for grouping data."""

    def __init__(self, data=None):
        """Given a dictionary, use keys and values to initialize attributes."""
        if data:
            for name, value in data.items():
                setattr(self, name, value)


class Product(Container):
    """Contains a product's raw data and tokens for use in matching."""

    def __init__(self, data):
        """Store attributes and tokenize those used in matching."""
        super().__init__(data)
        Parser.tokenize_attributes(self, 'manufacturer', 'family', 'model')

    def __str__(self):
        """Make a concise string representation for debugging."""
        family = self.family if hasattr(self, 'family') else '-'
        return ' '.join([self.id, self.manufacturer, family, self.model])


class Listing(Container):
    """Contains a listing's raw data and tokens for use in matching."""

    def __init__(self, data):
        """Store attributes and tokenize those used in matching."""
        super().__init__(data)
        Parser.tokenize_attributes(self, 'manufacturer', 'title')
        # Save a copy of the data for printing in challenge format.
        self.result_data = data.copy()
        del self.result_data['id']  # The Sortable validator rejects our ID.

    def __str__(self):
        """Make a concise string representation for debugging."""
        return ' '.join([self.id, self.manufacturer, self.title])


class Token:
    """Contains a token string and the position where it was found."""

    def __init__(self, text, start):
        """Make a convenient tuple of the token's start and end indices."""
        self.text, self.start = text, start
        self.span = (start, start + len(text))


class Parser:
    """Provides static methods for turning text into tokens."""

    letter_set = set(list(string.ascii_lowercase))
    digit_set = set(list(string.digits))

    @staticmethod
    def tokenize_attributes(item, *names):
        """Given an object and one or more attribute names, make token lists
        from the named attributes and assign them to a new .tokens attribute.
        """
        item.tokens = Container()
        for name in names:
            if hasattr(item, name):
                tokens = Parser.text_to_tokens(getattr(item, name))
                setattr(item.tokens, name, tokens)

    @staticmethod
    def text_to_tokens(text):
        """Parse text into an ordered list of lowercase tokens."""
        tokens = []
        text = text.lower()
        pos = 0
        while pos < len(text):
            ch = text[pos]
            made_token = False
            for char_set in [Parser.letter_set, Parser.digit_set]:
                if ch in char_set:
                    pos, token = Parser.parse_token(char_set, text, pos)
                    tokens.append(token)
                    made_token = True
                    break
            # Making a token causes pos to advance. If there was no token to be
            #  made, pos is unchanged, so we have to advance it now.
            if not made_token:
                pos += 1
        return tokens

    @staticmethod
    def parse_token(char_set, text, pos):
        """Extract a sequence of characters belonging to a character set.
        Return a tuple comprising the new text position and a Token object.
        """
        chars = []
        start = pos
        while True:
            if pos == len(text) or text[pos] not in char_set:
                break
            chars.append(text[pos])
            pos += 1
        token = Token(''.join(chars), start)
        return pos, token


class Main:
    """A programmatic front end to the processes of loading data from files,
    finding matches, and writing out the results in various formats.
    """

    def __init__(self, products_path, listings_path, results_path):
        """Load data, perform matching, and write out the results."""
        self.load_data(products_path, listings_path)
        self.make_matcher()
        self.write_results(results_path)

    def load_data(self, products_path, listings_path):
        """Slurp product and listing data from files."""
        print('loading data')
        start_time = time.time()
        self.products = self.load(Product, products_path)
        self.listings = self.load(Listing, listings_path)
        print('  %.3f s' % (time.time() - start_time))

    def make_matcher(self):
        """Instantiate a Matcher subclass to run the matching process."""
        self.matcher = TightMatcher(self.products, self.listings)

    @staticmethod
    def load(Item, file_path):
        """Make a list of Item objects from a file of JSON lines."""
        items = []
        with open(file_path) as in_file:
            for line_index, line in enumerate(in_file.readlines()):
                data = json.loads(line)
                # Allow for predefined IDs. Use the line number by default.
                if 'id' not in data:
                    data['id'] = line_index + 1
                items.append(Item(data))
        return items

    def write_results(self, results_path):
        """Print JSON lines as specified by the Sortable challenge."""
        print('writing results to %s' % results_path)
        start_time = time.time()
        with open(results_path, 'w') as out_file:
            self.matcher.write_results(out_file)
        print('  %.3f s' % (time.time() - start_time))

    def write_data_js(self, viewer_dir):
        """Generate a JavaScript file containing the data necessary to build
        a listing viewer in the client. This method is an alternative to
        generating a static HTML file on the server.
        """
        js_path = os.path.join(viewer_dir, 'js/data.js')
        print('writing data to %s' % js_path)
        start_time = time.time()
        with open(js_path, 'w') as out_file:
            self.matcher.write_data_js(out_file)
        print('  %.3f s' % (time.time() - start_time))

    def write_viewer_html(self, viewer_dir):
        """Generate a static HTML file showing listings and candidates."""
        # We assume the existence of a viewer directory containing the
        #  necessary HTML fragments along with supporting CSS and JS files.
        fragment_dir = os.path.join(viewer_dir, 'fragments')
        header = open(os.path.join(fragment_dir, 'header.html')).read()
        footer = open(os.path.join(fragment_dir, 'footer.html')).read()
        html_path = os.path.join(viewer_dir, 'listings.html')
        print('writing viewer to %s' % html_path)
        start_time = time.time()
        with open(html_path, 'w') as out_file:
            self.matcher.write_viewer_html(out_file, header, footer)
        print('  %.3f s' % (time.time() - start_time))


def run_script():
    """Figure out file paths and pass them to the Main initializer."""
    # Use relative paths for the required input/output files.
    file_names = ['products', 'listings', 'results']
    suffix = '.txt'
    paths = Container()
    for name in file_names:
        setattr(paths, name, name + suffix)
    # For the HTML viewer, get the absolute path of the script's location.
    script_dir = os.path.dirname(os.path.abspath(
            inspect.getframeinfo(inspect.currentframe()).filename))
    viewer_dir = os.path.join(script_dir, 'viewer')
    # Check command-line options.
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-p', '--products', help='path to products (input)')
    argparser.add_argument('-l', '--listings', help='path to listings (input)')
    argparser.add_argument('-r', '--results', help='path to results (output)')
    argparser.add_argument('-w', '--webviewer', help='generate web viewer',
            action='store_true')
    arguments = argparser.parse_args()
    for name in file_names:
        value = getattr(arguments, name)
        if value != None:
            setattr(paths, name, value)
    # Perform matching and optionally generate the HTML viewer.
    try:
        main = Main(paths.products, paths.listings, paths.results)
        if arguments.webviewer:
            main.write_viewer_html(viewer_dir)
    except (FileNotFoundError, PermissionError):
        error = sys.exc_info()[1]
        print('%s: %s' % (type(error).__name__, error))
        return
    # Print summary statistics.
    main.matcher.print_candidate_counts()

def check_python_version():
    """Do what it says on the tin."""
    major, minor = 3, 2
    if sys.version_info[:2] < (major, minor):
        sys.exit('Python version >= %d.%d required' % (major, minor))

check_python_version()
if __name__ == '__main__':
    run_script()

