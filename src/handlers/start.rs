// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use anyhow::Result;
use teloxide::adaptors::DefaultParseMode;
use teloxide::prelude::*;
use teloxide::utils::command::BotCommands;

use crate::handlers::BansCommand;

#[derive(BotCommands, Clone)]
#[command(rename_rule = "lowercase", description = "PM menu commands:")]
pub enum Command {
    #[command(description = "Start the bot")]
    Start,
    #[command(description = "Get this message")]
    Help,
}

pub async fn action(bot: DefaultParseMode<Bot>, message: Message, cmd: Command) -> Result<()> {
    match cmd {
        Command::Start => start(&bot, &message).await?,
        Command::Help => help(&bot, &message).await?,
    };

    Ok(())
}

async fn start(bot: &DefaultParseMode<Bot>, message: &Message) -> Result<()> {
    bot.send_message(message.chat.id, "<b>Hi!</b>").await?;
    Ok(())
}

async fn help(bot: &DefaultParseMode<Bot>, message: &Message) -> Result<()> {
    let text = format!(
        "{}\n\n{}",
        Command::descriptions(),
        BansCommand::descriptions()
    );

    bot.send_message(message.chat.id, text).await?;
    Ok(())
}
