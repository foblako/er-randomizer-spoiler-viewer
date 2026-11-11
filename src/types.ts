export interface SpoilerEntry {
  item: string;
  location: string;
  description: string;
  replaces?: string | null;
  cost?: number | null;
  raw: string;
}

export interface PlacementEntry {
  original: string;
  original_location: string;
  replacement: string;
  replacement_location: string;
  raw: string;
}

export interface ReplaceEntry {
  original: string;
  replacement: string;
}

export interface SpoilerLog {
  great_runes: SpoilerEntry[];
  remembrances: SpoilerEntry[];
  key_item_hints: SpoilerEntry[];
  bell_bearing_hints: SpoilerEntry[];
  core_mechanics_hints: SpoilerEntry[];
  quest_item_hints: SpoilerEntry[];
  boss_placements: PlacementEntry[];
  miniboss_placements: PlacementEntry[];
  basic_placements: PlacementEntry[];
  gesture_placements: ReplaceEntry[];
  level_bgm_placements: ReplaceEntry[];
  starting_gifts: ReplaceEntry[];
  spoilers: SpoilerEntry[];
  counts: Record<string, number>;
}

export type CategoryKey = keyof Omit<SpoilerLog, 'counts'>;

export interface BuiltinFilter {
  id: string;
  name: string;
  keys: CategoryKey[];
  description: string;
  itemFilters?: Record<string, string[]>;
  originalFilters?: Record<string, string[]>;
  sectionTitles?: Record<string, string>;
  originalOrder?: string[];
  mergedSectionTitle?: string;
}

export const CATEGORY_LABELS: Record<string, string> = {
  great_runes: "Великие Руны",
  remembrances: "Воспоминания боссов",
  key_item_hints: "Подсказки ключевых предметов",
  bell_bearing_hints: "Подсказки колокольчиков",
  core_mechanics_hints: "Подсказки основных механик",
  quest_item_hints: "Подсказки квестовых предметов",
  boss_placements: "Боссы (Арены)",
  miniboss_placements: "Мини-боссы (Полевые)",
  basic_placements: "Обычные и уникальные враги",
  gesture_placements: "Размещения жестов",
  level_bgm_placements: "Размещения фоновой музыки (BGM)",
  starting_gifts: "Стартовые подарки",
  spoilers: "Предметы мира (Спойлеры)",
};

export const GREAT_RUNE_ACCESS_KEYS = [
  "Academy Glintstone Key",
  "Drawing-Room Key",
  "Rold Medallion",
  "Haligtree Secret Medallion (Left)",
  "Haligtree Secret Medallion (Right)",
  "Pureblood Knight's Medal",
  "Discarded Palace Key",
  "Dectus Medallion (Left)",
  "Dectus Medallion (Right)",
  "Carian Inverted Statue",
];

export const ACHIEVEMENT_BOSS_ORDER = [
  "Margit, the Fell Omen",
  "Godrick the Grafted",
  "Magma Wyrm Makar",
  "Royal Knight Loretta",
  "Red Wolf of Radagon",
  "Rennala 1",
  "Rennala 2",
  "Starscourge Radahn",
  "Draconic Tree Sentinel Boss",
  "Goldfrey, First Elden Lord",
  "Morgott, the Omen King",
  "Elemer of the Briar",
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
  "God-Devouring Serpent",
  "Rykard, Lord of Blasphemy",
  "Dragonlord Placidusax",
  "Commander Niall",
  "Regal Ancestor Spirit",
  "Mimic Tear",
  "Ancestor Spirit",
  "Valiant Gargoyles",
  "Astel, Naturalborn of the Void",
  "Mohg, the Omen",
  "Lichdragon Fortissax",
  "Dragonkin Soldier of Nokstella",
  "Loretta, Knight of the Haligtree",
  "Mohg, Lord of Blood",
  "Malenia, Blade of Miquella",
  "Divine Beast Dancing Lion",
  "Rellana, Twin Moon Knight",
  "Messmer the Impaler",
  "Base Serpent Messmer",
  "Romina, Saint of the Bud",
  "Commander Gaius",
  "Putrescent Knight",
  "Scadutree Avatar",
  "Metyr, Mother of Fingers",
  "Midra, Lord of Frenzied Flame",
  "Bayle the Dread",
  "Promised Consort Radahn",
  "Radahn, Consort of Miquella",
];

export const BUILTIN_FILTERS: BuiltinFilter[] = [
  {
    id: "runes_and_keys",
    name: "Великие Руны + ключи доступа",
    keys: ["great_runes", "key_item_hints"],
    description: "Великие Руны вместе с ключами для доступа к их локациям (Академия, Волкан-Манор, Дектус, Ролд, Халигтри и др.)",
    itemFilters: {
      key_item_hints: GREAT_RUNE_ACCESS_KEYS,
    },
    sectionTitles: {
      key_item_hints: "Ключи доступа к локациям рун",
    },
  },
  {
    id: "remembrances",
    name: "Воспоминания боссов",
    keys: ["remembrances"],
    description: "Только Воспоминания боссов — что теперь даётся за каждого из них.",
  },
  {
    id: "achievement_bosses",
    name: "Боссы с ачивкой",
    keys: ["boss_placements", "miniboss_placements"],
    description: "Боссы ванильной Elden Ring + DLC, за победу над которыми даются достижения (в сюжетном порядке).",
    originalFilters: {
      boss_placements: ACHIEVEMENT_BOSS_ORDER,
      miniboss_placements: ACHIEVEMENT_BOSS_ORDER,
    },
    originalOrder: ACHIEVEMENT_BOSS_ORDER,
    mergedSectionTitle: "Боссы с достижениями (Сюжетный порядок)",
  },
  {
    id: "all_bosses",
    name: "Все боссы (Арены)",
    keys: ["boss_placements", "miniboss_placements"],
    description: "Все 218 боссов игры на своих аренах с туманными вратами.",
  },
  {
    id: "basic_enemies",
    name: "Обычные и уникальные мобы",
    keys: ["basic_placements"],
    description: "Все рядовые и уникальные мобы мира (Мини-Мидра, рыцари, инквизиторы, мобы подземелий).",
  },
  {
    id: "all_items",
    name: "Все предметы",
    keys: ["spoilers"],
    description: "Полный список всех сгенерированных предметов (~5 000+ записей).",
  },
  {
    id: "everything",
    name: "Вообще всё",
    keys: [
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
    ],
    description: "Абсолютно все данные из лога (включая 20 000+ обычных врагов).",
  },
];

export function isUniqueMob(name: string): boolean {
  const l = name.toLowerCase();
  const uniqueKeywords = [
    'mini midra',
    'inquisitor',
    'divine bird',
    'curseblade',
    'horned warrior',
    'death knight',
    'black knight',
    'fire knight',
    'crucible knight',
    'cleanrot knight',
    'bloodhound knight',
    'banished knight',
    'carian knight',
    'tree sentinel',
    'draconic tree sentinel',
    'night\'s cavalry',
    'deathbird',
    'death rite bird',
    'tibia mariner',
    'bell bearing hunter',
    'frenzied duelist',
    'grave warden',
    'runebear',
    'lion guardian',
    'abductor virgin',
    'ancient dragon',
    'baleful shadow',
    'battlemage',
    'sanguine noble',
    'red wolf',
    'crystalian',
    'golem',
    'grafted scion',
    'furnace golem',
    'lamenter',
    'omenkiller',
    'wormface',
    'ulcerated tree spirit',
    'erdtree avatar',
    'putrid tree spirit',
    'putrid avatar',
    'onyx lord',
    'alabaster lord',
    'beastman of farum',
    'demi-human queen',
    'pumpkin head',
    'fallingstar beast',
    'magma wyrm',
    'ancestor spirit',
    'dragonkin soldier',
    'astel',
    'bloodfiend chief',
  ];
  return uniqueKeywords.some((kw) => l.includes(kw));
}
