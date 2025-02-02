// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

use anyhow::Result;
use teloxide::{prelude::*, utils::command::BotCommands};

use super::StartCommand;
use crate::Bot;

pub async fn start(bot: Bot, message: Message) -> Result<()> {
    bot.send_message(message.chat.id, "<b>Hi!</b>").await?;
    Ok(())
}

pub async fn help(bot: Bot, message: Message) -> Result<()> {
    bot.send_message(message.chat.id, StartCommand::descriptions().to_string())
        .await?;
    Ok(())
}
