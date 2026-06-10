// PhysiqAI design tokens — light & minimal.
// White canvas, generous whitespace, near-black text, one calm green accent.
// The user's before/after photos are the hero; the UI is a quiet, premium frame.
export const colors = {
  background: '#FFFFFF', // screen canvas
  surface: '#F7F8FA', // subtle section fills / input wells
  card: '#FFFFFF', // card surface (pair with border + shadow.card)
  foreground: '#0B0D10', // primary text — near-black
  muted: '#6B7280', // secondary text
  faint: '#9CA3AF', // fine print, placeholders, disabled
  border: '#E6E8EC', // hairlines, input borders, dividers
  primary: '#16A34A', // brand green — wordmark, selected, progress, success
  primarySoft: '#EAF7EF', // faint green tint — selected fills on white
  ink: '#111418', // primary CTA button background
  accent: '#16A34A', // emphasis (alias of brand green)
  secondary: '#2563EB', // reserved link/info blue (rarely used)
  destructive: '#DC2626',
  onInk: '#FFFFFF', // text/icon on ink buttons
  onPrimary: '#FFFFFF', // text/icon on green fills
};

export const space = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48 };

export const radius = { sm: 8, md: 14, lg: 16, pill: 999 };

export const font = {
  xs: 12, sm: 14, base: 16, lg: 18, xl: 20, '2xl': 24, '3xl': 30, '4xl': 38,
};

// Font weights — restrained for a minimal feel (system font / SF Pro on iOS).
export const weight = {
  regular: '400', medium: '500', semibold: '600', bold: '700', heavy: '800',
} as const;

// Line-height multipliers to pair with font sizes.
export const leading = { tight: 1.15, snug: 1.3, normal: 1.5 };

// One soft, low shadow — used only on cards. Keeps elevation minimal.
export const shadow = {
  card: {
    shadowColor: '#0B0D10',
    shadowOpacity: 0.06,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
};
