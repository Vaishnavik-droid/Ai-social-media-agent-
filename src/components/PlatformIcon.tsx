import React from 'react';
import { Platform } from '../types';

interface PlatformIconProps {
  platform: Platform;
  size?: number;
  className?: string;
}

export const PlatformIcon: React.FC<PlatformIconProps> = ({
  platform,
  size = 20,
  className = ''
}) => {
  switch (platform) {
    case 'bluesky':
      return (
        <span
          className={`inline-flex items-center justify-center ${className}`}
          style={{ width: size, height: size }}
          title="Bluesky"
        >
          {/* Bluesky Butterfly SVG */}
          <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
            <path
              d="M12 10.8c1.8-3.4 4.8-6.8 8.4-6.8 1.4 0 2.6.8 2.6 2.4 0 2.2-1.3 7.8-2.1 9.4-1.2 2.4-3.5 3.2-5.4 2.8 3.5 1.5 4.5 4.3 2.5 6.2-2.8 2.6-5-1.5-6-4-1 2.5-3.2 6.6-6 4-2-1.9-1-4.7 2.5-6.2-1.9.4-4.2-.4-5.4-2.8C2.3 14.2 1 8.6 1 6.4 1 4.8 2.2 4 3.6 4c3.6 0 6.6 3.4 8.4 6.8z"
              fill="#1185FE"
            />
          </svg>
        </span>
      );

    case 'linkedin':
      return (
        <span
          className={`inline-flex items-center justify-center rounded ${className}`}
          style={{
            width: size,
            height: size,
            backgroundColor: '#0A66C2',
            borderRadius: Math.max(3, Math.round(size * 0.18))
          }}
          title="LinkedIn"
        >
          <svg width={size * 0.65} height={size * 0.65} viewBox="0 0 24 24" fill="#ffffff">
            <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
          </svg>
        </span>
      );

    case 'instagram':
      return (
        <span
          className={`inline-flex items-center justify-center ${className}`}
          style={{
            width: size,
            height: size,
            background: 'radial-gradient(circle at 30% 107%, #fdf497 0%, #fdf497 5%, #fd5949 45%, #d6249f 60%, #285AEB 90%)',
            borderRadius: Math.max(4, Math.round(size * 0.22))
          }}
          title="Instagram"
        >
          <svg
            width={size * 0.65}
            height={size * 0.65}
            viewBox="0 0 24 24"
            fill="none"
            stroke="#ffffff"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
            <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
          </svg>
        </span>
      );

    case 'facebook':
      return (
        <span
          className={`inline-flex items-center justify-center ${className}`}
          style={{
            width: size,
            height: size,
            backgroundColor: '#1877F2',
            borderRadius: '50%'
          }}
          title="Facebook"
        >
          <svg width={size * 0.65} height={size * 0.65} viewBox="0 0 24 24" fill="#ffffff">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
          </svg>
        </span>
      );



    case 'pinterest':
      return (
        <span
          className={`inline-flex items-center justify-center ${className}`}
          style={{
            width: size,
            height: size,
            backgroundColor: '#E60023',
            borderRadius: '50%'
          }}
          title="Pinterest"
        >
          <svg width={size * 0.65} height={size * 0.65} viewBox="0 0 24 24" fill="#ffffff">
            <path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738.098.119.112.224.083.345-.09.375-.291 1.199-.334 1.357-.053.225-.174.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.546.535 6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z" />
          </svg>
        </span>
      );

    case 'youtube':
      return (
        <span
          className={`inline-flex items-center justify-center ${className}`}
          style={{
            width: size,
            height: size,
            backgroundColor: '#FF0000',
            borderRadius: Math.max(4, Math.round(size * 0.22))
          }}
          title="YouTube"
        >
          <svg width={size * 0.7} height={size * 0.7} viewBox="0 0 24 24" fill="#ffffff">
            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
          </svg>
        </span>
      );

    case 'twitter':
    default:
      return (
        <span
          className={`inline-flex items-center justify-center ${className}`}
          style={{
            width: size,
            height: size,
            backgroundColor: '#000000',
            borderRadius: Math.max(3, Math.round(size * 0.18))
          }}
          title="X (Twitter)"
        >
          <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 24 24" fill="#ffffff">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
          </svg>
        </span>
      );
  }
};
