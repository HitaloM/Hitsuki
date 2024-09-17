// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use anyhow::Result;
use teloxide::{
    adaptors::throttle::Limits, prelude::*, types::ParseMode, update_listeners::Polling,
};

use hitsuki::{handlers, Config};

#[tokio::main]
async fn main() -> Result<()> {
    pretty_env_logger::formatted_builder()
        .filter_level(log::LevelFilter::Info)
        .init();

    log::info!("Starting bot...");

    let config = Config::load().expect("Failed to load configuration");

    let bot = Bot::new(config.bot.token)
        .throttle(Limits::default())
        .parse_mode(ParseMode::Html)
        .cache_me();

    let handler = dptree::entry()
        .branch(handlers::start::schema())
        .branch(handlers::bans::schema());

    let error_handler =
        LoggingErrorHandler::with_custom_text("An error has occurred in the dispatcher");
    let listener = Polling::builder(bot.clone())
        .timeout(std::time::Duration::from_secs(10))
        .drop_pending_updates()
        .build();

    Dispatcher::builder(bot, handler)
        .distribution_function(|_| None::<()>) // Always processing updates concurrently
        .default_handler(|_| async move {}) // Don't warn about unhandled updates
        .enable_ctrlc_handler()
        .build()
        .dispatch_with_listener(listener, error_handler)
        .await;

    Ok(())
}
