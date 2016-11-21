var Viewer = (function () {
  var wrapper,
      output,
      productNames;

  function load() {
    var lines = [];
    wrapper = M.make('div', { id: 'wrapper', parent: document.body });
    output = M.make('div', { id: 'output', parent: wrapper });
    listings.forEach(function (listing) {
      lines.push('#' + listing.line_id + ' listing');
      [ 'manufacturer', 'title' ].forEach(function (name) {
        lines.push(listing[name]);
      });
      lines.push(JSON.stringify(listing.candidateKeys));
      lines.push('');
    });
    products.forEach(function (product) {
      lines.push('#' + product.line_id + ' product');
      [ 'manufacturer', 'model', 'family' ].forEach(function (name) {
        if (name in product) {
          lines.push(product[name]);
        }
      });
      lines.push('');
    });
    output.innerHTML = lines.join('<br>');
  }

  return {
    load: load
  };
})();

onload = Viewer.load;
