var Viewer = (function () {
  var wrapper,
      output,
      productMap,
      listingGroups,
      groupOrder = [ 'several', 'one', 'zero' ],
      groupHeader = {
        zero: '0 candidates',
        one: '1 candidate',
        several: '2 or more candidates'
      };

  function countToGroupName(count) {
    return (count == 0 ? 'zero' : (count == 1 ? 'one' : 'several'));
  }

  function load() {
    // Index products by name.
    productMap = Object.create(null);
    products.forEach(function (product) {
      productMap[product.id] = product;
    });
    // Group listings according to candidate count.
    listingGroups = { zero: [], one: [], several: [] };
    listings.forEach(function (listing) {
      var count = listing.candidateKeys.length,
          name = countToGroupName(count);
      listingGroups[name].push(listing);
    });
    wrapper = M.make('div', { id: 'wrapper', parent: document.body });
    // Build DOM elements to display the contents of each group.
    groupOrder.forEach(function (name) {
      var group = listingGroups[name],
          size = group.length,
          header = groupHeader[name],
          groupBox = M.make('div', { className: 'group', parent: wrapper });
      M.make('h2', { parent: groupBox, innerHTML: header + ' (' + size + ')' });
      group.forEach(function (listing) {
        var listingBox = M.make('div', { className: 'listing',
            parent: groupBox });
        // Display the listing.
        [ 'id', 'manufacturer', 'title' ].forEach(function (field) {
          var pair = M.make('div', { className: 'pair ' + field,
                  parent: listingBox });
          M.make('span', { className: 'key', parent: pair,
              innerHTML: field == 'id' ? 'listing' : field });
          M.make('span', { className: 'value', parent: pair,
              innerHTML: field == 'id' ? listing.id : listing[field].text });
          if (field == 'manufacturer') {
            M.make('br', { parent: listingBox });
          }
        });
        // Display the listing's match candidates.
        listing.candidateKeys.forEach(function (id) {
          var product = productMap[id],
              productBox = M.make('div', { className: 'product',
                  parent: listingBox });
          [ 'id', 'manufacturer', 'family', 'model' ].forEach(function (field) {
            var pair;
            if (!(field in product)) {
              return;
            }
            pair = M.make('div', { className: 'pair ' + field,
                    parent: productBox });
            M.make('span', { className: 'key', parent: pair,
                innerHTML: field == 'id' ? 'product' : field });
            M.make('span', { className: 'value', parent: pair,
                innerHTML: field == 'id' ? product.id : product[field].text });
          });
        });
      });
    });
  }

  return {
    load: load
  };
})();

onload = Viewer.load;
