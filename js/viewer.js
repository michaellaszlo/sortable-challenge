var Viewer = (function () {
  var wrapper,
      output,
      productMap,
      listingGroups,
      groupOrder = [ 'several', 'one', 'zero' ],
      groupHeader = {
        zero: { text: 'No', plural: '' },
        one: { text: 'Single', plural: '' },
        several: { text: 'Multiple', plural: 's' }
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
      M.make('h2', { parent: groupBox, innerHTML: header.text +
          ' candidate' + header.plural + ': ' + size + ' listings' });
      group.forEach(function (listing) {
        var listingBox = M.make('div', { className: 'listing',
                parent: groupBox });
        // Display the listing.
        [ 'id', 'manufacturer', 'title' ].forEach(function (field) {
          var pair = M.make('div', { className: 'pair ' + field,
                  parent: listingBox });
          if (field == 'id') {
            M.make('span', { className: 'key', parent: pair,
                innerHTML: 'listing' });
            M.make('span', { className: 'value', parent: pair,
                innerHTML: listing.id });
            return;
          }
          M.make('span', { className: 'key', parent: pair, innerHTML: field });
          // Save the value container for later. The text needs highlighting.
          listing[field].element = M.make('span', { className: 'value',
              parent: pair });
          listing[field].tokenToField = Object.create(null);
          if (field == 'manufacturer') {
            M.make('br', { parent: listingBox });
          }
        });
        // Display the listing's match candidates.
        listing.candidateKeys.forEach(function (id) {
          var product = productMap[id],
              productBox = M.make('div', { className: 'product',
                  parent: listingBox }),
              text, spans, i, a, b, token, tokenToField;
          [ 'id', 'manufacturer', 'family', 'model' ].forEach(function (field) {
            var pair;
            if (!(field in product)) {
              return;
            }
            pair = M.make('div', { className: 'pair', parent: productBox });
            if (field == 'id') {
              M.make('span', { className: 'key', parent: pair,
                  innerHTML: 'product' });
              M.make('span', { className: 'value', parent: pair,
                  innerHTML: product.id });
              return;
            }
            // Inject highlighting into the product text.
            text = product[field].text;
            spans = product[field].tokenSpans;
            tokenToField = listing[field == 'manufacturer' ?
                'manufacturer' : 'title'].tokenToField;
            for (i = spans.length - 1; i >= 0; --i) {
              a = spans[i][0];
              b = spans[i][1];
              // Save the token to be highlighted later in the listing field.
              token = text.substring(a, b);
              tokenToField[token] = field;
              text = text.substring(0, a) + '<span class="match ' + field +
                  '">' + text.substring(a, b) + '</span>' + text.substring(b);
            }
            M.make('span', { className: 'key', parent: pair,
                innerHTML: field });
            M.make('span', { className: 'value', parent: pair,
                innerHTML: text });
          });
        });
        // Inject highlighting into the appropriate listing text.
        [ 'manufacturer', 'title' ].forEach(function (field) {
          var target = listing[field];
          text = target.text;
          spans = target.tokenSpans;
          tokenToField = target.tokenToField;
          for (i = spans.length - 1; i >= 0; --i) {
            a = spans[i][0];
            b = spans[i][1];
            token = text.substring(a, b);
            if (token in tokenToField) {
              text = text.substring(0, a) + '<span class="match ' + 
                  tokenToField[token] + '">' + text.substring(a, b) +
                  '</span>' + text.substring(b);
            }
          }
          target.element.innerHTML = text;
        });
      });
    });
  }

  return {
    load: load
  };
})();

onload = Viewer.load;
