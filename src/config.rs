// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use serde::{Deserialize, Serialize};
use std::{fs::File, io::Read};

use crate::Result;

const PATH: &str = "./config.toml";

#[derive(Deserialize, Serialize)]
pub struct Config {
    pub telegram: Telegram,
    pub bot: Bot,
}

impl Config {
    pub fn load() -> Result<Self> {
        let toml_str = read_file_to_string(PATH)?;
        parse_toml(&toml_str)
    }
}

fn read_file_to_string(path: &str) -> Result<String> {
    let mut file = File::open(path)?;
    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    Ok(contents)
}

fn parse_toml(toml_str: &str) -> Result<Config> {
    Ok(toml::from_str::<Config>(toml_str)?)
}

#[derive(Deserialize, Serialize)]
pub struct Telegram {
    pub api_id: i32,
    pub api_hash: String,
}

#[derive(Deserialize, Serialize)]
pub struct Bot {
    pub token: String,
}
