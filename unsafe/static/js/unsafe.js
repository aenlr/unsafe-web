'use strict';

const Burger = {
  toggle(event) {
    const $el = event.target;
    const target = $el.dataset.target;
    const $target = document.getElementById(target);
    $el.classList.toggle('is-active');
    $target.classList.toggle('is-active');
  },

  init() {
    Array.from(document.querySelectorAll('.navbar-burger'))
      .forEach(el => el.addEventListener('click', this.toggle));
  }
};

document.addEventListener('DOMContentLoaded', () => {
  Burger.init();
});
