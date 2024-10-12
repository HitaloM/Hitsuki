// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

pub mod models;
pub mod schema;

use diesel_async::{
    pooled_connection::{deadpool::Pool, AsyncDieselConnectionManager},
    AsyncPgConnection,
};
use std::sync::OnceLock;

pub type ConnectionPool = Pool<AsyncPgConnection>;

pub struct Database {
    pub connection_pool: ConnectionPool,
}

impl Database {
    pub fn new(database_url: String) -> Database {
        Database {
            connection_pool: Self::initialize_pool(database_url),
        }
    }

    fn initialize_pool(database_url: String) -> ConnectionPool {
        static POOL: OnceLock<ConnectionPool> = OnceLock::new();

        POOL.get_or_init(|| {
            let connection_manager =
                AsyncDieselConnectionManager::<AsyncPgConnection>::new(database_url);
            Pool::builder(connection_manager)
                .build()
                .expect("Failed to build the Database connection pool!")
        })
        .clone()
    }
}
