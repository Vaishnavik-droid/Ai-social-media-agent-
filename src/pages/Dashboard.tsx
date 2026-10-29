import React, { useState } from 'react';
import {
  FileText,
  CheckCircle2,
  CalendarDays,
  XCircle,
  MoreHorizontal,
  ArrowRight,
  Trash2,
  Send,
  Eye
} from 'lucide-react';
import { SocialPost, MetricSummary } from '../types';
import { PlatformIcon } from '../components/PlatformIcon';
import { StatusBadge } from '../components/StatusBadge';

interface DashboardProps {
  metrics: MetricSummary;
  posts: SocialPost[];
  onNavigate: (page: any) => void;
  onPublishNow: (id: string) => void;
  onDeletePost: (id: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  metrics,
  posts,
  onNavigate,
  onPublishNow,
  onDeletePost
}) => {
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);

  const recentPosts = posts.slice(0, 3);

  const totalPostsCount = posts.length;
  const publishedCount = posts.filter((p) => p.status === 'published').length;
  const scheduledCount = posts.filter((p) => p.status === 'scheduled').length;
  const failedCount = posts.filter((p) => p.status === 'failed').length;

  return (
    <div className="dashboard-page">
      <div className="dashboard-stats">
        <div
          onClick={() => onNavigate('posts')}
          className="dashboard-stat-card stat-card-clickable"
          title="View all posts"
        >
          <div className="stat-icon-wrap stat-icon-blue">
            <FileText size={18} strokeWidth={2.2} className="text-blue-500" />
          </div>
          <div className="dashboard-stat-content">
            <div className="dashboard-stat-label">Total Posts</div>
            <div className="dashboard-stat-number">{totalPostsCount}</div>
          </div>
        </div>

        <div
          onClick={() => onNavigate('posts')}
          className="dashboard-stat-card stat-card-clickable"
          title="View published posts"
        >
          <div className="stat-icon-wrap stat-icon-green">
            <CheckCircle2 size={18} strokeWidth={2.2} className="text-emerald-500" />
          </div>
          <div className="dashboard-stat-content">
            <div className="dashboard-stat-label">Published</div>
            <div className="dashboard-stat-number">{publishedCount}</div>
          </div>
        </div>

        <div
          onClick={() => onNavigate('scheduled')}
          className="dashboard-stat-card stat-card-clickable"
          title="View scheduled posts"
        >
          <div className="stat-icon-wrap stat-icon-purple">
            <CalendarDays size={18} strokeWidth={2.2} className="text-violet-500" />
          </div>
          <div className="dashboard-stat-content">
            <div className="dashboard-stat-label">Scheduled</div>
            <div className="dashboard-stat-number">{scheduledCount}</div>
          </div>
        </div>

        <div
          onClick={() => onNavigate('posts')}
          className="dashboard-stat-card stat-card-clickable"
          title="View failed posts"
        >
          <div className="stat-icon-wrap stat-icon-red">
            <XCircle size={18} strokeWidth={2.2} className="text-red-500" />
          </div>
          <div className="dashboard-stat-content">
            <div className="dashboard-stat-label">Failed</div>
            <div className="dashboard-stat-number">{failedCount}</div>
          </div>
        </div>
      </div>

      <div className="dashboard-recent-card">
        <div className="dashboard-recent-header">
          <h2 className="dashboard-recent-title">Recent Posts</h2>
          <button type="button" onClick={() => onNavigate('posts')} className="dashboard-view-all">
            <span>View All</span>
            <ArrowRight size={12} strokeWidth={2.2} />
          </button>
        </div>

        <div className="dashboard-table-wrap">
          <table className="dashboard-data-table">
            <thead>
              <tr>
                <th className="dashboard-th-cell">Content</th>
                <th className="dashboard-th-cell">Platforms</th>
                <th className="dashboard-th-cell">Status</th>
                <th className="dashboard-th-cell">Created At</th>
                <th className="dashboard-th-cell dashboard-th-cell-actions" aria-label="Actions"></th>
              </tr>
            </thead>
            <tbody>
              {recentPosts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="dashboard-empty-state">
                    No posts yet. Click "Create Post" to draft your first content!
                  </td>
                </tr>
              ) : (
                recentPosts.map((post) => (
                  <tr key={post.id} className="dashboard-row">
                    <td className="dashboard-td-cell" data-label="Content">
                      <div className="dashboard-content-cell">
                        {post.mediaUrl ? (
                          <img src={post.mediaUrl} alt={post.title} className="dashboard-table-thumbnail" />
                        ) : (
                          <div className="dashboard-table-thumbnail dashboard-table-thumbnail-placeholder">📝</div>
                        )}
                        <div className="dashboard-post-copy">
                          <div className="dashboard-post-title">{post.title}</div>
                          <div className="dashboard-post-snippet">{post.snippet}</div>
                        </div>
                      </div>
                    </td>

                    <td className="dashboard-td-cell" data-label="Platforms">
                      <div className="dashboard-platform-cell">
                        {post.platforms.map((platform) => (
                          <PlatformIcon key={platform} platform={platform} size={18} />
                        ))}
                      </div>
                    </td>

                    <td className="dashboard-td-cell" data-label="Status">
                      <StatusBadge status={post.status} className="dashboard-status-badge" />
                    </td>

                    <td className="dashboard-td-cell" data-label="Created At">
                      <div className="dashboard-date-box">{post.createdAt}</div>
                    </td>

                    <td className="dashboard-td-cell dashboard-menu-cell" data-label="Actions">
                      <div className="dashboard-menu-wrapper">
                        <button
                          type="button"
                          className="dashboard-table-action-button"
                          aria-label="More actions"
                          onClick={() =>
                            setActiveMenuId(activeMenuId === post.id ? null : post.id)
                          }
                        >
                          <MoreHorizontal size={16} strokeWidth={2.1} />
                        </button>

                        {activeMenuId === post.id && (
                          <div className="dashboard-action-menu">
                            {post.status !== 'published' && (
                              <button
                                type="button"
                                onClick={() => {
                                  onPublishNow(post.id);
                                  setActiveMenuId(null);
                                }}
                                className="dashboard-menu-item success"
                              >
                                <Send size={12} strokeWidth={2} />
                                <span>Publish Now</span>
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => {
                                onNavigate('posts');
                                setActiveMenuId(null);
                              }}
                              className="dashboard-menu-item"
                            >
                              <Eye size={12} strokeWidth={2} />
                              <span>View Details</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                onDeletePost(post.id);
                                setActiveMenuId(null);
                              }}
                              className="dashboard-menu-item danger"
                            >
                              <Trash2 size={12} strokeWidth={2} />
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
