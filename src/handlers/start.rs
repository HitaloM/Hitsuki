// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use anyhow::Result;
use teloxide::{adaptors::DefaultParseMode, prelude::*, utils::command::BotCommands};

use crate::commands::{BansCommand, StartCommand};

pub async fn start_cmd(bot: &DefaultParseMode<Bot>, message: &Message) -> Result<()> {
    bot.send_message(message.chat.id, "<b>Hi!</b>").await?;
    Ok(())
}

pub async fn help_cmd(bot: &DefaultParseMode<Bot>, message: &Message) -> Result<()> {
    let text = format!(
        "{}\n\n{}",
        StartCommand::descriptions(),
        BansCommand::descriptions()
    );

    bot.send_message(message.chat.id, text).await?;
    Ok(())
}
