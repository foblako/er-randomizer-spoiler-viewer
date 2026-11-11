import React from 'react';
import { FolderOpen, Sparkles, FileText } from 'lucide-react';
import { open } from '@tauri-apps/plugin-dialog';

interface HeaderProps {
  onOpenFile: (path: string) => void;
  fileName: string | null;
  totalEntries: number;
  loading: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenFile,
  fileName,
  totalEntries,
  loading,
}) => {
  const handleOpenClick = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'Spoiler Log',
          extensions: ['txt']
        }]
      });
      if (selected && typeof selected === 'string') {
        onOpenFile(selected);
      }
    } catch (e) {
      console.error('Failed to open file:', e);
    }
  };

  return (
    <header className="h-16 bg-tarnished-900 border-b border-gold-600/30 px-6 flex items-center justify-between shadow-md z-10 shrink-0">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-gold-600/30 to-amber-700/20 border border-gold-500/50 flex items-center justify-center shadow-inner">
          <Sparkles className="w-5 h-5 text-gold-400 animate-pulse" />
        </div>
        <div>
          <h1 className="font-serif text-lg font-bold tracking-wider text-gold-400 elden-glow">
            ELDEN RING
          </h1>
          <p className="text-xs text-neutral-400 -mt-1 font-medium tracking-wide">
            Spoiler Log Viewer
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {fileName ? (
          <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-lg bg-tarnished-850 border border-tarnished-700 text-sm">
            <FileText className="w-4 h-4 text-gold-500" />
            <span className="font-medium text-neutral-200 max-w-xs truncate" title={fileName}>
              {fileName}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-gold-600/20 text-gold-400 border border-gold-600/30 font-semibold">
              {totalEntries.toLocaleString()} записей
            </span>
          </div>
        ) : (
          <span className="text-xs text-neutral-500 italic">
            Лог не загружен
          </span>
        )}

        <button
          onClick={handleOpenClick}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-gold-600 to-amber-700 hover:from-gold-500 hover:to-amber-600 text-neutral-950 font-semibold text-sm shadow-lg shadow-gold-600/20 transition-all duration-200 active:scale-95 disabled:opacity-50 cursor-pointer"
        >
          <FolderOpen className="w-4 h-4" />
          <span>{loading ? 'Загрузка...' : 'Открыть лог'}</span>
        </button>
      </div>
    </header>
  );
};
