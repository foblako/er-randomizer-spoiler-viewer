"""Tkinter GUI for browsing parsed Elden Ring Randomizer spoiler logs.

Two-column layout with a header on top:

::

    ┌── header ────────────────────────────────────────────────────┐
    │  📂 Открыть лог       <filename>                       ☀/🌙 │
    ├── filters ────────────┬── search + results ──────────────────┤
    │  ФИЛЬТРЫ              │  Поиск [.....]  [⎘]  [💾]            │
    │                       │                                       │
    │  Встроенные           │  ── Великие Руны (7) ─────────────── │
    │  ★ Великие Руны…      │  ☐ Godrick's Great Rune              │
    │    Все обычные боссы  │      Limgrave · Groveside Cave        │
    │    Все боссы в игре   │      Beastman of Farum Azula          │
    │    Ключевые предметы  │            →  Flamedrake Talisman     │
    │    Все предметы       │                                       │
    │    Вообще всё         │  ☐ Great Rune of the Unborn          │
    │                       │      …                                │
    │  Свои фильтры         │                                       │
    │  🔖 Speedrun core     │                                       │
    │  🔖 Boss rush         │                                       │
    │       [Удалить]       │                                       │
    ├── selection bar ──────┴───────────────────────────────────────┤
    │  В сборке: 12        [Очистить]      [Сохранить как фильтр…] │
    ├── status bar ────────────────────────────────────────────────┤
    │  Загружен: <path>                                  Всего: 1024│
    └──────────────────────────────────────────────────────────────┘

The big design idea: there's one concept on the left — *filters*. Built-in
filters are a fixed list of 6 commonly-useful bundles. User filters are
hand-picked sets of items the user accumulated by ticking checkboxes in
the results pane and saved under a name. Everything else (mix-and-match
category checkboxes, applying-a-preset-then-fighting-with-the-category-
checkboxes) is gone — that was confusing and the source of the
"can't-click-categories-after-applying-preset" bug.
"""

from __future__ import annotations

import contextlib
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from er_randomizer.filters import BUILTIN_FILTERS, DEFAULT_FILTER, BuiltinFilter
from er_randomizer.formatting import (
    TAG_ARROW,
    TAG_DETAIL,
    TAG_INDENT,
    TAG_LOCATION,
    TAG_NAME,
    TAG_PLAIN,
    entry_fingerprint,
    entry_name,
    entry_searchable,
    format_entry,
)
from er_randomizer.parser import SpoilerLog, SpoilerParser
from er_randomizer.presets import CATEGORY_LABELS
from er_randomizer.theme import (
    Theme,
    load_preferred_theme,
    save_preferred_theme,
    toggle,
)
from er_randomizer.user_presets import (
    Fingerprint,
    delete_user_preset,
    load_user_presets,
    save_user_preset,
)

# Debounce search-input rerenders so rapid typing doesn't redraw thousands
# of entries on every keystroke. 150ms feels instantaneous while
# consolidating bursts.
_SEARCH_DEBOUNCE_MS = 150

# Hard cap on rendered entries. The "Вообще всё" filter on real logs hits
# ~26k entries; even a single Tk insert call for that volume plus the
# resulting Text-widget layout takes >1s. This cap keeps every render
# fast and shows a footer telling the user how many extra matches were
# hidden.
_RENDER_CAP = 2000

_TAG_HEADER = "header"
_TAG_CAP_NOTE = "cap_note"
_TAG_BOX = "box"
_TAG_BOX_OFF = "box_off"
_TAG_BOX_ON = "box_on"
_TAG_HINT = "hint"

_BOX_OFF = "☐"
_BOX_ON = "☑"

# Glyphs used in the filter list. The two flavours have distinct prefixes
# so the eye can scan "what's built-in vs what I made" quickly.
_BUILTIN_GLYPH = "★"
_USER_GLYPH = "🔖"

# Listbox row identifiers prefixed so we can tell builtin / user / heading
# apart from a single string.
_PREFIX_BUILTIN = "B:"
_PREFIX_USER = "U:"


class SpoilerViewerApp:
    """Top-level Tk application window."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Elden Ring Randomizer Spoiler Viewer")
        self.root.geometry("1180x740")
        self.root.minsize(940, 580)

        self.parser = SpoilerParser()
        self.log: SpoilerLog | None = None
        self.current_file: str | None = None

        # Pre-computed lower-cased haystacks for substring search, indexed
        # parallel to `log.get(key)` so search doesn't re-derive them per
        # keystroke.
        self._search_cache: dict[str, list[str]] = {}
        self._render_after_id: str | None = None

        # Cross-search shopping cart. Selection persists across filter
        # switches and across searches.
        self._selection: set[Fingerprint] = set()

        # Active filter — either a BuiltinFilter or a user-filter name.
        self._active_builtin: BuiltinFilter | None = None
        self._active_user_name: str | None = None
        # Resolved categories the active filter currently shows.
        self._active_keys: tuple[str, ...] = ()
        # When showing a user filter, restrict rendering to its fingerprints.
        self._active_user_fps: set[Fingerprint] | None = None

        # User filters live in the same on-disk slot as before.
        self._user_filters: dict[str, list[Fingerprint]] = load_user_presets()

        # Per-render bookkeeping for click handling on the results widget.
        self._render_tag_to_fp: dict[str, Fingerprint] = {}

        # Theme — palette + dynamic widget tracking lists so we can
        # repaint everything on a single toggle.
        self.theme: Theme = load_preferred_theme()
        self._frames: list[tuple[tk.Misc, str]] = []
        self._labels: list[tuple[tk.Label, str]] = []
        self._buttons: list[tk.Button] = []
        self._entries: list[tk.Entry] = []

        self._build_layout()
        self._configure_tags()
        self._apply_theme()
        self._bind_shortcuts()

        # Pre-load the file passed on the command line, if any. Useful when
        # the binary is associated with .txt logs in the OS file manager.
        cli_file = self._cli_path()
        if cli_file and os.path.isfile(cli_file):
            self.root.after_idle(lambda: self._load_log(cli_file))
        else:
            self._update_status("Откройте лог рандомайзера через 📂 «Открыть лог».")

        # Default selection in the filter list.
        self._select_filter_in_list(_PREFIX_BUILTIN + DEFAULT_FILTER)

    # ------------------------------------------------------------------ layout

    def _build_layout(self) -> None:
        self._build_header()
        body = self._frame(self.root, alt=False)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))

        self._build_filters_panel(body)
        self._build_results_panel(body)

        self._build_selection_bar()
        self._build_status_bar()

    def _build_header(self) -> None:
        bar = self._frame(self.root, alt=True)
        bar.pack(fill=tk.X, padx=8, pady=(8, 4))

        open_btn = self._button(bar, text="📂  Открыть лог…", command=self._open_dialog)
        open_btn.pack(side=tk.LEFT, padx=(6, 8), pady=6)

        self.file_label_var = tk.StringVar(value="файл не открыт")
        self._label(bar, textvariable=self.file_label_var, muted=True).pack(
            side=tk.LEFT, padx=4
        )

        self.theme_btn = self._button(
            bar, text=self._theme_glyph(), command=self._toggle_theme
        )
        self.theme_btn.pack(side=tk.RIGHT, padx=6, pady=6)

    def _build_filters_panel(self, parent: tk.Misc) -> None:
        panel = self._frame(parent, alt=True, width=270)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        panel.pack_propagate(False)

        self._label(panel, text="ФИЛЬТРЫ", font=("Arial", 10, "bold")).pack(
            anchor=tk.W, padx=14, pady=(12, 2)
        )
        self._label(
            panel,
            text="Один клик — применить",
            font=("Arial", 8),
            muted=True,
        ).pack(anchor=tk.W, padx=14, pady=(0, 6))

        list_frame = self._frame(panel, alt=True)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.filter_list = tk.Listbox(
            list_frame,
            activestyle="none",
            borderwidth=0,
            highlightthickness=0,
            relief=tk.FLAT,
            selectmode=tk.BROWSE,
            exportselection=False,
            font=("Arial", 10),
        )
        self.filter_list.pack(fill=tk.BOTH, expand=True)
        self.filter_list.bind("<<ListboxSelect>>", self._on_filter_pick)

        # Index of listbox-row → identifier (e.g. "B:Великие Руны…", "U:Speedrun")
        # or None for headings / blanks.
        self._filter_rows: list[str | None] = []

        self._populate_filter_list()

        # Right-click context menu for user filters → delete.
        self.filter_list.bind("<Button-3>", self._on_filter_right_click)

        btn_row = self._frame(panel, alt=True)
        btn_row.pack(fill=tk.X, padx=8, pady=(2, 10))
        self.delete_user_btn = self._button(
            btn_row,
            text="Удалить выбранный",
            command=self._delete_active_user_filter,
            state=tk.DISABLED,
        )
        self.delete_user_btn.pack(fill=tk.X)

    def _build_results_panel(self, parent: tk.Misc) -> None:
        panel = self._frame(parent, alt=False)
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        toolbar = self._frame(panel, alt=True)
        toolbar.pack(fill=tk.X, pady=(0, 6))

        self._label(toolbar, text="Поиск:").pack(side=tk.LEFT, padx=(8, 6), pady=8)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._schedule_render())
        self.search_entry = tk.Entry(
            toolbar,
            textvariable=self.search_var,
            relief=tk.FLAT,
            highlightthickness=1,
            font=("Arial", 10),
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=6)
        self._entries.append(self.search_entry)

        self._button(
            toolbar, text="Очистить", command=lambda: self.search_var.set("")
        ).pack(side=tk.LEFT, padx=4, pady=6)
        self._button(
            toolbar, text="⎘ Скопировать", command=self._copy_results
        ).pack(side=tk.LEFT, padx=4, pady=6)
        self._button(
            toolbar, text="💾 Сохранить…", command=self._save_results
        ).pack(side=tk.LEFT, padx=(4, 8), pady=6)

        # Results widget.
        body = self._frame(panel, alt=False)
        body.pack(fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(body, orient=tk.VERTICAL)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar = scroll

        self.results = tk.Text(
            body,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=14,
            pady=10,
            font=("Arial", 10),
            yscrollcommand=scroll.set,
            cursor="xterm",
        )
        self.results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.results.yview)

        # Tag-level <Button-1> bindings on a state="disabled" Text widget
        # are unreliable on some Tk builds, so we listen on the widget
        # itself and look up the click position's tags.
        self.results.bind("<Button-1>", self._on_results_click)
        self.results.bind("<Motion>", self._on_results_motion)

    def _build_selection_bar(self) -> None:
        bar = self._frame(self.root, alt=True)
        bar.pack(fill=tk.X, padx=8, pady=(0, 4))

        self.selection_var = tk.StringVar(value="В сборке: 0")
        self._label(
            bar, textvariable=self.selection_var, font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=14, pady=8)

        self.selection_hint_var = tk.StringVar(
            value="клик по ☐ слева от строки добавит её в сборку"
        )
        self._label(
            bar, textvariable=self.selection_hint_var, muted=True, font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=8, pady=8)

        self.save_filter_btn = self._button(
            bar,
            text="Сохранить как фильтр…",
            command=self._save_filter_dialog,
            state=tk.DISABLED,
        )
        self.save_filter_btn.pack(side=tk.RIGHT, padx=(4, 8), pady=6)

        self.clear_selection_btn = self._button(
            bar,
            text="Очистить сборку",
            command=self._clear_selection,
            state=tk.DISABLED,
        )
        self.clear_selection_btn.pack(side=tk.RIGHT, padx=4, pady=6)

    def _build_status_bar(self) -> None:
        bar = self._frame(self.root, alt=True)
        bar.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.status_var = tk.StringVar(value="")
        self._label(bar, textvariable=self.status_var, muted=True).pack(
            side=tk.LEFT, padx=14, pady=6
        )

        self.total_var = tk.StringVar(value="")
        self._label(bar, textvariable=self.total_var, muted=True).pack(
            side=tk.RIGHT, padx=14, pady=6
        )

    # ------------------------------------------------------------------ helpers

    def _frame(self, parent: tk.Misc, *, alt: bool, **kwargs) -> tk.Frame:
        f = tk.Frame(parent, **kwargs)
        self._frames.append((f, "panel_alt" if alt else "panel"))
        return f

    def _label(self, parent: tk.Misc, *, muted: bool = False, **kwargs) -> tk.Label:
        kwargs.setdefault("anchor", tk.W)
        lbl = tk.Label(parent, **kwargs)
        self._labels.append((lbl, "muted" if muted else "text"))
        return lbl

    def _button(self, parent: tk.Misc, **kwargs) -> tk.Button:
        kwargs.setdefault("relief", tk.FLAT)
        kwargs.setdefault("cursor", "hand2")
        kwargs.setdefault("borderwidth", 0)
        kwargs.setdefault("padx", 12)
        kwargs.setdefault("pady", 6)
        btn = tk.Button(parent, **kwargs)
        self._buttons.append(btn)
        return btn

    def _theme_glyph(self) -> str:
        return "🌙" if self.theme.name == "light" else "☀"

    @staticmethod
    def _cli_path() -> str | None:
        import sys

        for arg in sys.argv[1:]:
            if not arg.startswith("-"):
                return arg
        return None

    # ------------------------------------------------------------------ filter list

    def _populate_filter_list(self) -> None:
        """Re-render the left-side filter Listbox.

        Built-in filters live in a fixed top group; user filters in a second
        group below. Headings + blank rows are inserted as non-selectable
        text rows whose listbox-row identifier is ``None`` so we can ignore
        them in :meth:`_on_filter_pick`.
        """

        listbox = self.filter_list
        listbox.delete(0, tk.END)
        self._filter_rows = []

        def add(label: str, ident: str | None) -> None:
            listbox.insert(tk.END, label)
            self._filter_rows.append(ident)
            if ident is None:
                idx = listbox.size() - 1
                listbox.itemconfig(idx, foreground=self.theme.muted)

        add("  Встроенные", None)
        for f in BUILTIN_FILTERS:
            add(f"  {_BUILTIN_GLYPH}  {f.name}", _PREFIX_BUILTIN + f.name)

        add("", None)
        add("  Свои фильтры", None)
        if self._user_filters:
            for name in self._user_filters:
                add(f"  {_USER_GLYPH}  {name}", _PREFIX_USER + name)
        else:
            add("    (пусто — отметь предметы и сохрани)", None)

    def _select_filter_in_list(self, ident: str) -> None:
        """Highlight a specific row by identifier and trigger its handler."""

        for i, row in enumerate(self._filter_rows):
            if row == ident:
                self.filter_list.selection_clear(0, tk.END)
                self.filter_list.selection_set(i)
                self.filter_list.activate(i)
                self.filter_list.see(i)
                self._on_filter_pick(None)
                return

    def _on_filter_pick(self, _event: object) -> None:
        sel = self.filter_list.curselection()
        if not sel:
            return
        ident = self._filter_rows[sel[0]]
        if ident is None:
            # Heading or blank row clicked — bounce selection back to the
            # previously active filter (or the default).
            target = (
                _PREFIX_USER + self._active_user_name
                if self._active_user_name
                else _PREFIX_BUILTIN
                + (self._active_builtin.name if self._active_builtin else DEFAULT_FILTER)
            )
            self._select_filter_in_list(target)
            return

        if ident.startswith(_PREFIX_BUILTIN):
            name = ident[len(_PREFIX_BUILTIN):]
            self._activate_builtin(name)
        elif ident.startswith(_PREFIX_USER):
            name = ident[len(_PREFIX_USER):]
            self._activate_user(name)

    def _activate_builtin(self, name: str) -> None:
        for f in BUILTIN_FILTERS:
            if f.name == name:
                self._active_builtin = f
                self._active_user_name = None
                self._active_keys = f.keys
                self._active_user_fps = None
                self.delete_user_btn.config(state=tk.DISABLED)
                self._update_status(f"Фильтр: «{name}». {f.description}")
                self._render()
                return

    def _activate_user(self, name: str) -> None:
        fps = self._user_filters.get(name)
        if fps is None:
            return
        self._active_builtin = None
        self._active_user_name = name
        # The user filter narrows BOTH the categories shown AND the items
        # within them (only fingerprints in the saved list pass through).
        keys: list[str] = []
        for cat, _ in fps:
            if cat not in keys:
                keys.append(cat)
        self._active_keys = tuple(keys)
        self._active_user_fps = set(fps)
        self.delete_user_btn.config(state=tk.NORMAL)
        self._update_status(
            f"Свой фильтр: «{name}» — показано {len(fps)} отмеченных предметов "
            "из всех логов с такими же опциями."
        )
        self._render()

    def _on_filter_right_click(self, event: tk.Event) -> None:
        idx = self.filter_list.nearest(event.y)
        if idx < 0 or idx >= len(self._filter_rows):
            return
        ident = self._filter_rows[idx]
        if ident is None or not ident.startswith(_PREFIX_USER):
            return
        name = ident[len(_PREFIX_USER):]
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(
            label=f"Загрузить «{name}» в сборку",
            command=lambda n=name: self._load_user_filter_into_cart(n),
        )
        menu.add_command(
            label=f"Удалить «{name}»",
            command=lambda n=name: self._delete_user_filter(n),
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _delete_active_user_filter(self) -> None:
        if self._active_user_name is None:
            return
        self._delete_user_filter(self._active_user_name)

    def _delete_user_filter(self, name: str) -> None:
        if not messagebox.askyesno(
            "Удалить фильтр",
            f"Удалить «{name}» безвозвратно?",
            parent=self.root,
        ):
            return
        self._user_filters = delete_user_preset(name)
        if self._active_user_name == name:
            self._active_user_name = None
            self._active_user_fps = None
            self._select_filter_in_list(_PREFIX_BUILTIN + DEFAULT_FILTER)
        self._populate_filter_list()
        self._update_status(f"Фильтр «{name}» удалён.")

    def _load_user_filter_into_cart(self, name: str) -> None:
        fps = self._user_filters.get(name)
        if fps is None:
            return
        self._selection = set(fps)
        self._update_selection_bar()
        self._render()
        self._update_status(
            f"В сборку загружены предметы из «{name}» ({len(fps)} шт.)."
        )

    # ------------------------------------------------------------------ rendering

    def _schedule_render(self) -> None:
        """Debounce search-input rerenders."""

        if self._render_after_id:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._render_after_id)
        self._render_after_id = self.root.after(_SEARCH_DEBOUNCE_MS, self._render)

    def _render(self) -> None:
        self._render_after_id = None
        if self.log is None:
            self._set_results_text(
                "Откройте лог рандомайзера через 📂 «Открыть лог»."
            )
            self.total_var.set("")
            return

        query = self.search_var.get().strip().lower()
        keys = self._active_keys
        user_fps = self._active_user_fps

        text_chunks: list[tuple[str, str]] = []
        self._render_tag_to_fp = {}

        total_matches = 0
        rendered = 0
        truncated = False

        # Built-in filters can narrow a category to specific entries
        # (e.g. only access-key key items, only achievement-boss slots).
        # User filters never have these; their narrowing is done via
        # `user_fps`.
        builtin = self._active_builtin

        for key in keys:
            entries = self.log.get(key)
            if not entries:
                continue
            haystacks = self._search_cache.get(key) or [
                entry_searchable(e) for e in entries
            ]
            self._search_cache[key] = haystacks

            item_allow = builtin.item_filter_for(key) if builtin else None
            original_allow = (
                builtin.original_filter_for(key) if builtin else None
            )

            filtered: list[tuple[object, str]] = []
            for entry, hay in zip(entries, haystacks, strict=False):
                if query and query not in hay:
                    continue
                if item_allow is not None and entry_name(entry) not in item_allow:
                    continue
                if original_allow is not None:
                    original = getattr(entry, "original", None)
                    if original not in original_allow:
                        continue
                fp = entry_fingerprint(key, entry)
                if user_fps is not None and fp not in user_fps:
                    continue
                filtered.append((entry, fp))

            if builtin and builtin.original_order:
                order_map = {name: i for i, name in enumerate(builtin.original_order)}
                n = len(builtin.original_order)
                filtered.sort(
                    key=lambda pair: order_map.get(getattr(pair[0], "original", ""), n)
                )

            section_chunks: list[tuple[str, str]] = []
            section_count = 0
            for entry, fp in filtered:
                total_matches += 1
                if rendered >= _RENDER_CAP:
                    truncated = True
                    continue
                section_chunks.extend(self._format_row(entry, fp))
                section_count += 1
                rendered += 1

            if section_count == 0:
                continue
            label = (
                (builtin.section_title_for(key) if builtin else None)
                or CATEGORY_LABELS.get(key, key)
            )
            text_chunks.append((_TAG_HEADER, f"  {label} ({section_count})  \n"))
            text_chunks.extend(section_chunks)
            text_chunks.append((TAG_PLAIN, "\n"))

        self._render_tag_to_fp_temp: dict[str, Fingerprint] = {}
        if not text_chunks:
            if query:
                self._set_results_text(
                    f"Под запрос «{query}» в этом фильтре ничего не подходит."
                )
            elif user_fps is not None and not user_fps:
                self._set_results_text(
                    "Фильтр пустой. Сохрани сборку в фильтр или выбери другой."
                )
            elif user_fps is not None:
                self._set_results_text(
                    "В этом логе нет предметов из сохранённого фильтра. "
                    "Возможно, у логов разные Options-настройки."
                )
            else:
                self._set_results_text("Пусто.")
        else:
            if truncated:
                hidden = total_matches - _RENDER_CAP
                text_chunks.append(
                    (
                        _TAG_CAP_NOTE,
                        f"\n  и ещё {hidden} записей скрыто — уточни "
                        "поиск, чтобы увидеть всё.\n",
                    )
                )
            self._set_results_chunks(text_chunks)

        self.total_var.set(f"Всего: {total_matches}")

    def _format_row(
        self, entry: object, fp: Fingerprint
    ) -> list[tuple[str, str]]:
        """One log entry → tagged chunks. Wraps the formatter output with a
        leading clickable-checkbox glyph so the user can build a custom
        filter from the results pane.
        """

        box_glyph = _BOX_ON if fp in self._selection else _BOX_OFF
        state_tag = _TAG_BOX_ON if fp in self._selection else _TAG_BOX_OFF
        # Per-row tag with a distinct prefix from the visual state tags so
        # `_box_tag_at_index` can pick it out unambiguously.
        per_row_tag = f"boxid_{len(self._render_tag_to_fp)}"
        self._render_tag_to_fp[per_row_tag] = fp

        out: list[tuple[str, str]] = []
        # Box glyph carries multiple tags — use a tuple-as-tag chunk:
        # the rendering pass interprets a tuple value as "apply all of
        # these tags to this text".
        out.append(((_TAG_BOX, state_tag, per_row_tag), box_glyph + "  "))
        out.extend(format_entry(entry))
        return out

    def _set_results_text(self, msg: str) -> None:
        self.results.config(state=tk.NORMAL)
        self.results.delete("1.0", tk.END)
        self.results.insert("1.0", msg, (_TAG_HINT,))
        self.results.config(state=tk.DISABLED)

    def _set_results_chunks(self, chunks: list[tuple[str, str]]) -> None:
        self.results.config(state=tk.NORMAL)
        self.results.delete("1.0", tk.END)
        for tag, text in chunks:
            if isinstance(tag, tuple):
                self.results.insert(tk.END, text, tag)
            else:
                self.results.insert(tk.END, text, (tag,))
        self.results.config(state=tk.DISABLED)

    # ------------------------------------------------------------------ click handling

    def _box_tag_at_index(self, idx: str) -> str | None:
        for tag in self.results.tag_names(idx):
            if tag.startswith("boxid_"):
                return tag
        return None

    def _on_results_click(self, event: tk.Event) -> str | None:
        idx = self.results.index(f"@{event.x},{event.y}")
        tag = self._box_tag_at_index(idx)
        if tag is None:
            # Tiny grace zone — clicks at the leading edge of the box can
            # land in the preceding line wrap area.
            tag = self._box_tag_at_index(self.results.index(f"{idx} - 1c"))
        if tag is None:
            return None
        fp = self._render_tag_to_fp.get(tag)
        if fp is None:
            return None
        self._toggle_entry(fp)
        return "break"

    def _on_results_motion(self, event: tk.Event) -> None:
        idx = self.results.index(f"@{event.x},{event.y}")
        cursor = "hand2" if self._box_tag_at_index(idx) is not None else "xterm"
        self.results.configure(cursor=cursor)

    def _toggle_entry(self, fp: Fingerprint) -> None:
        if fp in self._selection:
            self._selection.remove(fp)
        else:
            self._selection.add(fp)
        self._update_selection_bar()
        self._render()

    def _clear_selection(self) -> None:
        if not self._selection:
            return
        self._selection.clear()
        self._update_selection_bar()
        self._render()
        self._update_status("Сборка очищена.")

    def _update_selection_bar(self) -> None:
        n = len(self._selection)
        self.selection_var.set(f"В сборке: {n}")
        if n == 0:
            self.selection_hint_var.set(
                "клик по ☐ слева от строки добавит её в сборку"
            )
        else:
            self.selection_hint_var.set(
                "сохрани сборку в фильтр, чтобы переиспользовать на других логах"
            )
        state = tk.NORMAL if n > 0 else tk.DISABLED
        self.save_filter_btn.config(state=state)
        self.clear_selection_btn.config(state=state)

    # ------------------------------------------------------------------ save / delete user filter

    def _save_filter_dialog(self) -> None:
        if not self._selection:
            return
        suggested = self._active_user_name or ""
        name = simpledialog.askstring(
            "Сохранить фильтр",
            "Имя фильтра (если совпадёт с существующим — перезапишется):",
            initialvalue=suggested,
            parent=self.root,
        )
        if not name:
            return
        try:
            self._user_filters = save_user_preset(name.strip(), list(self._selection))
        except ValueError as exc:
            messagebox.showerror("Не получилось", str(exc), parent=self.root)
            return
        self._populate_filter_list()
        self._select_filter_in_list(_PREFIX_USER + name.strip())
        self._update_status(
            f"Фильтр «{name.strip()}» сохранён ({len(self._selection)} предметов)."
        )

    # ------------------------------------------------------------------ file I/O

    def _open_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Открыть лог рандомайзера",
            filetypes=[("Spoiler logs", "*.txt"), ("All files", "*.*")],
            parent=self.root,
        )
        if path:
            self._load_log(path)

    def _load_log(self, path: str) -> None:
        try:
            self.log = self.parser.parse_file(path)
        except OSError as exc:
            messagebox.showerror(
                "Не удалось открыть файл", str(exc), parent=self.root
            )
            return
        self.current_file = path
        self.file_label_var.set(os.path.basename(path))
        self._search_cache.clear()
        self._update_status(f"Загружен: {path}")
        self._render()

    def _copy_results(self) -> None:
        text = self.results.get("1.0", tk.END).rstrip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._update_status("Содержимое скопировано в буфер обмена.")

    def _save_results(self) -> None:
        text = self.results.get("1.0", tk.END).rstrip()
        if not text:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            parent=self.root,
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as exc:
            messagebox.showerror("Не получилось сохранить", str(exc), parent=self.root)
            return
        self._update_status(f"Сохранено в {path}")

    # ------------------------------------------------------------------ status / theme

    def _update_status(self, msg: str) -> None:
        self.status_var.set(msg)

    def _toggle_theme(self) -> None:
        self.theme = toggle(self.theme)
        save_preferred_theme(self.theme)
        self.theme_btn.config(text=self._theme_glyph())
        self._apply_theme()
        self._render()

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-o>", lambda _e: self._open_dialog())
        self.root.bind("<Control-O>", lambda _e: self._open_dialog())
        self.root.bind("<Control-f>", lambda _e: self._focus_search())
        self.root.bind("<Control-F>", lambda _e: self._focus_search())
        self.root.bind("<Control-s>", lambda _e: self._save_results())
        self.root.bind("<Control-S>", lambda _e: self._save_results())
        self.root.bind("<Escape>", lambda _e: self.search_var.set(""))

    def _focus_search(self) -> str:
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, tk.END)
        return "break"

    # ------------------------------------------------------------------ tags + theme

    def _configure_tags(self) -> None:
        r = self.results
        # Configure ordering matters: later-defined tags win on overlapping ranges.
        r.tag_configure(TAG_PLAIN)
        r.tag_configure(TAG_INDENT)
        r.tag_configure(TAG_NAME, font=("Arial", 10, "bold"), spacing1=4)
        r.tag_configure(TAG_LOCATION, font=("Arial", 9, "italic"))
        r.tag_configure(TAG_DETAIL, font=("Arial", 9))
        r.tag_configure(TAG_ARROW, font=("Arial", 10, "bold"))
        r.tag_configure(_TAG_BOX, font=("Arial", 12))
        r.tag_configure(_TAG_BOX_OFF)
        r.tag_configure(_TAG_BOX_ON)
        r.tag_configure(
            _TAG_HEADER,
            font=("Arial", 10, "bold"),
            spacing1=14,
            spacing3=6,
            justify=tk.LEFT,
        )
        r.tag_configure(_TAG_CAP_NOTE, font=("Arial", 9, "italic"))
        r.tag_configure(_TAG_HINT, font=("Arial", 10, "italic"))

    def _apply_theme(self) -> None:
        t = self.theme
        self.root.configure(bg=t.bg)
        for frame, kind in self._frames:
            frame.configure(bg=t.panel_alt if kind == "panel_alt" else t.panel)
        for label, kind in self._labels:
            bg = (
                label.master.cget("bg")
                if isinstance(label.master, (tk.Frame, tk.Tk))
                else t.panel
            )
            label.configure(
                bg=bg, fg=t.muted if kind == "muted" else t.text
            )
        for btn in self._buttons:
            btn.configure(
                bg=t.button_bg,
                fg=t.button_fg,
                activebackground=t.button_active_bg,
                activeforeground=t.button_fg,
                disabledforeground=t.muted,
            )
        for entry in self._entries:
            entry.configure(
                bg=t.entry_bg,
                fg=t.entry_fg,
                insertbackground=t.text,
                highlightbackground=t.border,
                highlightcolor=t.accent,
            )

        # Filter list.
        self.filter_list.configure(
            bg=t.panel_alt,
            fg=t.text,
            selectbackground=t.accent,
            selectforeground=t.accent_fg,
            highlightthickness=0,
            borderwidth=0,
        )
        # Re-paint heading rows in muted colour after theme swap.
        for i, ident in enumerate(self._filter_rows):
            if ident is None:
                self.filter_list.itemconfig(i, foreground=t.muted)
            else:
                self.filter_list.itemconfig(i, foreground=t.text)

        # Scrollbar.
        self.scrollbar.configure(
            troughcolor=t.scrollbar_trough,
            bg=t.scrollbar_bg,
            activebackground=t.scrollbar_bg,
            highlightthickness=0,
            borderwidth=0,
        )

        # Results widget.
        self.results.configure(
            bg=t.results_bg,
            fg=t.text,
            selectbackground=t.accent,
            selectforeground=t.accent_fg,
            insertbackground=t.text,
        )
        self.results.tag_configure(TAG_NAME, foreground=t.name_fg)
        self.results.tag_configure(TAG_LOCATION, foreground=t.muted)
        self.results.tag_configure(TAG_DETAIL, foreground=t.value_fg)
        self.results.tag_configure(TAG_ARROW, foreground=t.accent)
        self.results.tag_configure(
            _TAG_HEADER,
            background=t.header_bg,
            foreground=t.header_fg,
            lmargin1=0,
            lmargin2=0,
        )
        self.results.tag_configure(_TAG_CAP_NOTE, foreground=t.cap_fg)
        self.results.tag_configure(_TAG_HINT, foreground=t.muted)
        self.results.tag_configure(_TAG_BOX_OFF, foreground=t.muted)
        self.results.tag_configure(_TAG_BOX_ON, foreground=t.accent)


def run() -> None:
    """Launch the Tk app. Entry-point used by `python -m er_randomizer`."""

    root = tk.Tk()
    SpoilerViewerApp(root)
    root.mainloop()


# Legacy alias, in case anyone scripted `from er_randomizer.gui import main`.
main = run


if __name__ == "__main__":
    run()
