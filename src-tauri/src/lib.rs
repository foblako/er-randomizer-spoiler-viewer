pub mod config;
pub mod models;
pub mod parser;

use models::SpoilerLog;
use parser::SpoilerParser;
use std::collections::HashMap;
use std::fs;

#[tauri::command]
fn parse_log_file(path: String) -> Result<SpoilerLog, String> {
    let content = fs::read_to_string(&path).map_err(|e| format!("Failed to read file: {e}"))?;
    let parser = SpoilerParser::new();
    Ok(parser.parse_text(&content))
}

#[tauri::command]
fn parse_log_text(text: String) -> Result<SpoilerLog, String> {
    let parser = SpoilerParser::new();
    Ok(parser.parse_text(&text))
}

#[tauri::command]
fn get_user_presets() -> Result<HashMap<String, Vec<(String, String)>>, String> {
    Ok(config::load_presets())
}

#[tauri::command]
fn save_user_preset(name: String, fingerprints: Vec<(String, String)>) -> Result<(), String> {
    config::save_preset(&name, fingerprints)
}

#[tauri::command]
fn delete_user_preset(name: String) -> Result<(), String> {
    config::delete_preset(&name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::new().level(log::LevelFilter::Info).build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .invoke_handler(tauri::generate_handler![
            parse_log_file,
            parse_log_text,
            get_user_presets,
            save_user_preset,
            delete_user_preset
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
