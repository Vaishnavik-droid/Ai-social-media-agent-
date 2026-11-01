import React, { useState, useEffect, useCallback } from 'react';
import { ConnectedPlatform, Platform } from '../types';
import { PlatformIcon } from '../components/PlatformIcon';
import {
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Lock,
  LogOut,
  Sparkles,
  X,
  Key,
  Globe,
  Clock,
  AlertTriangle,
  UserCheck,
} from 'lucide-react';
import { api, PlatformConnection } from '../lib/api';

interface PlatformsProps {
  platforms?: ConnectedPlatform[];
  onToggleStatus?: (id: Platform) => void;
  onUpdateHandle?: (id: Platform, newHandle: string) => void;
  onUpdateCredentials?: (
    id: Platform,
    credentials: {
      appId?: string;
      appSecret?: string;
      accessToken?: string;
      pageId?: string;
      handle?: string;
      status?: 'connected' | 'disconnected';
    }
  ) => void;
  onToast?: (message: string) => void;
}

interface PlatformDefinition {
  id: Platform;
  name: string;
  tagline: string;
  description: string;
  type: 'meta_oauth' | 'pinterest_oauth' | 'youtube_oauth' | 'modal';
}

const ALL_PLATFORMS: PlatformDefinition[] = [
  {
    id: 'bluesky',
    name: 'Bluesky',
    tagline: 'Decentralized AT Protocol',
    description: 'Broadcast short-form posts and embedded media over the open AT Protocol network.',
    type: 'modal',
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    tagline: 'Professional Network',
    description: 'Publish commentary, articles, and thought leadership to your profile or company page.',
    type: 'modal',
  },
  {
    id: 'facebook',
    name: 'Facebook',
    tagline: 'Meta Page Feed',
    description: 'Publish updates, links, and high-resolution photo posts directly to your Page feed.',
    type: 'meta_oauth',
  },
  {
    id: 'instagram',
    name: 'Instagram',
    tagline: 'Visual Content',
    description: 'Publish feed photos, carousel visuals, and captions to your Professional Business account.',
    type: 'meta_oauth',
  },
  {
    id: 'pinterest',
    name: 'Pinterest',
    tagline: 'Visual Discovery',
    description: 'Pin high-impact graphics, product visuals, and destination link cards to your boards.',
    type: 'pinterest_oauth',
  },
  {
    id: 'youtube',
    name: 'YouTube',
    tagline: 'Video & Shorts',
    description: 'Upload video content, shorts, descriptions, and tags directly to your YouTube channel.',
    type: 'youtube_oauth',
  },
];

export const Platforms: React.FC<PlatformsProps> = ({
  onToast,
}) => {
  const [platformList, setPlatformList] = useState<PlatformConnection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});

  // Active Connect Modals for Bluesky & LinkedIn
  const [activeModal, setActiveModal] = useState<'bluesky' | 'linkedin' | null>(null);
  const [blueskyHandle, setBlueskyHandle] = useState('');
  const [blueskyPassword, setBlueskyPassword] = useState('');
  const [linkedinToken, setLinkedinToken] = useState('');
  const [linkedinUrn, setLinkedinUrn] = useState('');
  const [modalError, setModalError] = useState<string | null>(null);
  const [modalSubmitting, setModalSubmitting] = useState(false);

  // Disconnection Confirmation Modal state
  const [disconnectTarget, setDisconnectTarget] = useState<{ id: string; name: string; handle: string } | null>(null);

  // Fetch real connection states from FastAPI backend as single source of truth
  const fetchConnections = useCallback(async (isManual = false) => {
    try {
      setIsLoading(true);
      setFetchError(null);
      const res = await api.listConnections();
      if (res && res.connections) {
        setPlatformList(res.connections);
        if (isManual && onToast) {
          onToast('✓ Platform connection statuses refreshed from server.');
        }
      } else {
        setPlatformList([]);
      }
    } catch (err: any) {
      console.error('Could not fetch server connections:', err);
      const msg = err?.message || 'Failed to retrieve connection statuses from backend.';
      setFetchError(msg);
      if (isManual && onToast) {
        onToast(`✕ Refresh failed: ${msg}`);
      }
    } finally {
      setIsLoading(false);
    }
  }, [onToast]);

  useEffect(() => {
    fetchConnections();
  }, [fetchConnections]);

  // Handle postMessage from OAuth Popup (Meta, Pinterest, YouTube)
  useEffect(() => {
    const handleOAuthMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) {
        return;
      }

      const data = event.data;
      if (!data || typeof data !== 'object') return;

      if (data.type === 'OMNIPULSE_OAUTH_SUCCESS') {
        const platMap: Record<string, string> = {
          facebook: 'Facebook',
          instagram: 'Instagram',
          pinterest: 'Pinterest',
          youtube: 'YouTube',
        };
        const platName = platMap[data.platform] || data.platform || 'Platform';
        if (onToast) {
          onToast(`🎉 ${platName} connected successfully (${data.handle || 'verified'})!`);
        }
        setActionLoading((prev) => ({ ...prev, [data.platform]: false }));
        fetchConnections();
      } else if (data.type === 'OMNIPULSE_OAUTH_ERROR') {
        const platName = data.platform ? data.platform.toUpperCase() : 'OAuth';
        if (onToast) {
          onToast(`✕ ${platName} Connection Error: ${data.error || 'Authorization failed'}`);
        }
        setActionLoading((prev) => ({ ...prev, [data.platform || 'oauth']: false }));
      }
    };

    window.addEventListener('message', handleOAuthMessage);
    return () => window.removeEventListener('message', handleOAuthMessage);
  }, [onToast, fetchConnections]);

  // Initiate OAuth in Popup (Facebook, Instagram, Pinterest, YouTube)
  const handleConnectOAuth = async (platform: 'facebook' | 'instagram' | 'pinterest' | 'youtube') => {
    setActionLoading((prev) => ({ ...prev, [platform]: true }));

    try {
      let res: { auth_url: string };
      if (platform === 'pinterest') {
        res = await api.initiatePinterestAuth(window.location.origin);
      } else if (platform === 'youtube') {
        res = await api.initiateYouTubeAuth(window.location.origin);
      } else {
        res = await api.initiateMetaAuth(platform, window.location.origin);
      }

      if (!res.auth_url) {
        throw new Error('Backend did not return an authorization URL.');
      }

      const width = 640;
      const height = 720;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;

      const popup = window.open(
        res.auth_url,
        `OmniPulse_Auth_${platform}`,
        `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,status=yes`
      );

      if (!popup || popup.closed || typeof popup.closed === 'undefined') {
        alert(`Popup was blocked by your browser. Please allow popups for OmniPulse to authorize ${platform}.`);
        setActionLoading((prev) => ({ ...prev, [platform]: false }));
        return;
      }

      if (onToast) {
        const platMap: Record<string, string> = {
          facebook: 'Facebook',
          instagram: 'Instagram',
          pinterest: 'Pinterest',
          youtube: 'YouTube',
        };
        const platName = platMap[platform] || platform;
        onToast(`${platName} authorization window opened. Complete sign-in in the popup.`);
      }

      const checkPopup = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkPopup);
          setActionLoading((prev) => ({ ...prev, [platform]: false }));
        }
      }, 1000);
    } catch (err: any) {
      setActionLoading((prev) => ({ ...prev, [platform]: false }));
      const msg = err?.message || `Failed to initiate ${platform} authorization.`;
      if (onToast) {
        onToast(`✕ Error: ${msg}`);
      } else {
        alert(msg);
      }
    }
  };

  // Submit Bluesky Modal Connect
  const handleSubmitBluesky = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setModalSubmitting(true);

    try {
      const res = await api.connectBluesky(blueskyHandle, blueskyPassword);
      if (res.is_valid) {
        if (onToast) onToast(`🎉 ${res.message}`);
        setActiveModal(null);
        setBlueskyPassword('');
        fetchConnections();
      } else {
        setModalError(res.message);
      }
    } catch (err: any) {
      setModalError(err?.message || 'Failed to connect to Bluesky.');
    } finally {
      setModalSubmitting(false);
    }
  };

  // Submit LinkedIn Modal Connect
  const handleSubmitLinkedIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setModalSubmitting(true);

    try {
      const res = await api.connectLinkedIn(linkedinToken, linkedinUrn);
      if (res.is_valid) {
        if (onToast) onToast(`🎉 ${res.message}`);
        setActiveModal(null);
        setLinkedinToken('');
        setLinkedinUrn('');
        fetchConnections();
      } else {
        setModalError(res.message);
      }
    } catch (err: any) {
      setModalError(err?.message || 'Failed to connect to LinkedIn.');
    } finally {
      setModalSubmitting(false);
    }
  };

  // Prompt Disconnect Confirmation
  const promptDisconnect = (platformId: string, name: string, handle: string) => {
    setDisconnectTarget({ id: platformId, name, handle });
  };

  // Execute Confirmed Disconnect
  const executeDisconnect = async () => {
    if (!disconnectTarget) return;
    const { id: platformId, name: platName } = disconnectTarget;

    setActionLoading((prev) => ({ ...prev, [platformId]: true }));
    try {
      await api.disconnectPlatform(platformId);
      if (onToast) onToast(`Disconnected from ${platName}.`);
      setDisconnectTarget(null);
      await fetchConnections();
    } catch (err: any) {
      if (onToast) onToast(`✕ Error disconnecting: ${err?.message}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [platformId]: false }));
    }
  };

  // Re-verify / Refresh handler
  const handleRefresh = async (platformId: string) => {
    setActionLoading((prev) => ({ ...prev, [platformId]: true }));
    try {
      const res = await api.refreshConnection(platformId);
      if (res.is_valid) {
        if (onToast) onToast(`✓ ${res.message}`);
      } else {
        if (onToast) onToast(`✕ ${res.message}`);
      }
      await fetchConnections();
    } catch (err: any) {
      if (onToast) onToast(`✕ Verification error: ${err?.message}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [platformId]: false }));
    }
  };

  // Compute live dynamic counts directly from server connection records
  const connectedCount = platformList.filter((p) => p.status === 'connected').length;
  const totalCount = ALL_PLATFORMS.length;

  return (
    <div className="platforms-page">
      {/* Top Action & Status Bar */}
      <div className="platforms-header">
        {/* Connection Summary Pill */}
        <div className="platform-summary-badge" title="Live connection count from server">
          <span className={`summary-dot ${connectedCount > 0 ? 'active' : ''}`}></span>
          <span className="summary-count-text">
            <strong>{connectedCount}</strong> of <strong>{totalCount}</strong> platforms connected
          </span>
        </div>

        <button
          type="button"
          onClick={() => fetchConnections(true)}
          disabled={isLoading}
          className="btn-refresh-all"
          title="Refresh connection statuses from server"
        >
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          <span>Refresh All</span>
        </button>
      </div>

      {/* Backend Synchronization Error Banner */}
      {fetchError && (
        <div className="platforms-fetch-error-banner">
          <div className="fetch-error-icon-wrap">
            <AlertCircle size={20} className="text-red-500" />
          </div>
          <div className="fetch-error-content">
            <span className="fetch-error-title">Backend Connection Error</span>
            <span className="fetch-error-text">
              Unable to retrieve connection statuses from the server ({fetchError}).
            </span>
          </div>
          <button
            type="button"
            onClick={() => fetchConnections(true)}
            disabled={isLoading}
            className="btn-fetch-retry"
          >
            <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Security Architecture Badge */}
      <div className="platforms-security-banner">
        <div className="security-icon-circle">
          <ShieldCheck size={18} className="text-emerald-500" />
        </div>
        <div className="security-banner-content">
          <span className="security-banner-title">Zero Client-Side Token Storage</span>
          <span className="security-banner-text">
            All OAuth access tokens are encrypted at rest with authenticated AES encryption and stored securely in Supabase. Plaintext secrets are never stored in your browser.
          </span>
        </div>
      </div>

      {/* Platforms 6-Card Grid */}
      <div className="platforms-grid">
        {ALL_PLATFORMS.map((def) => {
          const current = platformList.find((item) => item.id === def.id);
          const isConnected = current?.status === 'connected';
          const isExpired = current?.status === 'expired';
          const isReauthRequired = current?.status === 'reauth_required';
          const isTempUnavailable = current?.status === 'temp_unavailable';
          const isError = current?.status === 'error';
          const isProblematic = isExpired || isReauthRequired || isError;
          const isActionLoading = Boolean(actionLoading[def.id]);

          // Clean date formatter
          let lastVerifiedStr: string | null = null;
          if (current?.last_verified_at || current?.lastVerifiedAt) {
            const raw = (current.last_verified_at || current.lastVerifiedAt)!;
            try {
              const dt = new Date(raw);
              lastVerifiedStr = dt.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              });
            } catch {
              lastVerifiedStr = raw;
            }
          }

          // Resolved handle / account identity
          const accountIdentifier =
            current?.handle && current.handle !== 'Not Connected' && current.handle !== 'Coming Soon'
              ? current.handle
              : current?.accountName || current?.account_name || null;

          return (
            <div
              key={def.id}
              className={`platform-card ${
                isConnected ? 'is-connected' : isProblematic ? 'is-error' : isTempUnavailable ? 'is-warning' : 'is-disconnected'
              }`}
            >
              <div className="platform-card-main">
                {/* Top Row: Icon + Brand Name + Status Pill */}
                <div className="platform-card-top">
                  <div className="platform-brand-info">
                    <div className="platform-icon-wrap">
                      <PlatformIcon platform={def.id} size={30} />
                    </div>
                    <div className="platform-name-wrap">
                      <h3 className="platform-name">{def.name}</h3>
                      <span className="platform-tagline">{def.tagline}</span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className="platform-status-wrap">
                    {isConnected ? (
                      <span className="status-pill status-pill-connected" title="Active & ready for publishing">
                        <span className="status-dot green"></span>
                        Connected
                      </span>
                    ) : isExpired ? (
                      <span className="status-pill status-pill-error" title="Access token has expired">
                        <span className="status-dot amber" style={{ background: '#f59e0b' }}></span>
                        Token Expired
                      </span>
                    ) : isReauthRequired ? (
                      <span className="status-pill status-pill-error" title="Reauthorization required">
                        <span className="status-dot orange" style={{ background: '#f97316' }}></span>
                        Reauth Needed
                      </span>
                    ) : isTempUnavailable ? (
                      <span className="status-pill status-pill-disconnected" title="Service temporarily unavailable">
                        <span className="status-dot blue" style={{ background: '#38bdf8' }}></span>
                        Temp Unavailable
                      </span>
                    ) : isError ? (
                      <span className="status-pill status-pill-error" title="Verification error">
                        <span className="status-dot red"></span>
                        Connection issue
                      </span>
                    ) : (
                      <span className="status-pill status-pill-disconnected" title="Not connected">
                        <span className="status-dot gray"></span>
                        Not connected
                      </span>
                    )}
                  </div>
                </div>

                {/* Description */}
                <p className="platform-card-desc">{def.description}</p>

                {/* Contextual Account Identity or Status Box */}
                <div className="platform-identity-box">
                  {isConnected ? (
                    <div className="identity-content">
                      <div className="identity-account-row">
                        <UserCheck size={14} className="identity-icon text-emerald-600" />
                        <span className="identity-account-name" title={accountIdentifier || 'Connected Account'}>
                          {accountIdentifier || 'Active Account'}
                        </span>
                      </div>

                      <div className="identity-sub-details">
                        {(current?.accountId || current?.account_id) && (
                          <span className="identity-account-id">
                            ID: <code>{current.accountId || current.account_id}</code>
                          </span>
                        )}
                        {lastVerifiedStr && (
                          <span className="identity-verified-date">
                            Verified {lastVerifiedStr}
                          </span>
                        )}
                      </div>
                    </div>
                  ) : isTempUnavailable ? (
                    <div className="identity-temp-box" style={{ padding: '8px', borderRadius: '6px', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', fontSize: '12px', display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <Clock size={13} style={{ flexShrink: 0 }} />
                      <span>{current?.statusReason || current?.status_reason || 'Verification temporarily unavailable. Stored credentials preserved.'}</span>
                    </div>
                  ) : isProblematic ? (
                    <div className="identity-error-box">
                      <AlertCircle size={14} className="text-amber-500 flex-shrink-0" />
                      <div className="identity-error-text">
                        <span className="error-title">
                          {isExpired ? 'Token Expired' : isReauthRequired ? 'Reauthorization Required' : 'Verification Issue'}
                        </span>
                        <span className="error-subtitle">
                          {current?.statusReason || current?.status_reason || (accountIdentifier ? `${accountIdentifier} — credentials expired or invalid. Reconnect or verify.` : 'Credentials expired or invalid. Reconnect or verify.')}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="identity-disconnected-box">
                      <span className="text-xs text-slate-400">
                        Account not linked. Connect to enable autonomous multi-channel publishing.
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="platform-card-footer">
                {isConnected ? (
                  <div className="connected-btn-group">
                    <button
                      type="button"
                      onClick={() => handleRefresh(def.id)}
                      disabled={isActionLoading}
                      className="btn-card-verify"
                      title="Re-verify credentials against platform API"
                    >
                      <RefreshCw size={13} className={isActionLoading ? 'animate-spin' : ''} />
                      <span>{isActionLoading ? 'Verifying...' : 'Verify'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => promptDisconnect(def.id, def.name, accountIdentifier || def.name)}
                      disabled={isActionLoading}
                      className="btn-card-disconnect"
                      title="Disconnect and revoke stored credentials"
                    >
                      <LogOut size={13} />
                      <span>Disconnect</span>
                    </button>
                  </div>
                ) : isProblematic ? (
                  <div className="error-btn-group">
                    <button
                      type="button"
                      onClick={() => handleRefresh(def.id)}
                      disabled={isActionLoading}
                      className="btn-card-verify"
                      title="Re-verify credentials against platform API"
                    >
                      <RefreshCw size={13} className={isActionLoading ? 'animate-spin' : ''} />
                      <span>{isActionLoading ? 'Verifying...' : 'Verify'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (def.type === 'modal') {
                          setModalError(null);
                          setActiveModal(def.id as 'bluesky' | 'linkedin');
                        } else if (def.type === 'pinterest_oauth') {
                          handleConnectOAuth('pinterest');
                        } else if (def.type === 'youtube_oauth') {
                          handleConnectOAuth('youtube');
                        } else {
                          handleConnectOAuth(def.id as 'facebook' | 'instagram');
                        }
                      }}
                      disabled={isActionLoading}
                      className="btn-card-reconnect"
                      title="Re-authenticate with platform"
                    >
                      <Key size={13} />
                      <span>Reconnect</span>
                    </button>
                  </div>
                ) : isTempUnavailable ? (
                  <div className="connected-btn-group">
                    <button
                      type="button"
                      onClick={() => handleRefresh(def.id)}
                      disabled={isActionLoading}
                      className="btn-card-verify"
                      title="Re-verify credentials against platform API"
                    >
                      <RefreshCw size={13} className={isActionLoading ? 'animate-spin' : ''} />
                      <span>{isActionLoading ? 'Retrying...' : 'Retry Verify'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => promptDisconnect(def.id, def.name, accountIdentifier || def.name)}
                      disabled={isActionLoading}
                      className="btn-card-disconnect"
                      title="Disconnect and revoke stored credentials"
                    >
                      <LogOut size={13} />
                      <span>Disconnect</span>
                    </button>
                  </div>
                ) : (
                  <div className="disconnected-btn-group">
                    {def.type === 'meta_oauth' ? (
                      <button
                        type="button"
                        onClick={() => handleConnectOAuth(def.id as 'facebook' | 'instagram')}
                        disabled={isActionLoading}
                        className="btn-card-connect-meta"
                      >
                        {isActionLoading ? (
                          <>
                            <RefreshCw size={13} className="animate-spin" />
                            <span>Connecting...</span>
                          </>
                        ) : (
                          <>
                            <Globe size={14} />
                            <span>Connect with Meta</span>
                          </>
                        )}
                      </button>
                    ) : def.type === 'pinterest_oauth' ? (
                      <button
                        type="button"
                        onClick={() => handleConnectOAuth('pinterest')}
                        disabled={isActionLoading}
                        className="btn-card-connect-pinterest"
                      >
                        {isActionLoading ? (
                          <>
                            <RefreshCw size={13} className="animate-spin" />
                            <span>Connecting...</span>
                          </>
                        ) : (
                          <>
                            <PlatformIcon platform="pinterest" size={15} />
                            <span>Connect Pinterest</span>
                          </>
                        )}
                      </button>
                    ) : def.type === 'youtube_oauth' ? (
                      <button
                        type="button"
                        onClick={() => handleConnectOAuth('youtube')}
                        disabled={isActionLoading}
                        className="btn-card-connect-youtube"
                      >
                        {isActionLoading ? (
                          <>
                            <RefreshCw size={13} className="animate-spin" />
                            <span>Connecting...</span>
                          </>
                        ) : (
                          <>
                            <PlatformIcon platform="youtube" size={15} />
                            <span>Connect YouTube</span>
                          </>
                        )}
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          setModalError(null);
                          setActiveModal(def.id as 'bluesky' | 'linkedin');
                        }}
                        disabled={isActionLoading}
                        className="btn-card-connect-standard"
                      >
                        <Key size={13} />
                        <span>Connect {def.name}</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* =========================================================================
          MODAL: DISCONNECT CONFIRMATION
          ========================================================================= */}
      {disconnectTarget && (
        <div className="modal-overlay" onClick={() => !actionLoading[disconnectTarget.id] && setDisconnectTarget(null)}>
          <div className="modal-card modal-card-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-wrap">
                <AlertTriangle size={20} className="text-amber-500" />
                <h3>Disconnect {disconnectTarget.name}?</h3>
              </div>
              <button
                type="button"
                onClick={() => setDisconnectTarget(null)}
                className="modal-close-btn"
                disabled={Boolean(actionLoading[disconnectTarget.id])}
              >
                <X size={18} />
              </button>
            </div>

            <div className="modal-body">
              <p className="modal-instructions">
                Are you sure you want to disconnect <strong>{disconnectTarget.handle}</strong>?
                Encrypted credentials stored in Supabase will be permanently deleted. Scheduled posts targeting this platform will be paused.
              </p>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                onClick={() => setDisconnectTarget(null)}
                disabled={Boolean(actionLoading[disconnectTarget.id])}
                className="btn-modal-cancel"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={executeDisconnect}
                disabled={Boolean(actionLoading[disconnectTarget.id])}
                className="btn-modal-danger"
              >
                {actionLoading[disconnectTarget.id] ? 'Disconnecting...' : 'Yes, Disconnect'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL: BLUESKY CREDENTIALS
          ========================================================================= */}
      {activeModal === 'bluesky' && (
        <div className="modal-overlay" onClick={() => !modalSubmitting && setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-wrap">
                <PlatformIcon platform="bluesky" size={22} />
                <h3>Connect Bluesky Account</h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="modal-close-btn"
                disabled={modalSubmitting}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmitBluesky} className="modal-body">
              <p className="modal-instructions">
                Enter your Bluesky handle and an App Password. Passwords are encrypted with authenticated AES encryption and stored securely on the backend.
              </p>

              {modalError && (
                <div className="modal-error-box">
                  <AlertCircle size={15} />
                  <span>{modalError}</span>
                </div>
              )}

              <div className="modal-field">
                <label htmlFor="bsky-handle">Bluesky Handle</label>
                <input
                  id="bsky-handle"
                  type="text"
                  placeholder="e.g. username.bsky.social"
                  value={blueskyHandle}
                  onChange={(e) => setBlueskyHandle(e.target.value)}
                  required
                  autoFocus
                />
              </div>

              <div className="modal-field">
                <div className="label-with-link">
                  <label htmlFor="bsky-pwd">App Password</label>
                  <a
                    href="https://bsky.app/settings/app-passwords"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="modal-helper-link"
                  >
                    Generate App Password <ExternalLink size={11} />
                  </a>
                </div>
                <input
                  id="bsky-pwd"
                  type="password"
                  placeholder="xxxx-xxxx-xxxx-xxxx"
                  value={blueskyPassword}
                  onChange={(e) => setBlueskyPassword(e.target.value)}
                  required
                />
                <span className="field-hint">
                  Use an App Password rather than your primary account password for security.
                </span>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  disabled={modalSubmitting}
                  className="btn-modal-cancel"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalSubmitting}
                  className="btn-modal-submit"
                >
                  {modalSubmitting ? 'Verifying...' : 'Verify & Connect'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL: LINKEDIN CREDENTIALS
          ========================================================================= */}
      {activeModal === 'linkedin' && (
        <div className="modal-overlay" onClick={() => !modalSubmitting && setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-wrap">
                <PlatformIcon platform="linkedin" size={22} />
                <h3>Connect LinkedIn Account</h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="modal-close-btn"
                disabled={modalSubmitting}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmitLinkedIn} className="modal-body">
              <p className="modal-instructions">
                Provide your LinkedIn OAuth 2.0 Bearer access token. OmniPulse verifies access with LinkedIn and encrypts the token at rest.
              </p>

              {modalError && (
                <div className="modal-error-box">
                  <AlertCircle size={15} />
                  <span>{modalError}</span>
                </div>
              )}

              <div className="modal-field">
                <div className="label-with-link">
                  <label htmlFor="li-token">LinkedIn Access Token</label>
                  <a
                    href="https://www.linkedin.com/developers/tools/oauth"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="modal-helper-link"
                  >
                    LinkedIn Token Generator <ExternalLink size={11} />
                  </a>
                </div>
                <input
                  id="li-token"
                  type="password"
                  placeholder="AQ..."
                  value={linkedinToken}
                  onChange={(e) => setLinkedinToken(e.target.value)}
                  required
                  autoFocus
                />
                <span className="field-hint">
                  Requires <code>w_member_social</code> scope.
                </span>
              </div>

              <div className="modal-field">
                <label htmlFor="li-urn">Author URN (Optional)</label>
                <input
                  id="li-urn"
                  type="text"
                  placeholder="urn:li:person:... (auto-resolved if left empty)"
                  value={linkedinUrn}
                  onChange={(e) => setLinkedinUrn(e.target.value)}
                />
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  disabled={modalSubmitting}
                  className="btn-modal-cancel"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalSubmitting}
                  className="btn-modal-submit"
                >
                  {modalSubmitting ? 'Verifying...' : 'Verify & Connect'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
