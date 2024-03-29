PRAGMA FOREIGN_KEYS = ON;

CREATE TABLE IF NOT EXISTS user
(
  user_id  INTEGER PRIMARY KEY,
  username TEXT NOT NULL,
  password TEXT NULL,
  email    TEXT NULL,
  groups   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS note
(
  note_id    INTEGER PRIMARY KEY,
  user_id    INTEGER   NOT NULL,
  category   TEXT      NOT NULL DEFAULT '',
  content    TEXT      NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS post
(
  post_id    INTEGER PRIMARY KEY,
  user_id    INTEGER   NOT NULL,
  reply_to   INTEGER   NULL,
  content    TEXT      NOT NULL,
  likes      INTEGER   NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES user(user_id),
  FOREIGN KEY(reply_to) REFERENCES post(post_id)
);
