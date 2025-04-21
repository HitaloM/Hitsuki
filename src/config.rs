// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

use anyhow::{Context, Result};
use serde::Deserialize;
use tokio::fs;

const PATH: &str = "./config.toml";

#[derive(Deserialize)]
pub struct Config {
    pub bot: Bot,
}

impl Config {
    pub async fn load() -> Result<Self> {
        let toml_str = fs::read_to_string(PATH)
            .await
            .context("Failed to read config file")?;
        let config = toml::from_str::<Config>(&toml_str).context("Failed to parse config file")?;
        Ok(config)
    }
}

#[derive(Deserialize)]
pub struct Bot {
    pub token: String,
    pub database_url: String,
}
