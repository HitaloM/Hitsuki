// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

pub mod models;
pub mod operations;
pub mod schema;

use diesel_async::{
    pooled_connection::{deadpool::Pool, AsyncDieselConnectionManager},
    AsyncPgConnection,
};
use operations::{Chats, Users};
use std::sync::LazyLock;

use crate::config::Config;

pub type ConnectionPool = Pool<AsyncPgConnection>;

pub static DB: LazyLock<DatabaseOperations> = LazyLock::new(DatabaseOperations::new);

pub struct DatabaseOperations {
    pub chats: Chats,
    pub users: Users,
}

impl DatabaseOperations {
    fn new() -> Self {
        let pool = Database::get_connection_pool();
        Self {
            chats: Chats::new(pool.clone()),
            users: Users::new(pool),
        }
    }
}

pub struct Database;

impl Database {
    pub fn get_connection_pool() -> ConnectionPool {
        static POOL: LazyLock<ConnectionPool> = LazyLock::new(|| {
            let config = Config::load().expect("Failed to load configuration");

            let connection_manager = AsyncDieselConnectionManager::<AsyncPgConnection>::new(
                config.bot.database_url.clone(),
            );

            Pool::builder(connection_manager)
                .build()
                .expect("Failed to build the Database connection pool!")
        });

        POOL.clone()
    }
}
