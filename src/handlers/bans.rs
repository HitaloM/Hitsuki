// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use grammers_client::{Client, InputMessage, Update};
use grammers_friendly::prelude::*;

use crate::Result;

pub fn router() -> Router {
    Router::default()
        .add_handler(Handler::new_message(ban_user, macros::command!("ban")))
        .add_handler(Handler::new_message(kick_user, macros::command!("kick")))
}

async fn ban_user(client: &mut Client, update: &mut Update, _data: &mut Data) -> Result<()> {
    let message = update.get_message().unwrap();

    if let Some(reply) = message.get_reply().await? {
        let user = reply.sender().unwrap();
        let chat = message.chat();

        client
            .set_banned_rights(chat, user)
            .view_messages(false)
            .await?;

        message
            .reply(InputMessage::text("User has been banned."))
            .await?;
    } else {
        message
            .reply(InputMessage::text(
                "Please reply to the user's message you want to ban.",
            ))
            .await?;
    }

    Ok(())
}

async fn kick_user(client: &mut Client, update: &mut Update, _data: &mut Data) -> Result<()> {
    let message = update.get_message().unwrap();

    if let Some(reply) = message.get_reply().await? {
        let user = reply.sender().unwrap();
        let chat = message.chat();

        client.kick_participant(chat, user).await?;

        message
            .reply(InputMessage::text("User has been kicked."))
            .await?;
    } else {
        message
            .reply(InputMessage::text(
                "Please reply to the user's message you want to kick.",
            ))
            .await?;
    }

    Ok(())
}
