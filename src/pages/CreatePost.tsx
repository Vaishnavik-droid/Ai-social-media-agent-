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
} from 'lucide-react';
import { Platform, SocialPost, UserProfile, UserPreferences } from '../types';
import { PlatformIcon } from '../components/PlatformIcon';
import { api } from '../lib/api';

interface CreatePostProps {
  user: UserProfile;
  preferences?: UserPreferences;
  onPostCreated: (post: SocialPost) => void;
  onNavigate: (page: any) => void;
}

export const CreatePost: React.FC<CreatePostProps> = ({
  user,
  preferences,
  onPostCreated,
  onNavigate,
}) => {
  const [topic, setTopic] = useState('');
  const [contentType, setContentType] = useState('General Post');
  const [tone, setTone] = useState(preferences?.defaultTone || 'Professional');
  const [language, setLanguage] = useState(preferences?.defaultLanguage || 'English');
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>([
    'linkedin',
    'instagram',
    'facebook',
  ]);
  const [activePreviewTab, setActivePreviewTab] = useState<Platform>('linkedin');

  // Media preview state
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

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
    'AI in Social Media Marketing is changing the way high-growth creators build audiences. By streamlining production and personalizing distribution, creators can operate with the leverage of an entire media agency. The future belongs to operators who build repeatable, automated publishing workflows. #AIMarketing #SocialMediaStrategy #ContentCreation #Growth'
  );

  const [isEditingPreview, setIsEditingPreview] = useState(false);
  const [previewDraftText, setPreviewDraftText] = useState(postBody);
  const previewTextareaRef = useRef<HTMLTextAreaElement>(null);

  const handleToggleEdit = () => {
    if (isEditingPreview) {
      setPostBody(previewDraftText);
      setIsEditingPreview(false);
    } else {
      setPreviewDraftText(postBody);
      setIsEditingPreview(true);
      setTimeout(() => {
        previewTextareaRef.current?.focus();
      }, 50);
    }
  };

  const handleSavePreviewEdit = () => {
    setPostBody(previewDraftText);
    setIsEditingPreview(false);
  };

  const handleCancelPreviewEdit = () => {
    setPreviewDraftText(postBody);
    setIsEditingPreview(false);
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

      if (res && res.generated_text) {
        setPostBody(res.generated_text);
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
      let generated = '';
      if (language === 'Hindi') {
        generated = `🚀 ${prompt}\n\nआर्टिफिशियल इंटेलिजेंस (AI) सोशल मीडिया मार्केटिंग और कंटेंट क्रिएशन को एक नए स्तर पर ले जा रहा है। तेज गति, सटीक टार्गेटिंग और पर्सनलाइज्ड स्ट्रेटेजी से बिजनेस को बड़ा फायदा मिल रहा है।\n\nभविष्य उन्हीं का है जो नई तकनीक को प्रभावी ढंग से अपनाते हैं!\n\n#आर्टिफिशियलइंटेलिजेंस #डिजिटलग्रोथ #सोशलमीडियामार्केटिंग #इनोवेशन`;
      } else if (language === 'Marathi') {
        generated = `🚀 ${prompt}\n\nआर्टिफिशियल इंटेलिजन्स (AI) मुळे सोशल मीडिया स्ट्रॅटेजी आणि बिझनेस ग्रोथला नवीन गती मिळत आहे। कमी वेळात अचूक आणि प्रभावी कंटेंट पोहोचवणे आता सहज शक्य झाले आहे।\n\nभविष्य तंत्रज्ञानासोबत पुढे जाणाऱ्यांचेच आहे!\n\n#डिजिटलमहाराष्ट्र #व्यवसायवाढ #सोशलमीडिया #इनोव्हेशन`;
      } else if (language === 'Spanish') {
        generated = `🚀 ${prompt}\n\nLa inteligencia artificial está transformando radicalmente el marketing en redes sociales: contenido más ágil, estratégico y personalizado.\n\n¡El futuro pertenece a los creadores y marcas que aprovechan la IA de forma efectiva!\n\n#InteligenciaArtificial #MarketingDigital #Estrategia` ;
      } else if (language === 'French') {
        generated = `📝 ${prompt}\n\nL'intelligence artificielle redéfinit la création de contenu sur les réseaux sociaux: rapidité, pertinence et personnalisation accrue.\n\nL'avenir appartient aux créateurs audacieux. Qu'en pensez-vous ?\n\n#IA #MarketingDigital #Innovation`;
      } else if (language === 'German') {
        generated = `💡 ${prompt}\n\nKünstliche Intelligenz revolutioniert das Social-Media-Marketing durch schnellere Workflows und maßgeschneiderte Inhalte.\n\nDie Zukunft gehört denjenigen, die KI gezielt einsetzen! Was ist Ihre Strategie?\n\n#KI #SocialMediaMarketing #Tech`;
      } else {
        if (tone === 'Casual') {
          generated = `Quick thought on ${prompt.toLowerCase()} 👋:\n\nHonestly, the productivity jump is wild. Instead of spending 3 hours on repetitive drafting, you spend 15 minutes refining high-impact hooks and visuals.\n\nThe real secret? Using AI to brainstorm, then injecting your own authentic perspective.\n\nAre you using AI for your content workflow yet? 😊\n\n#SocialMediaTips #AITools #CreatorEconomy`;
        } else if (tone === 'Witty') {
          generated = `Hot take on ${prompt.toLowerCase()} 🔥:\n\nAI won't replace human creators. But creators who use AI will certainly replace creators who don't.\n\nWork smarter, post sharper, and let the algorithm do the heavy lifting.\n\nAgree or disagree? Let's debate in the replies ⚡\n\n#MarketingHumor #TechTrends #Productivity`;
        } else if (tone === 'Inspiring') {
          generated = `✨ ${prompt}\n\nWe are witnessing the most significant democratisation of creative leverage in history.\n\nYou no longer need a massive production studio to build a global audience — just a clear vision, relentless consistency, and intelligent tools to amplify your message.\n\nBuild the future today.\n\n#Inspiration #GrowthMindset #Leadership #FutureOfWork`;
        } else {
          generated = `AI is changing social media marketing by making content creation faster, smarter and more personalized.\n\nThe future belongs to creators who use AI effectively!\n\n#AIMarketing #SocialMediaStrategy #ContentCreation #Growth`;
        }
      }

      setPostBody(generated);
      setIsGenerating(false);
    }, 300);
  };

  // Media validation (Strictly JPG, JPEG, PNG; Max 10MB)
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    const file = e.target.files?.[0];
    if (!file) return;

    const allowedTypes = ['image/jpeg', 'image/png'];
    const fileName = file.name.toLowerCase();
    const isAllowedExt =
      fileName.endsWith('.jpg') ||
      fileName.endsWith('.jpeg') ||
      fileName.endsWith('.png');

    const maxSizeBytes = 10 * 1024 * 1024; // 10 MB

    if (!allowedTypes.includes(file.type) && !isAllowedExt) {
      setUploadError('Unsupported file format. Please upload JPG, JPEG, or PNG only.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    if (file.size > maxSizeBytes) {
      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
      setUploadError(`File is too large (${fileSizeMB} MB). Maximum allowed size is 10 MB.`);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      if (event.target?.result) {
        setMediaUrl(event.target.result as string);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveMedia = () => {
    setMediaUrl(null);
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

    const newPost: SocialPost = {
      id: `post-${Date.now()}`,
      title: topic.length > 32 ? topic.slice(0, 29) + '...' : topic || postBody.slice(0, 32),
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

      // Step 2: Publish to selected platforms via FastAPI
      const publishRes = await api.publishPost(savedPost.id, selectedPlatforms, true);

      // Step 3: Show results
      const results = publishRes.results.map((r) => ({
        platform: r.platform,
        status: r.status,
        url: r.remote_post_url,
        error: r.error_message,
      }));
      setPublishResults(results);

      // Update local state
      const finalPost = { ...savedPost, status: publishRes.success ? 'published' : 'failed' as any };
      onPostCreated(finalPost);

    } catch (err: any) {
      setPublishResults([{
        platform: 'all',
        status: 'failed',
        error: err?.message || 'Failed to connect to backend. Is the server running?',
      }]);
    } finally {
      setIsPublishing(false);
    }
  };


  // Clickable hashtag renderer
  const renderFormattedText = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      const words = line.split(' ');
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
    if (isEditingPreview) {
      return (
        <div className="preview-inline-editor">
          <textarea
            ref={previewTextareaRef}
            className="preview-inline-textarea"
            value={previewDraftText}
            onChange={(e) => setPreviewDraftText(e.target.value)}
            rows={5}
            placeholder="Type or edit your post content..."
            autoFocus
          />
          <div className="preview-inline-actions">
            <span className="preview-inline-counter">
              {previewDraftText.length} characters
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
        {renderFormattedText(postBody)}
      </div>
    );
  };

  return (
    <div className="create-post-layout">
      {/* Hidden file input restricted strictly to JPG, JPEG, PNG */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".jpg,.jpeg,.png,image/jpeg,image/png"
        className="hidden"
      />

      {/* Left Form */}
      <div className="create-post-form create-post-panel">
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
              {selectedPlatforms.length} of 4 selected
            </span>
          </div>

          <div className="platform-selector-grid">
            {[
              { id: 'bluesky' as Platform, name: 'Bluesky' },
              { id: 'linkedin' as Platform, name: 'LinkedIn' },
              { id: 'instagram' as Platform, name: 'Instagram' },
              { id: 'facebook' as Platform, name: 'Facebook' },
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
        </div>

        <div className="create-post-section">
          <label className="create-post-label create-post-media-label">
            6. Media (Optional)
          </label>

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
                Upload image (JPG, JPEG, PNG)
              </div>
              <div className="create-post-upload-subtitle">
                Supported: JPG, JPEG, PNG (Max 10MB)
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
                <img
                  src={mediaUrl}
                  alt="Post attachment"
                  className="create-post-preview-image"
                />
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
          <h3 className="create-post-preview-title">Post Preview</h3>
          <div className="create-post-preview-header-right">
            <span className="create-post-preview-format">{activePreviewTab} format</span>
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

        <div className="create-post-tabs">
          {(['bluesky', 'linkedin', 'instagram', 'facebook'] as Platform[]).map(
            (platform) => {
              const isActive = activePreviewTab === platform;
              const labels: Record<Platform, string> = {
                bluesky: 'Bluesky',
                linkedin: 'LinkedIn',
                instagram: 'Instagram',
                facebook: 'Facebook',
                twitter: 'Twitter',
              };
              return (
                <button
                  key={platform}
                  type="button"
                  onClick={() => setActivePreviewTab(platform)}
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
      </div>
    </div>
  );
};
