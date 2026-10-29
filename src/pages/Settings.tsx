import React, { useState } from 'react';
import { User, Sliders, Bell, CheckCircle2, LogOut, Building2, ShieldCheck } from 'lucide-react';
import {
  UserProfile,
  UserPreferences,
  UserNotifications
} from '../types';

interface SettingsProps {
  user: UserProfile;
  preferences: UserPreferences;
  notifications: UserNotifications;
  onUpdateUser: (user: UserProfile) => void;
  onUpdatePreferences: (pref: UserPreferences) => void;
  onUpdateNotifications: (notif: UserNotifications) => void;
  onLogout?: () => void;
}

export const Settings: React.FC<SettingsProps> = ({
  user,
  preferences,
  notifications,
  onUpdateUser,
  onUpdatePreferences,
  onUpdateNotifications,
  onLogout
}) => {
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'notifications'>(
    'profile'
  );

  // Profile Form state
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [brandName, setBrandName] = useState(user.brandName || '');
  const [isProfileSaved, setIsProfileSaved] = useState(false);

  // Preferences Form state
  const [prefState, setPrefState] = useState<UserPreferences>(preferences);
  const [isPrefSaved, setIsPrefSaved] = useState(false);

  // Notifications Form state
  const [notifState, setNotifState] = useState<UserNotifications>(notifications);
  const [isNotifSaved, setIsNotifSaved] = useState(false);

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdateUser({
      ...user,
      name,
      email,
      brandName: brandName.trim(),
      avatarChar: name.trim().charAt(0).toUpperCase() || 'R'
    });
    setIsProfileSaved(true);
    setTimeout(() => setIsProfileSaved(false), 2500);
  };

  const handlePrefSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdatePreferences(prefState);
    setIsPrefSaved(true);
    setTimeout(() => setIsPrefSaved(false), 2500);
  };

  const handleNotifSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdateNotifications(notifState);
    setIsNotifSaved(true);
    setTimeout(() => setIsNotifSaved(false), 2500);
  };

  return (
    <div className="settings-page">
      <div className="settings-layout">
        <nav className="settings-nav" aria-label="Settings navigation">
          <button
            type="button"
            onClick={() => setActiveTab('profile')}
            className={`settings-nav-item ${activeTab === 'profile' ? 'active' : ''}`}
          >
            <User size={14} />
            <span>Profile</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('preferences')}
            className={`settings-nav-item ${activeTab === 'preferences' ? 'active' : ''}`}
          >
            <Sliders size={14} />
            <span>Preferences</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('notifications')}
            className={`settings-nav-item ${activeTab === 'notifications' ? 'active' : ''}`}
          >
            <Bell size={14} />
            <span>Notifications</span>
          </button>
        </nav>

        <div className="settings-content-card">
          {activeTab === 'profile' && (
            <form onSubmit={handleProfileSubmit} className="settings-form">
              <h2 className="settings-section-title">Profile Information</h2>
              <p className="settings-section-copy">
                Update your personal info, workspace details, and manage your active login session.
              </p>

              <div className="settings-form-grid">
                <div className="settings-field">
                  <label htmlFor="profile-name">Full Name</label>
                  <input
                    id="profile-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>

                <div className="settings-field">
                  <label htmlFor="profile-email">Email Address</label>
                  <input
                    id="profile-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="settings-field full-width">
                  <label htmlFor="profile-brand">Workspace / Brand Name</label>
                  <input
                    id="profile-brand"
                    type="text"
                    value={brandName}
                    onChange={(e) => setBrandName(e.target.value)}
                    placeholder="e.g. Acme Media Corp"
                  />
                </div>
              </div>

              <div className="settings-form-actions">
                <button type="submit" className="settings-save-button">
                  Save Changes
                </button>
                {isProfileSaved && (
                  <span className="settings-success-message">
                    <CheckCircle2 size={13} />
                    <span>Profile updated dynamically!</span>
                  </span>
                )}
              </div>

              {/* Account Security & Session Management */}
              <div className="settings-security-card">
                <div className="settings-security-header">
                  <div className="settings-security-icon">
                    <ShieldCheck size={18} className="text-emerald-500" />
                  </div>
                  <div>
                    <h4 className="settings-security-title">Account Security & Session</h4>
                    <p className="settings-security-desc">
                      Currently authenticated as <strong>{user.email}</strong>.
                    </p>
                  </div>
                </div>

                {onLogout && (
                  <button
                    type="button"
                    onClick={onLogout}
                    className="settings-logout-action-btn"
                  >
                    <LogOut size={14} />
                    <span>Sign Out of OmniPulse</span>
                  </button>
                )}
              </div>
            </form>
          )}

          {activeTab === 'preferences' && (
            <form onSubmit={handlePrefSubmit} className="settings-form settings-form-compact">
              <h2 className="settings-section-title">Preferences</h2>
              <p className="settings-section-copy">
                Configure default post generation tone, auto-hashtag preferences, and scheduling behavior.
              </p>

              <div className="settings-option-list">
                <label className="settings-option-row">
                  <input
                    type="checkbox"
                    checked={prefState.autoSuggestTimes}
                    onChange={(e) =>
                      setPrefState({ ...prefState, autoSuggestTimes: e.target.checked })
                    }
                  />
                  <span>Auto-suggest optimal delivery times</span>
                </label>

                <label className="settings-option-row">
                  <input
                    type="checkbox"
                    checked={prefState.includeHashtags}
                    onChange={(e) =>
                      setPrefState({ ...prefState, includeHashtags: e.target.checked })
                    }
                  />
                  <span>Include AI-generated hashtags by default</span>
                </label>
              </div>

              <div className="settings-form-grid settings-form-grid-compact">
                <div className="settings-field">
                  <label htmlFor="pref-tone">Default Post Tone</label>
                  <select
                    id="pref-tone"
                    value={prefState.defaultTone}
                    onChange={(e) =>
                      setPrefState({ ...prefState, defaultTone: e.target.value })
                    }
                  >
                    <option value="Professional">Professional</option>
                    <option value="Casual">Casual</option>
                    <option value="Witty">Witty</option>
                    <option value="Inspiring">Inspiring</option>
                  </select>
                </div>

                <div className="settings-field">
                  <label htmlFor="pref-language">Default Language</label>
                  <select
                    id="pref-language"
                    value={prefState.defaultLanguage}
                    onChange={(e) =>
                      setPrefState({ ...prefState, defaultLanguage: e.target.value })
                    }
                  >
                    <option value="English">English</option>
                    <option value="Hindi">Hindi (हिंदी)</option>
                    <option value="Marathi">Marathi (मराठी)</option>
                    <option value="Spanish">Spanish</option>
                    <option value="French">French</option>
                    <option value="German">German</option>
                  </select>
                </div>
              </div>

              <div className="settings-form-actions">
                <button type="submit" className="settings-save-button">
                  Save Preferences
                </button>
                {isPrefSaved && (
                  <span className="settings-success-message">
                    <CheckCircle2 size={13} />
                    <span>Preferences saved!</span>
                  </span>
                )}
              </div>
            </form>
          )}

          {activeTab === 'notifications' && (
            <form onSubmit={handleNotifSubmit} className="settings-form settings-form-compact">
              <h2 className="settings-section-title">Notifications</h2>
              <p className="settings-section-copy">
                Receive updates when scheduled posts publish or encounter errors.
              </p>

              <div className="settings-option-list">
                <label className="settings-option-row">
                  <input
                    type="checkbox"
                    checked={notifState.emailSummary}
                    onChange={(e) =>
                      setNotifState({ ...notifState, emailSummary: e.target.checked })
                    }
                  />
                  <span>Email summary of daily posts</span>
                </label>

                <label className="settings-option-row">
                  <input
                    type="checkbox"
                    checked={notifState.failureAlerts}
                    onChange={(e) =>
                      setNotifState({ ...notifState, failureAlerts: e.target.checked })
                    }
                  />
                  <span>Alert on failed post publishing</span>
                </label>

                <label className="settings-option-row">
                  <input
                    type="checkbox"
                    checked={notifState.newFollowerAlerts}
                    onChange={(e) =>
                      setNotifState({ ...notifState, newFollowerAlerts: e.target.checked })
                    }
                  />
                  <span>Push alert on milestone audience growth</span>
                </label>
              </div>

              <div className="settings-form-actions">
                <button type="submit" className="settings-save-button">
                  Save Notifications
                </button>
                {isNotifSaved && (
                  <span className="settings-success-message">
                    <CheckCircle2 size={13} />
                    <span>Notification settings saved!</span>
                  </span>
                )}
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
