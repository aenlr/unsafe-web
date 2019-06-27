const ToggleMenu = (function () {
  function toggleMenu(menuToggle) {
    const target = menuToggle.dataset.target;
    const $target = document.getElementById(target);
    const expanded = !$target.classList.contains('is-expanded');
    menuToggle.setAttribute('aria-expanded', expanded);
    $target.classList.toggle('is-expanded', expanded);
  }

  function menuClicked(event) {
    toggleMenu(this);
  }

  function menuKeydown(event) {
    if (event.key === ' ' || event.key === 'Enter') {
      event.preventDefault();
      toggleMenu(this);
    }
  }

  return {
    init() {
      Array.from(document.querySelectorAll('.menu-toggle'))
        .forEach(el => {
          el.addEventListener('click', menuClicked);
          el.addEventListener('keydown', menuKeydown);
        });
    }
  };
})();

const Topics = (function () {
  function scrollToSection(id) {
    // Skrolla bara dokumentdelen istället för hela fönstret som webbläsaren gör som standard
    const element = document.getElementById(id);
    if (element) {
      const topPos = element.offsetTop;
      const container = document.querySelector('.topic-content .content');
      container.scrollTop = topPos;

      const bounds = element.getBoundingClientRect();
      if (bounds.top > window.innerHeight) {
        // Om avsnittet är utanför skärmen så skrollar vi hela fönstret
        element.scrollIntoView();
      }

      return true;
    }
  }

  function anchorClicked(event) {
    const link = this;
    const id = link.href.substr(link.href.indexOf('#') + 1);
    if (scrollToSection(id)) {
      event.preventDefault();
      history.replaceState({}, '', link.href);
    }
  }

  function initializeScrolling() {
    const hash = window.location.hash;
    if (hash && hash.startsWith('#')) {
      window.scrollTo(0, 0);
      scrollToSection(hash.substr(1));
    }

    const hashPos = window.location.href.indexOf('#');
    const currentTopicUrl = hashPos < 0 ? window.location.href + '#' : window.location.href.substr(0, hashPos + 1);
    Array.from(document.querySelectorAll('.menu-section ul a'))
      .forEach(el => {
        if (el.href.startsWith(currentTopicUrl)) {
          el.addEventListener('click', anchorClicked)
        }
      });
  }

  window.addEventListener('load', function () {
    initializeScrolling();
    ToggleMenu.init();
  });

  return {
  };

})();
