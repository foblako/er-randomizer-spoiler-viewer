use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpoilerEntry {
    pub item: String,
    pub location: String,
    pub description: String,
    pub replaces: Option<String>,
    pub cost: Option<u32>,
    pub raw: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlacementEntry {
    pub original: String,
    pub original_location: String,
    pub replacement: String,
    pub replacement_location: String,
    pub raw: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReplaceEntry {
    pub original: String,
    pub replacement: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HintEntry {
    pub name: String,
    pub location: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SpoilerLog {
    pub great_runes: Vec<SpoilerEntry>,
    pub remembrances: Vec<SpoilerEntry>,
    pub key_item_hints: Vec<SpoilerEntry>,
    pub bell_bearing_hints: Vec<SpoilerEntry>,
    pub core_mechanics_hints: Vec<SpoilerEntry>,
    pub quest_item_hints: Vec<SpoilerEntry>,
    pub boss_placements: Vec<PlacementEntry>,
    pub miniboss_placements: Vec<PlacementEntry>,
    pub basic_placements: Vec<PlacementEntry>,
    pub gesture_placements: Vec<ReplaceEntry>,
    pub level_bgm_placements: Vec<ReplaceEntry>,
    pub starting_gifts: Vec<ReplaceEntry>,
    pub spoilers: Vec<SpoilerEntry>,
    pub counts: HashMap<String, usize>,
}
