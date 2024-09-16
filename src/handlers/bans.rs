// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use teloxide::{prelude::*, types::ChatPermissions, utils::command::BotCommands};

#[derive(BotCommands, Clone)]
#[command(rename_rule = "lowercase")]
pub enum Command {
    #[command(description = "Reply to a user to kick him from the group")]
    Kick,
    #[command(description = "Reply to a user to ban him from the group")]
    Ban,
    #[command(description = "Reply to a user to mute him in the group")]
    Mute,
}

pub async fn action(bot: Bot, message: Message, cmd: Command) -> ResponseResult<()> {
    match cmd {
        Command::Kick => kick_user(bot, message).await?,
        Command::Ban => ban_user(bot, message).await?,
        Command::Mute => mute_user(bot, message).await?,
    };

    Ok(())
}

async fn kick_user(bot: Bot, message: Message) -> ResponseResult<()> {
    match message.reply_to_message() {
        Some(replied) => {
            bot.unban_chat_member(message.chat.id, replied.from.as_ref().unwrap().id)
                .await?;
        }
        None => {
            bot.send_message(
                message.chat.id,
                "Use this command in reply to another message",
            )
            .await?;
        }
    }
    Ok(())
}

async fn ban_user(bot: Bot, message: Message) -> ResponseResult<()> {
    match message.reply_to_message() {
        Some(replied) => {
            bot.ban_chat_member(
                message.chat.id,
                replied
                    .from
                    .as_ref()
                    .expect("Must be MessageKind::Common")
                    .id,
            )
            .await?;
        }
        None => {
            bot.send_message(
                message.chat.id,
                "Use this command in a reply to another message!",
            )
            .await?;
        }
    }
    Ok(())
}

async fn mute_user(bot: Bot, message: Message) -> ResponseResult<()> {
    match message.reply_to_message() {
        Some(replied) => {
            bot.restrict_chat_member(
                message.chat.id,
                replied
                    .from
                    .as_ref()
                    .expect("Must be MessageKind::Common")
                    .id,
                ChatPermissions::empty(),
            )
            .await?;
        }
        None => {
            bot.send_message(
                message.chat.id,
                "Use this command in a reply to another message!",
            )
            .await?;
        }
    }
    Ok(())
}
