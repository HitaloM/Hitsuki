// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use teloxide::macros::BotCommands;

pub mod bans;
pub mod start;

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

#[derive(BotCommands, Clone)]
#[command(
    rename_rule = "lowercase",
    description = "Commands for <i>bans</i> handler:"
)]
pub enum BansCommand {
    #[command(description = "Kick a user from the group (reply to the user).")]
    Kick,
    #[command(description = "Ban a user from the group (reply to the user).")]
    Ban,
    #[command(description = "Mute a user in the group (reply to the user).")]
    Mute,
}
