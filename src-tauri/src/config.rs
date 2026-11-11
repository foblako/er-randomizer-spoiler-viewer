use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

pub type Fingerprint = (String, String);

fn config_path() -> Option<PathBuf> {
    dirs_next::home_dir().map(|h| h.join(".er_randomizer.json"))
}

#[allow(dead_code)]
#[derive(Debug, Serialize, Deserialize, Default)]
struct ConfigData {
    #[serde(default)]
    item_presets: HashMap<String, Vec<Fingerprint>>,
    #[serde(default)]
    theme: Option<String>,
}

pub fn load_presets() -> HashMap<String, Vec<Fingerprint>> {
    let Some(path) = config_path() else {
        return HashMap::new();
    };

    if !path.exists() {
        return HashMap::new();
    }

    let Ok(content) = fs::read_to_string(path) else {
        return HashMap::new();
    };

    let Ok(val) = serde_json::from_str::<serde_json::Value>(&content) else {
        return HashMap::new();
    };

    let mut result = HashMap::new();
    if let Some(presets_obj) = val.get("item_presets").and_then(|v| v.as_object()) {
        for (name, list) in presets_obj {
            if let Some(arr) = list.as_array() {
                let mut fps = Vec::new();
                for item in arr {
                    if let Some(pair) = item.as_array() {
                        if pair.len() >= 2 {
                            if let (Some(cat), Some(item_name)) = (pair[0].as_str(), pair[1].as_str()) {
                                fps.push((cat.to_string(), item_name.to_string()));
                            }
                        }
                    }
                }
                result.insert(name.clone(), fps);
            }
        }
    }
    result
}

pub fn save_preset(name: &str, fingerprints: Vec<Fingerprint>) -> Result<(), String> {
    let path = config_path().ok_or("Cannot determine home directory")?;

    let mut val: serde_json::Value = if path.exists() {
        let content = fs::read_to_string(&path).map_err(|e| e.to_string())?;
        serde_json::from_str(&content).unwrap_or(serde_json::json!({}))
    } else {
        serde_json::json!({})
    };

    if !val.is_object() {
        val = serde_json::json!({});
    }

    let presets = val.as_object_mut().unwrap()
        .entry("item_presets")
        .or_insert_with(|| serde_json::json!({}));

    if let Some(p_obj) = presets.as_object_mut() {
        p_obj.insert(name.to_string(), serde_json::to_value(fingerprints).map_err(|e| e.to_string())?);
    }

    let serialized = serde_json::to_string_pretty(&val).map_err(|e| e.to_string())?;
    fs::write(path, serialized).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn delete_preset(name: &str) -> Result<(), String> {
    let path = config_path().ok_or("Cannot determine home directory")?;
    if !path.exists() {
        return Ok(());
    }

    let content = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    let mut val: serde_json::Value = serde_json::from_str(&content).unwrap_or(serde_json::json!({}));

    if let Some(obj) = val.as_object_mut() {
        if let Some(presets) = obj.get_mut("item_presets").and_then(|p| p.as_object_mut()) {
            presets.remove(name);
        }
    }

    let serialized = serde_json::to_string_pretty(&val).map_err(|e| e.to_string())?;
    fs::write(path, serialized).map_err(|e| e.to_string())?;
    Ok(())
}
