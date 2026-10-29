import React, { useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  Bell,
  CalendarClock,
  CheckCheck,
  CheckCircle2,
  Clock3,
  Menu,
  X,
  LogOut,
  Settings as SettingsIcon,
  ChevronDown
} from 'lucide-react';
import { UserProfile, NotificationItem } from '../types';

interface HeaderProps {
  title: string;
  subtitle: string;
  user: UserProfile;
  notifications: NotificationItem[];
  onMarkNotificationsRead: () => void;
  onOpenMobileMenu: () => void;
  onNavigateToSettings?: () => void;
  onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  user,
  notifications,
  onMarkNotificationsRead,
  onOpenMobileMenu,
  onNavigateToSettings,
  onLogout
}) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const bellButtonRef = useRef<HTMLButtonElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const userPillRef = useRef<HTMLDivElement>(null);
  const unreadCount = notifications.filter((n) => n.unread).length;

  useEffect(() => {
    if (!showNotifications) return;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target as Node;

      if (
        panelRef.current &&
        !panelRef.current.contains(target) &&
        bellButtonRef.current &&
        !bellButtonRef.current.contains(target)
      ) {
        setShowNotifications(false);
      }

      if (
        userMenuRef.current &&
        !userMenuRef.current.contains(target) &&
        userPillRef.current &&
        !userPillRef.current.contains(target)
      ) {
        setShowUserMenu(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowNotifications(false);
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showNotifications, showUserMenu]);

  const getNotificationMeta = (notif: NotificationItem) => {
    const normalizedTitle = notif.title.toLowerCase();

    if (notif.type === 'alert' || normalizedTitle.includes('failed')) {
      return {
        Icon: AlertCircle,
        toneClass: 'notification-icon-alert'
      };
    }

    if (notif.type === 'success' || normalizedTitle.includes('published')) {
      return {
        Icon: CheckCircle2,
        toneClass: 'notification-icon-success'
      };
    }

    if (normalizedTitle.includes('scheduled')) {
      return {
        Icon: CalendarClock,
        toneClass: 'notification-icon-scheduled'
      };
    }

    return {
      Icon: Clock3,
      toneClass: 'notification-icon-info'
    };
  };

  return (
    <header className="page-header-top">
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="lg:hidden header-menu-button"
          onClick={onOpenMobileMenu}
          aria-label="Toggle navigation menu"
        >
          <Menu size={18} strokeWidth={2.25} />
        </button>
        <div>
          <h1 className="page-header-title">{title}</h1>
          <p className="page-header-subtitle">{subtitle}</p>
        </div>
      </div>

      <div className="header-right-controls">
        <div className="notification-menu-wrapper">
          <button
            ref={bellButtonRef}
            type="button"
            className="header-bell-button"
            aria-label="Notifications"
            onClick={() => setShowNotifications((prev) => !prev)}
          >
            <Bell size={18} strokeWidth={2.1} />
            {unreadCount > 0 && <span className="bell-red-dot" />}
          </button>

          {showNotifications && (
            <div className="notification-panel" ref={panelRef} role="dialog" aria-label="Notifications panel">
              <div className="notification-panel-header">
                <div className="notification-panel-title-wrap">
                  <span className="notification-panel-title">Notifications</span>
                  {unreadCount > 0 && (
                    <span className="notification-panel-count">{unreadCount} new</span>
                  )}
                </div>

                <div className="notification-panel-actions">
                  {unreadCount > 0 && (
                    <button
                      type="button"
                      onClick={onMarkNotificationsRead}
                      className="notification-mark-read"
                    >
                      <CheckCheck size={12} />
                      <span>Mark all read</span>
                    </button>
                  )}
                  <button
                    type="button"
                    aria-label="Close notifications"
                    className="notification-close-btn"
                    onClick={() => setShowNotifications(false)}
                  >
                    <X size={15} strokeWidth={2.2} />
                  </button>
                </div>
              </div>

              <div className="notification-list">
                {notifications.length === 0 ? (
                  <div className="notification-empty-state">No new notifications</div>
                ) : (
                  notifications.map((notif) => {
                    const { Icon, toneClass } = getNotificationMeta(notif);

                    return (
                      <div
                        key={notif.id}
                        className={`notification-item ${notif.unread ? 'unread' : 'read'}`}
                      >
                        <div className={`notification-icon-wrap ${toneClass}`}>
                          <Icon size={16} strokeWidth={2.2} />
                        </div>

                        <div className="notification-content">
                          <div className="notification-message-row">
                            <p className="notification-message">{notif.title}</p>
                            {notif.unread && <span className="notification-unread-dot" />}
                          </div>

                          <div className="notification-time">
                            <Clock3 size={11} strokeWidth={2} />
                            <span>{notif.time}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              <div className="notification-footer">
                <button
                  type="button"
                  className="notification-view-all"
                  onClick={() => setShowNotifications(false)}
                >
                  View all notifications
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="header-user-wrapper">
          <div
            ref={userPillRef}
            className="header-user-pill"
            onClick={() => setShowUserMenu((prev) => !prev)}
            title="User Profile Menu"
            role="button"
            tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                setShowUserMenu((prev) => !prev);
              }
            }}
          >
            <div className="header-avatar-circle">{user.avatarChar}</div>
            <span className="header-user-name">{user.name}</span>
            <ChevronDown size={13} className="header-user-chevron" />
          </div>

          {showUserMenu && (
            <div className="header-user-dropdown animate-fadeIn" ref={userMenuRef}>
              <div className="header-dropdown-profile">
                <div className="header-dropdown-avatar">{user.avatarChar}</div>
                <div className="header-dropdown-details">
                  <div className="header-dropdown-name">{user.name}</div>
                  <div className="header-dropdown-email">{user.email}</div>
                  {user.brandName && (
                    <div className="header-dropdown-brand">{user.brandName}</div>
                  )}
                </div>
              </div>

              <div className="header-dropdown-divider" />

              <button
                type="button"
                className="header-dropdown-item"
                onClick={() => {
                  setShowUserMenu(false);
                  if (onNavigateToSettings) onNavigateToSettings();
                }}
              >
                <SettingsIcon size={15} />
                <span>Account & Preferences</span>
              </button>

              {onLogout && (
                <button
                  type="button"
                  className="header-dropdown-item header-dropdown-logout"
                  onClick={() => {
                    setShowUserMenu(false);
                    onLogout();
                  }}
                >
                  <LogOut size={15} />
                  <span>Sign Out / Switch Account</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
