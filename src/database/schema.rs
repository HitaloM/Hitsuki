// @generated automatically by Diesel CLI.

diesel::table! {
    chats (chat_id) {
        chat_id -> Int8,
        chat_name -> Text,
        language_code -> Text,
    }
}

diesel::table! {
    users (user_id) {
        user_id -> Int8,
        username -> Text,
        language_code -> Text,
    }
}

diesel::allow_tables_to_appear_in_same_query!(chats, users,);
