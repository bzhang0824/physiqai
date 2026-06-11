// A stylized front-facing body silhouette whose torso/waist/hips widen with body-fat %.
// Pure parametric SVG (no art assets) so it morphs smoothly as the slider moves.
import { memo } from 'react';
import Svg, { Circle, Path } from 'react-native-svg';

import { colors } from '@/lib/theme';
import type { Sex } from '@/lib/store';

// bf% range each sex's slider spans (lean endpoint → higher endpoint).
export const BF_RANGE: Record<Sex, { lean: number; high: number }> = {
  M: { lean: 6, high: 35 },
  F: { lean: 14, high: 42 },
};

// Friendly descriptor for a given bf%, by sex. Thresholds are the upper bound
// of each band; anything above the last is "Higher".
const BANDS: Record<Sex, { max: number; label: string; desc: string }[]> = {
  M: [
    { max: 12, label: 'Lean', desc: 'Visible abs, vascular' },
    { max: 17, label: 'Athletic', desc: 'Some definition' },
    { max: 23, label: 'Average', desc: 'Soft midsection' },
    { max: Infinity, label: 'Higher', desc: 'Rounder midsection' },
  ],
  F: [
    { max: 20, label: 'Lean', desc: 'Athletic, defined' },
    { max: 25, label: 'Athletic', desc: 'Toned' },
    { max: 31, label: 'Average', desc: 'Soft' },
    { max: Infinity, label: 'Higher', desc: 'Fuller' },
  ],
};

export function bodyDescriptor(sex: Sex, bfPct: number): { label: string; desc: string } {
  return BANDS[sex].find((b) => bfPct <= b.max) ?? BANDS[sex][BANDS[sex].length - 1];
}

// Half-widths (from the vertical centre, viewBox 100 wide) at the lean and high
// endpoints. Waist is the dominant signal; hips widen more for F, shoulders for M.
const SHAPE: Record<Sex, {
  shoulder: [number, number]; waist: [number, number]; hip: [number, number];
}> = {
  M: { shoulder: [27, 25], waist: [13, 31], hip: [17, 27] },
  F: { shoulder: [21, 20], waist: [11, 29], hip: [23, 33] },
};

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const clamp01 = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);

function buildPath(sex: Sex, t: number): string {
  const s = SHAPE[sex];
  const sh = lerp(s.shoulder[0], s.shoulder[1], t);
  const w = lerp(s.waist[0], s.waist[1], t);
  const h = lerp(s.hip[0], s.hip[1], t);
  const C = 50; // centre x

  // Left outline top→bottom, around the legs, then right outline bottom→top.
  return [
    `M ${C - 5} 34`,                                  // neck (left)
    `C ${C - 5} 40, ${C - sh} 42, ${C - sh} 50`,      // out to left shoulder
    `C ${C - sh} 70, ${C - w} 78, ${C - w} 98`,       // pinch in to left waist
    `C ${C - w} 112, ${C - h} 112, ${C - h} 122`,     // out to left hip
    `L ${C - h + 3} 190`,                             // down outer left leg
    `L ${C - 7} 190`,                                 // left foot (inner)
    `L ${C} 130`,                                     // up the inseam to crotch
    `L ${C + 7} 190`,                                 // down to right foot (inner)
    `L ${C + h - 3} 190`,                             // right foot (outer)
    `L ${C + h} 122`,                                 // up outer right leg to hip
    `C ${C + h} 112, ${C + w} 112, ${C + w} 98`,      // in to right waist
    `C ${C + w} 78, ${C + sh} 70, ${C + sh} 50`,      // out to right shoulder
    `C ${C + sh} 42, ${C + 5} 40, ${C + 5} 34`,       // back to neck
    'Z',
  ].join(' ');
}

export const BodySilhouette = memo(function BodySilhouette({
  sex,
  bfPct,
  size = 150,
}: {
  sex: Sex;
  bfPct: number;
  size?: number;
}) {
  const { lean, high } = BF_RANGE[sex];
  const t = clamp01((bfPct - lean) / (high - lean));
  const headR = lerp(10, 11.5, t); // face fills out a touch at higher bf

  return (
    <Svg width={size} height={size * 2} viewBox="0 0 100 200">
      <Circle cx={50} cy={20} r={headR} fill={colors.primarySoft} stroke={colors.primary} strokeWidth={2} />
      <Path d={buildPath(sex, t)} fill={colors.primarySoft} stroke={colors.primary} strokeWidth={2} strokeLinejoin="round" />
    </Svg>
  );
});
