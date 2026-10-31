export type Platform =
  | 'bluesky'
  | 'linkedin'
  | 'instagram'
  | 'facebook'
  | 'twitter'
  | 'pinterest'
  | 'youtube';

export type PostStatus =
  | 'published'
  | 'scheduled'
  | 'draft'
  | 'failed';

export interface SocialPost {
  id: string;
  title: string;
  snippet: string;
  content: string;
  platforms: Platform[];
  status: PostStatus;
  createdAt: string;
  scheduledAt?: string;
  mediaUrl?: string;
  tone?: string;
  contentType?: string;
  language?: string;
}

export interface ConnectedPlatform {
  id: Platform;
  name: string;
  handle: string;
  status: 'connected' | 'disconnected' | 'coming_soon' | 'error';
  connectedUser: string;
  lastVerifiedAt?: string;
  accountId?: string;
  accountName?: string;
  isComingSoon?: boolean;
  isConfigured?: boolean;
  appId?: string;
  appSecret?: string;
  accessToken?: string;
  pageId?: string;
}

export interface MetricSummary {
  totalPosts: number;
  published: number;
  scheduled: number;
  failed: number;
}

export interface UserProfile {
  name: string;
  email: string;
  avatarChar: string;
  brandName?: string;
  role?: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  time: string;
  unread: boolean;
  type: 'success' | 'alert' | 'info';
}

export interface UserPreferences {
  autoSuggestTimes: boolean;
  includeHashtags: boolean;
  defaultTone: string;
  defaultLanguage: string;
}

export interface UserNotifications {
  emailSummary: boolean;
  failureAlerts: boolean;
  newFollowerAlerts: boolean;
}
