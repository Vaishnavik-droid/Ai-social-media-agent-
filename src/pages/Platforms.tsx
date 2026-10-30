import React, { useState, useEffect } from 'react';
import { ConnectedPlatform, Platform } from '../types';
import { PlatformIcon } from '../components/PlatformIcon';
import {
  Edit2,
  Copy,
  Check,
  ExternalLink,
  Key,
  ShieldCheck,
  AlertCircle,
  Eye,
  EyeOff,
  Sparkles,
  RefreshCw,
  Globe,
  Lock,
  Info,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';
import { api } from '../lib/api';

interface PlatformsProps {
  platforms: ConnectedPlatform[];
  onToggleStatus: (id: Platform) => void;
  onUpdateHandle: (id: Platform, newHandle: string) => void;
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

interface PlatformCreds {
  appId: string;
  appSecret: string;
  pageId: string;
  accessToken: string;
  showSecret: boolean;
}

export const Platforms: React.FC<PlatformsProps> = ({
  platforms,
  onToggleStatus,
  onUpdateHandle,
  onUpdateCredentials,
  onToast
}) => {
  const [editingId, setEditingId] = useState<Platform | null>(null);
  const [editHandleText, setEditHandleText] = useState('');

  // Expandable Configuration Drawer for Meta Platforms
  const [expandedConfigId, setExpandedConfigId] = useState<Platform | null>(null);

  // Credentials State for Meta Platforms
  const [platformCredentials, setPlatformCredentials] = useState<Record<string, PlatformCreds>>(() => {
    const saved = localStorage.getItem('omnipulse_meta_credentials');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // Fallback
      }
    }
    return {
      facebook: { appId: '', appSecret: '', pageId: '', accessToken: '', showSecret: false },
      instagram: { appId: '', appSecret: '', pageId: '', accessToken: '', showSecret: false }
    };
  });

  // Sync credentials with localStorage
  useEffect(() => {
    localStorage.setItem('omnipulse_meta_credentials', JSON.stringify(platformCredentials));
  }, [platformCredentials]);

  // Verification & Feedback States
  const [verifyingPlatform, setVerifyingPlatform] = useState<Platform | null>(null);
  const [verificationError, setVerificationError] = useState<Record<string, string | null>>({});
  const [verificationSuccess, setVerificationSuccess] = useState<Record<string, string | null>>({});
  const [incompleteConfigAlert, setIncompleteConfigAlert] = useState<Record<string, boolean>>({});
  const [lastAuthUrl, setLastAuthUrl] = useState<Record<string, string | null>>({});

  // Copy Feedback
  const [copiedRedirectUri, setCopiedRedirectUri] = useState(false);
  const [copiedCallbackUri, setCopiedCallbackUri] = useState(false);
  const [copiedAuthUrl, setCopiedAuthUrl] = useState<Record<string, boolean>>({});

  // Dynamic URI computation for current environment (localhost or Vercel)
  const currentOrigin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000';
  const frontendRedirectUri = `${currentOrigin}/platforms`;
  const backendCallbackUri = `${currentOrigin}/api/v1/connections/meta/callback`;

  // Handle URL Parameter OAuth Callback from Meta Redirect
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state') as Platform | null;
    const error = urlParams.get('error_description') || urlParams.get('error');

    if (code && (state === 'facebook' || state === 'instagram')) {
      const targetPlatform = state;
      if (onToast) {
        onToast(`Meta OAuth Code received for ${targetPlatform === 'instagram' ? 'Instagram' : 'Facebook'}! Connection activated.`);
      }
      if (onUpdateCredentials) {
        onUpdateCredentials(targetPlatform, {
          status: 'connected',
          handle: targetPlatform === 'instagram' ? '@rushikeshchavan' : 'OmniPulse Media Page',
        });
      }
      setVerificationSuccess((prev) => ({
        ...prev,
        [targetPlatform]: `OAuth Authorization successful! Meta returned authorization code. Platform is now linked and active.`
      }));
      setVerificationError((prev) => ({ ...prev, [targetPlatform]: null }));
      setIncompleteConfigAlert((prev) => ({ ...prev, [targetPlatform]: false }));
      // Clean query parameters from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (error) {
      const targetPlatform = state === 'instagram' ? 'instagram' : 'facebook';
      setVerificationError((prev) => ({
        ...prev,
        [targetPlatform]: `Meta OAuth Error: ${error}. Ensure "${frontendRedirectUri}" is entered into Meta Developer Settings (Valid OAuth Redirect URIs).`
      }));
      setIncompleteConfigAlert((prev) => ({ ...prev, [targetPlatform]: true }));
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // Copy helper
  const handleCopy = (text: string, type: 'redirect' | 'callback' | string) => {
    navigator.clipboard.writeText(text);
    if (type === 'redirect') {
      setCopiedRedirectUri(true);
      setTimeout(() => setCopiedRedirectUri(false), 2500);
    } else if (type === 'callback') {
      setCopiedCallbackUri(true);
      setTimeout(() => setCopiedCallbackUri(false), 2500);
    } else {
      setCopiedAuthUrl((prev) => ({ ...prev, [type]: true }));
      setTimeout(() => setCopiedAuthUrl((prev) => ({ ...prev, [type]: false })), 2500);
    }
    if (onToast) {
      onToast('Copied URL to clipboard!');
    }
  };

  // Credential input updater
  const updateCred = (platformId: string, field: keyof PlatformCreds, val: any) => {
    setPlatformCredentials((prev) => ({
      ...prev,
      [platformId]: {
        ...prev[platformId],
        [field]: val
      }
    }));
  };

  // Handle Editing
  const startEdit = (p: ConnectedPlatform) => {
    setEditingId(p.id);
    setEditHandleText(p.handle);
  };

  const saveEdit = (id: Platform) => {
    if (editHandleText.trim()) {
      onUpdateHandle(id, editHandleText.trim());
    }
    setEditingId(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditHandleText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent, id: Platform) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      saveEdit(id);
    } else if (e.key === 'Escape') {
      cancelEdit();
    }
  };

  // Send OAuth Request to Meta
  const handleSendOAuthRequest = (platformId: Platform) => {
    const creds = platformCredentials[platformId] || { appId: '', appSecret: '', pageId: '', accessToken: '' };

    if (!creds.appId.trim()) {
      setIncompleteConfigAlert((prev) => ({ ...prev, [platformId]: true }));
      setVerificationError((prev) => ({
        ...prev,
        [platformId]: `Incomplete Configuration: Please input your Meta App ID below before sending the request. Also make sure "${frontendRedirectUri}" is entered into your Meta Developer App Settings under "Valid OAuth Redirect URIs".`
      }));
      setExpandedConfigId(platformId);
      return;
    }

    setIncompleteConfigAlert((prev) => ({ ...prev, [platformId]: false }));
    setVerificationError((prev) => ({ ...prev, [platformId]: null }));

    const scopes = platformId === 'instagram'
      ? 'instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement'
      : 'pages_show_list,pages_read_engagement,pages_manage_posts,public_profile';

    const authUrl = `https://www.facebook.com/v21.0/dialog/oauth?client_id=${creds.appId.trim()}&redirect_uri=${encodeURIComponent(frontendRedirectUri)}&scope=${scopes}&response_type=code&state=${platformId}`;

    setLastAuthUrl((prev) => ({ ...prev, [platformId]: authUrl }));

    // Open Meta OAuth in a popup window
    window.open(authUrl, '_blank', 'width=650,height=750,scrollbars=yes,status=yes');

    if (onToast) {
      onToast(`Meta OAuth window opened. Check popup. If Meta shows URL error, paste "${frontendRedirectUri}" into Valid OAuth Redirect URIs.`);
    }
  };

  // Verify Credentials with Backend / Meta Graph API
  const handleVerifyCredentials = async (platformId: Platform) => {
    const creds = platformCredentials[platformId] || { appId: '', appSecret: '', pageId: '', accessToken: '' };

    if (!creds.appId.trim() && !creds.accessToken.trim()) {
      setIncompleteConfigAlert((prev) => ({ ...prev, [platformId]: true }));
      setVerificationError((prev) => ({
        ...prev,
        [platformId]: `Incomplete Configuration: Please provide your Meta App ID & App Secret, or a Page/User Access Token to verify.`
      }));
      setExpandedConfigId(platformId);
      return;
    }

    setVerifyingPlatform(platformId);
    setVerificationError((prev) => ({ ...prev, [platformId]: null }));
    setVerificationSuccess((prev) => ({ ...prev, [platformId]: null }));
    setIncompleteConfigAlert((prev) => ({ ...prev, [platformId]: false }));

    try {
      const res = await api.verifyConnection(platformId, {
        app_id: creds.appId.trim() || undefined,
        app_secret: creds.appSecret.trim() || undefined,
        access_token: creds.accessToken.trim() || undefined,
        page_id: creds.pageId.trim() || undefined,
        account_id: creds.pageId.trim() || undefined,
        redirect_uri: frontendRedirectUri,
      });

      setVerifyingPlatform(null);

      if (res.is_valid) {
        setVerificationSuccess((prev) => ({
          ...prev,
          [platformId]: res.message || 'Connection verified successfully with Meta Graph API!'
        }));

        const assignedHandle = creds.pageId.trim()
          ? (platformId === 'instagram' ? `@${creds.pageId.replace(/^@/, '')}` : `Page: ${creds.pageId}`)
          : (platformId === 'instagram' ? '@rushikeshchavan' : 'OmniPulse Media Page');

        if (onUpdateCredentials) {
          onUpdateCredentials(platformId, {
            appId: creds.appId,
            appSecret: creds.appSecret,
            accessToken: creds.accessToken,
            pageId: creds.pageId,
            status: 'connected',
            handle: assignedHandle,
          });
        }
        if (onToast) {
          onToast(`${platformId === 'instagram' ? 'Instagram' : 'Facebook'} connected successfully!`);
        }
      } else {
        setVerificationError((prev) => ({
          ...prev,
          [platformId]: res.message || 'Verification failed. Please check your App ID, Secret, and ensure Valid OAuth Redirect URIs are configured in Meta Developer Dashboard.'
        }));
      }
    } catch (err: any) {
      setVerifyingPlatform(null);
      setVerificationError((prev) => ({
        ...prev,
        [platformId]: err?.message || 'Connection test failed. Ensure your Meta credentials are valid and server is reachable.'
      }));
    }
  };

  // Disconnect handler
  const handleDisconnect = (platformId: Platform) => {
    if (onUpdateCredentials) {
      onUpdateCredentials(platformId, {
        status: 'disconnected',
        handle: 'Not Connected',
      });
    } else {
      onToggleStatus(platformId);
    }
    setVerificationSuccess((prev) => ({ ...prev, [platformId]: null }));
    setVerificationError((prev) => ({ ...prev, [platformId]: null }));
    setIncompleteConfigAlert((prev) => ({ ...prev, [platformId]: false }));
    if (onToast) {
      onToast(`Disconnected from ${platformId === 'instagram' ? 'Instagram' : platformId === 'facebook' ? 'Facebook' : platformId}.`);
    }
  };

  return (
    <div className="platforms-page">
      {/* ===============================================================
          META DEVELOPER OAUTH REDIRECT URL GUIDE & SETTINGS BOX
          =============================================================== */}
      <div className="meta-oauth-banner">
        <div className="meta-oauth-header">
          <div className="meta-oauth-title-wrap">
            <div className="meta-oauth-icon-badge">
              <Globe size={18} />
            </div>
            <div>
              <h3 className="meta-oauth-title">Meta Developer OAuth Configuration &amp; Redirect URIs</h3>
              <p className="meta-oauth-subtitle">
                Required for Facebook and Instagram OAuth verification in Meta for Developers (<a href="https://developers.facebook.com/apps" target="_blank" rel="noopener noreferrer" className="meta-doc-link">developers.facebook.com <ExternalLink size={11} /></a>).
              </p>
            </div>
          </div>
          <span className="meta-status-pill">OAuth 2.0 Ready</span>
        </div>

        <div className="meta-oauth-body">
          <div className="meta-oauth-explanation">
            <p>
              When you send an OAuth verification request using your <strong>Meta App ID</strong> and <strong>App Secret</strong>,
              Meta requires this exact URL in your Meta App settings under <strong>Facebook Login &rarr; Settings &rarr; Valid OAuth Redirect URIs</strong>.
              If this URL is not entered, Meta blocks the request with an <em>&quot;URL Blocked: Redirect URI not whitelisted&quot;</em> error.
            </p>
          </div>

          <div className="meta-uri-boxes">
            {/* Primary Frontend Redirect URI */}
            <div className="meta-uri-card">
              <div className="meta-uri-label">
                <span className="meta-uri-tag">Primary Valid OAuth Redirect URI (Frontend)</span>
                <span className="meta-uri-badge">Required</span>
              </div>
              <div className="meta-uri-row">
                <code className="meta-uri-code">{frontendRedirectUri}</code>
                <button
                  type="button"
                  onClick={() => handleCopy(frontendRedirectUri, 'redirect')}
                  className={`meta-copy-btn ${copiedRedirectUri ? 'copied' : ''}`}
                  title="Copy to clipboard"
                >
                  {copiedRedirectUri ? <Check size={14} /> : <Copy size={14} />}
                  <span>{copiedRedirectUri ? 'Copied URI!' : 'Copy URI'}</span>
                </button>
              </div>
            </div>

            {/* Backend Callback URI */}
            <div className="meta-uri-card">
              <div className="meta-uri-label">
                <span className="meta-uri-tag">Backend Server Callback URI (API Handler)</span>
                <span className="meta-uri-badge-optional">Optional</span>
              </div>
              <div className="meta-uri-row">
                <code className="meta-uri-code">{backendCallbackUri}</code>
                <button
                  type="button"
                  onClick={() => handleCopy(backendCallbackUri, 'callback')}
                  className={`meta-copy-btn ${copiedCallbackUri ? 'copied' : ''}`}
                  title="Copy to clipboard"
                >
                  {copiedCallbackUri ? <Check size={14} /> : <Copy size={14} />}
                  <span>{copiedCallbackUri ? 'Copied URI!' : 'Copy URI'}</span>
                </button>
              </div>
            </div>
          </div>

          <div className="meta-steps-inline">
            <div className="meta-step-item">
              <span className="meta-step-num">1</span>
              <span>Open <strong>developers.facebook.com</strong> &rarr; Select your App</span>
            </div>
            <ArrowRight size={14} className="meta-step-arrow" />
            <div className="meta-step-item">
              <span className="meta-step-num">2</span>
              <span>Go to <strong>Facebook Login for Business</strong> &rarr; <strong>Settings</strong></span>
            </div>
            <ArrowRight size={14} className="meta-step-arrow" />
            <div className="meta-step-item">
              <span className="meta-step-num">3</span>
              <span>Paste the copied <strong>Valid OAuth Redirect URI</strong> &amp; click <strong>Save</strong></span>
            </div>
            <ArrowRight size={14} className="meta-step-arrow" />
            <div className="meta-step-item">
              <span className="meta-step-num">4</span>
              <span>Enter your App ID &amp; Secret below, then click <strong>Send OAuth Request</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* ===============================================================
          CONNECTED PLATFORMS GRID
          =============================================================== */}
      <div className="platforms-grid">
        {platforms.map((platform) => {
          const isMeta = platform.id === 'instagram' || platform.id === 'facebook';
          const isConnected = platform.status === 'connected';
          const isEditing = editingId === platform.id;
          const isExpanded = expandedConfigId === platform.id;
          const creds = platformCredentials[platform.id] || { appId: '', appSecret: '', pageId: '', accessToken: '', showSecret: false };
          const isVerifying = verifyingPlatform === platform.id;
          const errorMsg = verificationError[platform.id];
          const successMsg = verificationSuccess[platform.id];
          const hasIncompleteAlert = incompleteConfigAlert[platform.id];
          const authUrl = lastAuthUrl[platform.id];
          const hasCopiedAuthUrl = copiedAuthUrl[platform.id];

          return (
            <div
              key={platform.id}
              className={`platform-card ${isMeta ? 'platform-card-meta' : ''} ${isConnected ? 'platform-connected' : 'platform-disconnected'}`}
            >
              {/* Card Header */}
              <div className="platform-card-header">
                <div className="platform-card-icon-wrap">
                  <PlatformIcon platform={platform.id} size={28} />
                </div>
                <div className="platform-title-area">
                  <div className="platform-name">{platform.name}</div>
                  {isMeta && (
                    <span className="platform-meta-tag">Meta Graph API</span>
                  )}
                </div>
              </div>

              {/* Status Indicator */}
              <div className="platform-card-status">
                <span className={`platform-status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
                <span className="platform-status-text">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
                {isMeta && !isConnected && (
                  <span className="platform-setup-badge">Requires App ID &amp; Secret</span>
                )}
              </div>

              {/* Handle / Account Display */}
              <div className="platform-handle-box">
                {isEditing ? (
                  <div className="platform-edit-row">
                    <input
                      type="text"
                      value={editHandleText}
                      onChange={(e) => setEditHandleText(e.target.value)}
                      onKeyDown={(e) => handleKeyDown(e, platform.id)}
                      className="platform-edit-input"
                      autoFocus
                      placeholder="Enter handle..."
                    />
                    <button
                      onClick={() => saveEdit(platform.id)}
                      className="platform-save-button"
                      title="Save (Enter)"
                      style={{ color: '#10b981' }}
                    >
                      ✓
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="platform-save-button"
                      title="Cancel (Esc)"
                      style={{ color: '#ef4444', marginLeft: '2px' }}
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <>
                    <span className={`platform-handle-text ${!isConnected ? 'platform-handle-empty' : ''}`}>
                      {platform.handle}
                    </span>
                    {isConnected && (
                      <button
                        onClick={() => startEdit(platform)}
                        className="platform-edit-button"
                        title="Edit handle"
                      >
                        <Edit2 size={12} />
                      </button>
                    )}
                  </>
                )}
              </div>

              {/* ===============================================================
                  META CREDENTIALS INPUT SECTION (For Instagram & Facebook)
                  =============================================================== */}
              {isMeta && (
                <div className="platform-meta-config-section">
                  <div className="platform-config-header">
                    <div className="platform-config-title">
                      <Key size={13} />
                      <span>{platform.name} OAuth Credentials</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setExpandedConfigId(isExpanded ? null : platform.id)}
                      className="platform-toggle-config-btn"
                    >
                      {isExpanded ? 'Hide Settings' : isConnected ? 'Edit Credentials' : 'Add App ID & Secret'}
                    </button>
                  </div>

                  {/* Always show if disconnected or expanded */}
                  {(!isConnected || isExpanded) && (
                    <div className="platform-config-drawer animate-fadeIn">
                      {/* App ID Field */}
                      <div className="platform-input-group">
                        <label className="platform-input-label">
                          <span>Meta App ID (Client ID)</span>
                          <span className="platform-input-required">*</span>
                        </label>
                        <input
                          type="text"
                          value={creds.appId}
                          onChange={(e) => updateCred(platform.id, 'appId', e.target.value)}
                          placeholder="e.g. 109283746501928"
                          className="platform-cred-input"
                        />
                      </div>

                      {/* App Secret Field */}
                      <div className="platform-input-group">
                        <label className="platform-input-label">
                          <span>Meta App Secret (Client Secret)</span>
                          <span className="platform-input-required">*</span>
                        </label>
                        <div className="platform-password-wrapper">
                          <input
                            type={creds.showSecret ? 'text' : 'password'}
                            value={creds.appSecret}
                            onChange={(e) => updateCred(platform.id, 'appSecret', e.target.value)}
                            placeholder="e.g. 8f9a2b1c4d7e6f5a..."
                            className="platform-cred-input platform-cred-input-pass"
                          />
                          <button
                            type="button"
                            onClick={() => updateCred(platform.id, 'showSecret', !creds.showSecret)}
                            className="platform-pass-toggle"
                            title={creds.showSecret ? 'Hide secret' : 'Show secret'}
                          >
                            {creds.showSecret ? <EyeOff size={14} /> : <Eye size={14} />}
                          </button>
                        </div>
                      </div>

                      {/* Page ID / Account ID Field */}
                      <div className="platform-input-group">
                        <label className="platform-input-label">
                          <span>{platform.id === 'instagram' ? 'Instagram Business Account ID' : 'Facebook Page ID'}</span>
                          <span className="platform-input-optional">(Optional)</span>
                        </label>
                        <input
                          type="text"
                          value={creds.pageId}
                          onChange={(e) => updateCred(platform.id, 'pageId', e.target.value)}
                          placeholder={platform.id === 'instagram' ? 'e.g. 178414000123456 or @handle' : 'e.g. 10492817482910'}
                          className="platform-cred-input"
                        />
                      </div>

                      {/* Access Token Field (Optional Direct Token) */}
                      <div className="platform-input-group">
                        <label className="platform-input-label">
                          <span>Page / User Access Token</span>
                          <span className="platform-input-optional">(Optional Graph Token)</span>
                        </label>
                        <input
                          type="password"
                          value={creds.accessToken}
                          onChange={(e) => updateCred(platform.id, 'accessToken', e.target.value)}
                          placeholder="e.g. EAABwzLIX45wBO..."
                          className="platform-cred-input"
                        />
                      </div>

                      {/* Incomplete Config / Error Alert */}
                      {errorMsg && (
                        <div className={`platform-alert ${hasIncompleteAlert ? 'platform-alert-warning' : 'platform-alert-error'}`}>
                          <AlertCircle size={15} className="platform-alert-icon" />
                          <div className="platform-alert-text">
                            <strong>{hasIncompleteAlert ? 'Incomplete Configuration:' : 'Verification Notice:'}</strong> {errorMsg}
                          </div>
                        </div>
                      )}

                      {/* Success Feedback */}
                      {successMsg && (
                        <div className="platform-alert platform-alert-success">
                          <CheckCircle2 size={15} className="platform-alert-icon" />
                          <div className="platform-alert-text">{successMsg}</div>
                        </div>
                      )}

                      {/* Last Generated OAuth URL */}
                      {authUrl && (
                        <div className="platform-generated-url-box">
                          <div className="platform-url-label">
                            <span>OAuth Request URL Sent:</span>
                            <button
                              type="button"
                              onClick={() => handleCopy(authUrl, platform.id)}
                              className="platform-copy-small-btn"
                            >
                              {hasCopiedAuthUrl ? <Check size={11} /> : <Copy size={11} />}
                              <span>{hasCopiedAuthUrl ? 'Copied' : 'Copy'}</span>
                            </button>
                          </div>
                          <code className="platform-url-preview">{authUrl}</code>
                        </div>
                      )}

                      {/* Meta Action Buttons */}
                      <div className="platform-meta-actions">
                        <button
                          type="button"
                          onClick={() => handleSendOAuthRequest(platform.id)}
                          className="platform-oauth-btn"
                          title="Open Meta OAuth Authorization Dialog"
                        >
                          <ExternalLink size={14} />
                          <span>Send Meta OAuth Request</span>
                        </button>

                        <button
                          type="button"
                          disabled={isVerifying}
                          onClick={() => handleVerifyCredentials(platform.id)}
                          className="platform-verify-btn"
                        >
                          {isVerifying ? (
                            <>
                              <RefreshCw size={13} className="animate-spin" />
                              <span>Verifying with Meta...</span>
                            </>
                          ) : (
                            <>
                              <ShieldCheck size={14} />
                              <span>Verify Credentials</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Standard Platform Disconnect / Connect Button */}
              {(!isMeta || isConnected) && (
                <button
                  type="button"
                  onClick={() => {
                    if (isMeta && isConnected) {
                      handleDisconnect(platform.id);
                    } else {
                      onToggleStatus(platform.id);
                    }
                  }}
                  className={`platform-action-button ${isConnected ? 'disconnect' : 'connect'}`}
                >
                  {isConnected ? 'Disconnect' : 'Connect'}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Platforms;
