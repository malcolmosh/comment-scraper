DROP TABLE IF EXISTS url_queue;
CREATE TABLE url_queue (
    url VARCHAR(512) PRIMARY KEY,
    date_hash CHAR(19),
    host VARCHAR(128),
    title VARCHAR(1024),
    topic VARCHAR(256),
    category VARCHAR(64),
    published_time DATETIME,
    insert_time TIMESTAMP DEFAULT NOW(),
    status int DEFAULT 0,
    last_work_time TIMESTAMP, -- NOW() when status 0 -> 1
    last_finish_time TIMESTAMP, -- NOW() when status 1 -> 2
    hit_comment BOOLEAN,
    error_message TEXT
);


