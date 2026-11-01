import { Platform } from '../types';

export interface FrontendPlatformRule {
  id: Platform;
  name: string;
  maxLength: number;
  lengthUnit: 'graphemes' | 'characters';
  maxBytes?: number;
  supportsTitle: boolean;
  maxTitleLength?: number;
  supportsMedia: boolean;
  mediaRequired: boolean;
  formattingGuidance: string;
}

export const FRONTEND_PLATFORM_RULES: Record<Platform, FrontendPlatformRule> = {
  bluesky: {
    id: 'bluesky',
    name: 'Bluesky',
    maxLength: 300,
    lengthUnit: 'graphemes',
    maxBytes: 3000,
    supportsTitle: false,
    supportsMedia: true,
    mediaRequired: false,
    formattingGuidance: 'Punchy post under 300 Unicode grapheme clusters. No title field.',
  },
  linkedin: {
    id: 'linkedin',
    name: 'LinkedIn',
    maxLength: 3000,
    lengthUnit: 'characters',
    supportsTitle: true,
    maxTitleLength: 120,
    supportsMedia: true,
    mediaRequired: false,
    formattingGuidance: 'Professional, structured insights with clean line breaks and discussion prompt.',
  },
  instagram: {
    id: 'instagram',
    name: 'Instagram',
    maxLength: 2200,
    lengthUnit: 'characters',
    supportsTitle: false,
    supportsMedia: true,
    mediaRequired: true,
    formattingGuidance: 'Visual caption with strong opening hook, paragraph breaks, and relevant hashtags.',
  },
  facebook: {
    id: 'facebook',
    name: 'Facebook',
    maxLength: 5000,
    lengthUnit: 'characters',
    supportsTitle: false,
    supportsMedia: true,
    mediaRequired: false,
    formattingGuidance: 'Conversational community discussion prompt encouraging comments and shares.',
  },
  pinterest: {
    id: 'pinterest',
    name: 'Pinterest',
    maxLength: 500,
    lengthUnit: 'characters',
    supportsTitle: true,
    maxTitleLength: 100,
    supportsMedia: true,
    mediaRequired: true,
    formattingGuidance: 'Keyword-rich Pin title (under 100 chars) and actionable description (under 500 chars).',
  },
  youtube: {
    id: 'youtube',
    name: 'YouTube',
    maxLength: 5000,
    lengthUnit: 'characters',
    supportsTitle: true,
    maxTitleLength: 100,
    supportsMedia: true,
    mediaRequired: true,
    formattingGuidance: 'High-CTR video title (under 100 chars) and comprehensive description (under 5,000 chars).',
  },
  twitter: {
    id: 'twitter',
    name: 'Twitter',
    maxLength: 280,
    lengthUnit: 'characters',
    supportsTitle: false,
    supportsMedia: true,
    mediaRequired: false,
    formattingGuidance: 'Concise post under 280 characters.',
  },
};

/**
 * Counts Unicode grapheme clusters accurately according to Unicode UAX #29 standard.
 * Uses native Intl.Segmenter when available; falls back to Array.from iterator.
 */
export function countPlatformLength(platform: Platform, text: string): number {
  if (!text) return 0;
  const rule = FRONTEND_PLATFORM_RULES[platform];
  if (rule?.lengthUnit === 'graphemes') {
    if (typeof Intl !== 'undefined' && 'Segmenter' in Intl) {
      try {
        const segmenter = new (Intl as any).Segmenter('en', { granularity: 'grapheme' });
        return [...segmenter.segment(text)].length;
      } catch {
        // Fallback
      }
    }
    // Fallback spread handles surrogate pairs
    return Array.from(text).length;
  }
  return text.length;
}

/**
 * Formats a clean counter label e.g. "140 / 300 graphemes" or "820 / 3,000 characters"
 */
export function formatCounterLabel(platform: Platform, text: string): {
  count: number;
  max: number;
  unit: string;
  isOverLimit: boolean;
  label: string;
} {
  const rule = FRONTEND_PLATFORM_RULES[platform] || FRONTEND_PLATFORM_RULES.linkedin;
  const count = countPlatformLength(platform, text);
  const max = rule.maxLength;
  const isOverLimit = count > max;
  const unit = rule.lengthUnit;
  const label = `${count} / ${max.toLocaleString()} ${unit}`;
  return { count, max, unit, isOverLimit, label };
}

