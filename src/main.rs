// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

use grammers_client::{Client, Config, InitParams};
use grammers_friendly::prelude::*;
use grammers_session::Session;

use hitsuki::{handlers, Result};

const SESSION_FILE: &str = "hitsuki.session";

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();

    let config = hitsuki::Config::load()?;

    log::info!("Connecting bot...");
    let client = connect_bot(&config).await?;
    log::info!("Bot connected!");

    authorize_bot(&client, &config).await?;
    setup_dispatcher(&client).await?;
    save_session(&client)?;

    Ok(())
}

async fn connect_bot(config: &hitsuki::Config) -> Result<Client> {
    let session = Session::load_file_or_create(SESSION_FILE)?;

    let client_config = Config {
        session,
        api_id: config.telegram.api_id,
        api_hash: config.telegram.api_hash.clone(),
        params: InitParams {
            catch_up: false,
            flood_sleep_threshold: 180,
            ..Default::default()
        },
    };

    let client = Client::connect(client_config).await?;

    Ok(client)
}

async fn authorize_bot(client: &Client, config: &hitsuki::Config) -> Result<()> {
    if !client.is_authorized().await? {
        client.bot_sign_in(&config.bot.token).await?;
        client.session().save_to_file(SESSION_FILE)?;

        log::info!("Bot authorized");
    }
    Ok(())
}

async fn setup_dispatcher(client: &Client) -> Result<()> {
    Dispatcher::default()
        .add_router(handlers::start())
        .run(client.clone())
        .await?;

    log::info!("Dispatcher is running");

    Ok(())
}

fn save_session(client: &Client) -> Result<()> {
    client.session().save_to_file(SESSION_FILE)?;

    log::info!("Session saved");

    Ok(())
}
