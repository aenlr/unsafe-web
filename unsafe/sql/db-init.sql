PRAGMA FOREIGN_KEYS = ON;

INSERT INTO user (username, password, email, groups)
VALUES ('admin',
        'admin',
        'admin@bboard.com',
        'admin author'
       ),
       ('jane',
        '$pbkdf2-sha512$25000$6D1HiNGak7I2JiQEAEDI2Q$XFtCcDqGjyq7HEDnDW91FBOo3u89jgdoKs7NIZYXtjaF9FwB43TxcUZDCj8RObqxHGTqLnZYHP1rqt2.HCAVYA',
        'jane@example.com',
        'author'
       ),
       ('joe',
        '$2b$12$TW4ztsuT.Sp7eNKRfG8WE.FsNE16rT9lWNB0rcNjBpgXUhs7a2nMm',
        'joe@example.com',
        'author'
       ),
       ('bosse',
        'hemligt',
        'bosse@example.com',
        'author'
       );


INSERT INTO note (user_id, content, created_at, updated_at)
SELECT user_id, 'Recept på semlor' || x'0a' || 'Du behöver följande:' || x'0a' || '- Vetemjöl', '2019-05-26 20:33:28', '2019-05-29 12:25:01'
FROM user WHERE username = 'bosse';

INSERT INTO note (user_id, content, created_at, updated_at)
SELECT user_id, 'Som tam' || x'0a' || 'Papayasallad med Chili.' || x'0a' || 'Det är smaskens det.', '2019-04-26 18:15:17', '2019-04-26 18:15:17'
FROM user WHERE username = 'bosse';

INSERT INTO note (user_id, content)
SELECT user_id, 'SÄLJ!! Sandvik kommer att leverera en katastrofal rapport.'
FROM user WHERE username = 'jane';


INSERT INTO post (user_id, likes, content)
SELECT user_id, 99, 'Trump på krigsstigen igen. Very stable genius bping, bping, bping, bpong'
FROM user WHERE username = 'bosse';

INSERT INTO post (user_id, reply_to, content)
SELECT user_id, 1, 'Good genes!'
FROM user WHERE username = 'joe';
