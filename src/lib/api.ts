import { supabase } from './supabase';
import { SocialPost, Platform } from '../types';

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL !== undefined
    ? import.meta.env.VITE_API_BASE_URL
    : import.meta.env.DEV
    ? 'http://127.0.0.1:8000'
    : '';


interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

/**
 * Common fetch helper that attaches Supabase auth token if present
 */
async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { timeoutMs = 12000, headers, ...rest } = options;
  const url = `${API_BASE_URL.replace(/\/$/, '')}${endpoint}`;

  // Get current session token from Supabase if logged in
  let token: string | undefined;
  try {
    const { data } = await supabase.auth.getSession();
    token = data.session?.access_token;
  } catch {
    // Session retrieval failed, proceed without token
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const mergedHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...(headers as Record<string, string>),
  };

  if (!(rest.body instanceof FormData) && !mergedHeaders['Content-Type']) {
    mergedHeaders['Content-Type'] = 'application/json';
  }

  if (token) {
    mergedHeaders['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, {
      ...rest,
      headers: mergedHeaders,
      signal: controller.signal,
    });

    clearTimeout(timer);

    if (!res.ok) {
      let errDetail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const body = await res.json();
        if (body.detail) errDetail = body.detail;
      } catch {
        // Fallback to HTTP error
      }
      throw new Error(errDetail);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    clearTimeout(timer);
    throw err;
  }
}

export interface GenerationParams {
  topic: string;
  tone?: string;
  content_type?: string;
  language?: string;
  include_hashtags?: boolean;
  platforms?: Platform[];
}

export interface GenerationResult {
  generated_text: string;
  tone: string;
  language: string;
  provider: string;
  model: string;
}

export interface PlatformPublishResult {
  platform: string;
  status: 'pending' | 'processing' | 'published' | 'scheduled' | 'failed' | 'cancelled';
  remote_post_id?: string;
  remote_post_url?: string;
  error_message?: string;
}

export interface PublishResult {
  post_id: string;
  success: boolean;
  message: string;
  results: PlatformPublishResult[];
}

export interface PlatformConnection {
  id: string;
  name: string;
  handle: string;
  status: 'connected' | 'disconnected' | 'error' | 'coming_soon' | 'expired' | 'reauth_required' | 'temp_unavailable';
  connectedUser?: string;
  connected_user?: string;
  accountId?: string;
  account_id?: string;
  accountName?: string;
  account_name?: string;
  lastVerifiedAt?: string;
  last_verified_at?: string;
  isConfigured?: boolean;
  is_configured?: boolean;
  isComingSoon?: boolean;
  is_coming_soon?: boolean;
  statusReason?: string;
  status_reason?: string;
}

export function normalizePost(p: any): SocialPost {
  return {
    id: String(p.id),
    title: p.title || 'Untitled Post',
    snippet: p.snippet || (p.content ? p.content.slice(0, 50).replace(/\n/g, ' ') + '...' : ''),
    content: p.content || '',
    platforms: Array.isArray(p.platforms) ? p.platforms : [],
    status: (p.status || 'draft') as any,
    createdAt: p.createdAt || p.created_at || new Date().toISOString(),
    scheduledAt: p.scheduledAt || p.scheduled_at || undefined,
    mediaUrl: p.mediaUrl || p.media_url || undefined,
    tone: p.tone || 'Professional',
    contentType: p.contentType || p.content_type || 'General Post',
    language: p.language || 'English',
    youtubePostType: p.youtubePostType || p.youtube_post_type || undefined,
    pinterestBoardId: p.pinterestBoardId || p.pinterest_board_id || p.board_id || undefined,
  };
}

export interface ScheduleJob {
  id: string;
  post_id?: string;
  content?: string;
  media_url?: string;
  platforms: Platform[];
  scheduled_time: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  attempts: number;
  max_attempts: number;
  last_error?: string;
  platform_results?: PlatformPublishResult[];
  dry_run: boolean;
  variants?: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface SchedulerHealth {
  status: string;
  running: boolean;
  poll_interval_seconds: number;
  uptime_seconds: number;
  total_jobs: number;
  pending_jobs: number;
  processing_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  cancelled_jobs: number;
}

export const api = {
  /**
   * Health check to confirm backend is reachable
   */
  async checkHealth(): Promise<{ status: string; groq_configured: boolean }> {
    return fetchWithAuth('/api/health');
  },

  /**
   * Generate post preview using Groq backend LLM service
   */
  async generatePostPreview(params: GenerationParams): Promise<GenerationResult> {
    return fetchWithAuth('/api/v1/generation/preview', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  /**
   * List posts from backend persistence
   */
  async listPosts(statusFilter?: string): Promise<SocialPost[]> {
    const query = statusFilter && statusFilter !== 'all' ? `?status_filter=${statusFilter}` : '';
    const raw = await fetchWithAuth<any[]>(`/api/v1/posts${query}`);
    return Array.isArray(raw) ? raw.map(normalizePost) : [];
  },

  /**
   * Create or update a post draft
   */
  async savePost(post: SocialPost): Promise<SocialPost> {
    const raw = await fetchWithAuth<any>('/api/v1/posts', {
      method: 'POST',
      body: JSON.stringify(post),
    });
    return normalizePost(raw);
  },

  /**
   * Update an existing post draft
   */
  async updatePost(postId: string, partial: Partial<SocialPost>): Promise<SocialPost> {
    const raw = await fetchWithAuth<any>(`/api/v1/posts/${postId}`, {
      method: 'PATCH',
      body: JSON.stringify(partial),
    });
    return normalizePost(raw);
  },

  /**
   * Publish post to selected platforms through FastAPI backend
   */
  /**
   * Upload media file (image/video) to persistent public storage
   */
  async uploadMedia(file: File): Promise<{ url: string; filename: string; content_type: string; size: number; storage: string }> {
    const formData = new FormData();
    formData.append('file', file);
    return fetchWithAuth('/api/v1/media/upload', {
      method: 'POST',
      body: formData,
      timeoutMs: 60000,
    });
  },

  /**
   * Publish post to selected platforms through FastAPI backend
   */
  async publishPost(
    postId: string,
    platforms: Platform[],
    publishNow: boolean = true,
    content?: string,
    mediaUrl?: string,
    title?: string,
    boardId?: string,
    youtubePostType?: 'short' | 'long_form'
  ): Promise<PublishResult> {
    return fetchWithAuth('/api/v1/publishing/publish', {
      method: 'POST',
      body: JSON.stringify({
        post_id: postId,
        platforms,
        publish_now: publishNow,
        content: content || undefined,
        media_url: mediaUrl || undefined,
        title: title || undefined,
        board_id: boardId || undefined,
        youtube_post_type: youtubePostType || undefined,
      }),
      timeoutMs: 45000,
    });
  },

  /**
   * Delete post
   */
  async deletePost(postId: string): Promise<{ success: boolean; message: string }> {
    return fetchWithAuth(`/api/v1/posts/${postId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Fetch connected social platforms
   */
  async listConnections(): Promise<{ connections: PlatformConnection[] }> {
    return fetchWithAuth('/api/v1/connections');
  },

  /**
   * Initiate Meta OAuth (Facebook or Instagram)
   */
  async initiateMetaAuth(
    platform: 'facebook' | 'instagram',
    redirectOrigin?: string
  ): Promise<{ auth_url: string; state: string; platform: string }> {
    return fetchWithAuth('/api/v1/connections/meta/authorize', {
      method: 'POST',
      body: JSON.stringify({
        platform,
        redirect_origin: redirectOrigin || window.location.origin,
      }),
    });
  },

  /**
   * Initiate Pinterest OAuth 2.0 flow
   */
  async initiatePinterestAuth(
    redirectOrigin?: string
  ): Promise<{ auth_url: string; state: string; platform: string }> {
    return fetchWithAuth('/api/v1/connections/pinterest/authorize', {
      method: 'POST',
      body: JSON.stringify({
        platform: 'pinterest',
        redirect_origin: redirectOrigin || window.location.origin,
      }),
    });
  },

  /**
   * Initiate Google / YouTube OAuth 2.0 flow
   */
  async initiateYouTubeAuth(
    redirectOrigin?: string
  ): Promise<{ auth_url: string; state: string; platform: string }> {
    return fetchWithAuth('/api/v1/connections/youtube/authorize', {
      method: 'POST',
      body: JSON.stringify({
        platform: 'youtube',
        redirect_origin: redirectOrigin || window.location.origin,
      }),
    });
  },

  /**
   * Fetch authenticated user's Pinterest boards
   */
  async getPinterestBoards(): Promise<{ boards: Array<{ id: string; name: string }> }> {
    return fetchWithAuth<{ boards: Array<{ id: string; name: string }> }>('/api/v1/connections/pinterest/boards');
  },

  /**
   * Create a new Pinterest board in active environment (Sandbox)
   */
  async createPinterestBoard(name: string, description?: string): Promise<{ board: { id: string; name: string } }> {
    return fetchWithAuth<{ board: { id: string; name: string } }>('/api/v1/connections/pinterest/boards', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  },

  /**
   * Connect Bluesky via AT Protocol App Password
   */
  async connectBluesky(
    handle: string,
    appPassword: string
  ): Promise<{ platform: string; is_valid: boolean; status: string; message: string; account_name?: string }> {
    return fetchWithAuth('/api/v1/connections/bluesky/connect', {
      method: 'POST',
      body: JSON.stringify({ handle, app_password: appPassword }),
    });
  },

  /**
   * Connect LinkedIn via OAuth Bearer token
   */
  async connectLinkedIn(
    accessToken: string,
    authorUrn?: string
  ): Promise<{ platform: string; is_valid: boolean; status: string; message: string; account_name?: string }> {
    return fetchWithAuth('/api/v1/connections/linkedin/connect', {
      method: 'POST',
      body: JSON.stringify({ access_token: accessToken, author_urn: authorUrn || undefined }),
    });
  },

  /**
   * Disconnect a platform and delete credentials
   */
  async disconnectPlatform(
    platform: string
  ): Promise<{ success: boolean; platform: string; status: string; message: string }> {
    return fetchWithAuth(`/api/v1/connections/${platform}`, {
      method: 'DELETE',
    });
  },

  /**
   * Refresh or re-verify a platform connection
   */
  async refreshConnection(
    platform: string
  ): Promise<{ platform: string; is_valid: boolean; status: string; message: string; account_name?: string }> {
    return fetchWithAuth(`/api/v1/connections/${platform}/refresh`, {
      method: 'POST',
    });
  },

  /**
   * Verify a platform credentials and handshake
   */
  async verifyConnection(
    platform: string,
    credentials?: {
      app_id?: string;
      app_secret?: string;
      access_token?: string;
      page_id?: string;
      account_id?: string;
      redirect_uri?: string;
      code?: string;
    }
  ): Promise<{
    platform: string;
    is_valid: boolean;
    status: string;
    message: string;
  }> {
    return fetchWithAuth(`/api/v1/connections/${platform}/verify`, {
      method: 'POST',
      body: JSON.stringify({ platform, ...(credentials || {}) }),
    });
  },

  /**
   * Queue a scheduled post in the backend scheduling worker
   */
  async createSchedule(payload: {
    post_id?: string;
    content?: string;
    media_url?: string;
    platforms: Platform[];
    scheduled_time: string;
    dry_run?: boolean;
    max_attempts?: number;
    variants?: Record<string, string>;
  }): Promise<ScheduleJob> {
    return fetchWithAuth('/api/v1/schedules', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * List scheduled jobs from backend
   */
  async listSchedules(statusFilter?: string): Promise<ScheduleJob[]> {
    const query = statusFilter ? `?status=${statusFilter}` : '';
    return fetchWithAuth<ScheduleJob[]>(`/api/v1/schedules${query}`);
  },

  /**
   * Cancel a pending scheduled job
   */
  async cancelSchedule(scheduleId: string): Promise<ScheduleJob> {
    return fetchWithAuth(`/api/v1/schedules/${scheduleId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get scheduler engine health and metrics
   */
  async getSchedulerHealth(): Promise<SchedulerHealth> {
    return fetchWithAuth('/api/v1/schedules/health');
  },
};
