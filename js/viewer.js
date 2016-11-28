var Viewer = (function () {
  'use strict';

  var groupOrder = [ 'multipleUnresolved', 'multipleResolved', 'one', 'zero' ],
      groupInfo = {
        multipleUnresolved: { numberText: 'Unresolved multiple', plural: 's' },
        multipleResolved: { numberText: 'Resolved multiple', plural: 's' },
        one: { numberText: 'Single', plural: '' },
        zero: { numberText: 'No', plural: '' }
      };

  function format(x, decimalDigits) {
    var s = '' + Math.round(Math.pow(10, decimalDigits) * x),
        pos = s.length - decimalDigits;
    return (pos == 0 ? '0' : s.substring(0, pos)) + '.' + s.substring(pos);
  }

  function load() {
    var wrapper, spinnerFrame, productMap, listingGroups,
        menu, icon, linkContainer;
    // Index products by name.
    productMap = Object.create(null);
    products.forEach(function (product) {
      productMap[product.id] = product;
    });
    // Group listings according to candidate count.
    listingGroups = {};
    groupOrder.forEach(function (key) {
      listingGroups[key] = [];
    });
    listings.forEach(function (listing) {
      var count = listing.candidateKeys.length,
          key;
      if (count <= 1) {
        key = (count == 0 ? 'zero' : 'one');
      } else {
        key = 'multiple' + (typeof listing.bestCandidateKey == 'number' ?
            'Resolved' : 'Unresolved');
      }
      listingGroups[key].push(listing);
    });
    wrapper = M.make('div', { id: 'wrapper', parent: document.body });
    // Do some animation to bide the time until the listings are done.
    //spinnerFrame = M.make('div', { id: 'spinnerFrame', parent: wrapper });
    //M.make('div', { id: 'spinner', parent: spinnerFrame });
    // Build DOM elements to display the contents of each group.
    groupOrder.forEach(function (name) {
      var group = listingGroups[name],
          size = group.length,
          groupBox = M.make('div', { className: 'group', parent: wrapper }),
          info = groupInfo[name],
          headerText = info.headerText = info.numberText +
              ' candidate' + info.plural + ': ' + size +
              ' listing' + (size == 1 ? '' : 's') + ' (' +
              format(100 * size / listings.length, 1) + '%)',
          header = M.make('h2', { className: 'header', parent: groupBox,
              innerHTML: headerText });
      info.element = groupBox;
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
                parent: container }),
            spans, i, a, b, text, textLower, token, tokenLower, tokenMap;
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
                  parent: container });
          if (id == listing.bestCandidateKey) {
            M.classAdd(productBox, 'selected');
          }
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
            textLower = text.toLowerCase();
            spans = product[field].tokenSpans;
            tokenMap = listing[field == 'manufacturer' ?
                'manufacturer' : 'title'].tokenMap;
            for (i = spans.length - 1; i >= 0; --i) {
              a = spans[i][0];
              b = spans[i][1];
              // Save the token to be highlighted later in the listing field.
              token = textLower.substring(a, b);
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
          textLower = text.toLowerCase();
          spans = target.tokenSpans;
          tokenMap = target.tokenMap;
          for (i = spans.length - 1; i >= 0; --i) {
            a = spans[i][0];
            b = spans[i][1];
            token = textLower.substring(a, b);
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
    // Build navigation menu.
    menu = M.make('div', { id: 'menu', parent: wrapper });
    icon = M.make('div', { className: 'icon', parent: menu });
    linkContainer = M.make('ul', { className: 'links', parent: menu });
    groupOrder.forEach(function (name) {
      var info = groupInfo[name],
          link = M.make('li', { parent: linkContainer,
              innerHTML: info.headerText }),
          groupElement = info.element;
      link.onclick = function () {
        groupElement.scrollIntoView();
        icon.click();
      };
    });
    icon.onclick = function () {
      if (M.classContains(menu, 'show')) {
        M.classRemove(menu, 'show');
      } else {
        M.classAdd(menu, 'show');
      }
    };
    // Now we can get rid of the spinner.
    M.classAdd(document.getElementById('spinnerFrame'), 'done');
  }

  return {
    load: load
  };
})();

onload = Viewer.load;
