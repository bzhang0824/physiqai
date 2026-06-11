// Share the server-composed projection card (GET /share-card/{job}).
// Web: Web Share API Level 2 when available (iOS Safari ≥15, Android Chrome),
// else an <a download> fallback. Feature-detect, never UA-sniff. Safari's
// transient-activation window can expire while the card downloads — a
// NotAllowedError falls back to download instead of failing.
import { Platform } from 'react-native';

import { apiBase, authHeader } from './api';

export type ShareOutcome = 'shared' | 'downloaded' | 'unsupported';

export async function shareCard(job: string): Promise<ShareOutcome> {
  const res = await fetch(`${apiBase()}/share-card/${job}`, {
    headers: await authHeader(),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const blob = await res.blob();

  if (Platform.OS !== 'web') {
    // Native path lands with the app-store build (expo-file-system +
    // expo-sharing). The web build is today's distribution target.
    return 'unsupported';
  }

  const file = new File([blob], 'physiqai-projection.png', { type: 'image/png' });
  const nav = navigator as Navigator & {
    canShare?: (data: { files: File[] }) => boolean;
    share?: (data: { files: File[]; title?: string }) => Promise<void>;
  };

  if (nav.canShare?.({ files: [file] }) && nav.share) {
    try {
      await nav.share({ files: [file], title: 'My PhysiqAI projection' });
      return 'shared';
    } catch (e: unknown) {
      const name = e instanceof Error ? e.name : '';
      if (name === 'AbortError') return 'shared'; // user closed the sheet — not an error
      // NotAllowedError etc. → fall through to download
    }
  }

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'physiqai-projection.png';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
  return 'downloaded';
}
