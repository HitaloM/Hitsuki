// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use anyhow::Result;
use teloxide::{prelude::*, types::ParseMode};

use hitsuki::{
    commands::{BansCommand, StartCommand},
    Config,
};

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();

    let config = Config::load().expect("Failed to load configuration");

    log::info!("Starting Hitsuki...");
    let bot = Bot::new(config.bot.token).parse_mode(ParseMode::Html);

    let handler = Update::filter_message()
        .branch(
            dptree::entry()
                .filter_command::<StartCommand>()
                .endpoint(StartCommand::handler),
        )
        .branch(
            dptree::entry()
                .filter_command::<BansCommand>()
                .endpoint(BansCommand::handler),
        );

    Dispatcher::builder(bot, handler)
        .default_handler(|_upd| async move {}) // To stop warning about unhandled updates
        .error_handler(LoggingErrorHandler::with_custom_text(
            "An error has occurred in the dispatcher",
        ))
        .enable_ctrlc_handler()
        .build()
        .dispatch()
        .await;

    Ok(())
}
