use crate::models::{HintEntry, PlacementEntry, ReplaceEntry, SpoilerEntry, SpoilerLog};
use regex::Regex;
use std::collections::{HashMap, HashSet};

pub struct SpoilerParser {
    placement_re: Regex,
    replace_re: Regex,
    starting_gift_re: Regex,
    cost_re: Regex,
    id_noise_re: Regex,
    scaling_noise_re: Regex,
}

impl Default for SpoilerParser {
    fn default() -> Self {
        Self::new()
    }
}

impl SpoilerParser {
    pub fn new() -> Self {
        Self {
            placement_re: Regex::new(r"^Replacing (?P<orig>.+?) in (?P<orig_loc>.+?): (?P<repl>.+?) from (?P<repl_loc>.+)$").unwrap(),
            replace_re: Regex::new(r"^Replacing (?P<orig>.+?): (?P<repl>.+)$").unwrap(),
            starting_gift_re: Regex::new(r"^Replacing starting gift (?P<orig>.+?): (?P<repl>.+)$").unwrap(),
            cost_re: Regex::new(r"^\s*\(cost:\s*(\d+)\)\s*$").unwrap(),
            id_noise_re: Regex::new(r"\s*\(#\s*\d+\)").unwrap(),
            scaling_noise_re: Regex::new(r"\s*\(scaling [^)]*\)\s*$").unwrap(),
        }
    }

    fn strip_id<'a>(&self, text: &'a str) -> std::borrow::Cow<'a, str> {
        self.id_noise_re.replace_all(text, "")
    }

    fn strip_scaling<'a>(&self, text: &'a str) -> std::borrow::Cow<'a, str> {
        self.scaling_noise_re.replace_all(text, "")
    }

    pub fn parse_text(&self, text: &str) -> SpoilerLog {
        let mut log = SpoilerLog::default();
        let mut section: Option<&str> = None;
        let mut pending: HashMap<&str, Vec<HintEntry>> = HashMap::new();
        pending.insert("key_items", Vec::new());
        pending.insert("bell_bearings", Vec::new());
        pending.insert("core_mechanics", Vec::new());
        pending.insert("quest_items", Vec::new());

        for raw_line in text.lines() {
            let line = raw_line.trim_end();
            let stripped = line.trim();

            match stripped {
                "-- Hints for key items:" => {
                    section = Some("key_items");
                    continue;
                }
                "-- Hints for bell bearings:" => {
                    section = Some("bell_bearings");
                    continue;
                }
                "-- Hints for core mechanics:" => {
                    section = Some("core_mechanics");
                    continue;
                }
                "-- Hints for quest items:" => {
                    section = Some("quest_items");
                    continue;
                }
                "-- End of hints" => {
                    section = None;
                    continue;
                }
                "-- Spoilers:" => {
                    section = Some("spoilers");
                    continue;
                }
                "-- End of item spoilers" => {
                    section = None;
                    continue;
                }
                "-- Boss placements" => {
                    section = Some("bosses");
                    continue;
                }
                "-- Miniboss placements" => {
                    section = Some("minibosses");
                    continue;
                }
                "-- Basic placements" => {
                    section = Some("basic");
                    continue;
                }
                "-- Gesture placements" => {
                    section = Some("gestures");
                    continue;
                }
                "-- Level BGM placements" => {
                    section = Some("bgm");
                    continue;
                }
                s if s.starts_with("-- ") => {
                    section = None;
                    continue;
                }
                _ => {}
            }

            if section == Some("spoilers") {
                if let Some(caps) = self.cost_re.captures(stripped) {
                    if let Some(last) = log.spoilers.last_mut() {
                        if let Ok(cost) = caps[1].parse::<u32>() {
                            last.cost = Some(cost);
                            continue;
                        }
                    }
                }
            }

            if stripped.is_empty() {
                continue;
            }

            if section.is_none() {
                if let Some(gift) = self.parse_starting_gift(stripped) {
                    log.starting_gifts.push(gift);
                    continue;
                }
            }

            if let Some(sec) = section {
                if let Some(hints) = pending.get_mut(sec) {
                    if let Some(hint) = self.parse_hint(stripped) {
                        hints.push(hint);
                    }
                    continue;
                }

                if sec == "spoilers" {
                    if let Some(spoiler) = self.parse_spoiler(stripped) {
                        if spoiler.item.contains("Remembrance") {
                            log.remembrances.push(spoiler.clone());
                        }
                        log.spoilers.push(spoiler);
                    }
                    continue;
                }

                if sec == "bosses" || sec == "minibosses" || sec == "basic" {
                    if let Some(placement) = self.parse_placement(stripped) {
                        match sec {
                            "bosses" => log.boss_placements.push(placement),
                            "minibosses" => log.miniboss_placements.push(placement),
                            _ => log.basic_placements.push(placement),
                        }
                    }
                    continue;
                }

                if sec == "gestures" || sec == "bgm" {
                    if let Some(replace) = self.parse_replace(stripped) {
                        if sec == "gestures" {
                            log.gesture_placements.push(replace);
                        } else {
                            log.level_bgm_placements.push(replace);
                        }
                    }
                    continue;
                }
            }
        }

        self.resolve_hints(&mut log, pending);
        self.dedupe_quest_items(&mut log);

        // Populate counts
        log.counts.insert("great_runes".to_string(), log.great_runes.len());
        log.counts.insert("remembrances".to_string(), log.remembrances.len());
        log.counts.insert("key_item_hints".to_string(), log.key_item_hints.len());
        log.counts.insert("bell_bearing_hints".to_string(), log.bell_bearing_hints.len());
        log.counts.insert("core_mechanics_hints".to_string(), log.core_mechanics_hints.len());
        log.counts.insert("quest_item_hints".to_string(), log.quest_item_hints.len());
        log.counts.insert("boss_placements".to_string(), log.boss_placements.len());
        log.counts.insert("miniboss_placements".to_string(), log.miniboss_placements.len());
        log.counts.insert("basic_placements".to_string(), log.basic_placements.len());
        log.counts.insert("gesture_placements".to_string(), log.gesture_placements.len());
        log.counts.insert("level_bgm_placements".to_string(), log.level_bgm_placements.len());
        log.counts.insert("starting_gifts".to_string(), log.starting_gifts.len());
        log.counts.insert("spoilers".to_string(), log.spoilers.len());

        log
    }

    fn parse_hint(&self, line: &str) -> Option<HintEntry> {
        let (name, location) = line.split_once(':')?;
        let name = name.trim();
        let location = location.trim();
        if name.is_empty() || location.is_empty() {
            return None;
        }
        Some(HintEntry {
            name: name.to_string(),
            location: location.to_string(),
        })
    }

    fn parse_placement(&self, line: &str) -> Option<PlacementEntry> {
        let caps = self.placement_re.captures(line)?;
        let orig = self.strip_id(&caps["orig"]).trim().to_string();
        let orig_loc = caps["orig_loc"].trim().to_string();
        let repl = self.strip_id(&caps["repl"]).trim().to_string();
        let repl_loc_raw = self.strip_id(&caps["repl_loc"]);
        let repl_loc = self.strip_scaling(&repl_loc_raw).trim().to_string();

        Some(PlacementEntry {
            original: orig,
            original_location: orig_loc,
            replacement: repl,
            replacement_location: repl_loc,
            raw: line.to_string(),
        })
    }

    fn parse_replace(&self, line: &str) -> Option<ReplaceEntry> {
        let caps = self.replace_re.captures(line)?;
        Some(ReplaceEntry {
            original: caps["orig"].trim().to_string(),
            replacement: caps["repl"].trim().to_string(),
        })
    }

    fn parse_starting_gift(&self, line: &str) -> Option<ReplaceEntry> {
        let caps = self.starting_gift_re.captures(line)?;
        Some(ReplaceEntry {
            original: caps["orig"].trim().to_string(),
            replacement: caps["repl"].trim().to_string(),
        })
    }

    fn parse_spoiler(&self, line: &str) -> Option<SpoilerEntry> {
        if !line.contains(" in ") || !line.contains(':') {
            return None;
        }
        let (head, tail) = line.split_once(':')?;
        let in_idx = head.rfind(" in ")?;
        let item = head[..in_idx].trim();
        let location = head[in_idx + 4..].trim();
        if item.is_empty() || location.is_empty() {
            return None;
        }

        let mut description = tail.trim().to_string();
        let mut replaces: Option<String> = None;

        if let Some(rep_idx) = description.rfind("Replaces ") {
            let before = description[..rep_idx].trim_end_matches([' ', '.']);
            let rep = description[rep_idx + 9..].trim_end_matches([' ', '.']).trim();
            replaces = Some(rep.to_string());
            description = before.to_string();
        }

        Some(SpoilerEntry {
            item: item.to_string(),
            location: location.to_string(),
            description,
            replaces,
            cost: None,
            raw: line.to_string(),
        })
    }

    fn resolve_hints(&self, log: &mut SpoilerLog, pending: HashMap<&str, Vec<HintEntry>>) {
        let mut by_item: HashMap<&str, Vec<&SpoilerEntry>> = HashMap::new();
        for s in &log.spoilers {
            by_item.entry(&s.item).or_default().push(s);
        }

        let mut used_ptrs: HashSet<*const SpoilerEntry> = HashSet::new();

        for (section, hints) in pending {
            for hint in hints {
                let target_loc = hint.location.strip_prefix("In ").unwrap_or(&hint.location).trim();
                let mut matched: Option<SpoilerEntry> = None;

                if let Some(cands) = by_item.get(hint.name.as_str()) {
                    for cand in cands {
                        let ptr = *cand as *const SpoilerEntry;
                        if used_ptrs.contains(&ptr) {
                            continue;
                        }
                        if cand.location == target_loc {
                            matched = Some((*cand).clone());
                            used_ptrs.insert(ptr);
                            break;
                        }
                    }
                }

                let entry = matched.unwrap_or_else(|| SpoilerEntry {
                    item: hint.name.clone(),
                    location: if target_loc.is_empty() { hint.location.clone() } else { target_loc.to_string() },
                    description: String::new(),
                    replaces: None,
                    cost: None,
                    raw: format!("{}: {}", hint.name, target_loc),
                });

                match section {
                    "key_items" => {
                        if entry.item.contains("Great Rune") && !entry.item.contains("Restored") {
                            log.great_runes.push(entry);
                        } else {
                            log.key_item_hints.push(entry);
                        }
                    }
                    "bell_bearings" => log.bell_bearing_hints.push(entry),
                    "core_mechanics" => log.core_mechanics_hints.push(entry),
                    "quest_items" => log.quest_item_hints.push(entry),
                    _ => {}
                }
            }
        }
    }

    fn dedupe_quest_items(&self, log: &mut SpoilerLog) {
        let mut seen = HashSet::new();
        log.quest_item_hints.retain(|e| seen.insert((e.item.clone(), e.location.clone())));
    }
}
