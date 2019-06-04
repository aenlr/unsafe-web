const Unsafe = (function () {

  var deleteModal = null;

  function initBurger() {
    const toggleBurger = (event) => {
      const $el = event.target;
      const target = $el.dataset.target;
      const $target = document.getElementById(target);
      $el.classList.toggle('is-active');
      $target.classList.toggle('is-active');
    };

    const $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);
    for (let el of $navbarBurgers) {
      el.addEventListener('click', toggleBurger);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    initBurger();
  });

  return {
    confirmDelete(event) {
      function yes() {
        fetch(deleteModal.dataset.url, { credentials: 'include' })
          .then(response => {
            if (response.ok) {
              window.location.reload();
            } else {
              alert('Kunde inte ta bort');
            }
          })
      }

      function no() {
        deleteModal.classList.remove('is-active');
      }

      if (!deleteModal) {
        deleteModal = document.createElement('div');
        deleteModal.id = 'modal-delete';
        deleteModal.role = 'dialog';
        deleteModal.classList.add('modal');
        deleteModal.innerHTML = '<div class="modal-background"></div>\n' +
          '<div class="modal-card">\n' +
          '  <header class="modal-card-head">\n' +
          '    <p class="modal-card-title">Bekräfta</p>\n' +
          '    <button class="delete" aria-label="close"></button>\n' +
          '  </header>\n' +
          '  <section class="modal-card-body">\n    <p>Vill du ta bort det där?</p>\n' +
          '' +
          '  </section>\n' +
          '  <footer class="modal-card-foot">\n' +
          '    <button class="button is-danger yes">Ja, ta bort</button>\n' +
          '    <button class="button no">Nej, ta inte bort</button>\n' +
          '  </footer>\n' +
          '</div>';

        deleteModal.querySelector('button.yes').onclick = yes;
        deleteModal.querySelector('button.no').onclick = no;
        deleteModal.querySelector('button.delete').onclick = no;
        deleteModal.tabIndex = 0;
        deleteModal.onkeydown = function(event) {
          if (event.code === 'Escape') {
            event.preventDefault();
            no();
          }
        };
        document.body.appendChild(deleteModal);
      }

      deleteModal.dataset.url = event.currentTarget.href;
      deleteModal.classList.add('is-active');
      deleteModal.querySelector('button.no').focus();

      event.preventDefault();
    }
  }

})();
