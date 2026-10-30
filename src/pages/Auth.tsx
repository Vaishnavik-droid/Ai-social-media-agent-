import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Mail,
  Lock,
  Eye,
  EyeOff,
  User,
  Building2,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Share2,
  BarChart3,
  KeyRound,
  Zap,
  ArrowLeft,
  Bot,
  Radio,
  Rocket,
  Target,
  Palette,
  Check
} from 'lucide-react';
import { UserProfile } from '../types';
import { supabase, testSupabaseConnection } from '../lib/supabase';

interface AuthProps {
  onLoginSuccess: (user: UserProfile) => void;
  initialMode?: 'login' | 'signup';
}

export const Auth: React.FC<AuthProps> = ({
  onLoginSuccess,
  initialMode = 'login'
}) => {
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>(initialMode);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form Fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [workspaceName, setWorkspaceName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [agreeTerms, setAgreeTerms] = useState(true);

  // Forgot password email
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSent, setForgotSent] = useState(false);

  // 3D Card Tilt & Additional Workspace Goal
  const [selectedGoal, setSelectedGoal] = useState<'growth' | 'agency' | 'creator'>('growth');
  const [cardTilt, setCardTilt] = useState({ x: 0, y: 0, shineX: 50, shineY: 50 });
  const [isHoveringCard, setIsHoveringCard] = useState(false);
  const [supabaseConnected, setSupabaseConnected] = useState(true);

  // Check Supabase connection on mount
  useEffect(() => {
    testSupabaseConnection().then((res) => {
      setSupabaseConnected(res.connected);
    });
  }, []);

  const handleCardMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = -((y - centerY) / centerY) * 7;
    const rotateY = ((x - centerX) / centerX) * 7;
    const shineX = (x / rect.width) * 100;
    const shineY = (y / rect.height) * 100;
    setCardTilt({ x: rotateX, y: rotateY, shineX, shineY });
    setIsHoveringCard(true);
  };

  const handleCardMouseLeave = () => {
    setCardTilt({ x: 0, y: 0, shineX: 50, shineY: 50 });
    setIsHoveringCard(false);
  };

  // Calculate password strength
  const calculatePasswordStrength = (pwd: string): { score: number; label: string; color: string } => {
    if (!pwd) return { score: 0, label: 'None', color: 'bg-slate-700' };
    let score = 0;
    if (pwd.length >= 6) score += 1;
    if (pwd.length >= 10) score += 1;
    if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd) || /[^A-Za-z0-9]/.test(pwd)) score += 1;

    switch (score) {
      case 1:
        return { score: 25, label: 'Weak', color: '#ef4444' };
      case 2:
        return { score: 50, label: 'Fair', color: '#f59e0b' };
      case 3:
        return { score: 75, label: 'Good', color: '#3b82f6' };
      case 4:
      default:
        return { score: 100, label: 'Strong', color: '#10b981' };
    }
  };

  const strength = calculatePasswordStrength(password);


  // Submit Login with Supabase
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const inputEmail = email.trim();
    if (!inputEmail || !password.trim()) {
      setErrorMessage('Please enter both your email address and password.');
      return;
    }

    if (password.length < 4) {
      setErrorMessage('Password must be at least 4 characters long.');
      return;
    }

    setIsLoading(true);

    try {
      // If email format, authenticate directly with Supabase
      if (inputEmail.includes('@')) {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: inputEmail,
          password: password.trim()
        });

        if (error) {
          // If login failed on Supabase, check local accounts fallback before showing error
          const savedAccountsStr = localStorage.getItem('ai_social_accounts');
          let localMatch = null;
          if (savedAccountsStr) {
            try {
              const accounts = JSON.parse(savedAccountsStr);
              localMatch = accounts.find((a: any) =>
                a.email && a.email.toLowerCase() === inputEmail.toLowerCase()
              );
            } catch (err) {
              // ignore
            }
          }

          if (localMatch) {
            setIsLoading(false);
            onLoginSuccess({
              name: localMatch.name,
              email: localMatch.email,
              avatarChar: localMatch.avatarChar || 'U',
              brandName: localMatch.brandName || 'OmniPulse Media',
              role: 'Pro Creator'
            });
            return;
          }

          setIsLoading(false);
          setErrorMessage(error.message);
          return;
        }

        if (data?.user) {
          setIsLoading(false);
          const meta = data.user.user_metadata || {};
          const displayName = meta.full_name || inputEmail.split('@')[0];
          const userAvatar = displayName.charAt(0).toUpperCase() || 'U';
          const brandName = meta.brand_name || 'OmniPulse Media';
          const goal = meta.goal || 'growth';

          setSuccessMessage('Successfully signed in with Supabase!');
          setTimeout(() => {
            onLoginSuccess({
              name: displayName,
              email: data.user.email || inputEmail,
              avatarChar: userAvatar,
              brandName: brandName,
              role:
                goal === 'agency'
                  ? 'Agency Lead'
                  : goal === 'creator'
                  ? 'Pro Creator'
                  : 'Growth Strategist'
            });
          }, 400);
          return;
        }
      } else {
        // Username without @: local development mode
        setIsLoading(false);
        const displayName = inputEmail;
        onLoginSuccess({
          name: displayName,
          email: `${displayName.toLowerCase().replace(/[^a-z0-9]/g, '')}@pulse.ai`,
          avatarChar: displayName.charAt(0).toUpperCase(),
          brandName: 'OmniPulse Media',
          role: 'Pro Creator'
        });
        return;
      }
    } catch (err: any) {
      setIsLoading(false);
      setErrorMessage(err?.message || 'Authentication error occurred.');
    }
  };

  // Submit Sign Up with Supabase
  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!fullName.trim()) {
      setErrorMessage('Please enter your full name.');
      return;
    }

    if (!email.trim() || !email.includes('@')) {
      setErrorMessage('Please enter a valid email address.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please recheck.');
      return;
    }

    if (!agreeTerms) {
      setErrorMessage('Please accept the Terms of Service and Privacy Policy to continue.');
      return;
    }

    setIsLoading(true);

    const brandFallback =
      selectedGoal === 'agency'
        ? 'Client Media Studio'
        : selectedGoal === 'creator'
        ? 'Creator Brand Studio'
        : 'Growth Pulse Studio';
    const finalBrand = workspaceName.trim() || brandFallback;
    const initial = fullName.trim().charAt(0).toUpperCase() || 'U';

    try {
      // Register user in Supabase
      const { data, error } = await supabase.auth.signUp({
        email: email.trim(),
        password: password,
        options: {
          data: {
            full_name: fullName.trim(),
            brand_name: finalBrand,
            goal: selectedGoal
          }
        }
      });

      if (error) {
        setIsLoading(false);
        setErrorMessage(error.message);
        return;
      }

      // Also persist local record for fast offline resume
      try {
        const existing = JSON.parse(localStorage.getItem('ai_social_accounts') || '[]');
        const newAccount = {
          name: fullName.trim(),
          email: email.trim(),
          brandName: finalBrand,
          avatarChar: initial,
          goal: selectedGoal,
          createdAt: new Date().toISOString()
        };
        localStorage.setItem('ai_social_accounts', JSON.stringify([...existing, newAccount]));
      } catch (err) {
        // ignore
      }

      setIsLoading(false);

      if (data?.session) {
        setSuccessMessage('Supabase account created and connected! Logging you in...');
        setTimeout(() => {
          onLoginSuccess({
            name: fullName.trim(),
            email: email.trim(),
            avatarChar: initial,
            brandName: finalBrand,
            role:
              selectedGoal === 'agency'
                ? 'Agency Lead'
                : selectedGoal === 'creator'
                ? 'Pro Creator'
                : 'Growth Strategist'
          });
        }, 500);
      } else {
        // Confirmation required by Supabase auth configuration
        setSuccessMessage('Account registered in Supabase! If confirmation is required, please check your inbox, or you can sign in directly.');
        setTimeout(() => {
          onLoginSuccess({
            name: fullName.trim(),
            email: email.trim(),
            avatarChar: initial,
            brandName: finalBrand,
            role:
              selectedGoal === 'agency'
                ? 'Agency Lead'
                : selectedGoal === 'creator'
                ? 'Pro Creator'
                : 'Growth Strategist'
          });
        }, 1200);
      }
    } catch (err: any) {
      setIsLoading(false);
      setErrorMessage(err?.message || 'Failed to connect to Supabase.');
    }
  };

  // Forgot password handler with Supabase
  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!forgotEmail || !forgotEmail.includes('@')) {
      setErrorMessage('Please enter a valid email address.');
      return;
    }
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(forgotEmail.trim());
      setIsLoading(false);
      if (error) {
        setErrorMessage(error.message);
      } else {
        setForgotSent(true);
      }
    } catch (err: any) {
      setIsLoading(false);
      setForgotSent(true);
    }
  };


  return (
    <div className="auth-page-container">
      {/* 3D Celestial Orbit Rings */}
      <div className="auth-3d-backdrop-ring" />
      <div className="auth-3d-backdrop-ring-2" />

      {/* Decorative background atmospheric glow */}
      <div className="auth-ambient-glow auth-glow-1" />
      <div className="auth-ambient-glow auth-glow-2" />
      <div className="auth-ambient-glow auth-glow-3" />
      <div className="auth-grid-overlay" />

      <div className="auth-central-shell">
        {/* Left Column: Branding, Value Prop & 3D Live Simulator */}
        <div className="auth-hero-pane">
          <div className="auth-hero-header">
            <div className="auth-brand-badge">
              <div className="auth-brand-icon">
                <Sparkles size={18} strokeWidth={2.4} />
              </div>
              <div className="auth-brand-text">
                <span className="auth-brand-title">OmniPulse AI</span>
                <span className="auth-brand-tag">Autonomous Social Suite</span>
              </div>
            </div>


          </div>

          <div className="auth-hero-pitch">
            <h1 className="auth-hero-heading">
              Publish, schedule & scale across all socials with{' '}
              <span className="auth-text-gradient">Autonomous AI</span>
            </h1>
            <p className="auth-hero-subheading">
              One unified workspace to generate hyper-tailored content, automatically sync across Bluesky, LinkedIn, X, Instagram and Facebook, and track performance.
            </p>
          </div>

          {/* 3D Live AI Content Dispatch Simulator Card */}
          <div className="auth-hero-preview-card">
            <div className="auth-preview-header">
              <div className="auth-preview-agent-status">
                <span className="auth-agent-pulse-ring" />
                <span className="auth-agent-name">Autonomous Agent Engine</span>
              </div>
              <div className="auth-preview-engine-badge">
                <Bot size={13} />
                <span>Multi-Platform Dispatch</span>
              </div>
            </div>

            <div className="auth-preview-prompt-box">
              <div className="auth-preview-prompt-label">
                <Sparkles size={13} className="text-amber-400" />
                <span>Active Content Pipeline</span>
                <span className="auth-preview-time-tag">Peak: 2:45 PM</span>
              </div>
              <p className="auth-preview-copy">
                &ldquo;Automating omnichannel social distribution with predictive timing. 1 prompt &rarr; 4 natively tailored network posts.&rdquo;
              </p>
            </div>

            <div className="auth-preview-platforms">
              <div className="auth-preview-platform-pill">
                <span className="platform-tag">🦋 Bluesky</span>
                <span className="platform-status">✓ Ready</span>
              </div>
              <div className="auth-preview-platform-pill">
                <span className="platform-tag">💼 LinkedIn</span>
                <span className="platform-status">✓ Hook 98%</span>
              </div>
              <div className="auth-preview-platform-pill">
                <span className="platform-tag">📸 Instagram</span>
                <span className="platform-status">✓ Carousel</span>
              </div>
              <div className="auth-preview-platform-pill">
                <span className="platform-tag">🌐 Facebook</span>
                <span className="platform-status">✓ Sync</span>
              </div>
            </div>

            <div className="auth-preview-metrics-row">
              <div className="auth-metric-item">
                <span className="auth-metric-value">10x</span>
                <span className="auth-metric-label">Content Speed</span>
              </div>
              <div className="auth-metric-separator" />
              <div className="auth-metric-item">
                <span className="auth-metric-value">+340%</span>
                <span className="auth-metric-label">Reach Multiplier</span>
              </div>
              <div className="auth-metric-separator" />
              <div className="auth-metric-item">
                <span className="auth-metric-value">&lt; 2.5s</span>
                <span className="auth-metric-label">AI Latency</span>
              </div>
            </div>
          </div>

          {/* Feature Highlights Grid */}
          <div className="auth-feature-cards">
            <div className="auth-feature-item">
              <div className="auth-feature-icon-box bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Share2 size={18} strokeWidth={2.2} />
              </div>
              <div>
                <h4 className="auth-feature-title">Omnichannel Multi-Posting</h4>
                <p className="auth-feature-desc">Single click generation formatted natively for all major networks.</p>
              </div>
            </div>

            <div className="auth-feature-item">
              <div className="auth-feature-icon-box bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <Zap size={18} strokeWidth={2.2} />
              </div>
              <div>
                <h4 className="auth-feature-title">AI Content Engine</h4>
                <p className="auth-feature-desc">Viral hooks, tone-matching, auto-hashtags & contextual emojis.</p>
              </div>
            </div>

            <div className="auth-feature-item">
              <div className="auth-feature-icon-box bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <BarChart3 size={18} strokeWidth={2.2} />
              </div>
              <div>
                <h4 className="auth-feature-title">Smart Peak Timing</h4>
                <p className="auth-feature-desc">Predictive scheduling queues content when your audience is active.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: 3D Interactive Card with Floating Badges */}
        <div className="auth-form-pane">
          <div className="auth-3d-scene">
            {/* 3D Floating Holographic Badge 1 (Top Left) */}
            <div className="auth-float-3d-badge auth-badge-tl">
              <div className="auth-float-icon-box bg-sky-500/20 text-sky-400 border border-sky-400/30">
                <Radio size={13} className="animate-pulse" />
              </div>
              <div className="auth-float-text">
                <span className="auth-float-title">Bluesky Live</span>
                <span className="auth-float-subtitle">Auto-Sync 100%</span>
              </div>
            </div>

            {/* 3D Floating Holographic Badge 2 (Bottom Right) */}
            <div className="auth-float-3d-badge auth-badge-br">
              <div className="auth-float-icon-box bg-purple-500/20 text-purple-400 border border-purple-400/30">
                <Bot size={13} />
              </div>
              <div className="auth-float-text">
                <span className="auth-float-title">AI Engine 2.5</span>
                <span className="auth-float-subtitle">Autonomous Dispatch</span>
              </div>
            </div>

            <div
              className="auth-card-3d"
              onMouseMove={handleCardMouseMove}
              onMouseLeave={handleCardMouseLeave}
              style={{
                transform: isHoveringCard
                  ? `perspective(1000px) rotateX(${cardTilt.x}deg) rotateY(${cardTilt.y}deg) translateY(-2px)`
                  : 'perspective(1000px) rotateX(0deg) rotateY(0deg)'
              }}
            >
              {/* Dynamic specular light reflection */}
              <div
                className="auth-card-shine"
                style={{
                  background: isHoveringCard
                    ? `radial-gradient(circle at ${cardTilt.shineX}% ${cardTilt.shineY}%, rgba(255, 255, 255, 0.12) 0%, transparent 60%)`
                    : 'transparent',
                  opacity: isHoveringCard ? 1 : 0
                }}
              />
            {/* Header Tabs for Sign In vs Create Account */}
            {mode !== 'forgot' && (
              <div className="auth-tab-group">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setErrorMessage(null);
                    setSuccessMessage(null);
                  }}
                  className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMode('signup');
                    setErrorMessage(null);
                    setSuccessMessage(null);
                  }}
                  className={`auth-tab-btn ${mode === 'signup' ? 'active' : ''}`}
                >
                  Create Account
                </button>
              </div>
            )}

            {/* Error Message Box */}
            {errorMessage && (
              <div className="auth-alert-box auth-alert-error animate-fadeIn">
                <AlertCircle size={16} className="auth-alert-icon" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Success Message Box */}
            {successMessage && (
              <div className="auth-alert-box auth-alert-success animate-fadeIn">
                <CheckCircle2 size={16} className="auth-alert-icon" />
                <span>{successMessage}</span>
              </div>
            )}


            {/* ================= MODE: LOGIN ================= */}
            {mode === 'login' && (
              <form onSubmit={handleLoginSubmit} className="auth-actual-form">
                <div className="auth-form-intro">
                  <h2 className="auth-form-title">Welcome back</h2>
                  <p className="auth-form-subtitle">Enter your credentials to access your social agent</p>
                </div>

                {/* Email or Username field */}
                <div className="auth-input-group">
                  <label htmlFor="login-email" className="auth-label">
                    Email address or Username
                  </label>
                  <div className="auth-input-wrapper">
                    <Mail size={16} className="auth-input-icon" />
                    <input
                      id="login-email"
                      type="text"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="user@gmail.com or username"
                      required
                      className="auth-input"
                      autoComplete="username"
                    />
                  </div>
                </div>

                {/* Password field */}
                <div className="auth-input-group">
                  <div className="auth-label-row">
                    <label htmlFor="login-password" className="auth-label">
                      Password
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setMode('forgot');
                        setErrorMessage(null);
                        setSuccessMessage(null);
                      }}
                      className="auth-link-btn"
                    >
                      Forgot password?
                    </button>
                  </div>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-input-icon" />
                    <input
                      id="login-password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      required
                      className="auth-input"
                      autoComplete="current-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="auth-eye-btn"
                      aria-label="Toggle password visibility"
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                {/* Remember me checkbox */}
                <div className="auth-checkbox-row">
                  <label className="auth-checkbox-label">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="auth-checkbox"
                    />
                    <span>Remember my session on this device</span>
                  </label>
                </div>

                {/* Primary Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="auth-submit-btn"
                >
                  {isLoading ? (
                    <span className="auth-loading-spinner" />
                  ) : (
                    <>
                      <span>Sign In to Dashboard</span>
                      <ArrowRight size={16} strokeWidth={2.3} />
                    </>
                  )}
                </button>


                <div className="auth-footer-prompt">
                  <span>Don't have an account yet?</span>{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setMode('signup');
                      setErrorMessage(null);
                    }}
                    className="auth-switch-link"
                  >
                    Create one now
                  </button>
                </div>
              </form>
            )}

            {/* ================= MODE: SIGN UP ================= */}
            {mode === 'signup' && (
              <form onSubmit={handleSignupSubmit} className="auth-actual-form">
                <div className="auth-form-intro">
                  <h2 className="auth-form-title">Create your account</h2>
                </div>

                {/* Name */}
                <div className="auth-input-group">
                  <label htmlFor="signup-name" className="auth-label">
                    Full Name
                  </label>
                  <div className="auth-input-wrapper">
                    <User size={16} className="auth-input-icon" />
                    <input
                      id="signup-name"
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. John Doe / Jane Doe"
                      required
                      className="auth-input"
                    />
                  </div>
                </div>

                {/* Email address */}
                <div className="auth-input-group">
                  <label htmlFor="signup-email" className="auth-label">
                    Email address
                  </label>
                  <div className="auth-input-wrapper">
                    <Mail size={16} className="auth-input-icon" />
                    <input
                      id="signup-email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="e.g. user@gmail.com"
                      required
                      className="auth-input"
                    />
                  </div>
                </div>


                {/* Workspace / Brand Name */}
                <div className="auth-input-group">
                  <label htmlFor="signup-workspace" className="auth-label">
                    Workspace / Brand Name <span className="auth-optional-tag">(Optional)</span>
                  </label>
                  <div className="auth-input-wrapper">
                    <Building2 size={16} className="auth-input-icon" />
                    <input
                      id="signup-workspace"
                      type="text"
                      value={workspaceName}
                      onChange={(e) => setWorkspaceName(e.target.value)}
                      placeholder="e.g. Pulse Media Studio"
                      className="auth-input"
                    />
                  </div>
                </div>

                {/* Primary Objective / Goal selector */}
                <div className="auth-goal-selector">
                  <label className="auth-label">Primary Objective</label>
                  <div className="auth-goal-pills">
                    <button
                      type="button"
                      onClick={() => setSelectedGoal('growth')}
                      className={`auth-goal-btn ${selectedGoal === 'growth' ? 'active' : ''}`}
                    >
                      <Rocket size={14} className={selectedGoal === 'growth' ? 'text-violet-300' : 'text-slate-400'} />
                      <span>Brand Growth</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedGoal('agency')}
                      className={`auth-goal-btn ${selectedGoal === 'agency' ? 'active' : ''}`}
                    >
                      <Target size={14} className={selectedGoal === 'agency' ? 'text-violet-300' : 'text-slate-400'} />
                      <span>Agency & Studio</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedGoal('creator')}
                      className={`auth-goal-btn ${selectedGoal === 'creator' ? 'active' : ''}`}
                    >
                      <Palette size={14} className={selectedGoal === 'creator' ? 'text-violet-300' : 'text-slate-400'} />
                      <span>Pro Creator</span>
                    </button>
                  </div>
                </div>

                {/* Password with strength meter */}
                <div className="auth-input-group">
                  <label htmlFor="signup-password" className="auth-label">
                    Create Password
                  </label>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-input-icon" />
                    <input
                      id="signup-password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="At least 6 characters"
                      required
                      className="auth-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="auth-eye-btn"
                      aria-label="Toggle password visibility"
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>

                  {/* Password strength visualizer */}
                  {password && (
                    <div className="auth-strength-container">
                      <div className="auth-strength-bar-bg">
                        <div
                          className="auth-strength-bar-fill"
                          style={{
                            width: `${strength.score}%`,
                            backgroundColor: strength.color
                          }}
                        />
                      </div>
                      <div className="auth-strength-text">
                        <span>Strength:</span>
                        <strong style={{ color: strength.color }}>{strength.label}</strong>
                      </div>
                    </div>
                  )}
                </div>

                {/* Confirm Password with match badge */}
                <div className="auth-input-group">
                  <div className="auth-label-row">
                    <label htmlFor="signup-confirm-password" className="auth-label">
                      Confirm Password
                    </label>
                    {confirmPassword && (
                      password === confirmPassword ? (
                        <span className="auth-match-badge match">
                          <Check size={11} strokeWidth={3} />
                          <span>Passwords match</span>
                        </span>
                      ) : (
                        <span className="auth-match-badge mismatch">
                          <span>Passwords don't match</span>
                        </span>
                      )
                    )}
                  </div>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-input-icon" />
                    <input
                      id="signup-confirm-password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-enter your password"
                      required
                      className="auth-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="auth-eye-btn"
                      aria-label="Toggle password visibility"
                    >
                      {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                {/* Terms checkbox */}
                <div className="auth-checkbox-row">
                  <label className="auth-checkbox-label">
                    <input
                      type="checkbox"
                      checked={agreeTerms}
                      onChange={(e) => setAgreeTerms(e.target.checked)}
                      className="auth-checkbox"
                      required
                    />
                    <span>
                      I agree to the <span className="auth-highlight-text">Terms of Service</span> and{' '}
                      <span className="auth-highlight-text">Privacy Policy</span>
                    </span>
                  </label>
                </div>

                {/* Submit button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="auth-submit-btn"
                >
                  {isLoading ? (
                    <span className="auth-loading-spinner" />
                  ) : (
                    <>
                      <span>Create Account & Get Started</span>
                      <ArrowRight size={16} strokeWidth={2.3} />
                    </>
                  )}
                </button>

                <div className="auth-footer-prompt">
                  <span>Already have an OmniPulse account?</span>{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setMode('login');
                      setErrorMessage(null);
                    }}
                    className="auth-switch-link"
                  >
                    Sign in here
                  </button>
                </div>
              </form>
            )}

            {/* ================= MODE: FORGOT PASSWORD ================= */}
            {mode === 'forgot' && (
              <div className="auth-actual-form animate-fadeIn">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setForgotSent(false);
                    setErrorMessage(null);
                  }}
                  className="auth-back-link"
                >
                  <ArrowLeft size={14} />
                  <span>Back to Sign In</span>
                </button>

                <div className="auth-form-intro">
                  <div className="auth-forgot-icon-wrap">
                    <KeyRound size={24} className="text-violet-400" />
                  </div>
                  <h2 className="auth-form-title">Reset your password</h2>
                  <p className="auth-form-subtitle">
                    Enter the email registered with your account and we&apos;ll send recovery instructions.
                  </p>
                </div>

                {forgotSent ? (
                  <div className="auth-forgot-success-card animate-fadeIn">
                    <CheckCircle2 size={32} className="text-emerald-400" />
                    <h3 className="auth-forgot-success-title">Check your inbox</h3>
                    <p className="auth-forgot-success-desc">
                      We have sent password reset instructions to <br />
                      <strong className="text-white">{forgotEmail}</strong>
                    </p>
                    <button
                      type="button"
                      onClick={() => setMode('login')}
                      className="auth-submit-btn mt-4"
                    >
                      Return to Sign In
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleForgotSubmit}>
                    <div className="auth-input-group">
                      <label htmlFor="forgot-email" className="auth-label">
                        Your account email
                      </label>
                      <div className="auth-input-wrapper">
                        <Mail size={16} className="auth-input-icon" />
                        <input
                          id="forgot-email"
                          type="email"
                          value={forgotEmail}
                          onChange={(e) => setForgotEmail(e.target.value)}
                          placeholder="user@gmail.com"
                          required
                          className="auth-input"
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isLoading}
                      className="auth-submit-btn mt-4"
                    >
                      {isLoading ? (
                        <span className="auth-loading-spinner" />
                      ) : (
                        <span>Send Reset Instructions</span>
                      )}
                    </button>
                  </form>
                )}
              </div>
            )}

            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Auth;
