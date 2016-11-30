var ListingMenu = (function () {
  'use strict';
  // requires: mikelib.js

  var menu;

  function menuClick() {
    // Toggle the menu state.
    if (M.classContains(menu, 'show')) {
      M.classRemove(menu, 'show');
    } else {
      M.classAdd(menu, 'show');
    }
  }

  function makeGroupScroller(group, continuation) {
    // Handle a request to scroll to a group of listings.
    return function () {
      group.scrollIntoView();
      continuation();
    }
  }

  function load() {
    // Build the navigation menu dynamically and add it to the page.
    var button, linkContainer, i, child,
        groups, group, header, text, link,
        wrapper = document.getElementById('wrapper'),
        children = wrapper.children;
    menu = M.make('div', { id: 'menu', parent: wrapper });
    button = M.make('div', { className: 'button', parent: menu });
    linkContainer = M.make('ul', { className: 'links', parent: menu });
    // Find the listing groups. They are children of the wrapper.
    groups = [];
    for (i = 0; i < children.length; ++i) {
      child = children[i];
      if (M.classContains(child, 'group')) {
        groups.push(child);
      }
    }
    for (i = 0; i < groups.length; ++i) {
      // Find each group's header text and make a menu link out of it.
      group = groups[i];
      header = group.children[0];
      text = header.innerHTML.replace(/^\s+|\s+$/g, '');
      link = M.make('li', { parent: linkContainer, innerHTML: text });
      link.onclick = makeGroupScroller(group, menuClick);
    }
    button.onclick = menuClick;
    // Hide spinner.
    document.getElementById('spinner').style.display = 'none';
  }

  return {
    load: load
  };
})();

onload = ListingMenu.load;
