// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

pub mod start;

use teloxide::macros::BotCommands;

#[derive(BotCommands, Clone)]
#[command(
    rename_rule = "lowercase",
    description = "Commands for <i>start</i> handler:"
)]
pub enum StartCommand {
    #[command(description = "Initialize the bot.")]
    Start,
    #[command(description = "Display help information.")]
    Help,
}
