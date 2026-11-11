import React, { useState } from 'react';
import { Star, Bookmark, Trash2, CheckSquare, Plus, X } from 'lucide-react';
import { BUILTIN_FILTERS, BuiltinFilter } from '../types';

interface SidebarProps {
  activeFilterId: string;
  onSelectBuiltin: (filter: BuiltinFilter) => void;
  userPresets: Record<string, [string, string][]>;
  activeUserPreset: string | null;
  onSelectUserPreset: (name: string) => void;
  onDeleteUserPreset: (name: string) => void;
  onSavePreset: (name: string) => void;
  selectionCount: number;
  onClearSelection: () => void;
  filterCounts: Record<string, number>;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeFilterId,
  onSelectBuiltin,
  userPresets,
  activeUserPreset,
  onSelectUserPreset,
  onDeleteUserPreset,
  onSavePreset,
  selectionCount,
  onClearSelection,
  filterCounts,
}) => {
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [newPresetName, setNewPresetName] = useState('');

  const handleSaveSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPresetName.trim()) return;
    onSavePreset(newPresetName.trim());
    setNewPresetName('');
    setShowSaveModal(false);
  };

  return (
    <aside className="w-80 bg-tarnished-900 border-r border-tarnished-800 flex flex-col justify-between h-full select-none shrink-0">
      <div className="overflow-y-auto flex-1 p-4 space-y-6">
        {/* Built-in filters */}
        <div>
          <div className="flex items-center gap-2 px-2 pb-2 mb-1 text-xs font-semibold text-gold-500 uppercase tracking-wider border-b border-tarnished-800">
            <Star className="w-3.5 h-3.5 fill-gold-500/20" />
            <span>Встроенные фильтры</span>
          </div>
          <div className="space-y-1">
            {BUILTIN_FILTERS.map((f) => {
              const isActive = activeUserPreset === null && activeFilterId === f.id;
              const count = filterCounts[f.id] ?? 0;
              return (
                <button
                  key={f.id}
                  onClick={() => onSelectBuiltin(f)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-left transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-gold-600/20 to-amber-600/10 text-gold-400 border border-gold-600/40 font-medium shadow-sm'
                      : 'text-neutral-300 hover:bg-tarnished-800/80 hover:text-neutral-100 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <span className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-gold-400' : 'bg-neutral-600'}`} />
                    <span className="truncate">{f.name}</span>
                  </div>
                  {count > 0 && (
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                      isActive ? 'bg-gold-500/20 text-gold-400' : 'bg-tarnished-800 text-neutral-400'
                    }`}>
                      {count.toLocaleString()}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* User presets */}
        <div>
          <div className="flex items-center justify-between px-2 pb-2 mb-1 text-xs font-semibold text-gold-500 uppercase tracking-wider border-b border-tarnished-800">
            <div className="flex items-center gap-2">
              <Bookmark className="w-3.5 h-3.5 fill-gold-500/20" />
              <span>Свои фильтры</span>
            </div>
            <span className="text-[10px] text-neutral-400 font-normal">
              {Object.keys(userPresets).length}
            </span>
          </div>

          <div className="space-y-1">
            {Object.keys(userPresets).length === 0 ? (
              <p className="px-3 py-3 text-xs text-neutral-500 italic">
                Нет сохранённых фильтров. Выберите чекбоксы и нажмите «Сохранить сборку».
              </p>
            ) : (
              Object.entries(userPresets).map(([name, fps]) => {
                const isActive = activeUserPreset === name;
                return (
                  <div
                    key={name}
                    className={`group flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-all ${
                      isActive
                        ? 'bg-gradient-to-r from-gold-600/20 to-amber-600/10 text-gold-400 border border-gold-600/40 font-medium'
                        : 'text-neutral-300 hover:bg-tarnished-800/80 hover:text-neutral-100 border border-transparent'
                    }`}
                  >
                    <button
                      onClick={() => onSelectUserPreset(name)}
                      className="flex-1 flex items-center gap-2.5 truncate text-left"
                    >
                      <Bookmark className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-gold-400 fill-gold-400/30' : 'text-neutral-500'}`} />
                      <span className="truncate">{name}</span>
                      <span className="text-xs text-neutral-500">({fps.length})</span>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteUserPreset(name);
                      }}
                      title="Удалить фильтр"
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20 text-neutral-400 hover:text-red-400 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Shopping cart footer bar */}
      <div className="p-4 bg-tarnished-950 border-t border-tarnished-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckSquare className="w-4 h-4 text-gold-500" />
            <span className="text-sm font-semibold text-neutral-200">
              В сборке: <span className="text-gold-400 font-bold">{selectionCount}</span>
            </span>
          </div>
          {selectionCount > 0 && (
            <button
              onClick={onClearSelection}
              className="text-xs text-neutral-400 hover:text-red-400 hover:underline cursor-pointer"
            >
              Очистить
            </button>
          )}
        </div>

        <button
          onClick={() => setShowSaveModal(true)}
          disabled={selectionCount === 0}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-gold-600/20 hover:bg-gold-600/30 border border-gold-600/40 text-gold-400 font-medium text-xs transition duration-150 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Сохранить как фильтр…</span>
        </button>
      </div>

      {/* Save Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-tarnished-900 border border-gold-600/40 rounded-xl p-6 w-full max-w-sm shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-serif text-base font-bold text-gold-400">
                Новый фильтр
              </h3>
              <button
                onClick={() => setShowSaveModal(false)}
                className="text-neutral-400 hover:text-neutral-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleSaveSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-neutral-400 mb-1">
                  Название фильтра ({selectionCount} элементов):
                </label>
                <input
                  type="text"
                  autoFocus
                  required
                  value={newPresetName}
                  onChange={(e) => setNewPresetName(e.target.value)}
                  placeholder="Например: Мой любимый билд"
                  className="w-full px-3 py-2 rounded-lg bg-tarnished-800 border border-tarnished-700 text-neutral-100 text-sm focus:outline-none focus:border-gold-500"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowSaveModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs text-neutral-400 hover:bg-tarnished-800"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-gold-600 hover:bg-gold-500 text-neutral-950 font-semibold text-xs shadow-md"
                >
                  Сохранить
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </aside>
  );
};
