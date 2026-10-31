import { ErrorBoundary } from './components/ErrorBoundary';
import React, { useState, useEffect } from 'react';
import { Sidebar, NavPage } from './components/Sidebar';
import { Header } from './components/Header';
import { Dashboard } from './pages/Dashboard';
import { CreatePost } from './pages/CreatePost';
import { Posts } from './pages/Posts';
import { Scheduled } from './pages/Scheduled';
import { Platforms } from './pages/Platforms';
import { Settings } from './pages/Settings';
import { Auth } from './pages/Auth';
import { PrivacyPolicy } from './pages/PrivacyPolicy';
import { TermsOfService } from './pages/TermsOfService';
import { DataDeletion } from './pages/DataDeletion';
import { CheckCircle2 } from 'lucide-react';
import {
  mockPosts,
  mockConnectedPlatforms,
  mockMetrics,
  mockUserProfile,
  mockNotifications,
  mockUserPreferences,
  mockUserNotifications
} from './data/mockData';
import {
  SocialPost,
  ConnectedPlatform,
  Platform,
  UserProfile,
  NotificationItem,
  UserPreferences,
  UserNotifications
} from './types';
import { supabase } from './lib/supabase';
import { api } from './lib/api';

// Helper to determine active page from URL path or hash (crucial for Meta verification crawler & OAuth redirects)
const getPageFromUrl = (): NavPage | null => {
  if (typeof window === 'undefined') return null;
  const path = window.location.pathname.toLowerCase();
  const hash = window.location.hash.toLowerCase();
  const search = window.location.search.toLowerCase();

  // If returning with Meta OAuth callback parameters, always route to platforms
  if (search.includes('code=') || search.includes('state=facebook') || search.includes('state=instagram')) {
    return 'platforms';
  }

  if (path === '/privacy' || path === '/privacy-policy' || hash.includes('privacy')) {
    return 'privacy';
  }
  if (path === '/terms' || path === '/terms-of-service' || hash.includes('terms')) {
    return 'terms';
  }
  if (path === '/data-deletion' || path === '/user-data-deletion' || hash.includes('data-deletion')) {
    return 'data-deletion';
  }
  if (path === '/platforms' || hash.includes('platforms')) {
    return 'platforms';
  }
  if (path === '/create-post' || hash.includes('create-post')) {
    return 'create-post';
  }
  if (path === '/posts' || hash.includes('posts')) {
    return 'posts';
  }
  if (path === '/scheduled' || hash.includes('scheduled')) {
    return 'scheduled';
  }
  if (path === '/settings' || hash.includes('settings')) {
    return 'settings';
  }
  if (path === '/dashboard' || hash.includes('dashboard')) {
    return 'dashboard';
  }
  return null;
};

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<NavPage>(() => {
    return getPageFromUrl() || 'dashboard';
  });

  // Keep browser URL pathname synchronized
  const navigateTo = (page: NavPage) => {
    setCurrentPage(page);
    let targetPath = '/';
    if (page === 'privacy') targetPath = '/privacy';
    else if (page === 'terms') targetPath = '/terms';
    else if (page === 'data-deletion') targetPath = '/data-deletion';
    else if (page === 'platforms') targetPath = '/platforms';
    else if (page === 'create-post') targetPath = '/create-post';
    else if (page === 'posts') targetPath = '/posts';
    else if (page === 'scheduled') targetPath = '/scheduled';
    else if (page === 'settings') targetPath = '/settings';

    if (window.location.pathname !== targetPath) {
      window.history.pushState(null, '', targetPath);
    }
  };

  // Listen to browser forward/back buttons
  useEffect(() => {
    const handlePopState = () => {
      const page = getPageFromUrl();
      if (page) {
        setCurrentPage(page);
      } else {
        setCurrentPage('dashboard');
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    const search = window.location.search;
    if (search.includes('code=') || search.includes('state=facebook') || search.includes('state=instagram')) {
      return true;
    }
    const saved = localStorage.getItem('ai_social_authenticated');
    return saved === 'true';
  });

  // Sync session with Supabase on mount and listen to auth events
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        const metadata = session.user.user_metadata || {};
        const fullName = metadata.full_name || session.user.email?.split('@')[0] || 'John Doe';
        setUser({
          name: fullName,
          email: session.user.email || 'user@pulse.ai',
          avatarChar: fullName.charAt(0).toUpperCase() || 'J',
          brandName: metadata.brand_name || 'OmniPulse Media',
          role: metadata.goal === 'agency' ? 'Agency Lead' : metadata.goal === 'creator' ? 'Pro Creator' : 'Growth Strategist'
        });
        setIsAuthenticated(true);
        try {
          localStorage.setItem('ai_social_authenticated', 'true');
        } catch {}
      }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        const metadata = session.user.user_metadata || {};
        const fullName = metadata.full_name || session.user.email?.split('@')[0] || 'John Doe';
        setUser({
          name: fullName,
          email: session.user.email || 'user@pulse.ai',
          avatarChar: fullName.charAt(0).toUpperCase() || 'J',
          brandName: metadata.brand_name || 'OmniPulse Media',
          role: metadata.goal === 'agency' ? 'Agency Lead' : metadata.goal === 'creator' ? 'Pro Creator' : 'Growth Strategist'
        });
        setIsAuthenticated(true);
        try {
          localStorage.setItem('ai_social_authenticated', 'true');
        } catch {}
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Load from localStorage or fall back to initial mock data
  const [posts, setPosts] = useState<SocialPost[]>(() => {
    const saved = localStorage.getItem('ai_social_posts');
    return saved ? JSON.parse(saved) : mockPosts;
  });

  // Supabase Persistence: Fetch posts from FastAPI on mount
  useEffect(() => {
    let isMounted = true;
    api.listPosts().then((fetched) => {
      if (!isMounted) return;
      if (fetched && fetched.length > 0) {
        setPosts(fetched);
      } else {
        // Initial seed into Supabase if remote table is empty
        mockPosts.forEach((post) => {
          api.savePost(post).catch((err) => console.warn('Supabase initial seed notice:', err));
        });
      }
    }).catch((err) => {
      console.warn('Could not load posts from backend, using cached posts:', err);
    });

    return () => {
      isMounted = false;
    };
  }, []);

  const [platforms, setPlatforms] = useState<ConnectedPlatform[]>(() => {
    // Purge any legacy mock connection records from localStorage
    try {
      localStorage.removeItem('ai_social_platforms');
    } catch {}
    return mockConnectedPlatforms;
  });

  // Centralized Server Credential Synchronization: Load real connection states from FastAPI on mount
  useEffect(() => {
    let isMounted = true;
    api.listConnections().then((res) => {
      if (!isMounted) return;
      if (res && res.connections && res.connections.length > 0) {
        setPlatforms(
          res.connections.map((c) => ({
            id: c.id as Platform,
            name: c.name,
            handle: c.handle,
            status: c.status === 'connected' ? 'connected' : c.status === 'error' ? 'error' : 'disconnected',
            connectedUser: c.connectedUser || c.connected_user || '',
            lastVerifiedAt: c.lastVerifiedAt || c.last_verified_at,
            accountId: c.accountId || c.account_id,
            accountName: c.accountName || c.account_name,
            isComingSoon: false,
          }))
        );
      }
    }).catch((err) => {
      console.warn('Backend connection check failed on startup:', err);
    });

    return () => {
      isMounted = false;
    };
  }, []);

  const [user, setUser] = useState<UserProfile>(() => {
    const saved = localStorage.getItem('ai_social_user');
    return saved ? JSON.parse(saved) : mockUserProfile;
  });

  const [preferences, setPreferences] = useState<UserPreferences>(() => {
    const saved = localStorage.getItem('ai_social_preferences');
    return saved ? JSON.parse(saved) : mockUserPreferences;
  });

  const [notificationsSettings, setNotificationsSettings] = useState<UserNotifications>(
    () => {
      const saved = localStorage.getItem('ai_social_notif_settings');
      return saved ? JSON.parse(saved) : mockUserNotifications;
    }
  );

  const [notifications, setNotifications] = useState<NotificationItem[]>(() => {
    const saved = localStorage.getItem('ai_social_notifications');
    return saved ? JSON.parse(saved) : mockNotifications;
  });

  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Sync state changes with localStorage
  useEffect(() => {
    localStorage.setItem('ai_social_posts', JSON.stringify(posts));
  }, [posts]);

  useEffect(() => {
    localStorage.setItem('ai_social_user', JSON.stringify(user));
  }, [user]);

  useEffect(() => {
    localStorage.setItem('ai_social_preferences', JSON.stringify(preferences));
  }, [preferences]);

  useEffect(() => {
    localStorage.setItem(
      'ai_social_notif_settings',
      JSON.stringify(notificationsSettings)
    );
  }, [notificationsSettings]);

  useEffect(() => {
    localStorage.setItem(
      'ai_social_notifications',
      JSON.stringify(notifications)
    );
  }, [notifications]);

  const showToast = (message: string) => {
    setToastMessage(message);
    setTimeout(() => {
      setToastMessage(null);
    }, 4500);
  };

  const handleLoginSuccess = (authenticatedUser: UserProfile) => {
    setUser(authenticatedUser);
    setIsAuthenticated(true);
    try {
      localStorage.setItem('ai_social_authenticated', 'true');
    } catch {}
    showToast(`Welcome back, ${authenticatedUser.name}!`);
  };

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut();
    } catch (err) {
      // ignore
    }
    setIsAuthenticated(false);
    localStorage.removeItem('ai_social_authenticated');
    showToast('You have been signed out.');
  };

  // Dynamic handlers
  const handlePostCreated = (newPost: SocialPost) => {
    // Upsert post into state (replace existing if id matches, otherwise prepend)
    setPosts((prev) => {
      const filtered = prev.filter((p) => p.id !== newPost.id);
      return [newPost, ...filtered];
    });

    if (newPost.status === 'published') {
      showToast('Post published successfully!');
    } else if (newPost.status === 'scheduled') {
      showToast('Post scheduled for delivery!');
      // If post is scheduled, queue it into the backend durable scheduler
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(10, 0, 0, 0);

      api.createSchedule({
        post_id: newPost.id,
        content: newPost.content,
        platforms: newPost.platforms,
        scheduled_time: newPost.scheduledAt || tomorrow.toISOString(),
        media_url: newPost.mediaUrl,
      }).catch((err) => {
        console.warn('Backend schedule queue note:', err);
      });
    } else {
      showToast('Draft post saved.');
    }

    const newNotif: NotificationItem = {
      id: `notif-${Date.now()}`,
      title: `Post "${newPost.title}" ${
        newPost.status === 'published' ? 'published now' : 'queued for delivery'
      }`,
      time: 'Just now',
      unread: true,
      type: newPost.status === 'published' ? 'success' : 'info'
    };
    setNotifications((prev) => [newNotif, ...prev]);
    showToast(`Post created successfully with status: ${newPost.status}!`);
  };

  const handlePublishNow = (id: string) => {
    setPosts((prevPosts) =>
      prevPosts.map((p) => {
        if (p.id === id) {
          return {
            ...p,
            status: 'published',
            createdAt: 'Just now',
            scheduledAt: undefined
          };
        }
        return p;
      })
    );
    const postItem = posts.find((p) => p.id === id);
    if (postItem) {
      api.publishPost(postItem.id, postItem.platforms, true, postItem.content, postItem.mediaUrl).then((res) => {
        if (res.success) {
          showToast('Post published live via FastAPI backend!');
        } else {
          showToast('Publish result: ' + res.message);
        }
      }).catch((err) => {
        console.warn('Backend publish note:', err);
      });
    }

    const newNotif: NotificationItem = {
      id: `notif-${Date.now()}`,
      title: `Post "${postItem?.title || 'Selected post'}" published live!`,
      time: 'Just now',
      unread: true,
      type: 'success'
    };
    setNotifications((prev) => [newNotif, ...prev]);
    showToast('Post published immediately!');
  };

  const handleDeletePost = (id: string) => {
    const confirmed = window.confirm('Are you sure you want to delete this post?');
    if (!confirmed) return;

    const normalizedId = String(id);

    setPosts((prev) => prev.filter((p) => String(p.id) !== normalizedId));

    // Delete from Supabase via FastAPI
    api.deletePost(normalizedId).catch((err) => {
      console.warn('Backend post delete note:', err);
    });

    showToast('Post removed successfully.');
  };

  const handleCancelSchedule = (id: string) => {
    const target = posts.find((p) => p.id === id);
    if (target) {
      const updated: SocialPost = {
        ...target,
        status: 'draft',
        scheduledAt: undefined,
      };
      api.savePost(updated).catch((err) => {
        console.warn('Backend update draft note:', err);
      });
      // Attempt cancelling pending queue job in backend scheduler
      api.cancelSchedule(id).catch(() => {
        // Gracefully ignore if not queued under exact post ID
      });
    }

    setPosts((prev) =>
      prev.map((p) => {
        if (p.id === id) {
          return {
            ...p,
            status: 'draft',
            scheduledAt: undefined
          };
        }
        return p;
      })
    );
    showToast('Scheduled post moved back to Drafts.');
  };

  const handleSchedulePost = (id: string) => {
    const postItem = posts.find((p) => p.id === id);
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(10, 0, 0, 0);

    setPosts((prev) =>
      prev.map((p) => {
        if (p.id === id) {
          return {
            ...p,
            status: 'scheduled',
            scheduledAt: 'Tomorrow at 10:00 AM'
          };
        }
        return p;
      })
    );

    if (postItem) {
      api.createSchedule({
        post_id: postItem.id,
        content: postItem.content,
        platforms: postItem.platforms,
        scheduled_time: tomorrow.toISOString(),
        media_url: postItem.mediaUrl,
      }).catch((err) => {
        console.warn('Backend schedule queue note:', err);
      });

      api.savePost({
        ...postItem,
        status: 'scheduled',
        scheduledAt: tomorrow.toISOString(),
      }).catch((err) => console.warn('Supabase post status update note:', err));
    }

    showToast('Post scheduled for tomorrow 10:00 AM!');
  };

  // Clean URL parameters if redirect landed on frontend
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('code') || urlParams.has('state') || urlParams.has('error')) {
      if (window.history && window.history.replaceState) {
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
  }, []);

  // Multi-window communication listeners (when user authorized via popup or another tab)
  useEffect(() => {
    const refreshConnectionsFromServer = () => {
      api.listConnections().then((res) => {
        if (res && res.connections) {
          setPlatforms(
            res.connections.map((c) => ({
              id: c.id as Platform,
              name: c.name,
              handle: c.handle,
              status: c.status === 'connected' ? 'connected' : c.status === 'error' ? 'error' : 'disconnected',
              connectedUser: c.connectedUser || c.connected_user || '',
              lastVerifiedAt: c.lastVerifiedAt || c.last_verified_at,
              accountId: c.accountId || c.account_id,
              accountName: c.accountName || c.account_name,
            }))
          );
        }
      }).catch((err) => {
        console.warn('Failed to refresh connections from server:', err);
      });
    };

    // 1. postMessage listener from popup
    const handleWindowMessage = (event: MessageEvent) => {
      if (event.data && event.data.type === 'OMNIPULSE_OAUTH_SUCCESS') {
        refreshConnectionsFromServer();
        showToast(`🎉 ${event.data.platform?.toUpperCase() || 'Platform'} connected successfully!`);
      } else if (event.data && event.data.type === 'OMNIPULSE_OAUTH_ERROR') {
        showToast(`Meta Authorization failed: ${event.data.error}`);
      }
    };
    window.addEventListener('message', handleWindowMessage);

    return () => {
      window.removeEventListener('message', handleWindowMessage);
    };
  }, []);

  const handleMarkNotificationsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
  };

  // Dynamic header titles
  const getPageInfo = (): { title: string; subtitle: string } => {
    switch (currentPage) {
      case 'dashboard':
        return {
          title: 'Dashboard',
          subtitle: 'Overview of your social media content'
        };
      case 'create-post':
        return {
          title: 'Create Post',
          subtitle: 'Generate, customize and publish content across multiple platforms with AI'
        };
      case 'posts':
        return {
          title: 'All Posts',
          subtitle: 'View and manage your content'
        };
      case 'scheduled':
        return {
          title: 'Scheduled Posts',
          subtitle: 'Manage your upcoming scheduled content'
        };
      case 'platforms':
        return {
          title: 'Connected Platforms',
          subtitle: 'Connect and manage your social media accounts'
        };
      case 'settings':
        return {
          title: 'Settings',
          subtitle: 'Manage your account and preferences'
        };
      case 'privacy':
        return {
          title: 'Privacy Policy',
          subtitle: 'Meta & Multi-Platform Data Handling Policy'
        };
      case 'terms':
        return {
          title: 'Terms of Service',
          subtitle: 'Platform usage agreement and acceptable use rules'
        };
      case 'data-deletion':
        return {
          title: 'Data Deletion Instructions',
          subtitle: 'Meta user data deletion instructions and compliance'
        };
    }
  };

  const pageInfo = getPageInfo();

  // If this window is a popup completing Meta OAuth, render a dedicated clean success screen
  const isPopupCallback = typeof window !== 'undefined' &&
    Boolean(window.opener && window.opener !== window) &&
    (window.location.search.includes('code=') || window.location.search.includes('state=facebook') || window.location.search.includes('state=instagram'));

  if (isPopupCallback) {
    const params = new URLSearchParams(window.location.search);
    const platformLabel = params.get('state') === 'instagram' ? 'Instagram' : 'Facebook';
    return (
      <div className="meta-oauth-popup-container">
        <div className="meta-oauth-popup-card">
          <div className="meta-popup-icon-pulse">
            <CheckCircle2 size={48} color="#10b981" />
          </div>
          <h2 className="meta-popup-heading">Meta Authentication Successful!</h2>
          <p className="meta-popup-text">
            Your <strong>{platformLabel}</strong> account permissions were granted and verified.
          </p>
          <div className="meta-popup-badge">
            <span className="meta-popup-dot"></span>
            Connected to OmniPulse Media
          </div>
          <p className="meta-popup-sub">
            Syncing status with your dashboard and closing this window automatically...
          </p>
        </div>
      </div>
    );
  }

  // Public Unauthenticated Routes (Meta App Verification requires public access to Privacy, Terms, and Data Deletion)
  if (currentPage === 'privacy') {
    return (
      <PrivacyPolicy
        onBack={() => navigateTo('dashboard')}
        onNavigateTerms={() => navigateTo('terms')}
        onNavigateDataDeletion={() => navigateTo('data-deletion')}
      />
    );
  }

  if (currentPage === 'terms') {
    return (
      <TermsOfService
        onBack={() => navigateTo('dashboard')}
        onNavigatePrivacy={() => navigateTo('privacy')}
        onNavigateDataDeletion={() => navigateTo('data-deletion')}
      />
    );
  }

  if (currentPage === 'data-deletion') {
    return (
      <DataDeletion
        onBack={() => navigateTo('dashboard')}
        onNavigatePrivacy={() => navigateTo('privacy')}
        onNavigateTerms={() => navigateTo('terms')}
      />
    );
  }

  // If user is not authenticated, display the Login & Sign Up page
  if (!isAuthenticated) {
    return (
      <>
        <div className="auth-root-wrapper">
          <Auth
            onLoginSuccess={handleLoginSuccess}
            onNavigatePrivacy={() => navigateTo('privacy')}
            onNavigateTerms={() => navigateTo('terms')}
            onNavigateDataDeletion={() => navigateTo('data-deletion')}
          />
        </div>
        {toastMessage && (
          <div className="app-toast-pill" role="status" aria-live="polite">
            <span>✨</span>
            <span>{toastMessage}</span>
          </div>
        )}
      </>
    );
  }

  return (
    <>
      <div className="app-shell">
        {/* Dark Sidebar matching screenshots */}
        <Sidebar
          currentPage={currentPage}
          onNavigate={navigateTo}
          user={user}
          isMobileOpen={isMobileOpen}
          onCloseMobile={() => setIsMobileOpen(false)}
          onLogout={handleLogout}
        />

      {/* Main Workspace */}
      <div className="main-viewport">
        {/* Top Header */}
        <Header
          title={pageInfo.title}
          subtitle={pageInfo.subtitle}
          user={user}
          notifications={notifications}
          onMarkNotificationsRead={handleMarkNotificationsRead}
          onOpenMobileMenu={() => setIsMobileOpen(true)}
          onNavigateToSettings={() => navigateTo('settings')}
          onLogout={handleLogout}
        />

        {/* Dynamic Page Content */}
        <main className="page-content-body">
          <ErrorBoundary onReset={() => navigateTo('dashboard')}>
          {currentPage === 'dashboard' && (
            <Dashboard
              metrics={mockMetrics}
              posts={posts}
              onNavigate={navigateTo}
              onPublishNow={handlePublishNow}
              onDeletePost={handleDeletePost}
            />
          )}

          {currentPage === 'create-post' && (
            <CreatePost
              user={user}
              preferences={preferences}
              onPostCreated={handlePostCreated}
              onNavigate={navigateTo}
            />
          )}

          {currentPage === 'posts' && (
            <Posts
              posts={posts}
              onNavigate={navigateTo}
              onPublishNow={handlePublishNow}
              onDeletePost={handleDeletePost}
              onSchedulePost={handleSchedulePost}
            />
          )}

          {currentPage === 'scheduled' && (
            <Scheduled
              posts={posts}
              onNavigate={navigateTo}
              onPublishNow={handlePublishNow}
              onCancelSchedule={handleCancelSchedule}
              onDeletePost={handleDeletePost}
            />
          )}

          {currentPage === 'platforms' && (
            <Platforms
              platforms={platforms}
              onToast={showToast}
            />
          )}

          {currentPage === 'settings' && (
            <Settings
              user={user}
              preferences={preferences}
              notifications={notificationsSettings}
              onUpdateUser={setUser}
              onUpdatePreferences={setPreferences}
              onUpdateNotifications={setNotificationsSettings}
              onLogout={handleLogout}
              onNavigate={navigateTo}
            />
          )}
          </ErrorBoundary>
        </main>
      </div>
    </div>

    {/* Floating Toast Notification */}
    {toastMessage && (
      <div className="app-toast-pill" role="status" aria-live="polite">
        <span>✨</span>
        <span>{toastMessage}</span>
      </div>
    )}
  </>
);
};

export default App;
