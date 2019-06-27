const Embedded = {

  embeddedUrl(url) {
    if (url.indexOf('embedded') < 0) {
      return url + (url.indexOf('?') < 0 ? '?embedded' : '&embedded');
    } else {
      return url;
    }
  },

  unembeddedUrl(url) {
      let unembedUrl = url
        .replace(/\?embedded(=[^&])?/, '?')
        .replace(/&embedded(=[^&])?/, '');
      if (unembedUrl.endsWith('?')) {
        return unembedUrl.substr(0, unembedUrl.length - 1);
      } else {
        return unembedUrl;
      }
  },

  /**
   * @param {MouseEvent} event
   */
  onClick(event) {
    const target = event.currentTarget;
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
      return;
    }

    const url = target.dataset.url || target.href;
    const iframeSelector = target.dataset.target || 'iframe';
    const iframe = document.querySelector(iframeSelector);
    const linkSelector = target.dataset.linkTarget || '.topic-example a';
    const link = document.querySelector(linkSelector);

    iframe.onload = function() {
      link.href = Embedded.unembeddedUrl(this.contentWindow.location.href);
    };

    iframe.src = Embedded.embeddedUrl(url);
    event.preventDefault();
  },

  fixupLinks() {
    function fixupAttributes(elementType, attr, selector) {
      selector = selector || `${elementType}[${attr}]`;
      const elements = document.querySelectorAll(selector);
      for (let e of elements) {
        const url = e.getAttribute(attr);
        if (url && !url.startsWith('#')) {
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
