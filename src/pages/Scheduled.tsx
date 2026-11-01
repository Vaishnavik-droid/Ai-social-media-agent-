import React, { useState } from 'react';
import { Plus, MoreHorizontal, Send, Trash2, XCircle } from 'lucide-react';
import { SocialPost } from '../types';
import { PlatformIcon } from '../components/PlatformIcon';
import { StatusBadge } from '../components/StatusBadge';

interface ScheduledProps {
  posts: SocialPost[];
  onNavigate: (page: any) => void;
  onPublishNow: (id: string) => void;
  onCancelSchedule: (id: string) => void;
  onDeletePost: (id: string) => void;
}

export const Scheduled: React.FC<ScheduledProps> = ({
  posts,
  onNavigate,
  onPublishNow,
  onCancelSchedule,
  onDeletePost
}) => {
  const [activeTab, setActiveTab] = useState<'upcoming' | 'past'>('upcoming');
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  // Dynamic separation of upcoming vs past
  const upcomingPosts = posts.filter((p) => p.status === 'scheduled');
  const pastPosts = posts.filter(
    (p) => p.status === 'published' || p.status === 'failed'
  );

  const displayedPosts = activeTab === 'upcoming' ? upcomingPosts : pastPosts;

  return (
    <div className="scheduled-page">
      <div className="scheduled-toolbar">
        <div className="scheduled-tabs" role="tablist" aria-label="Scheduled posts tabs">
          <button
            type="button"
            onClick={() => setActiveTab('upcoming')}
            className={`scheduled-tab ${activeTab === 'upcoming' ? 'scheduled-tab-active' : ''}`}
          >
            Upcoming ({upcomingPosts.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('past')}
            className={`scheduled-tab ${activeTab === 'past' ? 'scheduled-tab-active' : ''}`}
          >
            Past ({pastPosts.length})
          </button>
        </div>

        <button
          onClick={() => onNavigate('create-post')}
          className="scheduled-create-button"
        >
          <Plus size={14} />
          <span>Schedule Post</span>
        </button>
      </div>

      <div className="scheduled-card">
        <div className="scheduled-table-wrap">
          <table className="scheduled-table">
            <thead>
              <tr>
                <th className="scheduled-table-header">Content</th>
                <th className="scheduled-table-header">Platforms</th>
                <th className="scheduled-table-header">
                  {activeTab === 'upcoming' ? 'Scheduled At' : 'Delivered At'}
                </th>
                <th className="scheduled-table-header">Status</th>
                <th className="scheduled-table-header scheduled-table-header-actions">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {displayedPosts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="scheduled-empty-state">
                    {activeTab === 'upcoming'
                      ? 'No upcoming scheduled posts. Click "Schedule Post" to queue new content.'
                      : 'No past posts recorded yet.'}
                  </td>
                </tr>
              ) : (
                displayedPosts.map((post) => (
                  <tr key={post.id} className="scheduled-row">
                    <td className="scheduled-cell" data-label="Content">
                      <div className="scheduled-content">
                        {post.mediaUrl ? (
                          <img
                            src={post.mediaUrl}
                            alt={post.title}
                            className="scheduled-thumbnail"
                          />
                        ) : (
                          <div className="scheduled-thumbnail scheduled-thumbnail-fallback">
                            📝
                          </div>
                        )}
                        <div className="scheduled-content-meta">
                          <div className="scheduled-post-title">{post.title}</div>
                          <div className="scheduled-post-snippet">{post.snippet}</div>
                        </div>
                      </div>
                    </td>

                    <td className="scheduled-cell" data-label="Platforms">
                      <div className="scheduled-platforms">
                        {post.platforms.map((platform) => (
                          <PlatformIcon key={platform} platform={platform} size={18} />
                        ))}
                      </div>
                    </td>

                    <td className="scheduled-cell" data-label="Scheduled At">
                      <div className="scheduled-date-stack">
                        <span className="scheduled-date">
                          {post.scheduledAt ? (post.scheduledAt || '').split(' ').slice(0, 3).join(' ') : (post.createdAt || '').split(' ').slice(0, 3).join(' ')}
                        </span>
                        <span className="scheduled-time">
                          {post.scheduledAt ? (post.scheduledAt || '').split(' ').slice(3).join(' ') : (post.createdAt || '').split(' ').slice(3).join(' ')}
                        </span>
                      </div>
                    </td>

                    <td className="scheduled-cell" data-label="Status">
                      <StatusBadge status={post.status} className="scheduled-status-badge" />
                    </td>

                    <td className="scheduled-cell scheduled-cell-actions" data-label="Actions">
                      <div className="scheduled-action-cell">
                        <button
                          className="scheduled-action-button"
                          aria-label="More actions"
                          onClick={() =>
                            setOpenMenuId(openMenuId === post.id ? null : post.id)
                          }
                        >
                          <MoreHorizontal size={18} />
                        </button>

                        {openMenuId === post.id && (
                          <div className="scheduled-menu">
                            {post.status === 'scheduled' && (
                              <>
                                <button
                                  onClick={() => {
                                    onPublishNow(post.id);
                                    setOpenMenuId(null);
                                  }}
                                  className="scheduled-menu-item scheduled-menu-item-success"
                                >
                                  <Send size={13} />
                                  <span>Publish Now</span>
                                </button>
                                <button
                                  onClick={() => {
                                    onCancelSchedule(post.id);
                                    setOpenMenuId(null);
                                  }}
                                  className="scheduled-menu-item scheduled-menu-item-warn"
                                >
                                  <XCircle size={13} />
                                  <span>To Draft</span>
                                </button>
                              </>
                            )}
                            <button
                              onClick={() => {
                                onDeletePost(post.id);
                                setOpenMenuId(null);
                              }}
                              className="scheduled-menu-item scheduled-menu-item-danger"
                            >
                              <Trash2 size={13} />
                              <span>Delete</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
