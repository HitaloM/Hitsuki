// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

use diesel_async::pooled_connection::deadpool::Pool;
use diesel_async::AsyncPgConnection;

pub struct Users {
    pool: Pool<AsyncPgConnection>,
}

impl Users {
    pub fn new(pool: Pool<AsyncPgConnection>) -> Self {
        Self { pool }
    }

    // TODO: Implement user-related database operations here
}
