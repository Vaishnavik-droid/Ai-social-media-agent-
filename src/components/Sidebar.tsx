import {
  LayoutDashboard,
  PenSquare,
  FileText,
  CalendarDays,
  Share2,
  Settings,
  Sparkles,
  LogOut,
  Radio
} from 'lucide-react';
import { UserProfile } from '../types';

export type NavPage =
  | 'dashboard'
  | 'create-post'
  | 'posts'
  | 'scheduled'
  | 'platforms'
  | 'settings';

interface SidebarProps {
  currentPage: NavPage;
  onNavigate: (page: NavPage) => void;
  user: UserProfile;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
  onLogout?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  user,
  isMobileOpen = false,
  onCloseMobile,
  onLogout
}) => {
  const mainNavItems = [
    {
      id: 'dashboard' as NavPage,
      label: 'Dashboard',
      icon: <LayoutDashboard size={16} strokeWidth={2} />
    },
    {
      id: 'create-post' as NavPage,
      label: 'Create Post',
      icon: <PenSquare size={16} strokeWidth={2} />
    },
    {
      id: 'posts' as NavPage,
      label: 'Posts',
      icon: <FileText size={16} strokeWidth={2} />
    },
    {
      id: 'scheduled' as NavPage,
      label: 'Scheduled',
      icon: <CalendarDays size={16} strokeWidth={2} />
    },
    {
      id: 'platforms' as NavPage,
      label: 'Platforms',
      icon: <Share2 size={16} strokeWidth={2} />
    }
  ];

  return (
    <>
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside className={`app-sidebar ${isMobileOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-brand-box">
          <div className="sidebar-brand-icon" aria-label="AI Social Media Agent logo">
            <Sparkles size={16} strokeWidth={2.3} className="text-violet-300" />
          </div>
          <div className="sidebar-brand-titles">
            <span className="brand-title-line">AI Social Media</span>
            <span className="brand-title-line">Agent</span>
          </div>
        </div>

        <nav className="sidebar-navigation" aria-label="Sidebar navigation">
          {/* Main Workspace Navigation */}
          <ul className="sidebar-nav-list">
            {mainNavItems.map((item) => {
              const isActive = currentPage === item.id;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => {
                      onNavigate(item.id);
                      if (onCloseMobile) onCloseMobile();
                    }}
                    className={`sidebar-nav-button ${isActive ? 'sidebar-nav-active' : ''}`}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <span className="sidebar-nav-icon">{item.icon}</span>
                    <span>{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>

          {/* System Settings */}
          <div className="mt-4 pt-3 border-t border-slate-800/80">
            <button
              type="button"
              onClick={() => {
                onNavigate('settings');
                if (onCloseMobile) onCloseMobile();
              }}
              className={`sidebar-nav-button ${currentPage === 'settings' ? 'sidebar-nav-active' : ''}`}
              aria-current={currentPage === 'settings' ? 'page' : undefined}
            >
              <span className="sidebar-nav-icon"><Settings size={16} strokeWidth={2} /></span>
              <span>Settings</span>
            </button>
          </div>
        </nav>

        <div className="sidebar-user-bottom">
          <div className="sidebar-avatar-circle">{user.avatarChar}</div>
          <div className="sidebar-user-details">
            <span className="sidebar-user-name">{user.name}</span>
            <span className="sidebar-user-email">{user.brandName || user.email}</span>
          </div>
          {onLogout && (
            <button
              type="button"
              onClick={onLogout}
              className="sidebar-logout-btn"
              title="Sign Out / Switch Account"
              aria-label="Sign Out"
            >
              <LogOut size={15} />
            </button>
          )}
        </div>
      </aside>
    </>
  );
};
