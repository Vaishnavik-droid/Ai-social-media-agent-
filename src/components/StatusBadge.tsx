import React from 'react';
import { PostStatus } from '../types';

interface StatusBadgeProps {
  status: PostStatus | string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  switch (status.toLowerCase()) {
    case 'published':
      return (
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium text-emerald-700 bg-emerald-100 ${className}`}
          style={{ backgroundColor: '#dcfce7', color: '#16a34a' }}
        >
          Published
        </span>
      );

    case 'partially_published':
      return (
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium text-amber-700 bg-amber-100 ${className}`}
          style={{ backgroundColor: '#fef3c7', color: '#d97706' }}
        >
          Partially Published
        </span>
      );

    case 'scheduled':
      return (
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium text-indigo-700 bg-indigo-100 ${className}`}
          style={{ backgroundColor: '#e0e7ff', color: '#4f46e5' }}
        >
          Scheduled
        </span>
      );

    case 'draft':
      return (
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium text-slate-600 bg-slate-100 ${className}`}
          style={{ backgroundColor: '#f1f5f9', color: '#64748b' }}
        >
          Draft
        </span>
      );

    case 'failed':
      return (
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium text-red-700 bg-red-100 ${className}`}
          style={{ backgroundColor: '#fee2e2', color: '#dc2626' }}
        >
          Failed
        </span>
      );

    default:
      return (
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium text-slate-700 bg-slate-100 ${className}`}
          style={{ backgroundColor: '#f1f5f9', color: '#475569' }}
        >
          {status}
        </span>
      );
  }
};
