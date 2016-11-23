var Viewer = (function () {
  var wrapper,
      output,
      productMap,
      listingGroups,
      groupOrder = [ 'several', 'one', 'zero' ],
      groupHeaderInfo = {
        zero: { text: 'No', plural: '' },
        one: { text: 'Single', plural: '' },
        several: { text: 'Multiple', plural: 's' }
      };

  function countToGroupName(count) {
    return (count == 0 ? 'zero' : (count == 1 ? 'one' : 'several'));
  }

  function format(x, decimalDigits) {
    var s = '' + Math.round(Math.pow(10, decimalDigits) * x),
        pos = s.length - decimalDigits;
    return s.substring(0, pos) + '.' + s.substring(pos);
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
          groupBox = M.make('div', { className: 'group', parent: wrapper }),
          headerInfo = groupHeaderInfo[name],
          header = M.make('h2', { className: 'header', parent: groupBox,
              innerHTML: '<span class="arrow">&#9656</span>' + headerInfo.text +
              ' candidate' + headerInfo.plural + ': ' + size + ' listings (' +
              format(100 * size / listings.length, 1) + '%)' });
      M.makeUnselectable(header);
      M.classAdd(groupBox, 'show');
      header.onclick = function () {
        if (M.classContains(groupBox, 'show')) {
          M.classRemove(groupBox, 'show');
        } else {
          M.classAdd(groupBox, 'show');
        }
      };
      group.forEach(function (listing) {
        var container = M.make('div', { className: 'listingContainer',
                parent: groupBox }),
            listingBox = M.make('div', { className: 'listing',
                parent: container });
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
          // Save the value element for later. The text needs highlighting.
          listing[field].element = M.make('span', { className: 'value',
              parent: pair });
          listing[field].tokenMap = Object.create(null);
          if (field == 'manufacturer') {
            M.make('br', { parent: listingBox });
          }
        });
        // Display the listing's match candidates.
        listing.candidateKeys.forEach(function (id) {
          var product = productMap[id],
              productBox = M.make('div', { className: 'product',
                  parent: container }),
              text, spans, i, a, b, token, tokenMap;
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
            tokenMap = listing[field == 'manufacturer' ?
                'manufacturer' : 'title'].tokenMap;
            for (i = spans.length - 1; i >= 0; --i) {
              a = spans[i][0];
              b = spans[i][1];
              // Save the token to be highlighted later in the listing field.
              token = text.substring(a, b);
              tokenMap[token] = field;
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
          tokenMap = target.tokenMap;
          for (i = spans.length - 1; i >= 0; --i) {
            a = spans[i][0];
            b = spans[i][1];
            token = text.substring(a, b);
            if (token in tokenMap) {
              text = text.substring(0, a) + '<span class="match ' + 
                  tokenMap[token] + '">' + text.substring(a, b) +
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
