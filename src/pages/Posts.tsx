import React, { useState } from 'react';
import {
  Search,
  Filter,
  Plus,
  MoreHorizontal,
  Send,
  Calendar,
  Trash2,
  Eye
} from 'lucide-react';
import { SocialPost } from '../types';
import { PlatformIcon } from '../components/PlatformIcon';
import { StatusBadge } from '../components/StatusBadge';

interface PostsProps {
  posts: SocialPost[];
  onNavigate: (page: any) => void;
  onPublishNow: (id: string) => void;
  onDeletePost: (id: string) => void;
  onSchedulePost: (id: string) => void;
}

export const Posts: React.FC<PostsProps> = ({
  posts,
  onNavigate,
  onPublishNow,
  onDeletePost,
  onSchedulePost
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  const filteredPosts = posts.filter((p) => {
    if (statusFilter !== 'all' && p.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchText =
        p.title.toLowerCase().includes(q) ||
        p.snippet.toLowerCase().includes(q) ||
        p.content.toLowerCase().includes(q);
      const matchPlatform = p.platforms.some((plat) =>
        plat.toLowerCase().includes(q)
      );
      return matchText || matchPlatform;
    }
    return true;
  });

  return (
    <div className="posts-page">
      <div className="posts-toolbar">
        <div className="posts-search-shell">
          <Search size={14} className="posts-search-icon" />
          <input
            type="text"
            placeholder="Search posts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="posts-search-input"
          />
        </div>

        <div className="posts-toolbar-actions">
          <div className="posts-filter-wrap">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="posts-filter-select"
            >
              <option value="all">All Statuses</option>
              <option value="published">Published</option>
              <option value="scheduled">Scheduled</option>
              <option value="draft">Draft</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          <button
            onClick={() => onNavigate('create-post')}
            className="btn-blue-primary posts-create-button"
          >
            <Plus size={14} />
            <span>Create Post</span>
          </button>
        </div>
      </div>

      <div className="posts-table-card">
        <div className="posts-table-wrap">
          <table className="posts-table">
            <thead>
              <tr>
                <th className="posts-table-header">Content</th>
                <th className="posts-table-header">Platforms</th>
                <th className="posts-table-header">Status</th>
                <th className="posts-table-header">Created At</th>
                <th className="posts-table-header posts-table-header-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredPosts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="posts-empty-state">
                    No posts found matching your criteria.
                  </td>
                </tr>
              ) : (
                filteredPosts.map((post) => {
                  const createdDateParts = post.createdAt.split(/\r?\n/);
                  const [dateText, timeText] = createdDateParts;

                  return (
                    <tr key={post.id} className="posts-row">
                      <td className="posts-cell" data-label="Content">
                        <div className="posts-content">
                          {post.mediaUrl ? (
                            <img
                              src={post.mediaUrl}
                              alt={post.title}
                              className="posts-thumbnail"
                            />
                          ) : (
                            <div className="posts-thumbnail posts-thumbnail-fallback">
                              📝
                            </div>
                          )}
                          <div className="posts-content-meta">
                            <div className="posts-title">{post.title}</div>
                            <div className="posts-snippet">{post.snippet}</div>
                          </div>
                        </div>
                      </td>

                      <td className="posts-cell" data-label="Platforms">
                        <div className="posts-platforms">
                          {post.platforms.map((platform) => (
                            <PlatformIcon key={platform} platform={platform} size={20} />
                          ))}
                        </div>
                      </td>

                      <td className="posts-cell" data-label="Status">
                        <StatusBadge status={post.status} className="posts-status-badge" />
                      </td>

                      <td className="posts-cell" data-label="Created At">
                        <div className="posts-date-stack">
                          <span className="posts-date">{dateText || post.createdAt}</span>
                          {timeText && <span className="posts-time">{timeText}</span>}
                        </div>
                      </td>

                      <td className="posts-cell posts-cell-actions" data-label="Actions">
                        <div className="posts-action-cell">
                          <button
                            className="posts-action-button"
                            aria-label="More actions"
                            onClick={() =>
                              setOpenMenuId(openMenuId === post.id ? null : post.id)
                            }
                          >
                            <MoreHorizontal size={18} />
                          </button>

                          {openMenuId === post.id && (
                            <div className="posts-menu">
                              {post.status !== 'published' && (
                                <button
                                  onClick={() => {
                                    onPublishNow(post.id);
                                    setOpenMenuId(null);
                                  }}
                                  className="posts-menu-item posts-menu-item-success"
                                >
                                  <Send size={13} />
                                  <span>Publish Now</span>
                                </button>
                              )}
                              {post.status === 'draft' && (
                                <button
                                  onClick={() => {
                                    onSchedulePost(post.id);
                                    setOpenMenuId(null);
                                  }}
                                  className="posts-menu-item posts-menu-item-primary"
                                >
                                  <Calendar size={13} />
                                  <span>Schedule</span>
                                </button>
                              )}
                              <button
                                onClick={() => {
                                  onDeletePost(post.id);
                                  setOpenMenuId(null);
                                }}
                                className="posts-menu-item posts-menu-item-danger"
                              >
                                <Trash2 size={13} />
                                <span>Delete</span>
                              </button>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
