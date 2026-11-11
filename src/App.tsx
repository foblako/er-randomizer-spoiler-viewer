import { useState, useEffect, useMemo, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ResultsView, UnifiedRow } from './components/ResultsView';
import {
  SpoilerLog,
  BUILTIN_FILTERS,
  BuiltinFilter,
  CATEGORY_LABELS,
} from './types';

export function App() {
  const [log, setLog] = useState<SpoilerLog | null>(null);
  const [filePath, setFilePath] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const [activeFilterId, setActiveFilterId] = useState<string>('runes_and_keys');
  const [activeUserPreset, setActiveUserPreset] = useState<string | null>(null);
  const [userPresets, setUserPresets] = useState<Record<string, [string, string][]>>({});

  const [selection, setSelection] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Load user presets from disk on mount
  useEffect(() => {
    invoke<Record<string, [string, string][]>>('get_user_presets')
      .then((presets) => setUserPresets(presets))
      .catch((err) => console.error('Failed to load user presets:', err));
  }, []);

  // Handle loading a spoiler log file
  const handleOpenFile = useCallback(async (path: string) => {
    setLoading(true);
    try {
      const parsed = await invoke<SpoilerLog>('parse_log_file', { path });
      setLog(parsed);
      setFilePath(path);
    } catch (err) {
      console.error('Failed to parse log file:', err);
      alert(`Ошибка чтения лога: ${err}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Select built-in filter
  const handleSelectBuiltin = useCallback((filter: BuiltinFilter) => {
    setActiveFilterId(filter.id);
    setActiveUserPreset(null);
  }, []);

  // Select user-saved preset
  const handleSelectUserPreset = useCallback((name: string) => {
    setActiveUserPreset(name);
    // Also load items from preset into cart
    const fps = userPresets[name] || [];
    setSelection(new Set(fps.map(([cat, n]) => `${cat}::${n}`)));
  }, [userPresets]);

  // Save new user preset
  const handleSavePreset = useCallback(async (name: string) => {
    const fps: [string, string][] = Array.from(selection).map((k) => {
      const idx = k.indexOf('::');
      return [k.substring(0, idx), k.substring(idx + 2)];
    });

    try {
      await invoke('save_user_preset', { name, fingerprints: fps });
      setUserPresets((prev) => ({ ...prev, [name]: fps }));
      setActiveUserPreset(name);
    } catch (err) {
      console.error('Failed to save preset:', err);
      alert(`Ошибка сохранения пресета: ${err}`);
    }
  }, [selection]);

  // Delete user preset
  const handleDeleteUserPreset = useCallback(async (name: string) => {
    try {
      await invoke('delete_user_preset', { name });
      setUserPresets((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
      if (activeUserPreset === name) {
        setActiveUserPreset(null);
      }
    } catch (err) {
      console.error('Failed to delete preset:', err);
    }
  }, [activeUserPreset]);

  // Toggle selection for shopping cart
  const handleToggleSelection = useCallback((fp: [string, string]) => {
    const key = `${fp[0]}::${fp[1]}`;
    setSelection((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  // Clear shopping cart
  const handleClearSelection = useCallback(() => {
    setSelection(new Set());
  }, []);

  // Calculate badge counts for built-in filters
  const filterCounts = useMemo(() => {
    if (!log) return {};
    const res: Record<string, number> = {};

    for (const bf of BUILTIN_FILTERS) {
      let count = 0;
      for (const key of bf.keys) {
        const entries = (log as any)[key] || [];
        const itemAllow = bf.itemFilters?.[key];
        const origAllow = bf.originalFilters?.[key];

        for (const entry of entries) {
          if (itemAllow && !itemAllow.includes(entry.item || entry.replacement)) continue;
          if (origAllow && !origAllow.includes(entry.original)) continue;
          count++;
        }
      }
      res[bf.id] = count;
    }
    return res;
  }, [log]);

  // Compute filtered rows
  const rows = useMemo<UnifiedRow[]>(() => {
    if (!log) return [];

    const query = searchQuery.trim().toLowerCase();
    const result: UnifiedRow[] = [];

    // Mode 1: User Preset
    if (activeUserPreset) {
      const fps = userPresets[activeUserPreset] || [];
      const matchedRows: UnifiedRow[] = [];

      for (const [cat, name] of fps) {
        const list = (log as any)[cat] || [];
        for (const entry of list) {
          const entryName = entry.item || entry.replacement || '';
          if (entryName === name) {
            const fp: [string, string] = [cat, entryName];
            if (cat === 'boss_placements' || cat === 'miniboss_placements' || cat === 'basic_placements') {
              if (query) {
                const hay = `${entry.original} ${entry.original_location} ${entry.replacement} ${entry.replacement_location}`.toLowerCase();
                if (!hay.includes(query)) continue;
              }
              matchedRows.push({ kind: 'placement', category: cat, entry, fp });
            } else if (cat === 'gesture_placements' || cat === 'level_bgm_placements' || cat === 'starting_gifts') {
              if (query) {
                const hay = `${entry.original} ${entry.replacement}`.toLowerCase();
                if (!hay.includes(query)) continue;
              }
              matchedRows.push({ kind: 'replace', category: cat, entry, fp });
            } else {
              if (query) {
                const hay = `${entry.item} ${entry.location} ${entry.description} ${entry.replaces || ''}`.toLowerCase();
                if (!hay.includes(query)) continue;
              }
              matchedRows.push({ kind: 'spoiler', category: cat, entry, fp });
            }
          }
        }
      }

      if (matchedRows.length > 0) {
        result.push({ kind: 'header', title: activeUserPreset, count: matchedRows.length });
        result.push(...matchedRows);
      }
      return result;
    }

    // Mode 2: Built-in Filter
    const activeFilter = BUILTIN_FILTERS.find((f) => f.id === activeFilterId) || BUILTIN_FILTERS[0];

    // Special case: Merged section (e.g. Achievement Bosses)
    if (activeFilter.mergedSectionTitle) {
      const allMatches: { entry: any; cat: string; fp: [string, string] }[] = [];

      for (const key of activeFilter.keys) {
        const entries = (log as any)[key] || [];
        const origAllow = activeFilter.originalFilters?.[key];

        for (const entry of entries) {
          if (origAllow && !origAllow.includes(entry.original)) continue;
          if (query) {
            const hay = `${entry.original} ${entry.original_location} ${entry.replacement} ${entry.replacement_location}`.toLowerCase();
            if (!hay.includes(query)) continue;
          }
          allMatches.push({
            entry,
            cat: key,
            fp: [key, entry.replacement],
          });
        }
      }

      // Sort by original story order if specified
      if (activeFilter.originalOrder) {
        const orderMap = new Map(activeFilter.originalOrder.map((name, i) => [name, i]));
        const maxOrder = activeFilter.originalOrder.length;
        allMatches.sort((a, b) => {
          const idxA = orderMap.get(a.entry.original) ?? maxOrder;
          const idxB = orderMap.get(b.entry.original) ?? maxOrder;
          return idxA - idxB;
        });
      }

      if (allMatches.length > 0) {
        result.push({
          kind: 'header',
          title: activeFilter.mergedSectionTitle,
          count: allMatches.length,
        });
        for (const item of allMatches) {
          result.push({
            kind: 'placement',
            category: item.cat,
            entry: item.entry,
            fp: item.fp,
          });
        }
      }
      return result;
    }

    // Default per-category rendering
    for (const key of activeFilter.keys) {
      const entries = (log as any)[key] || [];
      const itemAllow = activeFilter.itemFilters?.[key];
      const origAllow = activeFilter.originalFilters?.[key];

      const catMatches: UnifiedRow[] = [];

      for (const entry of entries) {
        const primaryName = entry.item || entry.replacement || '';
        if (itemAllow && !itemAllow.includes(primaryName)) continue;
        if (origAllow && !origAllow.includes(entry.original)) continue;

        const fp: [string, string] = [key, primaryName];

        if (key === 'boss_placements' || key === 'miniboss_placements' || key === 'basic_placements') {
          if (query) {
            const hay = `${entry.original} ${entry.original_location} ${entry.replacement} ${entry.replacement_location}`.toLowerCase();
            if (!hay.includes(query)) continue;
          }
          catMatches.push({ kind: 'placement', category: key, entry, fp });
        } else if (key === 'gesture_placements' || key === 'level_bgm_placements' || key === 'starting_gifts') {
          if (query) {
            const hay = `${entry.original} ${entry.replacement}`.toLowerCase();
            if (!hay.includes(query)) continue;
          }
          catMatches.push({ kind: 'replace', category: key, entry, fp });
        } else {
          if (query) {
            const hay = `${entry.item} ${entry.location} ${entry.description} ${entry.replaces || ''}`.toLowerCase();
            if (!hay.includes(query)) continue;
          }
          catMatches.push({ kind: 'spoiler', category: key, entry, fp });
        }
      }

      if (catMatches.length > 0) {
        const title = activeFilter.sectionTitles?.[key] || CATEGORY_LABELS[key] || key;
        result.push({
          kind: 'header',
          title,
          count: catMatches.length,
        });
        result.push(...catMatches);
      }
    }

    return result;
  }, [log, activeFilterId, activeUserPreset, userPresets, searchQuery]);

  const totalEntries = useMemo(() => {
    if (!log) return 0;
    return Object.values(log.counts).reduce((a, b) => a + b, 0);
  }, [log]);

  const shortFileName = useMemo(() => {
    if (!filePath) return null;
    const parts = filePath.split(/[/\\]/);
    return parts[parts.length - 1];
  }, [filePath]);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-tarnished-950 text-neutral-100 select-none">
      <Header
        onOpenFile={handleOpenFile}
        fileName={shortFileName}
        totalEntries={totalEntries}
        loading={loading}
      />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeFilterId={activeFilterId}
          onSelectBuiltin={handleSelectBuiltin}
          userPresets={userPresets}
          activeUserPreset={activeUserPreset}
          onSelectUserPreset={handleSelectUserPreset}
          onDeleteUserPreset={handleDeleteUserPreset}
          onSavePreset={handleSavePreset}
          selectionCount={selection.size}
          onClearSelection={handleClearSelection}
          filterCounts={filterCounts}
        />
        <ResultsView
          rows={rows}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selection={selection}
          onToggleSelection={handleToggleSelection}
          hasLog={log !== null}
        />
      </div>
    </div>
  );
}

export default App;
