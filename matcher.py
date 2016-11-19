import json
import os.path


class Matcher:

    def __init__(self, products, listings):
        print('%d products' % len(products))
        print('%d listings' % len(listings))


class Product:
    def __init__(self, data):
        add_data(self, data, 'id', 'product_name', 'manufacturer', 'model')

class Listing:
    def __init__(self, data):
        add_data(self, data, 'id', 'title', 'manufacturer')

def add_data(item, data, *names):
    """Set item attributes by getting named values from a data dictionary."""
    for name in names:
        value = data[name] if name in data else None
        setattr(item, name, value)
    item.data = data

def load_items(Item, file_path):
    """Make a list of Item objects loaded from a file of JSON lines."""
    items = []
    with open(file_path) as file:
        # Use the line number as the object ID.
        for id, line in enumerate(file.readlines()):
            data = json.loads(line)
            data['id'] = id + 1
            items.append(Item(data))
    return items


if __name__ == '__main__':
    data_dir = 'data/dev'
    products_name = 'products.txt'
    listings_name = 'listings.txt'
    products = load_items(Product, os.path.join(data_dir, products_name))
    listings = load_items(Listing, os.path.join(data_dir, listings_name))
    matcher = Matcher(products, listings)

