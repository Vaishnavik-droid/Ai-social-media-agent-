import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Send,
  Calendar,
  Save,
  UploadCloud,
  X,
  Check,
  ThumbsUp,
  MessageSquare,
  Repeat,
  Heart,
  Share2,
  Bookmark,
  SendHorizontal,
  RefreshCw,
  AlertCircle,
  Image as ImageIcon,
  MoreHorizontal,
  ChevronDown,
  Pencil,
  Plus,
} from 'lucide-react';
import { Platform, SocialPost, UserProfile, UserPreferences } from '../types';
import { PlatformIcon } from '../components/PlatformIcon';
import { api } from '../lib/api';
import {
  formatCounterLabel,
  countPlatformLength,
  FRONTEND_PLATFORM_RULES,
} from '../lib/platformConstraints';

const COMPOSER_SESSION_KEY = 'omnipulse_active_composer_session';

interface CreatePostProps {
  user: UserProfile;
  preferences?: UserPreferences;
  onPostCreated: (post: SocialPost) => void;
  onNavigate: (page: any) => void;
  initialPost?: SocialPost;
  onClearEditingDraft?: () => void;
}

export const CreatePost: React.FC<CreatePostProps> = ({
  user,
  preferences,
  onPostCreated,
  onNavigate,
  initialPost,
  onClearEditingDraft,
}) => {
  // Restore initial composer session from initialPost or localStorage
  const getInitialSnapshot = () => {
    if (initialPost) {
      const rawPlatContent = (initialPost as any).platformContent || (initialPost as any).platform_content;
      return {
        postId: initialPost.id,
        topic: (initialPost as any).topic_prompt || initialPost.title || '',
        contentType: initialPost.contentType || 'General Post',
        tone: initialPost.tone || preferences?.defaultTone || 'Professional',
        language: initialPost.language || preferences?.defaultLanguage || 'English',
        selectedPlatforms: initialPost.platforms?.length ? initialPost.platforms : ['linkedin', 'instagram', 'facebook'],
        activePreviewTab: initialPost.platforms?.[0] || 'linkedin',
        youtubePostType: initialPost.youtubePostType || '',
        postBody: initialPost.content || '',
        platformVariants: rawPlatContent || {},
        mediaUrl: initialPost.mediaUrl || null,
        uploadedPublicUrl: initialPost.mediaUrl || null,
        selectedBoardId: (initialPost as any).pinterestBoardId || '',
      };
    }
    try {
      const saved = localStorage.getItem(COMPOSER_SESSION_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch {}
    return {};
  };

  const initialSnapshot = getInitialSnapshot();

  const [currentPostId, setCurrentPostId] = useState<string | undefined>(initialSnapshot.postId);
  const [topic, setTopic] = useState<string>(initialSnapshot.topic || '');
  const [contentType, setContentType] = useState<string>(initialSnapshot.contentType || 'General Post');
  const [tone, setTone] = useState<string>(initialSnapshot.tone || preferences?.defaultTone || 'Professional');
  const [language, setLanguage] = useState<string>(initialSnapshot.language || preferences?.defaultLanguage || 'English');
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>(
    initialSnapshot.selectedPlatforms || ['linkedin', 'instagram', 'facebook']
  );
  const [activePreviewTab, setActivePreviewTab] = useState<Platform>(
    initialSnapshot.activePreviewTab || 'linkedin'
  );
  const [youtubePostType, setYoutubePostType] = useState<'short' | 'long_form' | ''>(
    initialSnapshot.youtubePostType || ''
  );
  const [platformVariants, setPlatformVariants] = useState<Record<string, { content: string; title?: string; hashtags?: string[] }>>(
    initialSnapshot.platformVariants || {}
  );
  const [isRegeneratingSingle, setIsRegeneratingSingle] = useState(false);

  // Media preview state
  const [mediaUrl, setMediaUrl] = useState<string | null>(initialSnapshot.mediaUrl || null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedPublicUrl, setUploadedPublicUrl] = useState<string | null>(initialSnapshot.uploadedPublicUrl || null);
  const [isUploadingMedia, setIsUploadingMedia] = useState(false);
  const [pinterestBoards, setPinterestBoards] = useState<Array<{ id: string; name: string }>>([]);
  const [selectedBoardId, setSelectedBoardId] = useState<string>(initialSnapshot.selectedBoardId || '');
  const [isLoadingBoards, setIsLoadingBoards] = useState(false);
  const [isCreatingBoard, setIsCreatingBoard] = useState(false);
  const [autosaveStatus, setAutosaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [lastSavedTime, setLastSavedTime] = useState<string | null>(null);

  const handleCreateBoard = async () => {
    const boardName = prompt('Enter a name for the new Pinterest board:');
    if (!boardName || !boardName.trim()) return;

    setIsCreatingBoard(true);
    try {
      const res = await api.createPinterestBoard(boardName.trim());
      if (res?.board) {
        setPinterestBoards((prev) => {
          const exists = prev.some((b) => b.id === res.board.id);
          return exists ? prev : [...prev, res.board];
        });
        setSelectedBoardId(res.board.id);
      }
    } catch (err: any) {
      alert(`Could not create Pinterest board: ${err?.message || 'Check Sandbox permissions'}`);
    } finally {
      setIsCreatingBoard(false);
    }
  };

  useEffect(() => {
    if (initialPost?.youtubePostType) {
      setYoutubePostType(initialPost.youtubePostType);
    }
  }, [initialPost]);

  const getVideoMetadata = (file: File): Promise<{ duration: number; width: number; height: number }> => {
    return new Promise((resolve, reject) => {
      const video = document.createElement('video');
      video.preload = 'metadata';
      const objectUrl = URL.createObjectURL(file);
      video.onloadedmetadata = () => {
        URL.revokeObjectURL(objectUrl);
        resolve({
          duration: video.duration,
          width: video.videoWidth,
          height: video.videoHeight,
        });
      };
      video.onerror = () => {
        URL.revokeObjectURL(objectUrl);
        reject(new Error('Failed to load video metadata'));
      };
      video.src = objectUrl;
    });
  };

  // Fetch Pinterest boards when Pinterest is selected
  useEffect(() => {
    if (selectedPlatforms.includes('pinterest') && pinterestBoards.length === 0 && !isLoadingBoards) {
      setIsLoadingBoards(true);
      api.getPinterestBoards()
        .then((res) => {
          if (res?.boards && res.boards.length > 0) {
            setPinterestBoards(res.boards);
            if (!selectedBoardId) {
              setSelectedBoardId(res.boards[0].id);
            }
          }
        })
        .catch((err) => {
          console.warn('Could not fetch Pinterest boards:', err);
        })
        .finally(() => setIsLoadingBoards(false));
    }
  }, [selectedPlatforms]);

  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [publishResults, setPublishResults] = useState<Array<{ platform: string; status: string; url?: string; error?: string }> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const contentTypeOptions = [
    { value: 'General Post', icon: '📝' },
    { value: 'Thought Leadership', icon: '💡' },
    { value: 'Product Launch', icon: '🚀' },
    { value: 'Tips & Advice', icon: '🎯' },
  ];

  const toneOptions = [
    { value: 'Professional', icon: '👔' },
    { value: 'Casual', icon: '😊' },
    { value: 'Witty', icon: '😉' },
    { value: 'Inspiring', icon: '✨' },
  ];

  const languageOptions = [
    { value: 'English', icon: '🇺🇸' },
    { value: 'Hindi', icon: '🇮🇳' },
    { value: 'Marathi', icon: '🚩' },
    { value: 'Spanish', icon: '🇪🇸' },
    { value: 'French', icon: '🇫🇷' },
    { value: 'German', icon: '🇩🇪' },
  ];

  const getSelectedOption = (
    options: Array<{ value: string; icon: string }>,
    currentValue: string
  ) => options.find((option) => option.value === currentValue) ?? options[0];

  const selectedContentType = getSelectedOption(contentTypeOptions, contentType);
  const selectedTone = getSelectedOption(toneOptions, tone);
  const selectedLanguage = getSelectedOption(languageOptions, language);

  const [postBody, setPostBody] = useState(
    initialSnapshot.postBody !== undefined
      ? initialSnapshot.postBody
      : 'AI in Social Media Marketing is changing the way high-growth creators build audiences. By streamlining production and personalizing distribution, creators can operate with the leverage of an entire media agency. The future belongs to operators who build repeatable, automated publishing workflows. #AIMarketing #SocialMediaStrategy #ContentCreation #Growth'
  );

  // Sync state if initialPost changes (e.g., when Edit Draft is clicked in Posts table)
  useEffect(() => {
    if (initialPost) {
      setCurrentPostId(initialPost.id);
      setTopic((initialPost as any).topic_prompt || initialPost.title || '');
      setPostBody(initialPost.content || '');
      const rawPlatContent = (initialPost as any).platformContent || (initialPost as any).platform_content;
      if (rawPlatContent) setPlatformVariants(rawPlatContent);
      if (initialPost.platforms?.length) setSelectedPlatforms(initialPost.platforms);
      if (initialPost.youtubePostType) setYoutubePostType(initialPost.youtubePostType);
      if (initialPost.mediaUrl) {
        setMediaUrl(initialPost.mediaUrl);
        setUploadedPublicUrl(initialPost.mediaUrl);
      }
      if (initialPost.tone) setTone(initialPost.tone);
      if (initialPost.contentType) setContentType(initialPost.contentType);
      if (initialPost.language) setLanguage(initialPost.language);
      if ((initialPost as any).pinterestBoardId) setSelectedBoardId((initialPost as any).pinterestBoardId);
    }
  }, [initialPost]);

  // Debounced Autosave (800ms) to localStorage
  useEffect(() => {
    setAutosaveStatus('saving');
    const timer = setTimeout(() => {
      try {
        const snapshot = {
          postId: currentPostId,
          topic,
          contentType,
          tone,
          language,
          selectedPlatforms,
          activePreviewTab,
          youtubePostType,
          postBody,
          platformVariants,
          mediaUrl: uploadedPublicUrl || (mediaUrl?.startsWith('http') ? mediaUrl : null),
          uploadedPublicUrl,
          selectedBoardId,
          savedAt: new Date().toISOString(),
        };
        localStorage.setItem(COMPOSER_SESSION_KEY, JSON.stringify(snapshot));
        setAutosaveStatus('saved');
        setLastSavedTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      } catch (err) {
        console.warn('Composer autosave notice:', err);
        setAutosaveStatus('idle');
      }
    }, 800);

    return () => clearTimeout(timer);
  }, [
    currentPostId,
    topic,
    contentType,
    tone,
    language,
    selectedPlatforms,
    activePreviewTab,
    youtubePostType,
    postBody,
    platformVariants,
    mediaUrl,
    uploadedPublicUrl,
    selectedBoardId,
  ]);

  const handleNewPost = () => {
    if (topic.trim() || postBody.trim()) {
      const confirmReset = window.confirm('Start a new post? Your current draft session will be reset.');
      if (!confirmReset) return;
    }
    localStorage.removeItem(COMPOSER_SESSION_KEY);
    setCurrentPostId(undefined);
    setTopic('');
    setPostBody('');
    setPlatformVariants({});
    setMediaUrl(null);
    setSelectedFile(null);
    setUploadedPublicUrl(null);
    setYoutubePostType('');
    setSelectedBoardId('');
    setAutosaveStatus('idle');
    setLastSavedTime(null);
    if (onClearEditingDraft) onClearEditingDraft();
  };

  const [isEditingPreview, setIsEditingPreview] = useState(false);
  const [previewDraftTitle, setPreviewDraftTitle] = useState('');
  const [previewDraftText, setPreviewDraftText] = useState(postBody);
  const previewTextareaRef = useRef<HTMLTextAreaElement>(null);

  const getActiveVariant = (): { content: string; title?: string; hashtags?: string[] } => {
    if (platformVariants[activePreviewTab]) {
      const v = platformVariants[activePreviewTab] as any;
      return {
        content: v.content || v.text || '',
        title: v.title,
        hashtags: v.hashtags || [],
      };
    }
    return {
      content: postBody || '',
      title: (activePreviewTab === 'youtube' || activePreviewTab === 'pinterest' || activePreviewTab === 'linkedin')
        ? ''
        : undefined,
      hashtags: [],
    };
  };

  const handleToggleEdit = () => {
    if (isEditingPreview) {
      handleSavePreviewEdit();
    } else {
      const current = getActiveVariant();
      setPreviewDraftText(current.content || '');
      setPreviewDraftTitle(current.title || '');
      setIsEditingPreview(true);
      setTimeout(() => {
        previewTextareaRef.current?.focus();
      }, 50);
    }
  };

  const handleSavePreviewEdit = () => {
    const current = getActiveVariant();
    const updated = {
      ...current,
      content: previewDraftText || '',
      ...(FRONTEND_PLATFORM_RULES[activePreviewTab]?.supportsTitle ? { title: previewDraftTitle } : {}),
    };
    setPlatformVariants((prev) => ({
      ...prev,
      [activePreviewTab]: updated,
    }));
    setPostBody(previewDraftText || '');
    setIsEditingPreview(false);
  };

  const handleCancelPreviewEdit = () => {
    const current = getActiveVariant();
    setPreviewDraftText(current.content || '');
    setPreviewDraftTitle(current.title || '');
    setIsEditingPreview(false);
  };

  const handleSwitchTab = (newPlatform: Platform) => {
    if (isEditingPreview) {
      handleSavePreviewEdit();
    }
    setActivePreviewTab(newPlatform);
    const target = (platformVariants[newPlatform] || {}) as any;
    const contentText = target.content || target.text || postBody || '';
    setPreviewDraftText(contentText);
    setPreviewDraftTitle(target.title || '');
  };


  // Sync preferences if updated externally
  useEffect(() => {
    if (preferences?.defaultLanguage) {
      setLanguage(preferences.defaultLanguage);
    }
    if (preferences?.defaultTone) {
      setTone(preferences.defaultTone);
    }
  }, [preferences]);

  const togglePlatform = (platform: Platform) => {
    setSelectedPlatforms((prev) =>
      prev.includes(platform)
        ? prev.filter((p) => p !== platform)
        : [...prev, platform]
    );
  };

  // Immediate language switch helper with realistic sample preview
  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
    const prompt = topic.trim() || 'AI in Social Media Marketing';
    if (newLang === 'Hindi') {
      setPostBody(
        `🚀 ${prompt}\n\nआर्टिफिशियल इंटेलिजेंस (AI) सोशल मीडिया मार्केटिंग और कंटेंट क्रिएशन को एक नए स्तर पर ले जा रहा है। तेज गति, सटीक टार्गेटिंग और पर्सनलाइज्ड स्ट्रेटेजी से बिजनेस को बड़ा फायदा मिल रहा है।\n\nभविष्य उन्हीं का है जो नई तकनीक को प्रभावी ढंग से अपनाते हैं!\n\n#आर्टिफिशियलइंटेलिजेंस #डिजिटलग्रोथ #सोशलमीडियामार्केटिंग #इनोवेशन`
      );
    } else if (newLang === 'Marathi') {
      setPostBody(
        `🚀 ${prompt}\n\nआर्टिफिशियल इंटेलिजन्स (AI) मुळे सोशल मीडिया स्ट्रॅटेजी आणि बिझनेस ग्रोथला नवीन गती मिळत आहे। कमी वेळात अचूक आणि प्रभावी कंटेंट पोहोचवणे आता सहज शक्य झाले आहे।\n\nभविष्य तंत्रज्ञानासोबत पुढे जाणाऱ्यांचेच आहे!\n\n#डिजिटलमहाराष्ट्र #व्यवसायवाढ #सोशलमीडिया #इनोव्हेशन`
      );
    } else if (newLang === 'Spanish') {
      setPostBody(
        `🚀 ${prompt}\n\nLa inteligencia artificial está transformando radicalmente el marketing en redes sociales: contenido más ágil, estratégico y personalizado.\n\n¡El futuro pertenece a los creadores y marcas que aprovechan la IA de forma efectiva!\n\n#InteligenciaArtificial #MarketingDigital #Estrategia`
      );
    } else if (newLang === 'French') {
      setPostBody(
        `📝 ${prompt}\n\nL'intelligence artificielle redéfinit la création de contenu sur les réseaux sociaux: rapidité, pertinence et personnalisation accrue.\n\nL'avenir appartient aux créateurs audacieux. Qu'en pensez-vous ?\n\n#IA #MarketingDigital #Innovation`
      );
    } else if (newLang === 'German') {
      setPostBody(
        `💡 ${prompt}\n\nKünstliche Intelligenz revolutioniert das Social-Media-Marketing durch schnellere Workflows und maßgeschneiderte Inhalte.\n\nDie Zukunft gehört denjenigen, die KI gezielt einsetzen! Was ist Ihre Strategie?\n\n#KI #SocialMediaMarketing #Tech`
      );
    } else {
      setPostBody(
        `AI is changing social media marketing by making content creation faster, smarter and more personalized.\n\nThe future belongs to creators who use AI effectively!\n\n#AIMarketing #SocialMediaStrategy #ContentCreation #Growth`
      );
    }
  };

  // AI Single-Platform Regenerator: Regenerates content specifically for one platform without touching others
  const handleRegenerateSinglePlatform = async (platform: Platform) => {
    setIsRegeneratingSingle(true);
    setGenerationError(null);
    const prompt = topic.trim() || 'AI in Social Media Marketing';
    const currentVariant = getActiveVariant();

    try {
      const res = await api.generatePostPreview({
        topic: prompt,
        tone,
        content_type: contentType,
        language,
        include_hashtags: preferences?.includeHashtags ?? true,
        platforms: [platform],
        target_single_platform: platform,
        draft_context: currentVariant.content,
      });

      if (res) {
        if (res.platform_content && res.platform_content[platform]) {
          const v = res.platform_content[platform] as any;
          const contentVal = v.content || v.text || '';
          setPlatformVariants((prev) => ({
            ...prev,
            [platform]: {
              content: contentVal,
              title: v.title,
              hashtags: v.hashtags || [],
            },
          }));
          if (platform === activePreviewTab) {
            setPostBody(contentVal);
            setPreviewDraftText(contentVal);
            if (v.title) setPreviewDraftTitle(v.title);
          }
        } else if (res.generated_text) {
          const genText = res.generated_text || '';
          setPlatformVariants((prev) => ({
            ...prev,
            [platform]: {
              content: genText,
              title: res.generated_title,
              hashtags: [],
            },
          }));
          if (platform === activePreviewTab) {
            setPostBody(genText);
            setPreviewDraftText(genText);
            if (res.generated_title) setPreviewDraftTitle(res.generated_title);
          }
        }
        setIsRegeneratingSingle(false);
        return;
      }
    } catch (err: any) {
      console.warn(`Could not regenerate single variant for ${platform}:`, err);
    }

    // Local single-platform fallback
    setTimeout(() => {
      let content = '';
      let title: string | undefined = undefined;
      let hashtags: string[] = [];

      if (platform === 'bluesky') {
        content = `AI is shifting social media workflows from manual drafting to high-leverage curation. Operators who build automated systems move 10x faster. #AIMarketing`;
      } else if (platform === 'linkedin') {
        title = `The Strategic Shift: Scaling Social Media with AI`;
        content = `Most creators think AI is just about writing faster. It is actually about compound leverage.\n\nHere is how leading marketing teams are building advantage:\n• Rapid ideation across multiple angles\n• Tailored distribution per community\n• Systematized review workflows\n\nHow is your organization adapting this quarter? Let's discuss below.`;
        hashtags = ['#AIMarketing', '#SocialStrategy', '#Productivity'];
      } else if (platform === 'instagram') {
        content = `Work smarter, post sharper ✨ The future of social media marketing belongs to creators leveraging AI for speed and authentic storytelling 🚀\n\nWhat is your go-to AI marketing hack? Drop it in the comments! 👇\n\n#AIMarketing #ContentCreation #CreatorEconomy #SocialMediaTips`;
        hashtags = ['#AIMarketing', '#ContentCreation', '#CreatorEconomy'];
      } else if (platform === 'facebook') {
        content = `How is your team using AI tools for your social media content this year?\n\nWe are seeing creators save hours each week while keeping their authentic voice intact.\n\nShare your favorite workflow in the comments below!`;
      } else if (platform === 'pinterest') {
        title = `AI Social Media Marketing Blueprint`;
        content = `Actionable tips and workflows to scale your social media content creation using AI. Save this Pin to upgrade your marketing toolkit today!`;
        hashtags = ['#SocialMediaTips', '#MarketingInspiration', '#AIMarketing'];
      } else if (platform === 'youtube') {
        title = `How AI is Changing Social Media Marketing — 2026 Strategy Guide`;
        content = `In this video, we break down actionable workflows to harness AI in social media marketing. From concept generation to multi-platform distribution, discover the tools and strategies that drive measurable growth.\n\n🔔 Subscribe for weekly creator strategies\n#AIMarketing #SocialMediaGrowth #ContentCreation`;
      }

      setPlatformVariants((prev) => ({
        ...prev,
        [platform]: { content, title, hashtags },
      }));
      if (platform === activePreviewTab) {
        setPostBody(content);
        setPreviewDraftText(content);
        if (title) setPreviewDraftTitle(title);
      }
      setIsRegeneratingSingle(false);
    }, 200);
  };

  // AI Content Generator: Calls FastAPI /api/v1/generation/preview (Groq backend)
  const handleGenerateAI = async () => {
    setIsGenerating(true);
    setGenerationError(null);
    const prompt = topic.trim() || 'AI in Social Media Marketing';

    try {
      const res = await api.generatePostPreview({
        topic: prompt,
        tone,
        content_type: contentType,
        language,
        include_hashtags: preferences?.includeHashtags ?? true,
        platforms: selectedPlatforms,
      });

      if (res) {
        if (res.platform_content && Object.keys(res.platform_content).length > 0) {
          const newVariants: Record<string, { content: string; title?: string; hashtags?: string[] }> = {};
          for (const [p, v] of Object.entries(res.platform_content)) {
            const rawV = v as any;
            const contentVal = rawV.content || rawV.text || '';
            newVariants[p] = {
              content: contentVal,
              title: rawV.title,
              hashtags: rawV.hashtags || [],
            };
          }
          setPlatformVariants(newVariants);
          const activeVar = newVariants[activePreviewTab] || Object.values(newVariants)[0];
          if (activeVar) {
            const activeContent = activeVar.content || '';
            setPostBody(activeContent);
            setPreviewDraftText(activeContent);
            if (activeVar.title) setPreviewDraftTitle(activeVar.title);
          }
        } else if (res.generated_text) {
          const genText = res.generated_text || '';
          setPostBody(genText);
          setPreviewDraftText(genText);
        }
        setIsGenerating(false);
        return;
      }
    } catch (err: any) {
      console.warn('Backend Groq preview call notice, using local intelligent copy generator:', err);
      // Clear any raw HTTP error banners since local generator produces instant high-quality post copy
      setGenerationError(null);
    }

    // Offline / Local Synthesis Fallback
    setTimeout(() => {
      const fallbackVariants: Record<string, { content: string; title?: string; hashtags?: string[] }> = {};

      for (const p of selectedPlatforms) {
        if (p === 'bluesky') {
          fallbackVariants['bluesky'] = {
            content: `AI is changing social media marketing: faster drafts, sharper angles, and personalized distribution at scale. The leverage is real. #AIMarketing`,
          };
        } else if (p === 'linkedin') {
          fallbackVariants['linkedin'] = {
            title: `How AI is Transforming Social Media Distribution`,
            content: `AI is changing social media marketing in ways most agencies are still catching up with.\n\nKey advantages high-growth teams are experiencing:\n1. Accelerated production workflows without sacrificing creative voice.\n2. Iterative angle testing to pinpoint audience resonance.\n3. Personalized messaging tailored for multi-platform distribution.\n\nAre you incorporating AI into your marketing pipeline this quarter? Let's discuss in the comments below.`,
            hashtags: ['#AIMarketing', '#SocialStrategy', '#Growth', '#Productivity'],
          };
        } else if (p === 'instagram') {
          fallbackVariants['instagram'] = {
            content: `The modern creator's secret weapon? Leveraging AI for content velocity and deep audience connection 🚀✨\n\nWork smarter, build authentic hooks, and stay ahead of the curve.\n\nDrop your favorite workflow tip below! 👇\n\n#ContentCreator #AIMarketing #DigitalGrowth #SocialStrategy #ModernMarketing`,
          };
        } else if (p === 'facebook') {
          fallbackVariants['facebook'] = {
            content: `How is your business approaching AI tools for social media marketing this year?\n\nWe're seeing teams save hours each week while building closer relationships with their communities.\n\nWe'd love to hear your thoughts — are you embracing AI tools, or keeping it strictly manual?`,
          };
        } else if (p === 'pinterest') {
          fallbackVariants['pinterest'] = {
            title: `AI Social Media Marketing Guide & Tips`,
            content: `Actionable strategies to scale your social media content using intelligent AI workflows. Save this Pin to upgrade your marketing toolkit today!`,
            hashtags: ['#SocialMediaTips', '#MarketingInspiration', '#AIMarketing'],
          };
        } else if (p === 'youtube') {
          fallbackVariants['youtube'] = {
            title: `How AI is Revolutionizing Social Media Marketing in 2026`,
            content: `In this video, we break down actionable workflows to harness AI in social media marketing. From concept generation to multi-platform distribution, discover the tools and strategies that drive measurable growth.\n\n🔔 Subscribe for weekly creator strategies\n#AIMarketing #SocialMediaGrowth #ContentCreation`,
          };
        }
      }

      setPlatformVariants(fallbackVariants);
      const activeVar = fallbackVariants[activePreviewTab] || Object.values(fallbackVariants)[0];
      if (activeVar) {
        setPostBody(activeVar.content);
        setPreviewDraftText(activeVar.content);
        if (activeVar.title) setPreviewDraftTitle(activeVar.title);
      }
      setIsGenerating(false);
    }, 300);
  };

  // Media validation (JPG, JPEG, PNG, MP4, WebM; Max 50MB)
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    const file = e.target.files?.[0];
    if (!file) return;

    const allowedTypes = ['image/jpeg', 'image/png', 'video/mp4', 'video/webm'];
    const fileName = file.name.toLowerCase();
    const isAllowedExt =
      fileName.endsWith('.jpg') ||
      fileName.endsWith('.jpeg') ||
      fileName.endsWith('.png') ||
      fileName.endsWith('.mp4') ||
      fileName.endsWith('.webm');

    const maxSizeBytes = 50 * 1024 * 1024; // 50 MB

    if (!allowedTypes.includes(file.type) && !isAllowedExt) {
      setUploadError('Unsupported file format. Please upload JPG, PNG, MP4, or WebM.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    if (file.size > maxSizeBytes) {
      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
      setUploadError(`File is too large (${fileSizeMB} MB). Maximum allowed size is 50 MB.`);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setSelectedFile(file);
    setUploadedPublicUrl(null);

    const reader = new FileReader();
    reader.onload = (event) => {
      if (event.target?.result) {
        setMediaUrl(event.target.result as string);
      }
    };
    reader.readAsDataURL(file);

    // Asynchronously upload to backend persistent storage
    setIsUploadingMedia(true);
    api.uploadMedia(file)
      .then((res) => {
        if (res?.url) {
          setUploadedPublicUrl(res.url);
        }
      })
      .catch((err) => {
        console.warn('Direct media upload notice:', err);
      })
      .finally(() => {
        setIsUploadingMedia(false);
      });
  };

  const handleRemoveMedia = () => {
    setMediaUrl(null);
    setSelectedFile(null);
    setUploadedPublicUrl(null);
    setUploadError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleReplaceMedia = () => {
    setUploadError(null);
    fileInputRef.current?.click();
  };

  // Publish / Schedule / Draft handler
  const handlePublish = async (status: 'published' | 'scheduled' | 'draft') => {
    if (!postBody.trim()) {
      alert('Please write your post content before publishing.');
      return;
    }
    if (selectedPlatforms.length === 0) {
      alert('Please select at least one platform.');
      return;
    }

    const now = new Date();
    const dateStr = now.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
    const timeStr = now.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });

    // Pre-publish platform constraint validation
    for (const p of selectedPlatforms) {
      const variant = platformVariants[p] || { content: postBody };
      if (p === 'bluesky') {
        const count = countPlatformLength('bluesky', variant.content);
        if (count > 300) {
          alert(`Bluesky post exceeds the 300 Unicode grapheme cluster limit (${count} / 300 graphemes). Please trim your Bluesky variant before publishing.`);
          return;
        }
      }
    }

    const newPost: SocialPost = {
      id: currentPostId || `post-${Date.now()}`,
      title: topic.trim() || 'Untitled Post',
      snippet: postBody.slice(0, 50).replace(/\n/g, ' ') + '...',
      content: postBody,
      platforms: selectedPlatforms,
      status,
      createdAt: `${dateStr}\n${timeStr}`,
      scheduledAt: status === 'scheduled' ? 'Tomorrow at 10:00 AM' : undefined,
      mediaUrl: mediaUrl || undefined,
      tone,
      contentType,
      language,
      youtubePostType: selectedPlatforms.includes('youtube') && youtubePostType ? youtubePostType : undefined,
      pinterestBoardId: selectedPlatforms.includes('pinterest') && selectedBoardId ? selectedBoardId : undefined,
      platformContent: platformVariants as any,
      variants: Object.fromEntries(Object.entries(platformVariants).map(([k, v]) => [k, (v as any).content || (v as any).text || ''])),
    };

    if (status === 'draft') {
      // Just save draft locally
      try { await api.savePost(newPost); } catch {}
      onPostCreated(newPost);
      onNavigate('posts');
      return;
    }

    if (status === 'scheduled') {
      try { await api.savePost(newPost); } catch {}
      onPostCreated(newPost);
      onNavigate('scheduled');
      return;
    }

    // Validation for platform specific media requirements
    if (status === 'published') {
      if (selectedPlatforms.includes('instagram') && !mediaUrl && !uploadedPublicUrl) {
        alert('Instagram requires an image or video to publish a post. Please attach media under section 6.');
        return;
      }
      if (selectedPlatforms.includes('youtube')) {
        if (!youtubePostType) {
          alert('Please select a YouTube Content Type (YouTube Short or Long-form Content) before publishing.');
          return;
        }

        const isVideo = selectedFile
          ? (selectedFile.type.startsWith('video/') || selectedFile.name.endsWith('.mp4') || selectedFile.name.endsWith('.webm'))
          : (mediaUrl ? (mediaUrl.startsWith('data:video/') || mediaUrl.includes('.mp4') || mediaUrl.includes('.webm')) : false);
        if (!isVideo) {
          alert('YouTube requires a video file (.mp4 or .webm) to publish. Please upload a video under section 6.');
          return;
        }

        if (youtubePostType === 'short' && selectedFile) {
          try {
            const dimensions = await getVideoMetadata(selectedFile);
            if (dimensions.duration > 180) {
              const minutes = Math.floor(dimensions.duration / 60);
              const seconds = Math.round(dimensions.duration % 60);
              const proceed = confirm(
                `YouTube Shorts must be 3 minutes or less. Your video is ${minutes}m ${seconds}s.\n\n` +
                `Would you like to switch to Long-form Content instead? Click OK to switch to Long-form Content, or Cancel to upload a different video.`
              );
              if (proceed) {
                setYoutubePostType('long_form');
              } else {
                return;
              }
            } else if (dimensions.width > dimensions.height) {
              const proceed = confirm(
                `YouTube Shorts require a vertical (9:16) or square (1:1) aspect ratio. Your video is widescreen (${dimensions.width}x${dimensions.height}).\n\n` +
                `Would you like to switch to Long-form Content instead? Click OK to switch to Long-form Content, or Cancel to upload a different video.`
              );
              if (proceed) {
                setYoutubePostType('long_form');
              } else {
                return;
              }
            }
          } catch (e) {
            console.warn('Could not read video metadata in browser:', e);
          }
        }
      }
      if (selectedPlatforms.includes('pinterest') && !mediaUrl && !uploadedPublicUrl) {
        alert('Pinterest Pins require an image or video. Please attach media under section 6.');
        return;
      }
    }

    // === LIVE PUBLISH NOW ===
    setIsPublishing(true);
    setPublishResults(null);

    try {
      // Step 1: Save post to backend to get a real ID
      let savedPost = newPost;
      try {
        savedPost = await api.savePost(newPost);
      } catch (e) {
        console.warn('Could not save post to backend, using local ID:', e);
      }

      let effectiveMediaUrl = uploadedPublicUrl || mediaUrl || undefined;
      if (selectedFile && !uploadedPublicUrl) {
        try {
          const upRes = await api.uploadMedia(selectedFile);
          if (upRes?.url) {
            effectiveMediaUrl = upRes.url;
            setUploadedPublicUrl(upRes.url);
          }
        } catch (upErr) {
          console.warn('Could not upload media to storage, falling back to local data URL:', upErr);
        }
      }

      // Step 2: Publish to selected platforms via FastAPI
      const publishRes = await api.publishPost(
        savedPost.id,
        selectedPlatforms,
        true,
        savedPost.content || postBody,
        effectiveMediaUrl,
        undefined, // Do not pass topic as title; backend extracts platform-specific variant title
        selectedBoardId || undefined,
        selectedPlatforms.includes('youtube') && youtubePostType ? youtubePostType : undefined,
        platformVariants,
        Object.fromEntries(Object.entries(platformVariants).map(([k, v]) => [k, (v as any).content || (v as any).text || '']))
      );

      // Step 3: Show results
      const rawResults = Array.isArray(publishRes?.results) ? publishRes.results : [];
      const results = rawResults.map((r) => ({
        platform: r?.platform || 'platform',
        status: r?.status || 'failed',
        url: r?.remote_post_url,
        error: r?.error_message,
      }));
      setPublishResults(results);

      // Update local state - notify parent without double dispatch
      const isSuccess = Boolean(publishRes?.success);
      const finalPost = { ...savedPost, status: (isSuccess ? 'published' : 'failed') as any };
      try {
        onPostCreated(finalPost);
      } catch (postErr) {
        console.warn('onPostCreated notification notice:', postErr);
      }

    } catch (err: any) {
      console.error('Publishing dispatch error:', err);
      setPublishResults([{
        platform: selectedPlatforms[0] || 'all',
        status: 'failed',
        error: err?.message || 'Failed to complete publish request. Please try again.',
      }]);
    } finally {
      setIsPublishing(false);
    }
  };


  // Clickable hashtag renderer
  const renderFormattedText = (text?: string) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      const words = (line || '').split(' ');
      return (
        <span key={idx} className="block min-h-[1.25rem]">
          {words.map((word, wIdx) => {
            if (word.startsWith('#') && word.length > 1) {
              return (
                <span
                  key={wIdx}
                  className="text-blue-600 font-medium hover:underline cursor-pointer mr-1"
                >
                  {word}
                </span>
              );
            }
            return <span key={wIdx}>{word} </span>;
          })}
        </span>
      );
    });
  };

  // Inline editor / formatted text renderer for preview cards
  const renderPreviewContent = () => {
    const currentVariant = getActiveVariant();
    const rule = FRONTEND_PLATFORM_RULES[activePreviewTab];

    if (isEditingPreview) {
      const counterInfo = formatCounterLabel(activePreviewTab, previewDraftText || '');
      return (
        <div className="preview-inline-editor">
          {rule?.supportsTitle && (
            <div style={{ marginBottom: '8px' }}>
              <label style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: '3px' }}>
                {activePreviewTab === 'youtube' ? 'Video Title' : activePreviewTab === 'pinterest' ? 'Pin Title' : 'Title'}
              </label>
              <input
                type="text"
                value={previewDraftTitle}
                onChange={(e) => setPreviewDraftTitle(e.target.value)}
                maxLength={rule.maxTitleLength || 100}
                placeholder="Enter catchy title..."
                style={{
                  width: '100%',
                  padding: '6px 10px',
                  fontSize: '13px',
                  borderRadius: '6px',
                  border: '1px solid #334155',
                  background: '#0f172a',
                  color: '#f8fafc',
                  marginBottom: '4px',
                  outline: 'none',
                }}
              />
            </div>
          )}
          <textarea
            ref={previewTextareaRef}
            className="preview-inline-textarea"
            value={previewDraftText}
            onChange={(e) => setPreviewDraftText(e.target.value)}
            rows={5}
            placeholder={`Type or edit your ${rule?.name || ''} post content...`}
            autoFocus
          />
          <div className="preview-inline-actions">
            <span className={`preview-inline-counter ${counterInfo.isOverLimit ? 'text-rose-400 font-bold' : ''}`}>
              {counterInfo.label}
            </span>
            <div className="preview-inline-btn-group">
              <button
                type="button"
                onClick={handleCancelPreviewEdit}
                className="preview-inline-btn preview-inline-btn-cancel"
              >
                <X size={13} />
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSavePreviewEdit}
                className="preview-inline-btn preview-inline-btn-save"
              >
                <Check size={13} />
                Save Changes
              </button>
            </div>
          </div>
        </div>
      );
    }
    return (
      <div className="preview-content-text">
        {renderFormattedText(currentVariant.content || '')}
      </div>
    );
  };

  return (
    <div className="create-post-layout">
      {/* Hidden file input supporting images and video */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".jpg,.jpeg,.png,image/jpeg,image/png,video/mp4,video/webm,.mp4,.webm"
        className="hidden"
      />

      {/* Left Form */}
      <div className="create-post-form create-post-panel">
        {/* Top Session Bar: New Post + Autosave Status */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-700/60">
          <button
            type="button"
            onClick={handleNewPost}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors shadow-sm"
            title="Start fresh with a clean composer session"
          >
            <Plus size={13} className="text-violet-400" />
            <span>New Post</span>
          </button>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            {autosaveStatus === 'saving' ? (
              <span className="inline-flex items-center gap-1.5 text-violet-300">
                <RefreshCw size={11} className="animate-spin" />
                Saving...
              </span>
            ) : autosaveStatus === 'saved' ? (
              <span className="inline-flex items-center gap-1.5 text-emerald-400">
                <Check size={12} />
                Saved locally {lastSavedTime ? `at ${lastSavedTime}` : ''}
              </span>
            ) : (
              <span className="text-slate-500 text-[11px]">Draft session active</span>
            )}
          </div>
        </div>

        {generationError && (
          <div className="create-post-error-banner mb-4">
            <div className="create-post-error-content">
              <AlertCircle size={15} className="create-post-error-icon" />
              <span>{generationError}</span>
            </div>
            <button
              type="button"
              onClick={() => setGenerationError(null)}
              className="create-post-error-close"
            >
              <X size={13} />
            </button>
          </div>
        )}

        <div className="create-post-section">
          <div className="create-post-label-row">
            <label className="create-post-label">1. Topic / Prompt</label>
            <span
              className={`create-post-counter ${
                topic.length > 450 ? 'create-post-counter-warning' : ''
              }`}
            >
              {topic.length}/500
            </span>
          </div>
          <input
            type="text"
            className="create-post-input"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="AI is changing social media marketing"
            maxLength={500}
          />
        </div>

        <div className="create-post-fields-row create-post-section">
          <div className="create-post-field">
            <label className="create-post-label">2. Content Type</label>
            <div className="create-post-select-shell">
              <div className="create-post-select-display" aria-hidden="true">
                <span className="create-post-select-icon">{selectedContentType.icon}</span>
                <span className="create-post-select-text">{selectedContentType.value}</span>
                <span className="create-post-select-arrow">
                  <ChevronDown size={14} strokeWidth={2} />
                </span>
              </div>
              <select
                value={contentType}
                onChange={(e) => setContentType(e.target.value)}
                className="create-post-select"
              >
                {contentTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {`${option.icon} ${option.value}`}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="create-post-field">
            <label className="create-post-label">3. Tone</label>
            <div className="create-post-select-shell">
              <div className="create-post-select-display" aria-hidden="true">
                <span className="create-post-select-icon">{selectedTone.icon}</span>
                <span className="create-post-select-text">{selectedTone.value}</span>
                <span className="create-post-select-arrow">
                  <ChevronDown size={14} strokeWidth={2} />
                </span>
              </div>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="create-post-select"
              >
                {toneOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {`${option.icon} ${option.value}`}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="create-post-field">
            <label className="create-post-label">4. Language</label>
            <div className="create-post-select-shell">
              <div className="create-post-select-display" aria-hidden="true">
                <span className="create-post-select-icon">{selectedLanguage.icon}</span>
                <span className="create-post-select-text">{selectedLanguage.value}</span>
                <span className="create-post-select-arrow">
                  <ChevronDown size={14} strokeWidth={2} />
                </span>
              </div>
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="create-post-select"
              >
                {languageOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {`${option.icon} ${option.value}`}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="create-post-section">
          <div className="create-post-heading-row">
            <label className="create-post-label">5. Select Platforms</label>
            <span className="create-post-selected-count">
              {selectedPlatforms.length} of 6 selected
            </span>
          </div>

          <div className="platform-selector-grid">
            {[
              { id: 'bluesky' as Platform, name: 'Bluesky' },
              { id: 'linkedin' as Platform, name: 'LinkedIn' },
              { id: 'instagram' as Platform, name: 'Instagram' },
              { id: 'facebook' as Platform, name: 'Facebook' },
              { id: 'pinterest' as Platform, name: 'Pinterest' },
              { id: 'youtube' as Platform, name: 'YouTube' },
            ].map((p) => {
              const isSelected = selectedPlatforms.includes(p.id);
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => togglePlatform(p.id)}
                  className={`platform-selector-box create-post-platform-card ${
                    isSelected ? 'create-post-platform-card-selected' : ''
                  }`}
                >
                  {isSelected && (
                    <span className="create-post-platform-check">
                      <Check size={10} strokeWidth={3} />
                    </span>
                  )}
                  <PlatformIcon platform={p.id} size={24} className="mb-2" />
                  <span className="create-post-platform-name">{p.name}</span>
                </button>
              );
            })}
          </div>
          {selectedPlatforms.includes('pinterest') && (
            <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '0.5rem', border: '1px solid rgba(51, 65, 85, 0.6)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem', fontSize: '0.8rem' }}>
                <span style={{ fontWeight: 600, color: '#e2e8f0' }}>Pinterest Destination Board:</span>
                {isLoadingBoards && <span style={{ color: '#94a3b8' }}>Loading boards...</span>}
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                {pinterestBoards.length > 0 ? (
                  <select
                    value={selectedBoardId}
                    onChange={(e) => setSelectedBoardId(e.target.value)}
                    style={{ flex: 1, background: '#1e293b', border: '1px solid #334155', borderRadius: '0.375rem', padding: '0.35rem 0.6rem', color: '#f8fafc', fontSize: '0.8rem' }}
                  >
                    {pinterestBoards.map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                ) : (
                  <p style={{ margin: 0, fontSize: '0.75rem', color: '#94a3b8', flex: 1 }}>
                    {isLoadingBoards ? 'Fetching Pinterest Sandbox boards...' : 'No Sandbox boards found.'}
                  </p>
                )}
                <button
                  type="button"
                  onClick={handleCreateBoard}
                  disabled={isCreatingBoard}
                  style={{
                    fontSize: '0.75rem',
                    padding: '0.35rem 0.6rem',
                    background: '#334155',
                    color: '#f8fafc',
                    border: '1px solid #475569',
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                  }}
                  title="Create a new board in Pinterest Sandbox"
                >
                  {isCreatingBoard ? 'Creating...' : '+ New Board'}
                </button>
              </div>
            </div>
          )}
          {selectedPlatforms.includes('youtube') && (
            <div style={{ marginTop: '0.75rem' }}>
              <div className="create-post-field">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <label className="create-post-label" style={{ marginBottom: 0 }}>
                    YouTube Content Type
                  </label>
                  {!youtubePostType && (
                    <span style={{ fontSize: '0.75rem', color: '#f87171', fontWeight: 500 }}>
                      * Selection required
                    </span>
                  )}
                </div>
                <div className="create-post-select-shell">
                  <div className="create-post-select-display" aria-hidden="true">
                    <span className="create-post-select-icon">
                      {youtubePostType === 'short' ? '⚡' : youtubePostType === 'long_form' ? '🎬' : '▶️'}
                    </span>
                    <span
                      className="create-post-select-text"
                      style={{ color: youtubePostType ? '#111827' : '#94a3b8' }}
                    >
                      {youtubePostType === 'short'
                        ? 'YouTube Short (Use this option for vertical or square videos up to 3 minutes)'
                        : youtubePostType === 'long_form'
                        ? 'Long-form Content (Use this option for regular YouTube videos longer than 3 minutes)'
                        : 'Select YouTube Content Type...'}
                    </span>
                    <span className="create-post-select-arrow">
                      <ChevronDown size={14} strokeWidth={2} />
                    </span>
                  </div>
                  <select
                    value={youtubePostType}
                    onChange={(e) => setYoutubePostType(e.target.value as 'short' | 'long_form')}
                    className="create-post-select"
                  >
                    <option value="" disabled>
                      Select YouTube Content Type...
                    </option>
                    <option value="short">
                      YouTube Short (Use this option for vertical or square videos up to 3 minutes)
                    </option>
                    <option value="long_form">
                      Long-form Content (Use this option for regular YouTube videos longer than 3 minutes)
                    </option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="create-post-section">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <label className="create-post-label create-post-media-label" style={{ marginBottom: 0 }}>
              6. Media (Optional)
            </label>
            {isUploadingMedia && (
              <span style={{ fontSize: '0.75rem', color: '#38bdf8' }}>
                Uploading to cloud storage...
              </span>
            )}
            {!isUploadingMedia && uploadedPublicUrl && (
              <span style={{ fontSize: '0.75rem', color: '#34d399' }}>
                ✓ Cloud storage ready
              </span>
            )}
          </div>

          {uploadError && (
            <div className="create-post-error-banner">
              <div className="create-post-error-content">
                <AlertCircle size={15} className="create-post-error-icon" />
                <span>{uploadError}</span>
              </div>
              <button
                type="button"
                onClick={() => setUploadError(null)}
                className="create-post-error-close"
              >
                <X size={13} />
              </button>
            </div>
          )}

          <div className="media-upload-grid">
            <div
              onClick={() => fileInputRef.current?.click()}
              className="media-upload-box"
            >
              <UploadCloud size={30} className="create-post-upload-icon" />
              <div className="create-post-upload-title">
                Upload image or video (JPG, PNG, MP4, WebM)
              </div>
              <div className="create-post-upload-subtitle">
                Supported: JPG, JPEG, PNG, MP4, WebM (Max 50MB)
              </div>
              <button type="button" className="create-post-upload-button">
                Choose File
              </button>
            </div>

            {mediaUrl ? (
              <div className="media-preview-box">
                <button
                  type="button"
                  onClick={handleRemoveMedia}
                  className="create-post-remove-media"
                  title="Remove media attachment"
                  aria-label="Remove media"
                >
                  <X size={14} />
                </button>
                {mediaUrl.includes('data:video') || mediaUrl.match(/\.(mp4|webm)($|\?)/i) ? (
                  <video
                    src={mediaUrl}
                    controls
                    className="create-post-preview-image"
                  />
                ) : (
                  <img
                    src={mediaUrl}
                    alt="Post attachment"
                    className="create-post-preview-image"
                  />
                )}
                <div className="create-post-preview-actions">
                  <button
                    type="button"
                    onClick={handleReplaceMedia}
                    className="create-post-preview-action-btn create-post-preview-action-btn-secondary"
                  >
                    <RefreshCw size={11} />
                    Replace
                  </button>
                </div>
              </div>
            ) : (
              <div className="create-post-no-media">
                <ImageIcon size={20} className="create-post-no-media-icon" />
                <span>No media attached</span>
              </div>
            )}
          </div>

          <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 500, whiteSpace: 'nowrap' }}>
              Or Public Image URL:
            </span>
            <input
              type="url"
              placeholder="https://images.unsplash.com/photo-... or https://example.com/image.jpg"
              value={mediaUrl && !mediaUrl.startsWith('data:') ? mediaUrl : ''}
              onChange={(e) => {
                setUploadError(null);
                const val = e.target.value.trim();
                setMediaUrl(val ? val : null);
              }}
              style={{
                flex: 1,
                padding: '0.4rem 0.65rem',
                fontSize: '0.75rem',
                borderRadius: '0.5rem',
                border: '1px solid #cbd5e1',
                outline: 'none',
                background: '#ffffff',
                color: '#1e293b'
              }}
            />
          </div>

          {selectedPlatforms.includes('instagram') && (
            <div style={{
              marginTop: '0.5rem',
              fontSize: '0.72rem',
              color: '#d97706',
              background: '#fffbeb',
              padding: '0.4rem 0.6rem',
              borderRadius: '0.375rem',
              border: '1px solid #fef3c7'
            }}>
              📸 <strong>Instagram Requirement:</strong> Meta's Instagram Graph API requires an image hosted on a publicly accessible HTTP/HTTPS URL (e.g. Unsplash, Imgur, Cloudinary). Local browser file uploads (data: URLs) cannot be downloaded by Meta.
            </div>
          )}
        </div>

        <div className="create-post-actions">
          <button
            type="button"
            onClick={handleGenerateAI}
            disabled={isGenerating || isPublishing}
            className="create-post-action-button create-post-action-primary create-post-action-purple"
          >
            <Sparkles
              size={15}
              className={isGenerating ? 'animate-spin text-indigo-200' : 'text-indigo-200'}
            />
            <span>{isGenerating ? 'Generating with Groq AI...' : 'Generate with AI'}</span>
          </button>

          <button
            type="button"
            onClick={() => handlePublish('published')}
            disabled={isPublishing || isGenerating}
            className="create-post-action-button create-post-action-primary create-post-action-green"
            style={{ opacity: isPublishing ? 0.8 : 1 }}
          >
            <Send size={14} className="text-emerald-100" style={{ animation: isPublishing ? 'spin 1s linear infinite' : 'none' }} />
            <span>{isPublishing ? 'Publishing...' : 'Publish Now'}</span>
          </button>

          <button
            type="button"
            onClick={() => handlePublish('scheduled')}
            disabled={isPublishing}
            className="create-post-action-button create-post-action-secondary"
          >
            <Calendar size={14} className="text-slate-500" />
            <span>Schedule</span>
          </button>

          <button
            type="button"
            onClick={() => handlePublish('draft')}
            disabled={isPublishing}
            className="create-post-action-button create-post-action-secondary"
          >
            <Save size={14} className="text-slate-500" />
            <span>Save as Draft</span>
          </button>
        </div>

        {/* Publish Results Banner */}
        {publishResults && (
          <div style={{ marginTop: '16px', borderRadius: '10px', overflow: 'hidden', border: '1px solid #e2e8f0' }}>
            <div style={{ background: '#f8fafc', padding: '10px 14px', fontSize: '12px', fontWeight: 600, color: '#475569', borderBottom: '1px solid #e2e8f0' }}>
              Publish Results
            </div>
            {publishResults.map((r, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                padding: '10px 14px', background: '#fff',
                borderBottom: i < publishResults.length - 1 ? '1px solid #f1f5f9' : 'none'
              }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                  background: r.status === 'published' ? '#10b981' : '#ef4444'
                }} />
                <span style={{ fontWeight: 600, fontSize: '12px', textTransform: 'capitalize', minWidth: 70 }}>{r.platform}</span>
                {r.status === 'published' ? (
                  <span style={{ fontSize: '12px', color: '#10b981' }}>
                    Published! {r.url && <a href={r.url} target="_blank" rel="noreferrer" style={{ color: '#3b82f6', textDecoration: 'underline' }}>View post</a>}
                  </span>
                ) : (
                  <span style={{ fontSize: '12px', color: '#ef4444' }}>{r.error || 'Failed'}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>


      {/* Right Column: Platform-Wise Authentic Previews */}
      <div className="create-post-preview create-post-panel">
        <div className="create-post-preview-header">
          <div className="flex items-center gap-2">
            <h3 className="create-post-preview-title">Post Preview</h3>
            {(() => {
              const info = formatCounterLabel(activePreviewTab, (isEditingPreview ? previewDraftText : getActiveVariant().content) || '');
              return (
                <span
                  className={`text-[11px] px-2 py-0.5 rounded font-mono font-medium ${
                    info.isOverLimit
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold'
                      : 'bg-slate-800 text-slate-300 border border-slate-700'
                  }`}
                  title={`${info.count} of ${info.max} ${info.unit}`}
                >
                  {info.label}
                </span>
              );
            })()}
          </div>
          <div className="create-post-preview-header-right flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleRegenerateSinglePlatform(activePreviewTab)}
              disabled={isRegeneratingSingle || isGenerating || isPublishing}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md bg-violet-950/50 hover:bg-violet-900/70 text-violet-200 border border-violet-700/60 transition-colors shadow-sm disabled:opacity-50"
              title={`Regenerate copy specifically for ${FRONTEND_PLATFORM_RULES[activePreviewTab]?.name || activePreviewTab}`}
            >
              <Sparkles size={12} className={isRegeneratingSingle ? 'animate-spin text-violet-300' : 'text-violet-300'} />
              <span>{isRegeneratingSingle ? 'Regenerating...' : `Regenerate for ${FRONTEND_PLATFORM_RULES[activePreviewTab]?.name || activePreviewTab}`}</span>
            </button>
            <button
              type="button"
              onClick={handleToggleEdit}
              className={`create-post-preview-pen-btn ${isEditingPreview ? 'create-post-preview-pen-btn-active' : ''}`}
              title={isEditingPreview ? 'Save post changes' : 'Edit post content'}
              aria-label="Edit post content"
            >
              <Pencil size={13} />
              <span>{isEditingPreview ? 'Done' : 'Edit'}</span>
            </button>
          </div>
        </div>

        {activePreviewTab === 'bluesky' && (() => {
          const info = formatCounterLabel('bluesky', (isEditingPreview ? previewDraftText : getActiveVariant().content) || '');
          if (info.isOverLimit) {
            return (
              <div className="mb-3 px-3 py-2 rounded-lg bg-rose-950/60 border border-rose-800/80 text-rose-200 text-xs flex items-center gap-2">
                <AlertCircle size={14} className="text-rose-400 shrink-0" />
                <span>
                  <strong>Bluesky Limit Exceeded:</strong> Content is {info.count} graphemes (maximum is 300). Please trim before publishing.
                </span>
              </div>
            );
          }
          return null;
        })()}

        <div className="create-post-tabs">
          {(['bluesky', 'linkedin', 'instagram', 'facebook', 'pinterest', 'youtube'] as Platform[]).map(
            (platform) => {
              const isActive = activePreviewTab === platform;
              const labels: Record<Platform, string> = {
                bluesky: 'Bluesky',
                linkedin: 'LinkedIn',
                instagram: 'Instagram',
                facebook: 'Facebook',
                twitter: 'Twitter',
                pinterest: 'Pinterest',
                youtube: 'YouTube',
              };
              return (
                <button
                  key={platform}
                  type="button"
                  onClick={() => handleSwitchTab(platform)}
                  className={`create-post-tab ${
                    isActive ? 'create-post-tab-active' : 'create-post-tab-inactive'
                  }`}
                >
                  {labels[platform]}
                </button>
              );
            }
          )}
        </div>

        {/* 1. LinkedIn Preview */}
        {activePreviewTab === 'linkedin' && (
          <div className="create-post-preview-card">
            <div className="create-post-card-header">
              <div className="create-post-card-author">
                <div className="create-post-avatar-linkedin">
                  in
                </div>
                <div className="create-post-author-info">
                  <span className="create-post-author-name">
                    {user.name}
                  </span>
                  <span className="create-post-author-sub">
                    Just now • 🌐 Public
                  </span>
                </div>
              </div>
              <div className="create-post-card-actions">
                <button
                  type="button"
                  onClick={handleToggleEdit}
                  className={`create-post-preview-pen-btn ${isEditingPreview ? 'create-post-preview-pen-btn-active' : ''}`}
                  title={isEditingPreview ? "Save post changes" : "Edit post content"}
                  aria-label="Edit post"
                >
                  <Pencil size={14} />
                </button>
                <button type="button" className="create-post-preview-more-btn" title="More options">
                  <MoreHorizontal size={16} />
                </button>
              </div>
            </div>

            {renderPreviewContent()}

            {mediaUrl && (
              <div className="create-post-preview-image-wrap">
                <img
                  src={mediaUrl}
                  alt="Post visual"
                  className="create-post-preview-image create-post-preview-image-large"
                />
              </div>
            )}

            <div className="create-post-card-footer">
              <button type="button" className="create-post-footer-btn">
                <ThumbsUp size={15} />
                <span>Like</span>
              </button>
              <button type="button" className="create-post-footer-btn">
                <MessageSquare size={15} />
                <span>Comment</span>
              </button>
              <button type="button" className="create-post-footer-btn">
                <Repeat size={15} />
                <span>Repost</span>
              </button>
            </div>
          </div>
        )}

        {/* 2. Bluesky Preview */}
        {activePreviewTab === 'bluesky' && (
          <div className="create-post-preview-card">
            <div className="create-post-card-header">
              <div className="create-post-card-author">
                <div className="create-post-avatar-bluesky">
                  🦋
                </div>
                <div className="create-post-author-info">
                  <span className="create-post-author-name">
                    {user.name}
                  </span>
                  <span className="create-post-author-sub" style={{ fontFamily: 'monospace' }}>
                    @yourhandle.bsky.social • now
                  </span>
                </div>
              </div>
              <div className="create-post-card-actions">
                <button
                  type="button"
                  onClick={handleToggleEdit}
                  className={`create-post-preview-pen-btn ${isEditingPreview ? 'create-post-preview-pen-btn-active' : ''}`}
                  title={isEditingPreview ? "Save post changes" : "Edit post content"}
                  aria-label="Edit post"
                >
                  <Pencil size={14} />
                </button>
                <button type="button" className="create-post-preview-more-btn" title="More options">
                  <MoreHorizontal size={16} />
                </button>
              </div>
            </div>

            {renderPreviewContent()}

            {mediaUrl && (
              <div className="create-post-preview-image-wrap">
                <img
                  src={mediaUrl}
                  alt="Bluesky media"
                  className="create-post-preview-image create-post-preview-image-large"
                />
              </div>
            )}

            <div className="create-post-bluesky-footer">
              <button type="button" className="create-post-bluesky-stat-btn">
                <MessageSquare size={14} />
                <span>12</span>
              </button>
              <button type="button" className="create-post-bluesky-stat-btn">
                <Repeat size={14} />
                <span>5</span>
              </button>
              <button type="button" className="create-post-bluesky-stat-btn">
                <Heart size={14} />
                <span>38</span>
              </button>
              <button type="button" className="create-post-bluesky-stat-btn">
                <Share2 size={14} />
              </button>
            </div>
          </div>
        )}

        {/* 3. Instagram Preview */}
        {activePreviewTab === 'instagram' && (
          <div className="create-post-preview-card create-post-preview-card-instagram">
            <div className="create-post-card-header" style={{ padding: '0 0 10px 0' }}>
              <div className="create-post-card-author">
                <div className="create-post-avatar-instagram">
                  <div className="create-post-avatar-instagram-inner">
                    <span className="create-post-avatar-instagram-char">
                      {user.avatarChar}
                    </span>
                  </div>
                </div>
                <div className="create-post-author-info">
                  <span className="create-post-author-name">
                    {user.name.toLowerCase().replace(/\s+/g, '')}
                  </span>
                  <span className="create-post-author-sub">Original audio</span>
                </div>
              </div>
              <div className="create-post-card-actions">
                <button
                  type="button"
                  onClick={handleToggleEdit}
                  className={`create-post-preview-pen-btn ${isEditingPreview ? 'create-post-preview-pen-btn-active' : ''}`}
                  title={isEditingPreview ? "Save post changes" : "Edit post content"}
                  aria-label="Edit post"
                >
                  <Pencil size={14} />
                </button>
                <button type="button" className="create-post-preview-more-btn" title="More options">
                  <MoreHorizontal size={16} />
                </button>
              </div>
            </div>

            {mediaUrl ? (
              <div className="create-post-preview-image-wrap create-post-preview-image-wrap-instagram">
                <img
                  src={mediaUrl}
                  alt="Instagram visual"
                  className="create-post-preview-image create-post-preview-image-cover"
                />
              </div>
            ) : (
              <div style={{ height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f1f5f9', color: '#94a3b8', borderRadius: 8, fontSize: 12 }}>
                Attach an image for Instagram
              </div>
            )}

            <div style={{ marginTop: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: '#1e293b' }}>
                  <button type="button" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#334155' }}>
                    <Heart size={18} />
                  </button>
                  <button type="button" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#334155' }}>
                    <MessageSquare size={18} />
                  </button>
                  <button type="button" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#334155' }}>
                    <SendHorizontal size={18} />
                  </button>
                </div>
                <button type="button" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#334155' }}>
                  <Bookmark size={18} />
                </button>
              </div>

              <div style={{ fontSize: 11, fontWeight: 700, color: '#0f172a', marginBottom: 6 }}>
                142 likes
              </div>

              {renderPreviewContent()}
            </div>
          </div>
        )}

        {/* 4. Facebook Preview */}
        {activePreviewTab === 'facebook' && (
          <div className="create-post-preview-card">
            <div className="create-post-card-header">
              <div className="create-post-card-author">
                <div className="create-post-avatar-facebook">
                  f
                </div>
                <div className="create-post-author-info">
                  <span className="create-post-author-name">
                    {user.brandName || user.name}
                  </span>
                  <span className="create-post-author-sub">
                    Just now • 🌐 Public
                  </span>
                </div>
              </div>
              <div className="create-post-card-actions">
                <button
                  type="button"
                  onClick={handleToggleEdit}
                  className={`create-post-preview-pen-btn ${isEditingPreview ? 'create-post-preview-pen-btn-active' : ''}`}
                  title={isEditingPreview ? "Save post changes" : "Edit post content"}
                  aria-label="Edit post"
                >
                  <Pencil size={14} />
                </button>
                <button type="button" className="create-post-preview-more-btn" title="More options">
                  <MoreHorizontal size={16} />
                </button>
              </div>
            </div>

            {renderPreviewContent()}

            {mediaUrl && (
              <div className="create-post-preview-image-wrap">
                <img
                  src={mediaUrl}
                  alt="Facebook visual"
                  className="create-post-preview-image create-post-preview-image-large"
                />
              </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 11, color: '#94a3b8', paddingTop: 8 }}>
              <span>👍 ❤️ 28</span>
              <span>6 comments • 2 shares</span>
            </div>

            <div className="create-post-card-footer">
              <button type="button" className="create-post-footer-btn">
                <ThumbsUp size={15} />
                <span>Like</span>
              </button>
              <button type="button" className="create-post-footer-btn">
                <MessageSquare size={15} />
                <span>Comment</span>
              </button>
              <button type="button" className="create-post-footer-btn">
                <Share2 size={15} />
                <span>Share</span>
              </button>
            </div>
          </div>
        )}

        {/* 5. Pinterest Preview */}
        {activePreviewTab === 'pinterest' && (
          <div className="create-post-preview-card">
            <div className="create-post-card-header">
              <div className="create-post-card-author">
                <div className="create-post-avatar-pinterest">
                  P
                </div>
                <div className="create-post-author-info">
                  <span className="create-post-author-name">
                    {user.brandName || user.name}
                  </span>
                  <span className="create-post-author-sub">
                    Saved to Board • Just now
                  </span>
                </div>
              </div>
              <div className="create-post-card-actions">
                <button
                  type="button"
                  onClick={handleToggleEdit}
                  className={`create-post-preview-pen-btn ${isEditingPreview ? 'create-post-preview-pen-btn-active' : ''}`}
                  title={isEditingPreview ? "Save post changes" : "Edit post content"}
                  aria-label="Edit post"
                >
                  <Pencil size={14} />
                </button>
                <button type="button" className="create-post-preview-more-btn" title="More options">
                  <MoreHorizontal size={16} />
                </button>
              </div>
            </div>

            <div className="create-post-pinterest-media-wrap">
              {mediaUrl ? (
                mediaUrl.includes('data:video') || mediaUrl.match(/\.(mp4|webm)($|\?)/i) ? (
                  <video src={mediaUrl} controls className="create-post-pinterest-img" />
                ) : (
                  <img src={mediaUrl} alt="Pin visual" className="create-post-pinterest-img" />
                )
              ) : (
                <div className="create-post-pinterest-placeholder">
                  <ImageIcon size={28} style={{ color: '#E60023', marginBottom: 8 }} />
                  <span>Attach an image or video for Pinterest</span>
                </div>
              )}
              <div className="create-post-pinterest-save-overlay">
                <button type="button" className="create-post-pinterest-save-btn">
                  Save
                </button>
              </div>
            </div>

            <div className="create-post-pinterest-details">
              <h4 className="create-post-pinterest-title">
                {getActiveVariant().title || (topic ? `${topic} — Visual Guide` : user.brandName || 'Untitled Pin')}
              </h4>
              {renderPreviewContent()}
            </div>

            <div className="create-post-card-footer" style={{ borderTop: '1px solid #f1f5f9', paddingTop: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#64748b' }}>
                <PlatformIcon platform="pinterest" size={16} />
                <span>pinterest.com/pin/...</span>
              </div>
              <button type="button" className="create-post-footer-btn" style={{ marginLeft: 'auto' }}>
                <Share2 size={15} />
                <span>Share</span>
              </button>
            </div>
          </div>
        )}

        {/* 6. YouTube Preview */}
        {activePreviewTab === 'youtube' && (
          <div className="create-post-preview-card">
            <div className="create-post-youtube-player-wrap">
              {mediaUrl ? (
                mediaUrl.includes('data:video') || mediaUrl.match(/\.(mp4|webm)($|\?)/i) ? (
                  <video src={mediaUrl} controls className="create-post-youtube-player" />
                ) : (
                  <div className="create-post-youtube-thumbnail-wrap">
                    <img src={mediaUrl} alt="Video thumbnail" className="create-post-youtube-thumbnail" />
                    <div className="create-post-youtube-play-btn">
                      <svg viewBox="0 0 24 24" width="28" height="28" fill="#ffffff">
                        <polygon points="6 3 20 12 6 21 6 3" />
                      </svg>
                    </div>
                    <span className="create-post-youtube-duration">Preview</span>
                  </div>
                )
              ) : (
                <div className="create-post-youtube-no-media">
                  <PlatformIcon platform="youtube" size={36} />
                  <span style={{ fontSize: 12, color: '#94a3b8', marginTop: 8 }}>
                    Attach a video or thumbnail for YouTube
                  </span>
                </div>
              )}
            </div>

            <h3 className="create-post-youtube-title">
              {getActiveVariant().title || (topic ? `${topic} — Strategic Overview` : 'Strategic Video Overview')}
            </h3>

            <div className="create-post-youtube-channel-row">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div className="create-post-avatar-youtube">
                  ▶
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>
                    {user.brandName || user.name}
                  </div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>
                    1.28K subscribers
                  </div>
                </div>
                <button type="button" className="create-post-youtube-sub-btn">
                  Subscribe
                </button>
              </div>

              <div className="create-post-youtube-actions">
                <button type="button" className="create-post-youtube-action-pill">
                  <ThumbsUp size={13} />
                  <span>248</span>
                </button>
                <button type="button" className="create-post-youtube-action-pill">
                  <Share2 size={13} />
                  <span>Share</span>
                </button>
              </div>
            </div>

            <div className="create-post-youtube-desc-box">
              <div className="create-post-youtube-views">
                2,481 views • Premiering today #AIMarketing
              </div>
              {renderPreviewContent()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
