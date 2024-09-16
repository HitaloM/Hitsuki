// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use anyhow::Result;
use teloxide::{adaptors::DefaultParseMode, prelude::*, types::ChatPermissions};

pub async fn kick_cmd(bot: &DefaultParseMode<Bot>, message: &Message) -> Result<()> {
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

pub async fn ban_cmd(bot: &DefaultParseMode<Bot>, message: &Message) -> Result<()> {
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

pub async fn mute_cmd(bot: &DefaultParseMode<Bot>, message: &Message) -> Result<()> {
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
