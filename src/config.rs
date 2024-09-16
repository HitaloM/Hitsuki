// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use serde::{Deserialize, Serialize};
use std::{fs::File, io::Read};

const PATH: &str = "./config.toml";

#[derive(Deserialize, Serialize)]
pub struct Config {
    pub bot: Bot,
}

impl Config {
    pub fn load() -> anyhow::Result<Self> {
        let toml_str = read_file_to_string(PATH)?;
        parse_toml(&toml_str)
    }
}

fn read_file_to_string(path: &str) -> anyhow::Result<String> {
    let mut file = File::open(path)?;
    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    Ok(contents)
}

fn parse_toml(toml_str: &str) -> anyhow::Result<Config> {
    Ok(toml::from_str::<Config>(toml_str)?)
}

#[derive(Deserialize, Serialize)]
pub struct Bot {
    pub token: String,
}
