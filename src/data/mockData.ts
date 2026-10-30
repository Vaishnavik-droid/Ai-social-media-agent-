import {
  SocialPost,
  ConnectedPlatform,
  MetricSummary,
  UserProfile,
  NotificationItem,
  UserPreferences,
  UserNotifications
} from '../types';

export const mockUserProfile: UserProfile = {
  name: 'John Doe',
  email: 'user@example.com',
  avatarChar: 'J'
};

export const mockMetrics: MetricSummary = {
  totalPosts: 24,
  published: 18,
  scheduled: 4,
  failed: 2
};

export const mockUserPreferences: UserPreferences = {
  autoSuggestTimes: true,
  includeHashtags: true,
  defaultTone: 'Professional',
  defaultLanguage: 'English'
};

export const mockUserNotifications: UserNotifications = {
  emailSummary: true,
  failureAlerts: true,
  newFollowerAlerts: false
};

export const mockNotifications: NotificationItem[] = [
  {
    id: 'notif-1',
    title: 'Post "5 Tips for Better Content" scheduled for Oct 2 at 10:00 AM',
    time: '10m ago',
    unread: true,
    type: 'info'
  },
  {
    id: 'notif-2',
    title: 'Post "AI is changing social media..." published successfully',
    time: '2h ago',
    unread: true,
    type: 'success'
  },
  {
    id: 'notif-3',
    title: 'Post "Productivity Hacks" failed to reach X due to rate limit',
    time: '1d ago',
    unread: false,
    type: 'alert'
  }
];

export const mockPosts: SocialPost[] = [
  {
    id: 'post-omnipulse-ai-growth',
    title: 'Omni-Channel AI Growth',
    snippet: 'Powering Omni-Channel Growth with AI across all social channels.',
    content:
      '🚀 Powering Omni-Channel Growth with AI! ⚡\n\nScale audience reach and automate publishing seamlessly across all your social channels. The future belongs to creators and brands with high-leverage workflows.\n\n#AIMarketing #OmniChannel #Automation #Growth #PulseAI',
    platforms: ['bluesky', 'linkedin', 'facebook', 'instagram'],
    status: 'published',
    createdAt: 'Just now',
    mediaUrl: '/social_media_ai_post.jpg',
    tone: 'Inspiring',
    contentType: 'Product Launch'
  },
  {
    id: 'post-1',
    title: 'AI is changing social media...',
    snippet: 'The future belongs to creators.',
    content:
      'AI is changing social media marketing by making content creation faster, smarter and more personalized.\n\nThe future belongs to creators who use AI effectively!',
    platforms: ['linkedin', 'instagram', 'facebook'],
    status: 'published',
    createdAt: '30 Sep 2026\n10:30 AM',
    mediaUrl:
      'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600&auto=format&fit=crop&q=80',
    tone: 'Professional',
    contentType: 'General Post'
  },
  {
    id: 'post-2',
    title: '5 Tips for Better Content',
    snippet: 'Simple tips to grow faster.',
    content:
      '5 Tips for Better Content:\n1. Hook them in the first 3 seconds\n2. Solve one specific problem\n3. Format with clean spacing\n4. Add actionable takeaways\n5. Engage in comments immediately!',
    platforms: ['twitter', 'linkedin', 'instagram'],
    status: 'scheduled',
    createdAt: '02 Oct 2026\n10:00 AM',
    scheduledAt: '02 Oct 2026\n10:00 AM',
    mediaUrl:
      'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=600&auto=format&fit=crop&q=80',
    tone: 'Tips & Advice',
    contentType: 'General Post'
  },
  {
    id: 'post-3',
    title: 'New AI Tools in 2026',
    snippet: 'Top AI tools for creators.',
    content:
      'Exploring the newest wave of autonomous creative intelligence tools. Workflow automation is now a baseline requirement for high-output growth teams.',
    platforms: ['linkedin', 'facebook'],
    status: 'draft',
    createdAt: '29 Sep 2026\n04:15 PM',
    mediaUrl:
      'https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&auto=format&fit=crop&q=80',
    tone: 'Professional',
    contentType: 'Thought Leadership'
  },
  {
    id: 'post-4',
    title: 'Productivity Hacks',
    snippet: 'Boost your productivity with AI.',
    content:
      'Boost your daily output 10x with intelligent workflow batching, scheduled distribution, and real-time cross-platform feedback loops.',
    platforms: ['twitter', 'linkedin'],
    status: 'failed',
    createdAt: '28 Sep 2026\n11:20 AM',
    mediaUrl:
      'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=600&auto=format&fit=crop&q=80',
    tone: 'Productivity',
    contentType: 'Tips & Advice'
  },
  {
    id: 'post-5',
    title: 'Weekend Motivation',
    snippet: 'Stay consistent and keep going!',
    content:
      'Success in building an audience isn’t about going viral once. It’s about showing up consistently with genuine value every single week.',
    platforms: ['instagram', 'facebook'],
    status: 'published',
    createdAt: '27 Sep 2026\n09:10 AM',
    scheduledAt: '03 Oct 2026\n09:00 AM',
    mediaUrl:
      'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&auto=format&fit=crop&q=80',
    tone: 'Inspiring',
    contentType: 'General Post'
  },
  {
    id: 'post-6',
    title: 'New Features in AI',
    snippet: 'Exploring latest AI tools.',
    content:
      'Autonomous scheduling, automated tone adaptation, and seamless multi-channel distribution are live in the new update!',
    platforms: ['linkedin', 'facebook', 'instagram'],
    status: 'scheduled',
    createdAt: '26 Sep 2026\n03:00 PM',
    scheduledAt: '04 Oct 2026\n12:30 PM',
    mediaUrl:
      'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=600&auto=format&fit=crop&q=80',
    tone: 'Professional',
    contentType: 'Product Launch'
  },
  {
    id: 'post-7',
    title: 'Growth Strategies',
    snippet: 'How to grow on social media.',
    content:
      'The modern playbook for cross-platform expansion: focus on depth of connection over superficial vanity impressions.',
    platforms: ['twitter', 'linkedin'],
    status: 'scheduled',
    createdAt: '25 Sep 2026\n02:00 PM',
    scheduledAt: '05 Oct 2026\n11:00 AM',
    mediaUrl:
      'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&auto=format&fit=crop&q=80',
    tone: 'Professional',
    contentType: 'Thought Leadership'
  }
];

export const mockConnectedPlatforms: ConnectedPlatform[] = [
  {
    id: 'bluesky',
    name: 'Bluesky',
    handle: '@yourhandle.bsky.social',
    status: 'connected',
    connectedUser: '@yourhandle.bsky.social'
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    handle: 'Rushikesh Chavan',
    status: 'connected',
    connectedUser: 'Rushikesh Chavan'
  },
  {
    id: 'instagram',
    name: 'Instagram',
    handle: 'Not Connected',
    status: 'disconnected',
    connectedUser: ''
  },
  {
    id: 'facebook',
    name: 'Facebook',
    handle: 'Not Connected',
    status: 'disconnected',
    connectedUser: ''
  }
];
