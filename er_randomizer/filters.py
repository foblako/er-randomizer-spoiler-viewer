"""Filters: the unified way to scope what's shown in the GUI.

Earlier versions of this app exposed two separate concepts side-by-side:
*categories* (one checkbox per parser key, mix-and-match) and *presets*
(named bundles of categories). On top of that user-built selections were
stored as a third, somewhat overlapping concept (a list of fingerprints
that turn into "show only these specific items").

The two-knob model was confusing — applying a custom preset would silently
turn on a hidden "only-selection" filter and the category checkboxes
became useless without explanation. The fix is to merge everything into a
single concept:

* A **filter** is anything you can click in the left panel and see the
  matching log entries on the right.
* The app ships with a small, opinionated set of *built-in* filters
  covering the common cases ("just the bosses", "just the items",
  "everything"). Each is just a list of category keys plus, optionally,
  a hand-curated whitelist of entry names within those categories.
* A **user filter** is the same shape, but defined as a list of
  fingerprints `(category, name)` instead of category keys — that's how
  you carry a hand-picked selection from one seed to another.

Built-in filters live here. User filters live in :mod:`user_presets` and
keep the on-disk file name (`user_presets`) for backwards compatibility
with `~/.er_randomizer.json` files written by older versions.
"""

from __future__ import annotations

from dataclasses import dataclass

# Key items in vanilla Elden Ring needed to *reach* a Great Rune location.
# In the randomizer, the Great Runes themselves live wherever the seed
# decided to drop them, but you still have to physically get into the
# legacy dungeon / region the slot lives in — and that gate is the same
# vanilla key item. Listing those items alongside the runes in tab 1
# lets the user plan "to clear this rune slot, I first need to find
# this key in *this* seed".
GREAT_RUNE_ACCESS_KEYS: frozenset[str] = frozenset(
    {
        # Academy of Raya Lucaria (Rennala's slot)
        "Academy Glintstone Key",
        # Volcano Manor (Rykard's slot, plus Godskin Noble nearby)
        "Drawing-Room Key",
        # Mountaintops of the Giants (Fire Giant slot + Morgott via the long route)
        "Rold Medallion",
        # Consecrated Snowfield / Haligtree (Malenia's slot)
        "Haligtree Secret Medallion (Left)",
        "Haligtree Secret Medallion (Right)",
        # Mohgwyn Palace — two routes: Varré's shortcut medal OR the
        # underground door in Subterranean Shunning-Grounds (Mohg's slot).
        "Pureblood Knight's Medal",
        "Discarded Palace Key",
        # Lift of Dectus → Altus Plateau (alternate route to Morgott)
        "Dectus Medallion (Left)",
        "Dectus Medallion (Right)",
        # Carian Manor → Three Sisters → Ranni's questline (gates the Lake of
        # Rot / Nokstella / Astel path that in vanilla is the Age of the
        # Stars ending — listed in the same "key items" group of the log so
        # we surface it here for completeness).
        "Carian Inverted Statue",
    }
)


# Boss-defeat achievements in vanilla Elden Ring + Shadow of the Erdtree.
# Each phase of a multi-phase fight is listed separately because in the
# spoiler log they show up as distinct boss slots (Rennala 1/2, Fire
# Giant 1/2, Beast Clergyman/Maliketh, Godfrey/Hoarah Loux, Radagon/
# Elden Beast, Messmer human/snake form, Radahn Phase 1/Consort).
#
# Names match what the parser writes after stripping ``(#1234)`` ids:
# ``Leonine Misbegotten Boss`` (not ``Leonine Misbegotten``),
# ``Godskin Noble Boss`` (the Volcano Manor fight, not the apostles),
# and so on. ``Goldfrey`` is the typo'd Erdtree-Sanctuary illusion fight
# in the randomizer's enemy data — it's the slot that drops the
# "Godfrey the First Lord" achievement in vanilla.
# Canonical story-progression display order for the "Боссы с ачивкой" filter.
# Each phase of a multi-phase fight is listed separately because in the
# spoiler log they show up as distinct boss slots (Rennala 1/2, Fire
# Giant 1/2, Beast Clergyman/Maliketh, Godfrey/Hoarah Loux, Radagon/
# Elden Beast, Messmer human/snake form, Radahn Phase 1/Consort).
#
# Names match what the parser writes after stripping ``(#1234)`` ids:
# ``Leonine Misbegotten Boss`` (not ``Leonine Misbegotten``),
# ``Godskin Noble Boss`` (the Volcano Manor fight, not the apostles),
# and so on. ``Goldfrey`` is the typo'd Erdtree-Sanctuary illusion fight
# in the randomizer's enemy data — it's the slot that drops the
# "Godfrey the First Lord" achievement in vanilla.
ACHIEVEMENT_BOSS_ORDER: tuple[str, ...] = (
    # === Story-progression order (user-specified) ===
    "Margit, the Fell Omen",
    "Godrick the Grafted",
    "Magma Wyrm Makar",
    "Royal Knight Loretta",
    "Red Wolf of Radagon",
    "Rennala 1",
    "Rennala 2",
    "Starscourge Radahn",
    "Goldfrey, First Elden Lord",        # Erdtree-Sanctuary illusion (typo in randomizer data)
    "Morgott, the Omen King",
    "Fire Giant 1",
    "Fire Giant 2",
    "Godskin Duo",
    "Beast Clergyman",
    "Maliketh, the Black Blade",
    "Sir Gideon Ofnir, the All-Knowing",
    "Godfrey, First Elden Lord",
    "Hoarah Loux, Warrior",
    "Radagon of the Golden Order",
    "Elden Beast",
    "Leonine Misbegotten Boss",
    "Godskin Noble Boss",
    "God-Devouring Serpent",             # Phase 1 of Rykard — separate slot in randomizer data
    "Rykard, Lord of Blasphemy",
    "Elemer of the Briar",
    "Dragonlord Placidusax",
    "Commander Niall",
    "Regal Ancestor Spirit",
    "Mimic Tear",
    "Ancestor Spirit",
    "Valiant Gargoyles",
    "Astel, Naturalborn of the Void",
    # === Remaining base game ===
    "Mohg, the Omen",
    "Lichdragon Fortissax",
    "Dragonkin Soldier of Nokstella",
    "Loretta, Knight of the Haligtree",
    "Mohg, Lord of Blood",
    "Malenia, Blade of Miquella",
    # === Shadow of the Erdtree (боссы, дропающие воспоминания) ===
    "Divine Beast Dancing Lion",
    "Rellana, Twin Moon Knight",
    "Messmer the Impaler",
    # Phase 2 of Messmer — the snake-form slot in the randomizer's data.
    "Base Serpent Messmer",
    "Romina, Saint of the Bud",
    "Commander Gaius",
    "Putrescent Knight",
    "Scadutree Avatar",
    "Metyr, Mother of Fingers",
    "Midra, Lord of Frenzied Flame",
    "Bayle the Dread",
    # Final DLC boss — two slots: phase 1 ("Promised Consort Radahn")
    # and phase 2 ("Radahn, Consort of Miquella").
    "Promised Consort Radahn",
    "Radahn, Consort of Miquella",
)

# Derived frozenset for O(1) membership testing — edit ACHIEVEMENT_BOSS_ORDER above,
# not this variable directly.
ACHIEVEMENT_BOSSES: frozenset[str] = frozenset(ACHIEVEMENT_BOSS_ORDER)


@dataclass(frozen=True)
class BuiltinFilter:
    """A read-only filter that maps to a fixed list of parser category keys.

    Optional fields narrow the view further:

    ``item_filters``
        Per-key allow-list applied against the entry's "primary name"
        (``SpoilerEntry.item``, ``PlacementEntry.replacement``,
        ``ReplaceEntry.replacement``). Used by the
        "Великие Руны + ключи доступа" filter to keep only the
        legacy-dungeon keys out of the otherwise-noisy key-item hints.

    ``original_filters``
        Per-key allow-list applied against ``PlacementEntry.original``
        — the *vanilla* boss occupying the slot. Used by the
        "Боссы с ачивкой" filter so the seed-randomised
        ``replacement`` doesn't get matched accidentally.

    ``section_titles``
        Per-key display label override. The default label comes from
        :data:`er_randomizer.presets.CATEGORY_LABELS` and reads
        e.g. "Подсказки ключевых предметов"; when we re-use the same
        category as a narrow access-key list we want a shorter,
        purpose-specific header.
    """

    name: str
    keys: tuple[str, ...]
    description: str = ""
    item_filters: tuple[tuple[str, frozenset[str]], ...] = ()
    original_filters: tuple[tuple[str, frozenset[str]], ...] = ()
    section_titles: tuple[tuple[str, str], ...] = ()
    original_order: tuple[str, ...] = ()

    def item_filter_for(self, key: str) -> frozenset[str] | None:
        for k, names in self.item_filters:
            if k == key:
                return names
        return None

    def original_filter_for(self, key: str) -> frozenset[str] | None:
        for k, names in self.original_filters:
            if k == key:
                return names
        return None

    def section_title_for(self, key: str) -> str | None:
        for k, title in self.section_titles:
            if k == key:
                return title
        return None


# The default selection used when a log is opened. Picking a single
# obviously-relevant default avoids the "empty results" first impression.
DEFAULT_FILTER = "Великие Руны + ключи доступа"


# Hand-picked, intentionally small set. Anything not covered here can be
# built by the user via the "Сохранить как фильтр…" flow.
BUILTIN_FILTERS: tuple[BuiltinFilter, ...] = (
    BuiltinFilter(
        name=DEFAULT_FILTER,
        keys=("great_runes", "key_item_hints"),
        description=(
            "Великие Руны вместе с ключами, которыми в оригинале "
            "открывается доступ к их локациям: ключ Академии (Реннала), "
            "ключ от гостиной Волкан-Манора (Рикард), медальоны Дектуса/"
            "Ролда/Халигтри, медаль Чистокровного Рыцаря и т.д."
        ),
        item_filters=(("key_item_hints", GREAT_RUNE_ACCESS_KEYS),),
        section_titles=(("key_item_hints", "Ключи доступа к локациям рун"),),
    ),
    BuiltinFilter(
        name="Воспоминания",
        keys=("remembrances",),
        description=("Только Воспоминания боссов — что теперь сидит на каждом из них."),
    ),
    BuiltinFilter(
        name="Боссы с ачивкой",
        # Boss-vs-miniboss is decided per-seed by the randomizer's enemy
        # preset (e.g. "Elemer of the Briar" lands in `-- Miniboss
        # placements` in one seed and `-- Boss placements` in another),
        # so we scan both lists and let `original_filters` pick out the
        # 35 vanilla achievement slots regardless of which bucket they
        # fell into.
        keys=("boss_placements", "miniboss_placements"),
        description=(
            "Боссы, за которых в оригинальной Elden Ring падает ачивка "
            "(шардбэреры, финал-боссы, опциональные сюжетные). С учётом "
            "двух фаз — ~35 слотов. Имена в строке «заменяет …» — это "
            "и есть ванильный босс; рядом видно, кто теперь сидит "
            "на его месте в этом сиде."
        ),
        original_filters=(
            ("boss_placements", ACHIEVEMENT_BOSSES),
            ("miniboss_placements", ACHIEVEMENT_BOSSES),
        ),
        section_titles=(
            ("boss_placements", "Ачивочные слоты (Boss placements)"),
            ("miniboss_placements", "Ачивочные слоты (Miniboss placements)"),
        ),
        original_order=ACHIEVEMENT_BOSS_ORDER,
    ),
    BuiltinFilter(
        name="Все боссы",
        keys=("boss_placements", "miniboss_placements"),
        description=(
            "Полный список боссовых сражений: основные боссы (включая "
            "шардбэреров и финальных) плюс мини-боссы / эверголы / "
            "полевые боссы."
        ),
    ),
    BuiltinFilter(
        name="Все предметы",
        keys=("spoilers",),
        description=(
            "Полный спойлер-список всех предметов лога. Несколько тысяч "
            "записей — пользуйся поиском."
        ),
    ),
    BuiltinFilter(
        name="Вообще всё",
        keys=(
            "great_runes",
            "remembrances",
            "key_item_hints",
            "bell_bearing_hints",
            "core_mechanics_hints",
            "quest_item_hints",
            "boss_placements",
            "miniboss_placements",
            "basic_placements",
            "gesture_placements",
            "level_bgm_placements",
            "starting_gifts",
            "spoilers",
        ),
        description="Всё, что есть в логе. Поиск + фильтр сверху обязательны.",
    ),
)


def builtin_filter_by_name(name: str) -> BuiltinFilter | None:
    for f in BUILTIN_FILTERS:
        if f.name == name:
            return f
    return None
