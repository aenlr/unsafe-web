const Embedded = {
  /**
   * @param {MouseEvent} event
   */
  onClick(event) {
    const target = event.currentTarget;
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
      return;
    }

    let url = target.dataset.url || target.href;
    if (url.indexOf('embedded') < 0) {
      url = url + (url.indexOf('?') < 0 ? '?embedded' : '&embedded');
    }

    const selector = target.dataset.target || 'iframe';
    document.querySelector(selector).src = url;
    event.preventDefault();
  },

  fixupLinks() {
    function fixupAttributes(elementType, attr, selector) {
      selector = selector || `${elementType}[${attr}]`;
      const elements = document.querySelectorAll(selector);
      for (let e of elements) {
        const url = e.getAttribute(attr);
        if (url) {
          let hashpos = url.indexOf('#');
          if (hashpos < 0) {
            hashpos = url.length;
          }

          const newUrl = url.substr(0, hashpos)
            + (url.indexOf('?') < 0 ? '?embedded' : '&embedded')
            + url.substr(hashpos);
          e.setAttribute(attr, newUrl);
        }
      }
      return elements;
    }

    if (document.querySelector('html.embedded')) {
      fixupAttributes('a', 'href');
      fixupAttributes('form', 'action');
      fixupAttributes('iframe', 'src');
    }

    Array.from(document.querySelectorAll('a.embed'))
      .forEach(a => a.addEventListener('click', this.onClick));
  }

};
