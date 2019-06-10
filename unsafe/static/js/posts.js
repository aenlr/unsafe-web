'use strict';

const Posts = {
  like(id) {
    const csrf_token = document.getElementById('csrf_token').value;
    const url = `${BASE_URL}/posts/${id}`;
    const body = {
      csrf_token
    };

    fetch(url, {
      method: 'POST',
      //mode: 'cors', // no-cors, cors, *same-origin
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf_token
      },
      body: JSON.stringify(body)
    })
    .then(response => {
      if (response.ok) {
        return response.json();
      } else {
        alert('Kunde inte ta gilla');
      }
    })
    .then(post => {
      const $el = document.getElementById(`likes-${id}`);
      $el.textContent = '' + post.likes
      $el.classList.toggle('is-hidden', post.likes <= 0);
    });
  }
};
