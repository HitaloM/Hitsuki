// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

pub mod commands;
mod config;
pub mod handlers;

pub use config::Config;
use teloxide::adaptors::{CacheMe, DefaultParseMode, Throttle};

type Bot = CacheMe<DefaultParseMode<Throttle<teloxide::Bot>>>;
