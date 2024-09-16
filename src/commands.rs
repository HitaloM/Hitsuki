// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use anyhow::Result;
use teloxide::{adaptors::DefaultParseMode, macros::BotCommands, types::Message, Bot};

use crate::handlers::{bans, start};

#[derive(BotCommands, Clone)]
#[command(rename_rule = "lowercase", description = "Start commands:")]
pub enum StartCommand {
    #[command(description = "Initialize the bot.")]
    Start,
    #[command(description = "Display help information.")]
    Help,
}

#[derive(BotCommands, Clone)]
#[command(rename_rule = "lowercase", description = "Bans commands:")]
pub enum BansCommand {
    #[command(description = "Kick a user from the group (reply to the user).")]
    Kick,
    #[command(description = "Ban a user from the group (reply to the user).")]
    Ban,
    #[command(description = "Mute a user in the group (reply to the user).")]
    Mute,
}

impl StartCommand {
    pub async fn handler(self, bot: DefaultParseMode<Bot>, message: Message) -> Result<()> {
        match self {
            StartCommand::Start => start::start_cmd(&bot, &message).await?,
            StartCommand::Help => start::help_cmd(&bot, &message).await?,
        };
        Ok(())
    }
}

impl BansCommand {
    pub async fn handler(self, bot: DefaultParseMode<Bot>, message: Message) -> Result<()> {
        match self {
            BansCommand::Kick => bans::kick_cmd(&bot, &message).await?,
            BansCommand::Ban => bans::ban_cmd(&bot, &message).await?,
            BansCommand::Mute => bans::mute_cmd(&bot, &message).await?,
        };
        Ok(())
    }
}
