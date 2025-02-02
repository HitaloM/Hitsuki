// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

use teloxide::adaptors::{CacheMe, DefaultParseMode, Throttle};

mod config;
pub mod database;
pub mod handlers;

pub use config::Config;

type Bot = CacheMe<DefaultParseMode<Throttle<teloxide::Bot>>>;
