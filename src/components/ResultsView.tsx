import React, { useRef, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Search, Copy, Download, Check, X, MapPin, RefreshCw, Sparkles, Package, Crown, Swords, Skull } from 'lucide-react';
import { PlacementEntry, ReplaceEntry, SpoilerEntry, isUniqueMob } from '../types';
import { ItemIcon } from './ItemIcon';
import { writeText } from '@tauri-apps/plugin-clipboard-manager';
import { save } from '@tauri-apps/plugin-dialog';
import { writeTextFile } from '@tauri-apps/plugin-fs';

export type UnifiedRow =
  | { kind: 'header'; title: string; count: number }
  | { kind: 'placement'; category: string; entry: PlacementEntry; fp: [string, string] }
  | { kind: 'spoiler'; category: string; entry: SpoilerEntry; fp: [string, string] }
  | { kind: 'replace'; category: string; entry: ReplaceEntry; fp: [string, string] };

interface ResultsViewProps {
  rows: UnifiedRow[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selection: Set<string>;
  onToggleSelection: (fp: [string, string]) => void;
  hasLog: boolean;
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  rows,
  searchQuery,
  onSearchChange,
  selection,
  onToggleSelection,
  hasLog,
}) => {
  const parentRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = React.useState(false);

  // Locked item heights ensure scrollbar dragging stops dead accurately with zero drift or jumping
  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    getItemKey: (index) => {
      const r = rows[index];
      if (r.kind === 'header') return `h_${r.title}_${index}`;
      return `${r.fp[0]}::${r.fp[1]}::${index}`;
    },
    estimateSize: (index) => {
      const row = rows[index];
      if (row.kind === 'header') return 48;
      if (row.kind === 'replace') return 76;
      return 96;
    },
    overscan: 15,
  });

  const totalItemsCount = useMemo(() => {
    return rows.filter((r) => r.kind !== 'header').length;
  }, [rows]);

  const exportText = useMemo(() => {
    const lines: string[] = [];
    for (const r of rows) {
      if (r.kind === 'header') {
        lines.push(`\n=== ${r.title} (${r.count}) ===\n`);
      } else if (r.kind === 'placement') {
        const e = r.entry;
        const from = e.replacement_location ? ` (из: ${e.replacement_location})` : '';
        const locLabel = r.category === 'boss_placements'
          ? 'Арена'
          : r.category === 'miniboss_placements'
          ? 'Локация'
          : 'Местоположение';
        lines.push(`${e.replacement}${from}`);
        if (e.original_location) lines.push(`  📍 ${locLabel}: ${e.original_location}`);
        if (e.original) lines.push(`  🔄 Вместо: ${e.original}`);
        lines.push('');
      } else if (r.kind === 'spoiler') {
        const e = r.entry;
        lines.push(`${e.item}`);
        if (e.location) lines.push(`  📍 Где: ${e.location}`);
        if (e.description) lines.push(`  Как: ${e.description}`);
        if (e.replaces) lines.push(`  🔄 Заменяет: ${e.replaces}`);
        if (e.cost != null) lines.push(`  Стоимость: ${e.cost} рун`);
        lines.push('');
      } else if (r.kind === 'replace') {
        const e = r.entry;
        lines.push(`${e.replacement}`);
        if (e.original) lines.push(`  🔄 Заменяет: ${e.original}`);
        lines.push('');
      }
    }
    return lines.join('\n');
  }, [rows]);

  const handleCopy = async () => {
    try {
      await writeText(exportText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Failed to copy:', e);
    }
  };

  const handleSave = async () => {
    try {
      const filePath = await save({
        filters: [{
          name: 'Text File',
          extensions: ['txt']
        }],
        defaultPath: 'spoiler_results.txt'
      });
      if (filePath) {
        await writeTextFile(filePath, exportText);
      }
    } catch (e) {
      console.error('Failed to save file:', e);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-tarnished-950 overflow-hidden">
      {/* Top action bar: Search & Export */}
      <div className="h-16 px-6 border-b border-tarnished-800 flex items-center justify-between gap-4 bg-tarnished-900/60 shrink-0">
        <div className="relative flex-1 max-w-xl">
          <Search className="w-4 h-4 text-neutral-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Поиск по предметам, боссам, аренам, описаниям..."
            className="w-full pl-10 pr-9 py-2 rounded-lg bg-tarnished-850 border border-tarnished-700 text-sm text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-gold-500 focus:ring-1 focus:ring-gold-500/50 transition"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-200 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            disabled={rows.length === 0}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-tarnished-850 hover:bg-tarnished-800 border border-tarnished-700 text-xs font-medium text-neutral-200 transition disabled:opacity-40 cursor-pointer"
            title="Скопировать всё видимое в буфер обмена"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5 text-gold-500" />}
            <span>{copied ? 'Скопировано!' : 'Копировать'}</span>
          </button>

          <button
            onClick={handleSave}
            disabled={rows.length === 0}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-tarnished-850 hover:bg-tarnished-800 border border-tarnished-700 text-xs font-medium text-neutral-200 transition disabled:opacity-40 cursor-pointer"
            title="Сохранить в текстовый файл"
          >
            <Download className="w-3.5 h-3.5 text-gold-500" />
            <span>Сохранить в файл</span>
          </button>
        </div>
      </div>

      {/* Main Results View */}
      <div ref={parentRef} className="flex-1 overflow-y-auto px-6 py-4">
        {!hasLog ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-neutral-500 space-y-3">
            <div className="w-16 h-16 rounded-2xl bg-tarnished-900 border border-gold-600/20 flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-gold-500/40" />
            </div>
            <h3 className="font-serif text-lg font-bold text-neutral-300">
              Лог рандомайзера не загружен
            </h3>
            <p className="text-sm max-w-md">
              Нажмите кнопку <strong className="text-gold-400">«Открыть лог»</strong> сверху, чтобы выбрать текстовый спойлер-лог рандомайзера (.txt).
            </p>
          </div>
        ) : rows.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-neutral-500 space-y-2">
            <Package className="w-12 h-12 text-neutral-600" />
            <p className="text-base text-neutral-300 font-medium">Ничего не найдено</p>
            <p className="text-xs text-neutral-500">
              Попробуйте изменить поисковый запрос или выбрать другой фильтр слева.
            </p>
          </div>
        ) : (
          <div
            style={{
              height: `${virtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            {virtualizer.getVirtualItems().map((virtualItem) => {
              const row = rows[virtualItem.index];

              if (row.kind === 'header') {
                return (
                  <div
                    key={virtualItem.key}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '48px',
                      transform: `translateY(${virtualItem.start}px)`,
                    }}
                    className="pt-3 pb-1"
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-px bg-gradient-to-r from-transparent via-gold-600/40 to-transparent flex-1" />
                      <div className="flex items-center gap-2 px-3.5 py-1 rounded-full bg-tarnished-900 border border-gold-600/40 text-gold-400 font-serif text-xs font-bold tracking-wider uppercase shadow-sm">
                        <span>{row.title}</span>
                        <span className="text-[11px] px-1.5 py-0.2 rounded-full bg-gold-600/20 text-gold-300">
                          {row.count}
                        </span>
                      </div>
                      <div className="h-px bg-gradient-to-r from-transparent via-gold-600/40 to-transparent flex-1" />
                    </div>
                  </div>
                );
              }

              const fpKey = `${row.fp[0]}::${row.fp[1]}`;
              const isChecked = selection.has(fpKey);

              if (row.kind === 'placement') {
                return (
                  <div
                    key={virtualItem.key}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '96px',
                      transform: `translateY(${virtualItem.start}px)`,
                    }}
                    className="pb-2"
                  >
                    <div
                      onClick={() => onToggleSelection(row.fp)}
                      className={`elden-card h-[88px] rounded-xl px-3.5 py-2.5 flex items-center gap-3.5 cursor-pointer transition select-none ${
                        isChecked
                          ? 'border-gold-500/70 bg-gradient-to-r from-gold-600/15 via-tarnished-850 to-tarnished-900 shadow-md'
                          : ''
                      }`}
                    >
                      {/* Checkbox */}
                      <div className="shrink-0">
                        <div
                          className={`w-5 h-5 rounded-md border flex items-center justify-center transition ${
                            isChecked
                              ? 'bg-gold-500 border-gold-400 text-neutral-950'
                              : 'border-neutral-600 bg-tarnished-950/60 hover:border-gold-500/60'
                          }`}
                        >
                          {isChecked && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                        </div>
                      </div>

                      {/* Icon */}
                      <ItemIcon
                        kind="placement"
                        category={row.category}
                        name={row.entry.replacement}
                        originalName={row.entry.original}
                      />

                      {/* Content */}
                      <div className="flex-1 min-w-0 space-y-0.5 overflow-hidden">
                        <div className="flex items-center justify-between gap-2 overflow-hidden">
                          <div className="flex items-center gap-2 truncate min-w-0">
                            <span className="font-semibold text-neutral-100 text-sm tracking-wide truncate">
                              {row.entry.replacement}
                            </span>
                            {row.entry.replacement_location && (
                              <span className="text-neutral-400 text-xs truncate">
                                (из: <span className="text-neutral-300">{row.entry.replacement_location}</span>)
                              </span>
                            )}
                          </div>

                          {/* Category Badge on the right */}
                          {row.category === 'boss_placements' && (
                            <span className="shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/35 text-amber-300 flex items-center gap-1 shadow-sm">
                              <Crown className="w-2.5 h-2.5 text-amber-400" />
                              <span>Босс арены</span>
                            </span>
                          )}
                          {row.category === 'miniboss_placements' && (
                            <span className="shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-sky-500/15 border border-sky-500/35 text-sky-300 flex items-center gap-1 shadow-sm">
                              <Swords className="w-2.5 h-2.5 text-sky-400" />
                              <span>Мини-босс</span>
                            </span>
                          )}
                          {row.category === 'basic_placements' && (
                            isUniqueMob(row.entry.replacement) ? (
                              <span className="shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-purple-500/15 border border-purple-500/35 text-purple-300 flex items-center gap-1 shadow-sm">
                                <Sparkles className="w-2.5 h-2.5 text-purple-400" />
                                <span>Уникальный моб</span>
                              </span>
                            ) : (
                              <span className="shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-neutral-800/80 border border-neutral-700 text-neutral-400 flex items-center gap-1">
                                <Skull className="w-2.5 h-2.5 text-neutral-400" />
                                <span>Обычный враг</span>
                              </span>
                            )
                          )}
                        </div>

                        <div className="flex items-center gap-1.5 text-xs text-neutral-400 truncate">
                          <MapPin className="w-3.5 h-3.5 text-gold-500 shrink-0" />
                          {row.category === 'boss_placements' ? (
                            <span className="text-amber-400 font-medium shrink-0">Арена:</span>
                          ) : row.category === 'miniboss_placements' ? (
                            <span className="text-sky-400 font-medium shrink-0">Локация:</span>
                          ) : (
                            <span className="text-purple-400/90 font-medium shrink-0">Местоположение:</span>
                          )}
                          <span className="text-neutral-200 truncate">{row.entry.original_location}</span>
                        </div>

                        {row.entry.original ? (
                          <div className="flex items-center gap-1.5 text-xs text-neutral-400 truncate">
                            <RefreshCw className="w-3 h-3 text-amber-500/80 shrink-0" />
                            <span className="text-neutral-400 font-medium shrink-0">Вместо:</span>
                            <span className="text-neutral-300 font-medium truncate">{row.entry.original}</span>
                          </div>
                        ) : (
                          <div className="h-4" />
                        )}
                      </div>
                    </div>
                  </div>
                );
              }

              if (row.kind === 'spoiler') {
                return (
                  <div
                    key={virtualItem.key}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '96px',
                      transform: `translateY(${virtualItem.start}px)`,
                    }}
                    className="pb-2"
                  >
                    <div
                      onClick={() => onToggleSelection(row.fp)}
                      className={`elden-card h-[88px] rounded-xl px-3.5 py-2.5 flex items-center gap-3.5 cursor-pointer transition select-none ${
                        isChecked
                          ? 'border-gold-500/70 bg-gradient-to-r from-gold-600/15 via-tarnished-850 to-tarnished-900 shadow-md'
                          : ''
                      }`}
                    >
                      {/* Checkbox */}
                      <div className="shrink-0">
                        <div
                          className={`w-5 h-5 rounded-md border flex items-center justify-center transition ${
                            isChecked
                              ? 'bg-gold-500 border-gold-400 text-neutral-950'
                              : 'border-neutral-600 bg-tarnished-950/60 hover:border-gold-500/60'
                          }`}
                        >
                          {isChecked && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                        </div>
                      </div>

                      {/* Icon */}
                      <ItemIcon
                        kind="spoiler"
                        category={row.category}
                        name={row.entry.item}
                      />

                      {/* Content */}
                      <div className="flex-1 min-w-0 space-y-0.5 overflow-hidden">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-neutral-100 text-sm tracking-wide truncate">
                            {row.entry.item}
                          </span>
                          {row.entry.cost != null && (
                            <span className="text-[10px] px-2 py-0.2 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold shrink-0">
                              {row.entry.cost.toLocaleString()} рун
                            </span>
                          )}
                        </div>

                        {row.entry.location ? (
                          <div className="flex items-center gap-1.5 text-xs text-neutral-400 truncate">
                            <MapPin className="w-3.5 h-3.5 text-gold-500 shrink-0" />
                            <span className="text-gold-400 font-medium shrink-0">Где:</span>
                            <span className="text-neutral-200 truncate">{row.entry.location}</span>
                          </div>
                        ) : (
                          <div className="h-4" />
                        )}

                        <div className="flex items-center gap-x-3 text-xs text-neutral-400 truncate">
                          {row.entry.description && (
                            <span className="truncate">
                              <strong className="text-neutral-400 font-medium">Как:</strong> {row.entry.description}
                            </span>
                          )}
                          {row.entry.replaces && (
                            <span className="flex items-center gap-1 text-neutral-400 truncate">
                              <RefreshCw className="w-3 h-3 text-amber-500/80 shrink-0" />
                              <strong className="text-neutral-400 font-medium shrink-0">Заменяет:</strong>
                              <span className="truncate">{row.entry.replaces}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              }

              // Replace (Gestures, BGM, Starting Gifts)
              return (
                <div
                  key={virtualItem.key}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '76px',
                    transform: `translateY(${virtualItem.start}px)`,
                  }}
                  className="pb-2"
                >
                  <div
                    onClick={() => onToggleSelection(row.fp)}
                    className={`elden-card h-[68px] rounded-xl px-3.5 py-2.5 flex items-center gap-3.5 cursor-pointer transition select-none ${
                      isChecked
                        ? 'border-gold-500/70 bg-gradient-to-r from-gold-600/15 via-tarnished-850 to-tarnished-900 shadow-md'
                        : ''
                    }`}
                  >
                    {/* Checkbox */}
                    <div className="shrink-0">
                      <div
                        className={`w-5 h-5 rounded-md border flex items-center justify-center transition ${
                          isChecked
                            ? 'bg-gold-500 border-gold-400 text-neutral-950'
                            : 'border-neutral-600 bg-tarnished-950/60 hover:border-gold-500/60'
                        }`}
                      >
                        {isChecked && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                      </div>
                    </div>

                    {/* Icon */}
                    <ItemIcon
                      kind="replace"
                      category={row.category}
                      name={row.entry.replacement}
                      originalName={row.entry.original}
                    />

                    {/* Content */}
                    <div className="flex-1 min-w-0 space-y-0.5 overflow-hidden">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-neutral-100 text-sm tracking-wide truncate">
                          {row.entry.replacement}
                        </span>
                      </div>
                      {row.entry.original ? (
                        <div className="flex items-center gap-1.5 text-xs text-neutral-400 truncate">
                          <RefreshCw className="w-3 h-3 text-amber-500/80 shrink-0" />
                          <span className="text-neutral-400 font-medium shrink-0">Заменяет:</span>
                          <span className="text-neutral-300 font-medium truncate">{row.entry.original}</span>
                        </div>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer bar */}
      <div className="h-8 px-6 bg-tarnished-900 border-t border-tarnished-800 flex items-center justify-between text-xs text-neutral-500 shrink-0">
        <span>Элементов в текущем виде: <strong className="text-neutral-300">{totalItemsCount.toLocaleString()}</strong></span>
        <span>Elden Ring Spoiler Viewer v1.0.0 (Rust & Tauri)</span>
      </div>
    </div>
  );
};
