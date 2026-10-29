import React, { useState } from 'react';
import { ConnectedPlatform, Platform } from '../types';
import { PlatformIcon } from '../components/PlatformIcon';
import { Edit2 } from 'lucide-react';

interface PlatformsProps {
  platforms: ConnectedPlatform[];
  onToggleStatus: (id: Platform) => void;
  onUpdateHandle: (id: Platform, newHandle: string) => void;
}

export const Platforms: React.FC<PlatformsProps> = ({
  platforms,
  onToggleStatus,
  onUpdateHandle
}) => {
  const [editingId, setEditingId] = useState<Platform | null>(null);
  const [editHandleText, setEditHandleText] = useState('');

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

  return (
    <div className="platforms-page">
      <div className="platforms-grid">
        {platforms.map((platform) => {
          const isConnected = platform.status === 'connected';
          const isEditing = editingId === platform.id;

          return (
            <div key={platform.id} className="platform-card">
              <div className="platform-card-header">
                <div className="platform-card-icon-wrap">
                  <PlatformIcon platform={platform.id} size={28} />
                </div>
                <div className="platform-name">{platform.name}</div>
              </div>

              <div className="platform-card-status">
                <span className={`platform-status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
                <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
              </div>

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
                    <span className="platform-handle-text">{platform.handle}</span>
                    <button
                      onClick={() => startEdit(platform)}
                      className="platform-edit-button"
                      title="Edit handle"
                    >
                      <Edit2 size={12} />
                    </button>
                  </>
                )}
              </div>

              <button
                type="button"
                onClick={() => onToggleStatus(platform.id)}
                className={`platform-action-button ${isConnected ? 'disconnect' : 'connect'}`}
              >
                {isConnected ? 'Disconnect' : 'Connect'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
