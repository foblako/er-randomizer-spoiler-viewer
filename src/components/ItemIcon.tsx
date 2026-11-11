import React from 'react';
import {
  Crown,
  Sparkles,
  Swords,
  Sword,
  Flame,
  Skull,
  Shield,
  Key,
  Bell,
  Gem,
  Droplet,
  Coins,
  Package,
  FlaskConical,
  BookOpen,
  Scroll,
  Ghost,
  Feather,
  Apple,
  Leaf,
  Shirt,
  Music,
  Hand,
  Crosshair,
  Wand,
  Sun,
  Axe,
  Hammer,
} from 'lucide-react';
import { isUniqueMob } from '../types';

interface ItemIconProps {
  kind: 'placement' | 'spoiler' | 'replace';
  category: string;
  name: string;
  originalName?: string;
  size?: 'sm' | 'md' | 'lg';
}

interface IconTheme {
  icon: React.ComponentType<{ className?: string }>;
  bgGradient: string;
  borderColor: string;
  iconColor: string;
  glowColor: string;
}

export function classifyItem(kind: string, category: string, name: string, originalName?: string): IconTheme {
  const lowerName = name.toLowerCase();
  const lowerOrig = (originalName || '').toLowerCase();
  const lowerCat = category.toLowerCase();

  // 1. Great Runes (Великие Руны)
  if (
    lowerCat === 'great_runes' ||
    lowerName.includes('great rune') ||
    lowerOrig.includes('great rune')
  ) {
    return {
      icon: Crown,
      bgGradient: 'from-amber-400/30 via-yellow-600/25 to-amber-950/50',
      borderColor: 'border-amber-400/80',
      iconColor: 'text-amber-300',
      glowColor: 'shadow-[0_0_14px_rgba(251,191,36,0.45)]',
    };
  }

  // 2. Remembrances (Воспоминания)
  if (lowerCat === 'remembrances' || lowerName.includes('remembrance')) {
    return {
      icon: Sparkles,
      bgGradient: 'from-yellow-400/30 via-amber-500/25 to-orange-950/50',
      borderColor: 'border-yellow-400/80',
      iconColor: 'text-yellow-200',
      glowColor: 'shadow-[0_0_14px_rgba(250,204,21,0.45)]',
    };
  }

  // 3. Bosses & Enemies (Боссы и противники)
  if (kind === 'placement' || lowerCat.includes('boss') || lowerCat === 'basic_placements') {
    // Basic placements: check if unique mob or regular fodder
    if (lowerCat === 'basic_placements') {
      if (isUniqueMob(lowerName) || isUniqueMob(lowerOrig)) {
        return {
          icon: Sparkles,
          bgGradient: 'from-purple-600/35 via-indigo-900/25 to-neutral-950',
          borderColor: 'border-purple-400/70',
          iconColor: 'text-purple-300',
          glowColor: 'shadow-[0_0_12px_rgba(168,85,247,0.35)]',
        };
      }
      return {
        icon: Skull,
        bgGradient: 'from-stone-700/25 via-neutral-800/25 to-neutral-950',
        borderColor: 'border-stone-600/40',
        iconColor: 'text-neutral-400',
        glowColor: 'shadow-[0_0_6px_rgba(168,162,158,0.15)]',
      };
    }

    // Legendary Bosses, Demigods & Shardbearers (only true arena bosses)
    const demigods = [
      'godrick', 'radahn', 'rennala', 'morgott', 'rykard', 'malenia',
      'mohg', 'godfrey', 'maliketh', 'fire giant', 'placidusax',
      'radagon', 'elden beast', 'messmer', 'bayle', 'rellana',
      'midra, lord', 'lord of frenzied flame',
      'gideon', 'astel', 'fortissax', 'hoarah loux', 'romina', 'metyr'
    ];
    if (
      !lowerName.includes('mini midra') &&
      demigods.some((d) => lowerName.includes(d) || lowerOrig.includes(d))
    ) {
      return {
        icon: Crown,
        bgGradient: 'from-red-600/35 via-rose-800/25 to-neutral-950',
        borderColor: 'border-red-500/70',
        iconColor: 'text-red-400',
        glowColor: 'shadow-[0_0_14px_rgba(239,68,68,0.4)]',
      };
    }

    // Dragons & Magma Wyrms
    if (lowerName.includes('dragon') || lowerName.includes('drake') || lowerName.includes('wyrm') || lowerOrig.includes('dragon')) {
      return {
        icon: Flame,
        bgGradient: 'from-orange-600/35 via-amber-700/25 to-neutral-950',
        borderColor: 'border-orange-500/70',
        iconColor: 'text-orange-400',
        glowColor: 'shadow-[0_0_12px_rgba(249,115,22,0.35)]',
      };
    }

    // Knights, Sentinels, Cavalry
    if (lowerName.includes('knight') || lowerName.includes('sentinel') || lowerName.includes('cavalry') || lowerName.includes('cleanrot')) {
      return {
        icon: Shield,
        bgGradient: 'from-blue-600/30 via-indigo-800/25 to-neutral-950',
        borderColor: 'border-blue-400/60',
        iconColor: 'text-blue-300',
        glowColor: 'shadow-[0_0_12px_rgba(96,165,250,0.3)]',
      };
    }

    // Beast / Monsters
    if (lowerName.includes('beast') || lowerName.includes('troll') || lowerName.includes('gargoyle') || lowerName.includes('avatar') || lowerName.includes('bear')) {
      return {
        icon: Swords,
        bgGradient: 'from-amber-600/30 via-stone-800/25 to-neutral-950',
        borderColor: 'border-amber-500/60',
        iconColor: 'text-amber-400',
        glowColor: 'shadow-[0_0_10px_rgba(245,158,11,0.3)]',
      };
    }

    // Miniboss placements default
    if (lowerCat === 'miniboss_placements') {
      return {
        icon: Swords,
        bgGradient: 'from-sky-600/30 via-cyan-900/25 to-neutral-950',
        borderColor: 'border-sky-400/60',
        iconColor: 'text-sky-300',
        glowColor: 'shadow-[0_0_10px_rgba(56,189,248,0.25)]',
      };
    }

    // Default combat encounter
    return {
      icon: Sword,
      bgGradient: 'from-zinc-600/30 via-neutral-800/25 to-neutral-950',
      borderColor: 'border-neutral-500/60',
      iconColor: 'text-neutral-300',
      glowColor: 'shadow-[0_0_8px_rgba(212,212,216,0.2)]',
    };
  }

  // 4. Runes, Golden Runes & Currency (Руны и валюта)
  if (lowerName.includes('rune [') || lowerName.includes("hero's rune") || lowerName.includes("lord's rune") || lowerName.includes('rune arc')) {
    return {
      icon: Coins,
      bgGradient: 'from-amber-400/30 via-yellow-600/20 to-neutral-950',
      borderColor: 'border-amber-400/60',
      iconColor: 'text-amber-300',
      glowColor: 'shadow-[0_0_10px_rgba(251,191,36,0.35)]',
    };
  }

  // 5. Upgrade Stones (Кузнечные камни и ландыши)
  if (lowerName.includes('smithing stone') || lowerName.includes('somber') || lowerName.includes('glovewort')) {
    const isSomber = lowerName.includes('somber') || lowerName.includes('ghost');
    return {
      icon: Gem,
      bgGradient: isSomber
        ? 'from-sky-500/30 via-indigo-700/20 to-neutral-950'
        : 'from-amber-500/30 via-stone-700/20 to-neutral-950',
      borderColor: isSomber ? 'border-sky-400/60' : 'border-amber-400/60',
      iconColor: isSomber ? 'text-sky-300' : 'text-amber-300',
      glowColor: 'shadow-[0_0_10px_rgba(56,189,248,0.3)]',
    };
  }

  // 6. Keys, Medallions & Progression (Ключи и медальоны)
  if (
    lowerCat === 'key_item_hints' ||
    lowerName.includes('key') ||
    lowerName.includes('medallion') ||
    lowerName.includes('statue') ||
    lowerName.includes('medal') ||
    lowerName.includes('dectus') ||
    lowerName.includes('rold') ||
    lowerName.includes('haligtree') ||
    lowerName.includes('whetblade')
  ) {
    return {
      icon: Key,
      bgGradient: 'from-emerald-500/30 via-teal-700/20 to-neutral-950',
      borderColor: 'border-emerald-400/70',
      iconColor: 'text-emerald-300',
      glowColor: 'shadow-[0_0_12px_rgba(52,211,153,0.35)]',
    };
  }

  // 7. Bell Bearings (Колокольные сферы)
  if (lowerCat === 'bell_bearing_hints' || lowerName.includes('bell bearing')) {
    return {
      icon: Bell,
      bgGradient: 'from-amber-600/30 via-yellow-800/20 to-neutral-950',
      borderColor: 'border-amber-500/70',
      iconColor: 'text-amber-300',
      glowColor: 'shadow-[0_0_12px_rgba(245,158,11,0.35)]',
    };
  }

  // 8. Tears, Flasks, Physick & Seeds (Слёзы, фляги, семена)
  if (lowerName.includes('tear') || lowerName.includes('flask') || lowerName.includes('seed') || lowerName.includes('physick')) {
    return {
      icon: Droplet,
      bgGradient: 'from-cyan-500/30 via-sky-700/20 to-neutral-950',
      borderColor: 'border-cyan-400/70',
      iconColor: 'text-cyan-300',
      glowColor: 'shadow-[0_0_12px_rgba(34,211,238,0.35)]',
    };
  }

  // 9. Talismans (Талисманы)
  if (
    lowerName.includes('talisman') ||
    lowerName.includes('charm') ||
    lowerName.includes('heirloom') ||
    lowerName.includes('scarseal') ||
    lowerName.includes('soreseal') ||
    lowerName.includes('cameo') ||
    lowerName.includes('insignia') ||
    lowerName.includes('amber')
  ) {
    return {
      icon: Gem,
      bgGradient: 'from-purple-600/30 via-violet-800/20 to-neutral-950',
      borderColor: 'border-purple-400/70',
      iconColor: 'text-purple-300',
      glowColor: 'shadow-[0_0_12px_rgba(192,132,252,0.35)]',
    };
  }

  // 10. Ashes of War (Пеплы войны)
  if (lowerName.includes('ash of war') || lowerName.includes('whetblade')) {
    return {
      icon: Swords,
      bgGradient: 'from-zinc-500/30 via-neutral-700/20 to-neutral-950',
      borderColor: 'border-amber-400/60',
      iconColor: 'text-amber-300',
      glowColor: 'shadow-[0_0_10px_rgba(251,191,36,0.3)]',
    };
  }

  // 11. Spirit Summons (Прах духов)
  if (lowerName.includes('ashes') || lowerName.includes('puppet') || lowerName.includes('spirit')) {
    return {
      icon: Ghost,
      bgGradient: 'from-teal-600/30 via-slate-800/20 to-neutral-950',
      borderColor: 'border-teal-400/60',
      iconColor: 'text-teal-300',
      glowColor: 'shadow-[0_0_12px_rgba(45,212,191,0.35)]',
    };
  }

  // 12. Magic, Sorceries & Incantations (Магия и молитвы)
  if (lowerName.includes('sorcery') || lowerName.includes('glintstone') || lowerName.includes('comet') || lowerName.includes('carian') || lowerName.includes('moon')) {
    return {
      icon: Wand,
      bgGradient: 'from-blue-600/30 via-indigo-800/20 to-neutral-950',
      borderColor: 'border-blue-400/70',
      iconColor: 'text-blue-300',
      glowColor: 'shadow-[0_0_12px_rgba(96,165,250,0.35)]',
    };
  }
  if (lowerName.includes('incantation') || lowerName.includes('flame') || lowerName.includes('lightning') || lowerName.includes('heal') || lowerName.includes('blessing')) {
    return {
      icon: Sun,
      bgGradient: 'from-amber-500/30 via-yellow-700/20 to-neutral-950',
      borderColor: 'border-amber-400/70',
      iconColor: 'text-yellow-300',
      glowColor: 'shadow-[0_0_12px_rgba(250,204,21,0.35)]',
    };
  }

  // 13. Weapons (Оружие)
  if (lowerName.includes('axe')) {
    return {
      icon: Axe,
      bgGradient: 'from-stone-600/30 via-zinc-800/20 to-neutral-950',
      borderColor: 'border-stone-400/60',
      iconColor: 'text-stone-200',
      glowColor: 'shadow-[0_0_8px_rgba(214,211,209,0.25)]',
    };
  }
  if (lowerName.includes('hammer') || lowerName.includes('club') || lowerName.includes('mace') || lowerName.includes('flail')) {
    return {
      icon: Hammer,
      bgGradient: 'from-stone-600/30 via-zinc-800/20 to-neutral-950',
      borderColor: 'border-stone-400/60',
      iconColor: 'text-stone-200',
      glowColor: 'shadow-[0_0_8px_rgba(214,211,209,0.25)]',
    };
  }
  const weapons = ['sword', 'blade', 'katana', 'greatsword', 'staff', 'seal', 'dagger', 'spear', 'halberd', 'whip', 'scythe', 'colossal', 'rapier', 'twinblade'];
  if (weapons.some((w) => lowerName.includes(w))) {
    return {
      icon: Sword,
      bgGradient: 'from-zinc-500/30 via-neutral-700/20 to-neutral-950',
      borderColor: 'border-zinc-400/60',
      iconColor: 'text-zinc-200',
      glowColor: 'shadow-[0_0_10px_rgba(228,228,231,0.3)]',
    };
  }

  // 14. Shields (Щиты)
  if (lowerName.includes('shield') || lowerName.includes('buckler')) {
    return {
      icon: Shield,
      bgGradient: 'from-slate-600/30 via-neutral-800/20 to-neutral-950',
      borderColor: 'border-slate-400/60',
      iconColor: 'text-slate-200',
      glowColor: 'shadow-[0_0_8px_rgba(148,163,184,0.25)]',
    };
  }

  // 15. Bows, Crossbows, Arrows & Bolts (Луки, стрелы, болты)
  if (lowerName.includes('bow') || lowerName.includes('arrow') || lowerName.includes('bolt') || lowerName.includes('dart') || lowerName.includes('ballista')) {
    return {
      icon: Crosshair,
      bgGradient: 'from-amber-700/25 via-stone-800/20 to-neutral-950',
      borderColor: 'border-amber-600/50',
      iconColor: 'text-amber-300',
      glowColor: 'shadow-[0_0_8px_rgba(217,119,6,0.25)]',
    };
  }

  // 16. Armor & Apparel (Броня и одежда)
  const armorWords = ['helm', 'armor', 'gauntlets', 'greaves', 'set', 'robe', 'hood', 'hat', 'cap', 'mask', 'crown', 'attire', 'surcoat', 'mail', 'boots', 'gloves', 'trousers', 'vest'];
  if (armorWords.some((w) => lowerName.includes(w))) {
    return {
      icon: Shirt,
      bgGradient: 'from-stone-600/25 via-neutral-800/20 to-neutral-950',
      borderColor: 'border-neutral-500/50',
      iconColor: 'text-neutral-300',
      glowColor: 'shadow-[0_0_8px_rgba(163,163,163,0.2)]',
    };
  }

  // 17. Pots & Perfumes (Горшки и парфюмерия)
  if (lowerName.includes('pot') || lowerName.includes('perfume') || lowerName.includes('aromatic') || lowerName.includes('bottle')) {
    return {
      icon: lowerName.includes('perfume') || lowerName.includes('bottle') ? FlaskConical : Package,
      bgGradient: 'from-amber-600/25 via-stone-800/20 to-neutral-950',
      borderColor: 'border-amber-500/50',
      iconColor: 'text-amber-300',
      glowColor: 'shadow-[0_0_8px_rgba(245,158,11,0.2)]',
    };
  }

  // 18. Cookbooks, Scrolls, Maps & Paintings (Книги, свитки, карты, картины)
  if (lowerName.includes('cookbook') || lowerName.includes('scroll') || lowerName.includes('painting') || lowerName.includes('map') || lowerName.includes('letter')) {
    return {
      icon: lowerName.includes('cookbook') ? BookOpen : Scroll,
      bgGradient: 'from-amber-600/30 via-yellow-800/20 to-neutral-950',
      borderColor: 'border-amber-400/60',
      iconColor: 'text-amber-300',
      glowColor: 'shadow-[0_0_10px_rgba(245,158,11,0.3)]',
    };
  }

  // 19. Consumables & Boluses (Еда, пилюли, мясо, наживки)
  if (lowerName.includes('boluses') || lowerName.includes('meat') || lowerName.includes('prawn') || lowerName.includes('crab') || lowerName.includes('liver') || lowerName.includes('fowl foot') || lowerName.includes('grease')) {
    return {
      icon: Apple,
      bgGradient: 'from-rose-600/25 via-stone-800/20 to-neutral-950',
      borderColor: 'border-rose-400/50',
      iconColor: 'text-rose-300',
      glowColor: 'shadow-[0_0_8px_rgba(244,63,94,0.25)]',
    };
  }

  // 20. Crafting Flora, Fauna & Materials (Материалы крафта)
  const materials = ['fruit', 'lily', 'leaf', 'herba', 'moss', 'resin', 'mushroom', 'butterfly', 'firefly', 'feather', 'bone', 'fang', 'eye', 'blood', 'stone', 'fragment'];
  if (materials.some((m) => lowerName.includes(m))) {
    return {
      icon: lowerName.includes('feather') ? Feather : Leaf,
      bgGradient: 'from-emerald-600/25 via-stone-800/20 to-neutral-950',
      borderColor: 'border-emerald-500/50',
      iconColor: 'text-emerald-300',
      glowColor: 'shadow-[0_0_8px_rgba(16,185,129,0.25)]',
    };
  }

  // 21. Gestures (Жесты)
  if (lowerCat === 'gesture_placements' || lowerName.includes('gesture')) {
    return {
      icon: Hand,
      bgGradient: 'from-orange-600/25 via-amber-800/20 to-neutral-950',
      borderColor: 'border-orange-400/50',
      iconColor: 'text-orange-300',
      glowColor: 'shadow-[0_0_8px_rgba(251,146,60,0.25)]',
    };
  }

  // 22. Music / BGM
  if (lowerCat === 'level_bgm_placements') {
    return {
      icon: Music,
      bgGradient: 'from-violet-600/30 via-fuchsia-800/20 to-neutral-950',
      borderColor: 'border-violet-400/60',
      iconColor: 'text-violet-300',
      glowColor: 'shadow-[0_0_12px_rgba(167,139,250,0.3)]',
    };
  }

  // Default elegant golden treasure box (Никаких вопросительных знаков!)
  return {
    icon: Sparkles,
    bgGradient: 'from-amber-600/20 via-neutral-800/25 to-neutral-950',
    borderColor: 'border-gold-600/40',
    iconColor: 'text-gold-400',
    glowColor: 'shadow-[0_0_8px_rgba(212,163,75,0.2)]',
  };
}

export const ItemIcon: React.FC<ItemIconProps> = ({
  kind,
  category,
  name,
  originalName,
  size = 'md',
}) => {
  const theme = classifyItem(kind, category, name, originalName);
  const IconComponent = theme.icon;

  const sizeClasses = {
    sm: 'w-8 h-8 rounded-lg',
    md: 'w-10 h-10 rounded-xl',
    lg: 'w-12 h-12 rounded-xl',
  }[size];

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  }[size];

  return (
    <div
      className={`${sizeClasses} bg-gradient-to-br ${theme.bgGradient} border ${theme.borderColor} ${theme.glowColor} flex items-center justify-center shrink-0 relative overflow-hidden transition-all duration-200 group-hover:scale-105`}
    >
      <IconComponent className={`${iconSizes} ${theme.iconColor} drop-shadow`} />
    </div>
  );
};
