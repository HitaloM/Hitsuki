// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use teloxide::prelude::*;
use teloxide::types::ParseMode;

use hitsuki::handlers::{bans, start, BansCommand, StartCommand};
use hitsuki::Config;

#[tokio::main]
async fn main() -> ResponseResult<()> {
    env_logger::init();

    let config = Config::load().expect("Failed to load configuration");

    log::info!("Starting Hitsuki...");
    let bot = Bot::new(config.bot.token).parse_mode(ParseMode::Html);

    let handler = Update::filter_message()
        .branch(
            dptree::entry()
                .filter_command::<StartCommand>()
                .endpoint(start),
        )
        .branch(
            dptree::entry()
                .filter_command::<BansCommand>()
                .endpoint(bans),
        );

    Dispatcher::builder(bot.clone(), handler)
        .dependencies(dptree::deps![bot])
        .default_handler(|_upd| async move {}) // For Teloxide to stop warning about unhandled updates
        .error_handler(LoggingErrorHandler::with_custom_text(
            "An error has occurred in the dispatcher",
        ))
        .enable_ctrlc_handler()
        .build()
        .dispatch()
        .await;

    Ok(())
}
