// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use anyhow::{Error, Result};
use teloxide::{dispatching::UpdateHandler, prelude::*, types::ChatPermissions};

use crate::Bot;

use super::BansCommand;

pub fn schema() -> UpdateHandler<Error> {
    dptree::entry()
        .filter_command::<BansCommand>()
        .branch(dptree::case![BansCommand::Kick].endpoint(kick))
        .branch(dptree::case![BansCommand::Ban].endpoint(ban))
        .branch(dptree::case![BansCommand::Mute].endpoint(mute))
}

pub async fn kick(bot: Bot, message: Message) -> Result<()> {
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

pub async fn ban(bot: Bot, message: Message) -> Result<()> {
    if let Some(replied) = message.reply_to_message() {
        bot.ban_chat_member(message.chat.id, replied.from.as_ref().unwrap().id)
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

pub async fn mute(bot: Bot, message: Message) -> Result<()> {
    if let Some(replied) = message.reply_to_message() {
        bot.restrict_chat_member(
            message.chat.id,
            replied.from.as_ref().unwrap().id,
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
