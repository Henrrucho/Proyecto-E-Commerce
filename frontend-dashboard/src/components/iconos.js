import {
  BookOpen, Car, Coffee, Dumbbell, Gem, Gift, Heart, House, Laptop, Shirt, ShieldAlert, Sparkles, Split, UserPlus,
} from 'lucide-react'

// Las claves coinciden con `iconKey` de public/data/dashboard.json
export const ICONOS = {
  shieldAlert: ShieldAlert,
  gem: Gem,
  userPlus: UserPlus,
  split: Split,
  laptop: Laptop,
  home: House,
  shirt: Shirt,
  dumbbell: Dumbbell,
  car: Car,
  coffee: Coffee,
  bookOpen: BookOpen,
  heart: Heart,
  gift: Gift,
  sparkles: Sparkles,
}

export const ACENTOS = {
  rose: {
    badge: 'bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 border-rose-200 dark:border-rose-800/50',
    iconBox: 'bg-rose-500/10 text-rose-600 dark:text-rose-400',
    borderTop: 'border-t-rose-500',
  },
  blue: {
    badge: 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-800/50',
    iconBox: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
    borderTop: 'border-t-blue-600',
  },
  amber: {
    badge: 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800/50',
    iconBox: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
    borderTop: 'border-t-amber-500',
  },
  indigo: {
    badge: 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 border-indigo-200 dark:border-indigo-800/50',
    iconBox: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400',
    borderTop: 'border-t-indigo-500',
  },
}

export const TARJETA = 'bg-white dark:bg-slate-900 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-800 transition-colors'
export const BOTON_VOLVER =
  'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2 rounded-full text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center gap-1.5 shadow-sm hover:bg-slate-50 dark:hover:bg-slate-800 transition'
