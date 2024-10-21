// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use anyhow::{Error, Result};
use teloxide::{dispatching::UpdateHandler, prelude::*, utils::command::BotCommands};

use super::StartCommand;
use crate::Bot;

pub fn schema() -> UpdateHandler<Error> {
    dptree::entry()
        .filter_command::<StartCommand>()
        .branch(dptree::case![StartCommand::Start].endpoint(start))
        .branch(dptree::case![StartCommand::Help].endpoint(help))
}

pub async fn start(bot: Bot, message: Message) -> Result<()> {
    bot.send_message(message.chat.id, "<b>Hi!</b>").await?;
    Ok(())
}

pub async fn help(bot: Bot, message: Message) -> Result<()> {
    bot.send_message(message.chat.id, StartCommand::descriptions().to_string())
        .await?;
    Ok(())
}
