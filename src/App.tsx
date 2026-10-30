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

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<NavPage>('dashboard');

  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

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
    const saved = localStorage.getItem('ai_social_platforms');
    return saved ? JSON.parse(saved) : mockConnectedPlatforms;
  });

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
    localStorage.setItem('ai_social_platforms', JSON.stringify(platforms));
  }, [platforms]);

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
    }, 2800);
  };

  const handleLoginSuccess = (authenticatedUser: UserProfile) => {
    setUser(authenticatedUser);
    setIsAuthenticated(true);
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
    setPosts((prev) => [newPost, ...prev]);

    // Persist durably to Supabase via FastAPI and trigger publish if published
    api.savePost(newPost).then(() => {
      if (newPost.status === 'published') {
        api.publishPost(newPost.id, newPost.platforms).then((res) => {
          if (res.success) {
            showToast('Post published across all channels!');
          } else {
            showToast(res.message || 'Publishing completed with warnings.');
          }
        }).catch((err) => {
          console.error('Publish dispatch error:', err);
          showToast(`Publish notice: ${err.message}`);
        });
      }
    }).catch((err) => {
      console.error('Failed to save post to backend persistence:', err);
      showToast('Warning: Post saved locally, remote database sync pending.');
    });

    // If post is scheduled, queue it into the backend durable scheduler
    if (newPost.status === 'scheduled') {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(10, 0, 0, 0);

      api.createSchedule({
        post_id: newPost.id,
        content: newPost.content,
        platforms: newPost.platforms,
        scheduled_time: tomorrow.toISOString(),
        media_url: newPost.mediaUrl,
      }).catch((err) => {
        console.warn('Backend schedule queue note:', err);
      });
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
      api.publishPost(postItem.id, postItem.platforms).then((res) => {
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

  const handleTogglePlatformStatus = (platformId: Platform) => {
    setPlatforms((prev) =>
      prev.map((p) => {
        if (p.id === platformId) {
          const nextStatus = p.status === 'connected' ? 'disconnected' : 'connected';
          return {
            ...p,
            status: nextStatus
          };
        }
        return p;
      })
    );
    showToast(`Platform connection state updated.`);
  };

  const handleUpdatePlatformHandle = (platformId: Platform, newHandle: string) => {
    setPlatforms((prev) =>
      prev.map((p) => {
        if (p.id === platformId) {
          return {
            ...p,
            handle: newHandle
          };
        }
        return p;
      })
    );
    showToast('Platform handle updated.');
  };

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
    }
  };

  const pageInfo = getPageInfo();

  // If user is not authenticated, display the Login & Sign Up page
  if (!isAuthenticated) {
    return (
      <>
        <div className="auth-root-wrapper">
          <Auth onLoginSuccess={handleLoginSuccess} />
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
          onNavigate={setCurrentPage}
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
          onNavigateToSettings={() => setCurrentPage('settings')}
          onLogout={handleLogout}
        />

        {/* Dynamic Page Content */}
        <main className="page-content-body">
          {currentPage === 'dashboard' && (
            <Dashboard
              metrics={mockMetrics}
              posts={posts}
              onNavigate={setCurrentPage}
              onPublishNow={handlePublishNow}
              onDeletePost={handleDeletePost}
            />
          )}

          {currentPage === 'create-post' && (
            <CreatePost
              user={user}
              preferences={preferences}
              onPostCreated={handlePostCreated}
              onNavigate={setCurrentPage}
            />
          )}

          {currentPage === 'posts' && (
            <Posts
              posts={posts}
              onNavigate={setCurrentPage}
              onPublishNow={handlePublishNow}
              onDeletePost={handleDeletePost}
              onSchedulePost={handleSchedulePost}
            />
          )}

          {currentPage === 'scheduled' && (
            <Scheduled
              posts={posts}
              onNavigate={setCurrentPage}
              onPublishNow={handlePublishNow}
              onCancelSchedule={handleCancelSchedule}
              onDeletePost={handleDeletePost}
            />
          )}

          {currentPage === 'platforms' && (
            <Platforms
              platforms={platforms}
              onToggleStatus={handleTogglePlatformStatus}
              onUpdateHandle={handleUpdatePlatformHandle}
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
            />
          )}
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
