// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use teloxide::{prelude::*, utils::command::BotCommands};

use crate::handlers::BansCommand;

#[derive(BotCommands, Clone)]
#[command(rename_rule = "lowercase")]
pub enum Command {
    #[command(description = "Start the bot")]
    Start,
    #[command(description = "Get this message")]
    Help,
}

pub async fn action(bot: Bot, message: Message, cmd: Command) -> ResponseResult<()> {
    match cmd {
        Command::Start => start(bot, message).await?,
        Command::Help => help(bot, message).await?,
    };

    Ok(())
}

async fn start(bot: Bot, message: Message) -> ResponseResult<()> {
    bot.send_message(message.chat.id, "Hi!").await?;
    Ok(())
}

async fn help(bot: Bot, message: Message) -> ResponseResult<()> {
    let text = format!(
        "{}\n{}",
        Command::descriptions(),
        BansCommand::descriptions()
    );

    bot.send_message(message.chat.id, text).await?;
    Ok(())
}
