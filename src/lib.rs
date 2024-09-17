// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use teloxide::adaptors::{CacheMe, DefaultParseMode, Throttle};

mod config;
pub mod handlers;

pub use config::Config;

type Bot = CacheMe<DefaultParseMode<Throttle<teloxide::Bot>>>;
