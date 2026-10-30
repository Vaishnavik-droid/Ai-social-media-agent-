import React, { useState } from 'react';
import {
  ShieldCheck,
  ArrowLeft,
  Printer,
  FileText,
  Lock,
  Database,
  ExternalLink,
  Trash2,
  Mail,
  CheckCircle2,
  AlertTriangle,
  Globe,
  Share2,
  Sparkles
} from 'lucide-react';

interface PrivacyPolicyProps {
  onBack?: () => void;
  onNavigateTerms?: () => void;
  onNavigateDataDeletion?: () => void;
}

export const PrivacyPolicy: React.FC<PrivacyPolicyProps> = ({
  onBack,
  onNavigateTerms,
  onNavigateDataDeletion,
}) => {
  const [activeSection, setActiveSection] = useState<string>('meta-data');

  const handlePrint = () => {
    window.print();
  };

  const sections = [
    { id: 'overview', title: '1. Overview & Purpose' },
    { id: 'meta-data', title: '2. Meta (Facebook & Instagram) Platform Data' },
    { id: 'data-collection', title: '3. What Information We Collect' },
    { id: 'data-usage', title: '4. How We Use Your Information' },
    { id: 'ai-processing', title: '5. AI Processing & Groq Integration' },
    { id: 'data-storage', title: '6. Storage, Security & Retention' },
    { id: 'data-deletion', title: '7. User Data Deletion Instructions' },
    { id: 'user-rights', title: '8. Your Rights (GDPR & CCPA)' },
    { id: 'contact', title: '9. Contact & Data Protection Officer' },
  ];

  const scrollTo = (id: string) => {
    setActiveSection(id);
    const elem = document.getElementById(id);
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="legal-page-container">
      {/* Top Navigation Bar */}
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
              <span className="legal-badge">Privacy Policy</span>
            </div>
          </div>

          <div className="legal-header-actions">
            <button
              type="button"
              onClick={onNavigateTerms || (() => { window.location.href = '/terms'; })}
              className="legal-action-link"
            >
              <FileText size={14} />
              <span>Terms of Service</span>
            </button>
            <button
              type="button"
              onClick={handlePrint}
              className="legal-print-btn"
              title="Print or Save as PDF"
            >
              <Printer size={14} />
              <span>Print / PDF</span>
            </button>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <div className="legal-hero">
        <div className="legal-hero-inner">
          <div className="legal-meta-badge">
            <ShieldCheck size={14} className="text-emerald-400" />
            <span>Compliant with Meta Platform Terms & Community Standards</span>
          </div>
          <h1 className="legal-hero-title">OmniPulse Privacy Policy</h1>
          <p className="legal-hero-subtitle">
            Last Updated & Effective: <strong>October 30, 2026</strong>
          </p>
          <p className="legal-hero-desc">
            This Privacy Policy governs your use of the OmniPulse AI Social Media Agent. It describes our policies
            and procedures on the collection, usage, storage, and deletion of your personal data when you interact with our
            platform, connect social accounts (including Facebook and Instagram via the Meta Graph API), and publish content.
          </p>
        </div>
      </div>

      {/* Main Content Body */}
      <div className="legal-body-container">
        <div className="legal-body-layout">
          {/* Sidebar Table of Contents */}
          <aside className="legal-toc-aside">
            <div className="legal-toc-card">
              <div className="legal-toc-header">
                <FileText size={15} />
                <span>Table of Contents</span>
              </div>
              <nav className="legal-toc-nav">
                {sections.map((sec) => (
                  <button
                    key={sec.id}
                    type="button"
                    onClick={() => scrollTo(sec.id)}
                    className={`legal-toc-item ${activeSection === sec.id ? 'legal-toc-item-active' : ''}`}
                  >
                    {sec.title}
                  </button>
                ))}
              </nav>

              <div className="legal-toc-footer">
                <button
                  type="button"
                  onClick={onNavigateDataDeletion || (() => { window.location.href = '/data-deletion'; })}
                  className="legal-toc-highlight-btn"
                >
                  <Trash2 size={13} />
                  <span>Data Deletion Instructions</span>
                </button>
              </div>
            </div>
          </aside>

          {/* Legal Document Content */}
          <main className="legal-content-main">
            {/* Section 1 */}
            <section id="overview" className="legal-section">
              <h2 className="legal-section-title">1. Overview & Purpose</h2>
              <p>
                <strong>OmniPulse AI Social Media Agent</strong> (&quot;OmniPulse&quot;, &quot;we&quot;, &quot;us&quot;, or &quot;our&quot;) is a cloud-based
                productivity platform that enables individuals, creator teams, and businesses to compose, plan, generate, schedule,
                and publish social media content across multiple networks, specifically including <strong>Facebook Pages</strong>,{' '}
                <strong>Instagram Professional / Creator Accounts</strong>, <strong>LinkedIn</strong>, and <strong>Bluesky</strong>.
              </p>
              <p>
                We value your privacy and transparency. We strictly adhere to the guidelines set forth by the{' '}
                <strong>Meta Platform Terms</strong>, the <strong>Instagram Community Guidelines</strong>, the General Data Protection
                Regulation (<strong>GDPR</strong>), and the California Consumer Privacy Act (<strong>CCPA</strong>).
              </p>
            </section>

            {/* Section 2 — Meta Specifics */}
            <section id="meta-data" className="legal-section legal-section-highlight">
              <div className="legal-highlight-badge">
                <Globe size={14} />
                <span>Meta Platform Data Compliance</span>
              </div>
              <h2 className="legal-section-title">2. Meta (Facebook & Instagram) Platform Data</h2>
              <p>
                When you connect your Meta accounts (Facebook Page or Instagram Business/Creator Account) to OmniPulse,
                we use official Meta Graph APIs with OAuth 2.0 authorization tokens. We request only the minimal permissions
                strictly required to publish, schedule, and preview your posts:
              </p>

              <div className="legal-table-wrapper">
                <table className="legal-table">
                  <thead>
                    <tr>
                      <th>Meta Permission</th>
                      <th>Purpose & Scope</th>
                      <th>Data Accessed</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><code>pages_show_list</code></td>
                      <td>Allows you to choose which Facebook Page to connect and manage</td>
                      <td>List of Facebook Pages you administrate (Name, Page ID)</td>
                    </tr>
                    <tr>
                      <td><code>pages_read_engagement</code></td>
                      <td>Verifies account health, status, and publish confirmation</td>
                      <td>Publish verification response metadata</td>
                    </tr>
                    <tr>
                      <td><code>pages_manage_posts</code></td>
                      <td>Publishes text updates, links, and media to your chosen Facebook Page</td>
                      <td>Post status and post ID returned upon dispatch</td>
                    </tr>
                    <tr>
                      <td><code>instagram_basic</code></td>
                      <td>Identifies your connected Instagram Professional account</td>
                      <td>Instagram Business Account ID, handle/username</td>
                    </tr>
                    <tr>
                      <td><code>instagram_content_publish</code></td>
                      <td>Creates media containers and publishes posts to your Instagram grid</td>
                      <td>Media URLs uploaded for publication and publication confirmation</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="legal-callout legal-callout-info">
                <CheckCircle2 size={18} className="legal-callout-icon text-emerald-500" />
                <div className="legal-callout-text">
                  <strong>Strict Non-Commercialization Guarantee:</strong> OmniPulse does <strong>NOT</strong> sell, rent, monetize,
                  or transfer Meta user data, Facebook page metrics, or Instagram follower details to third-party data brokers,
                  advertising networks, or unauthorized entities. All access is strictly used to deliver publishing operations requested by you.
                </div>
              </div>
            </section>

            {/* Section 3 */}
            <section id="data-collection" className="legal-section">
              <h2 className="legal-section-title">3. What Information We Collect</h2>
              <p>We collect and process the following categories of information:</p>
              <ul className="legal-list">
                <li>
                  <strong>Account Identification:</strong> Your full name, email address, password hash (securely hashed via Supabase Auth),
                  role, and brand name.
                </li>
                <li>
                  <strong>Social Media Connection Tokens:</strong> Encrypted platform tokens, page IDs, and user handles necessary to interact
                  with social platform APIs on your behalf.
                </li>
                <li>
                  <strong>Post Content & Media:</strong> Post text drafts, prompts, chosen tone, scheduled publishing dates/times, and media
                  attachments (images in JPG, JPEG, and PNG format) uploaded directly by you.
                </li>
                <li>
                  <strong>Operational Logs:</strong> Request timestamps, delivery status (published, scheduled, or failed), and platform error codes
                  necessary for diagnostics and automated retries.
                </li>
              </ul>
            </section>

            {/* Section 4 */}
            <section id="data-usage" className="legal-section">
              <h2 className="legal-section-title">4. How We Use Your Information</h2>
              <p>Your information is used solely for the following explicit purposes:</p>
              <ol className="legal-ordered-list">
                <li>To authenticate your session and protect your OmniPulse account from unauthorized access.</li>
                <li>To dispatch authorized social media posts to your chosen networks at your instructed schedule.</li>
                <li>To provide live status reports and audit logs indicating whether each post succeeded or encountered an API limit.</li>
                <li>To prevent fraud, abuse, and violation of social platform guidelines.</li>
                <li>To enforce our Terms of Service and comply with applicable legal obligations.</li>
              </ol>
            </section>

            {/* Section 5 — AI Processing */}
            <section id="ai-processing" className="legal-section">
              <h2 className="legal-section-title">5. AI Processing & Groq Integration</h2>
              <p>
                OmniPulse integrates with <strong>Groq Cloud API</strong> (using open high-performance models like LLaMA 3.3)
                to generate post drafts, headlines, and tone variations when you click <em>Generate with AI</em>.
              </p>
              <div className="legal-callout legal-callout-security">
                <Lock size={18} className="legal-callout-icon text-indigo-500" />
                <div className="legal-callout-text">
                  <strong>AI Privacy Safeguards:</strong>
                  <ul className="mt-2 space-y-1">
                    <li>Only the prompt, topic, tone, and language you enter into the form are sent to the Groq API.</li>
                    <li>No Meta account tokens, passwords, personal emails, or private social profiles are ever shared with Groq.</li>
                    <li>Prompts are not used to train global public AI models without your express consent.</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Section 6 */}
            <section id="data-storage" className="legal-section">
              <h2 className="legal-section-title">6. Storage, Security & Retention</h2>
              <p>
                We implement industry-standard administrative, physical, and technical security safeguards to protect your data:
              </p>
              <ul className="legal-list">
                <li>
                  <strong>Database Infrastructure:</strong> All account metadata, draft posts, and scheduled queues are stored in{' '}
                  <strong>Supabase</strong> with AES-256 encryption at rest and TLS 1.3 encryption in transit.
                </li>
                <li>
                  <strong>Row Level Security (RLS):</strong> Strict database isolation guarantees that users can only access their own
                  posts and credentials.
                </li>
                <li>
                  <strong>Data Retention Period:</strong> We retain your posts and connection credentials only for as long as your
                  account remains active. You can delete individual posts or disconnect platforms at any time.
                </li>
              </ul>
            </section>

            {/* Section 7 — User Data Deletion Instructions */}
            <section id="data-deletion" className="legal-section legal-section-action">
              <div className="legal-highlight-badge legal-highlight-badge-warning">
                <Trash2 size={14} />
                <span>Facebook App Verification Requirement</span>
              </div>
              <h2 className="legal-section-title">7. User Data Deletion Instructions</h2>
              <p>
                In compliance with <strong>Facebook Platform Terms (Section 4.d)</strong> and international privacy regulations,
                OmniPulse provides clear, simple mechanisms for users to request the complete deletion of their account data and
                associated Meta platform data.
              </p>

              <div className="legal-steps-grid">
                <div className="legal-step-card">
                  <div className="legal-step-num">Option 1</div>
                  <h3 className="legal-step-title">In-App Immediate Disconnect & Deletion</h3>
                  <p className="legal-step-desc">
                    1. Log into your OmniPulse dashboard.<br />
                    2. Go to <strong>Connected Platforms</strong>.<br />
                    3. Locate Facebook or Instagram and click <strong>Disconnect</strong>.<br />
                    4. To delete all post history, navigate to <strong>Settings &rarr; Account &rarr; Delete All Data</strong>.
                    All associated tokens and cached drafts are immediately purged from our database.
                  </p>
                </div>

                <div className="legal-step-card">
                  <div className="legal-step-num">Option 2</div>
                  <h3 className="legal-step-title">Revoke Access via Facebook Settings</h3>
                  <p className="legal-step-desc">
                    1. Go to your Facebook profile &rarr; <strong>Settings &amp; Privacy &rarr; Settings</strong>.<br />
                    2. In the left menu, select <strong>Business Integrations</strong> (or <em>Apps and Websites</em>).<br />
                    3. Find <strong>OmniPulse</strong> in the active list and click <strong>Remove</strong>.<br />
                    4. Check the box to delete all posts and links published by OmniPulse on your behalf if desired.
                  </p>
                </div>

                <div className="legal-step-card">
                  <div className="legal-step-num">Option 3</div>
                  <h3 className="legal-step-title">Direct Privacy Deletion Request</h3>
                  <p className="legal-step-desc">
                    You can email our Privacy Officer directly at <a href="mailto:privacy@omnipulse.ai" className="text-violet-600 font-semibold underline">privacy@omnipulse.ai</a> with
                    the subject <em>&quot;Meta Data Deletion Request&quot;</em> along with your account email.
                    Requests are fulfilled within 48 business hours with an email confirmation and audit reference ID.
                  </p>
                </div>
              </div>

              <div className="mt-4 text-center">
                <button
                  type="button"
                  onClick={onNavigateDataDeletion || (() => { window.location.href = '/data-deletion'; })}
                  className="legal-deletion-direct-btn"
                >
                  <span>Open Dedicated Data Deletion Instructions Page &rarr;</span>
                </button>
              </div>
            </section>

            {/* Section 8 */}
            <section id="user-rights" className="legal-section">
              <h2 className="legal-section-title">8. Your Rights (GDPR &amp; CCPA)</h2>
              <p>Depending on your jurisdiction, you have the following rights regarding your personal information:</p>
              <ul className="legal-list">
                <li><strong>Right of Access:</strong> Request a copy of the personal information we hold about you.</li>
                <li><strong>Right of Rectification:</strong> Request correction of inaccurate or incomplete personal records.</li>
                <li><strong>Right to Erasure (&quot;Right to be Forgotten&quot;):</strong> Request the permanent deletion of your account and credentials.</li>
                <li><strong>Right to Restrict or Object:</strong> Restrict or object to the processing of your data.</li>
                <li><strong>Right to Data Portability:</strong> Obtain an export of your created posts in a machine-readable JSON format.</li>
                <li><strong>Non-Discrimination:</strong> We will never discriminate against you for exercising any of your privacy rights.</li>
              </ul>
            </section>

            {/* Section 9 */}
            <section id="contact" className="legal-section">
              <h2 className="legal-section-title">9. Contact &amp; Data Protection Officer</h2>
              <p>
                If you have questions, feedback, or requests regarding this Privacy Policy or our compliance with Meta Platform Terms,
                please contact our Data Protection Officer:
              </p>

              <div className="legal-contact-card">
                <div className="legal-contact-item">
                  <Mail size={18} className="legal-contact-icon-violet" />
                  <div>
                    <span className="legal-contact-label">Privacy &amp; Data Compliance</span>
                    <a href="mailto:privacy@omnipulse.ai" className="legal-contact-value">
                      privacy@omnipulse.ai
                    </a>
                  </div>
                </div>

                <div className="legal-contact-item">
                  <ShieldCheck size={18} className="legal-contact-icon-emerald" />
                  <div>
                    <span className="legal-contact-label">Technical Support &amp; Verification</span>
                    <a href="mailto:support@omnipulse.ai" className="legal-contact-value">
                      support@omnipulse.ai
                    </a>
                  </div>
                </div>
              </div>
            </section>
          </main>
        </div>
      </div>

      {/* Footer */}
      <footer className="legal-footer">
        <div className="legal-footer-inner">
          <p>&copy; {new Date().getFullYear()} OmniPulse AI Social Media Agent. All rights reserved.</p>
          <div className="legal-footer-links">
            <button
              type="button"
              onClick={onNavigateTerms || (() => { window.location.href = '/terms'; })}
              className="legal-footer-link"
            >
              Terms of Service
            </button>
            <span className="text-slate-400">&bull;</span>
            <button
              type="button"
              onClick={onNavigateDataDeletion || (() => { window.location.href = '/data-deletion'; })}
              className="legal-footer-link"
            >
              User Data Deletion
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default PrivacyPolicy;
