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
      productMap[product.product_name] = product;
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
        [ 'line_id', 'manufacturer', 'title' ].forEach(function (field) {
          var keyValue = M.make('div', { className: 'keyValue ' + field,
                  parent: listingBox });
          M.make('span', { className: 'key', parent: keyValue,
              innerHTML: (field == 'line_id' ? 'listing line' : field) });
          M.make('span', { className: 'value', parent: keyValue,
              innerHTML: listing[field] });
          if (field == 'manufacturer') {
            M.make('br', { parent: listingBox });
          }
        });
      });
    });
  }

  return {
    load: load
  };
})();

onload = Viewer.load;
