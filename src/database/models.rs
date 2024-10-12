// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use diesel::prelude::*;

#[derive(Queryable, Selectable)]
#[diesel(table_name = super::schema::users)]
pub struct Users {
    pub user_id: i64,
    pub username: String,
    pub language_code: String,
}

#[derive(Queryable, Selectable)]
#[diesel(table_name = super::schema::chats)]
pub struct Chats {
    pub chat_id: i64,
    pub chat_name: String,
    pub language_code: String,
}
