// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use anyhow::{Error, Result};
use teloxide::{dispatching::UpdateHandler, prelude::*, utils::command::BotCommands};

use crate::Bot;

use super::{BansCommand, StartCommand};

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
    let text = format!(
        "{}\n\n{}",
        StartCommand::descriptions(),
        BansCommand::descriptions()
    );

    bot.send_message(message.chat.id, text).await?;
    Ok(())
}
