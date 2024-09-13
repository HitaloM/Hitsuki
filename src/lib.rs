// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

mod config;
pub mod handlers;

pub use config::Config;

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
