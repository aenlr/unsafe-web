'use strict';

/**
 * Modal dialog.
 */
class Modal {
  /**
   * @typedef {Object} Modal.Button
   * @property {string} title Knapptext
   * @property {string} role Knappens roll, används för att identifiera knappen
   */

  /**
   * @param {Object} config
   * @param {string} config.title Rubrik för dialogrutan
   * @param {string} config.message Meddelandetext
   * @param {Button[]} config.buttons
   */
  constructor({title, message, buttons}) {
    this._handlers = {};

    /**
     * Dialogens DOM-element.
     * @type {HTMLElement}
     */
    this.element = document.createElement('div');
    this.element.tabIndex = 0;
    this.element.classList.add('modal');
    this.element.innerHTML = Modal.template({
      title,
      message,
      buttons
    }, {helpers: Modal.helpers});

    this.element.addEventListener('keydown', event => {
      if (event.code === 'Escape') {
        event.preventDefault();
        this.dismiss('cancel');
      }
    });

    for (let btn of buttons) {
      if (btn.handler) {
        this.on(btn.role, btn.handler);
      }
    }

    for (let btn of this.element.querySelectorAll('button[data-role]')) {
      let role = btn.getAttribute('data-role');
      btn.addEventListener('click', this.dismiss.bind(this, role));
    }
  }

  /**
   * Visa och fokusera dialogen
   * @returns {Modal}
   */
  show() {
    this.element.classList.add('is-active');
    if (!this.element.parentElement) {
      document.body.appendChild(this.element);
    }

    let focusButton = this.element.querySelector('footer [data-role="cancel"]')
      || this.element.querySelector('footer button');

    if (focusButton) {
      focusButton.focus();
    }

    return this;
  }

  /**
   * Hämta DOM-element för knapp.
   * @param {string} role Knappens roll
   * @returns {HTMLButtonElement}
   */
  button(role) {
    return this.element.querySelector(`button[data-role='${role}']`);
  }


  _event(role) {
    if (role) {
      let handler = this._handlers[role];
      if (handler) {
        handler.call(this, role);
      }
    }
  }

  /**
   * Destruera och ta bort dialogen från DOM-trädet.
   */
  destroy() {
    if (this.element) {
      this._event('destroy');
      if (this.element.parentElement) {
        this.element.parentElement.removeChild(this.element);
      }
      this.element = null;
    }
  }

  /**
   * Simulera att en angiven knapp har valts.
   * @param {string} role Roll för den knapp som valts
   * @returns {Modal}
   */
  dismiss(role) {
    if (this.element && this.element.classList.contains('is-active')) {
      this.element.classList.remove('is-active');
      this._event(role);
      this._event('_always');
    }
    return this;
  }

  /**
   * Registrera callback.
   * Callback-funktionen anropas efter att dialogen har dolts.
   *
   * @param {string} role En roll för en knapp eller 'destroy' för att registrera callback
   * när dialogen destrueras.
   * @param {function(string):void} callback Funktion att anropa när knappen med (roll) väljs
   * @returns {Modal}
   */
  on(role, callback) {
    this._handlers[role] = callback;
    return this;
  }

  /**
   * Registrera callback som anropas för alla knappar
   * @param {function(string):void} callback Funktion att anropa när knappen med (roll) väljs
   * @returns {Modal}
   */
  always(callback) {
    return this.on('_always', callback);
  }

}

Modal.helpers = {
  buttonClass() {
    return this.class ? `button ${this.class}` : 'button';
  }
};

Modal.template = Handlebars.compile(`
  <div class="modal-background"></div>
    <div class="modal-card" role="dialog" aria-modal="true">
      <header class="modal-card-head">
        <p class="modal-card-title">{{title}}</p>
        <button class="delete" aria-label="Stäng" data-role="cancel"></button>
      </header>
      <section class="modal-card-body">
       <p>{{message}}</p>
      </section>
      <footer class="modal-card-foot">
      {{#each buttons}}
        <button class="{{buttonClass}}" data-role="{{this.role}}">{{this.title}}</button>
      {{/each}}
      </footer>
    </div>`);
