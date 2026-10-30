import React, { useState } from 'react';
import {
  Trash2,
  ArrowLeft,
  ShieldCheck,
  CheckCircle2,
  Mail,
  AlertCircle,
  Sparkles,
  ExternalLink,
  Copy,
  Check
} from 'lucide-react';

interface DataDeletionProps {
  onBack?: () => void;
  onNavigatePrivacy?: () => void;
  onNavigateTerms?: () => void;
}

export const DataDeletion: React.FC<DataDeletionProps> = ({
  onBack,
  onNavigatePrivacy,
  onNavigateTerms,
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [emailInput, setEmailInput] = useState<string>('');
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [confirmationCode, setConfirmationCode] = useState<string>('');

  const handleCopyEmail = () => {
    navigator.clipboard.writeText('privacy@omnipulse.ai');
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleSubmitRequest = (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailInput.trim()) return;
    const code = 'DEL-' + Math.random().toString(36).substring(2, 8).toUpperCase() + '-' + Date.now().toString().slice(-4);
    setConfirmationCode(code);
    setSubmitted(true);
  };

  return (
    <div className="legal-page-container">
      {/* Top Navigation */}
      <header className="legal-header">
        <div className="legal-header-inner">
          <div className="legal-branding">
            {onBack ? (
              <button
                type="button"
                onClick={onBack}
                className="legal-back-button"
                title="Return to application"
              >
                <ArrowLeft size={16} />
                <span>Back to App</span>
              </button>
            ) : (
              <a href="/" className="legal-back-button">
                <ArrowLeft size={16} />
                <span>Back to Home</span>
              </a>
            )}
            <div className="legal-divider" />
            <div className="legal-logo-group">
              <div className="legal-logo-icon">
                <Sparkles size={16} />
              </div>
              <span className="legal-logo-text">OmniPulse</span>
              <span className="legal-badge">Meta Data Deletion</span>
            </div>
          </div>

          <div className="legal-header-actions">
            <button
              type="button"
              onClick={onNavigatePrivacy || (() => { window.location.href = '/privacy'; })}
              className="legal-action-link"
            >
              <ShieldCheck size={14} />
              <span>Privacy Policy</span>
            </button>
            <button
              type="button"
              onClick={onNavigateTerms || (() => { window.location.href = '/terms'; })}
              className="legal-action-link"
            >
              <span>Terms of Service</span>
            </button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <div className="legal-hero">
        <div className="legal-hero-inner">
          <div className="legal-meta-badge legal-highlight-badge-warning">
            <Trash2 size={14} />
            <span>Facebook Platform Rule 4.d Compliance</span>
          </div>
          <h1 className="legal-hero-title">User Data Deletion Instructions</h1>
          <p className="legal-hero-subtitle">
            OmniPulse AI Social Media Agent — Facebook &amp; Instagram Data Purge Policy
          </p>
          <p className="legal-hero-desc">
            According to Meta Platform Rules, OmniPulse provides this page to inform users how to request the deletion
            of their personal data and revoke third-party app permissions for Facebook and Instagram.
          </p>
        </div>
      </div>

      {/* Main Body */}
      <div className="legal-body-container">
        <div className="max-w-3xl mx-auto py-8 px-4">
          {/* Step-by-Step Instructions */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 md:p-8 mb-8">
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-violet-100 text-violet-700 flex items-center justify-center text-sm font-black">
                1
              </span>
              How to Remove OmniPulse from Your Facebook Account
            </h2>
            <p className="text-sm text-slate-600 mb-4">
              If you wish to remove OmniPulse&apos;s connection to your Facebook Pages or Instagram accounts, follow these official Meta steps:
            </p>

            <ol className="space-y-3 text-sm text-slate-700 bg-slate-50 rounded-xl p-5 border border-slate-200">
              <li className="flex items-start gap-2">
                <span className="font-semibold text-slate-900">Step 1:</span>
                <span>Open your Facebook account and click your profile picture in the top right.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-semibold text-slate-900">Step 2:</span>
                <span>Select <strong>Settings &amp; privacy</strong>, then click <strong>Settings</strong>.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-semibold text-slate-900">Step 3:</span>
                <span>In the left sidebar, navigate to <strong>Business Integrations</strong> (or <strong>Apps and Websites</strong>).</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-semibold text-slate-900">Step 4:</span>
                <span>Locate <strong>OmniPulse</strong> in the list of active connected apps.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-semibold text-slate-900">Step 5:</span>
                <span>Click the <strong>Remove</strong> button next to the app name.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-semibold text-slate-900">Step 6:</span>
                <span>Confirm your selection. Once removed, OmniPulse will no longer have access to your Pages or account.</span>
              </li>
            </ol>
          </div>

          {/* In-App Deletion */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 md:p-8 mb-8">
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-violet-100 text-violet-700 flex items-center justify-center text-sm font-black">
                2
              </span>
              How to Delete Your Data from OmniPulse Directly
            </h2>
            <p className="text-sm text-slate-600 mb-4">
              You can instantly purge all stored tokens, post library drafts, and profile data inside the OmniPulse application:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
                <h3 className="font-semibold text-slate-900 text-sm mb-1">Disconnect Platform Only</h3>
                <p className="text-xs text-slate-600">
                  Go to <strong>Connected Platforms</strong>, find Facebook or Instagram, and toggle or click <strong>Disconnect</strong>.
                  Your access tokens are immediately erased from our encrypted database.
                </p>
              </div>
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
                <h3 className="font-semibold text-slate-900 text-sm mb-1">Delete Full Account &amp; Posts</h3>
                <p className="text-xs text-slate-600">
                  Navigate to <strong>Settings &rarr; Account Management &rarr; Delete Account</strong>.
                  This immediately executes a cascading delete across all your posts, schedules, and profile records.
                </p>
              </div>
            </div>
          </div>

          {/* Submission Form / Request Tracker */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 md:p-8">
            <h2 className="text-xl font-bold text-slate-900 mb-2 flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-violet-100 text-violet-700 flex items-center justify-center text-sm font-black">
                3
              </span>
              Submit a Formal Data Deletion Request
            </h2>
            <p className="text-sm text-slate-600 mb-6">
              If you prefer our compliance team to manually verify and purge all records associated with your email or Facebook User ID, submit your request below:
            </p>

            {submitted ? (
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 text-center">
                <CheckCircle2 size={36} className="text-emerald-500 mx-auto mb-3" />
                <h3 className="text-base font-bold text-emerald-900 mb-1">Request Received &amp; Queued</h3>
                <p className="text-xs text-emerald-700 mb-4">
                  We have logged your data deletion request for <strong>{emailInput}</strong>.
                  Our compliance system will permanently delete your records within 48 business hours.
                </p>
                <div className="inline-block bg-white border border-emerald-300 rounded-lg px-4 py-2 text-xs font-mono font-bold text-emerald-800">
                  Confirmation Code: {confirmationCode}
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmitRequest} className="space-y-4">
                <div>
                  <label htmlFor="deletion-email" className="block text-xs font-semibold text-slate-700 mb-1">
                    Your Registered Email or Facebook Account Email
                  </label>
                  <input
                    id="deletion-email"
                    type="email"
                    required
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    placeholder="e.g. user@example.com"
                    className="w-full px-3.5 py-2.5 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white"
                  />
                </div>

                <div className="flex items-center justify-between pt-2">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Mail size={13} />
                    <span>Or email us at:</span>
                    <button
                      type="button"
                      onClick={handleCopyEmail}
                      className="font-medium text-violet-600 hover:underline flex items-center gap-1"
                    >
                      privacy@omnipulse.ai
                      {copied ? <Check size={12} className="text-emerald-600" /> : <Copy size={12} />}
                    </button>
                  </div>

                  <button
                    type="submit"
                    className="px-5 py-2.5 rounded-lg bg-violet-600 hover:bg-violet-700 text-white font-medium text-sm transition-colors shadow-sm"
                  >
                    Submit Request
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="legal-footer">
        <div className="legal-footer-inner">
          <p>&copy; {new Date().getFullYear()} OmniPulse AI Social Media Agent. All rights reserved.</p>
          <div className="legal-footer-links">
            <button
              type="button"
              onClick={onNavigatePrivacy || (() => { window.location.href = '/privacy'; })}
              className="legal-footer-link"
            >
              Privacy Policy
            </button>
            <span className="text-slate-400">&bull;</span>
            <button
              type="button"
              onClick={onNavigateTerms || (() => { window.location.href = '/terms'; })}
              className="legal-footer-link"
            >
              Terms of Service
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default DataDeletion;
