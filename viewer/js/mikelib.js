var M = (function () {
  'use strict';

  // Create a new DOM element with arbitrary attributes.
  function make(tag, options) {
    var keys, i,
        element = document.createElement(tag);
    if (options === undefined) {
      return element;
    }
    if ('parent' in options) {
      options.parent.appendChild(element);
      delete options.parent;
    }
    keys = Object.keys(options);
    for (i = keys.length - 1; i >= 0; --i) {
      element[keys[i]] = options[keys[i]];
    }
    return element;
  }

  // Check an element's className for a name.
  function classContains(element, name) {
    var names, i,
        className = element.className;
    if (className === '' || className === null || className === undefined) {
      return false;
    }
    names = className.split(/\s+/);
    for (i = names.length-1; i >= 0; --i) {
      if (names[i] === name) {
        return true;
      }
    }
    return false;
  }

  // Modify an element's className by adding a name.
  function classAdd(element, name) {
    var className;
    if (classContains(element, name)) {
      return;
    }
    className = element.className;
    if (className === '' || className === null || className === undefined) {
      element.className = name;
    } else {
      element.className = className + ' ' + name;
    }
  }

  // Modify an element's className by removing a name.
  function classRemove(element, name) {
    var names, newNames, i;
    if (!classContains(element, name)) {
      return;
    }
    names = element.className.split(/\s+/);
    newNames = [];
    for (i = names.length-1; i >= 0; --i) {
      if (names[i] !== name) {
        newNames.push(names[i]);
      }
    }
    element.className = newNames.join(' ');
  }

  // Prevent the user from selecting an element with the mouse.
  function makeUnselectable(element) {
    // Based on Evan Hahn's advice:
    //   http://evanhahn.com/how-to-disable-copy-paste-on-your-website/
    // Relies on the existence of this CSS rule:
    //   .unselectable {
    //     -webkit-user-select: none;
    //     -khtml-user-drag: none;
    //     -khtml-user-select: none;
    //     -moz-user-select: none;
    //     -moz-user-select: -moz-none;
    //     -ms-user-select: none;
    //     user-select: none;
    //   }
    classAdd(element, 'unselectable');
    element.ondragstart = element.onselectstart = function (event) {
      event.preventDefault();
    };
  }

  // Compute an element's left and top offset relative to an ancestor.
  function getOffset(element, ancestor) {
    var left = 0,
        top = 0,
        originalElement = element;
    while (element != ancestor) {
      if (element === null) {
        console.log(originalElement);
        console.log(ancestor);
      }
      left += element.offsetLeft;
      top += element.offsetTop;
      element = element.parentNode;
    }
    return { left: left, top: top };
  }

  // Get event coordinates relative to the page's top left corner.
  function getMousePosition(event) {
    event = event || window.event;
    if (event.pageX) {
      return { x: event.pageX, y: event.pageY };
    }
    return {
      x: event.clientX + document.body.scrollLeft +
          document.documentElement.scrollLeft,
      y: event.clientY + document.body.scrollTop +
          document.documentElement.scrollTop
    };
  }

  return {
    make: make,
    classContains: classContains,
    classAdd: classAdd,
    classRemove: classRemove,
    makeUnselectable: makeUnselectable,
    getOffset: getOffset,
    getMousePosition: getMousePosition
  };

})();
