// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use anyhow::Result;
use teloxide::adaptors::DefaultParseMode;
use teloxide::prelude::*;
use teloxide::types::ChatPermissions;
use teloxide::utils::command::BotCommands;

#[derive(BotCommands, Clone)]
#[command(rename_rule = "lowercase", description = "Bans commands:")]
pub enum Command {
    #[command(description = "Reply to a user to kick him from the group")]
    Kick,
    #[command(description = "Reply to a user to ban him from the group")]
    Ban,
    #[command(description = "Reply to a user to mute him in the group")]
    Mute,
}

pub async fn action(bot: DefaultParseMode<Bot>, message: Message, cmd: Command) -> Result<()> {
    match cmd {
        Command::Kick => kick_user(&bot, &message).await?,
        Command::Ban => ban_user(&bot, &message).await?,
        Command::Mute => mute_user(&bot, &message).await?,
    };

    Ok(())
}

async fn kick_user(bot: &DefaultParseMode<Bot>, message: &Message) -> Result<()> {
    if let Some(replied) = message.reply_to_message() {
        bot.unban_chat_member(message.chat.id, replied.from.as_ref().unwrap().id)
            .await?;
    } else {
        bot.send_message(
            message.chat.id,
            "Use this command in reply to another message",
        )
        .await?;
    }
    Ok(())
}

async fn ban_user(bot: &DefaultParseMode<Bot>, message: &Message) -> Result<()> {
    if let Some(replied) = message.reply_to_message() {
        bot.ban_chat_member(
            message.chat.id,
            replied
                .from
                .as_ref()
                .expect("Must be MessageKind::Common")
                .id,
        )
        .await?;
    } else {
        bot.send_message(
            message.chat.id,
            "Use this command in a reply to another message!",
        )
        .await?;
    }
    Ok(())
}

async fn mute_user(bot: &DefaultParseMode<Bot>, message: &Message) -> Result<()> {
    if let Some(replied) = message.reply_to_message() {
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
    } else {
        bot.send_message(
            message.chat.id,
            "Use this command in a reply to another message!",
        )
        .await?;
    }
    Ok(())
}
