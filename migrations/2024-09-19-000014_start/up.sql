-- Your SQL goes here

CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    language_code TEXT NOT NULL
);

CREATE TABLE chats (
    chat_id BIGINT PRIMARY KEY,
    chat_name TEXT NOT NULL,
    language_code TEXT NOT NULL
);
