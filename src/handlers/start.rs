// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use grammers_client::{Client, InputMessage, Update};
use grammers_friendly::prelude::*;

use crate::Result;

pub fn router() -> Router {
    Router::default().add_handler(Handler::new_message(start, macros::command!("start")))
}

async fn start(_client: &mut Client, update: &mut Update, _data: &mut Data) -> Result<()> {
    let message = update.get_message().unwrap();
    message.reply(InputMessage::text("Hi!")).await?;
    Ok(())
}
