import React, { useState } from 'react';
import {
  FileText,
  ArrowLeft,
  Printer,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Scale,
  Sparkles,
  ExternalLink,
  Lock,
  Globe
} from 'lucide-react';

interface TermsOfServiceProps {
  onBack?: () => void;
  onNavigatePrivacy?: () => void;
  onNavigateDataDeletion?: () => void;
}

export const TermsOfService: React.FC<TermsOfServiceProps> = ({
  onBack,
  onNavigatePrivacy,
  onNavigateDataDeletion,
}) => {
  const [activeSection, setActiveSection] = useState<string>('social-terms');

  const handlePrint = () => {
    window.print();
  };

  const sections = [
    { id: 'acceptance', title: '1. Acceptance of Terms' },
    { id: 'service-desc', title: '2. Description of OmniPulse' },
    { id: 'social-terms', title: '3. Meta & Social Platform Terms' },
    { id: 'user-accounts', title: '4. User Accounts & Security' },
    { id: 'acceptable-use', title: '5. Acceptable Use Policy' },
    { id: 'content-ownership', title: '6. User Content & IP Rights' },
    { id: 'ai-disclaimer', title: '7. AI-Generated Content Disclaimer' },
    { id: 'availability', title: '8. Service Availability & API Limits' },
    { id: 'termination', title: '9. Account Termination' },
    { id: 'liability', title: '10. Limitation of Liability' },
    { id: 'contact', title: '11. Governing Law & Contact' },
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
              <span className="legal-badge">Terms of Service</span>
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
            <Scale size={14} className="text-violet-400" />
            <span>Standard Terms &amp; Conditions for Multi-Platform Social Publishing</span>
          </div>
          <h1 className="legal-hero-title">OmniPulse Terms of Service</h1>
          <p className="legal-hero-subtitle">
            Last Updated &amp; Effective: <strong>October 30, 2026</strong>
          </p>
          <p className="legal-hero-desc">
            These Terms of Service (&quot;Terms&quot;) govern your access to and use of the OmniPulse AI Social Media Agent.
            By creating an account, connecting third-party platforms (including Meta Facebook Pages and Instagram Professional
            accounts), or publishing content through our service, you agree to be bound by these Terms.
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
                  onClick={onNavigatePrivacy || (() => { window.location.href = '/privacy'; })}
                  className="legal-toc-highlight-btn"
                >
                  <ShieldCheck size={13} />
                  <span>Review Privacy Policy</span>
                </button>
              </div>
            </div>
          </aside>

          {/* Legal Document Content */}
          <main className="legal-content-main">
            {/* Section 1 */}
            <section id="acceptance" className="legal-section">
              <h2 className="legal-section-title">1. Acceptance of Terms</h2>
              <p>
                By accessing or using <strong>OmniPulse AI Social Media Agent</strong> (&quot;OmniPulse&quot;, &quot;the Service&quot;),
                you confirm that you are at least 18 years old, legally capable of entering into binding contracts, and accept
                these Terms in full. If you represent an entity or agency, you warrant that you possess the authorized authority
                to bind that organization.
              </p>
            </section>

            {/* Section 2 */}
            <section id="service-desc" className="legal-section">
              <h2 className="legal-section-title">2. Description of OmniPulse</h2>
              <p>
                OmniPulse is an automated social media management application providing content drafting, AI-assisted copy
                generation, multi-channel previewing, automated scheduling, and one-click publishing to connected social media networks,
                including:
              </p>
              <ul className="legal-list">
                <li><strong>Facebook:</strong> Publishing to authorized Facebook Pages via the Meta Graph API.</li>
                <li><strong>Instagram:</strong> Publishing media posts to Instagram Creator and Business accounts via Meta Graph API.</li>
                <li><strong>LinkedIn:</strong> Publishing professional status updates and articles to LinkedIn personal profiles.</li>
                <li><strong>Bluesky:</strong> Publishing short-form updates via the AT Protocol.</li>
              </ul>
            </section>

            {/* Section 3 — Meta Specific Compliance */}
            <section id="social-terms" className="legal-section legal-section-highlight">
              <div className="legal-highlight-badge">
                <Globe size={14} />
                <span>Meta Platform Compliance</span>
              </div>
              <h2 className="legal-section-title">3. Compliance with Meta &amp; Social Platform Terms</h2>
              <p>
                Your use of OmniPulse to connect or publish to third-party social networks requires strict compliance with the
                respective platform policies. Specifically, you agree to abide by:
              </p>
              <ul className="legal-list">
                <li>
                  <a
                    href="https://developers.facebook.com/terms/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="legal-external-link"
                  >
                    Meta Platform Terms <ExternalLink size={12} />
                  </a>
                </li>
                <li>
                  <a
                    href="https://help.instagram.com/477434105621119"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="legal-external-link"
                  >
                    Instagram Community Guidelines <ExternalLink size={12} />
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.facebook.com/page_guidelines.php"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="legal-external-link"
                  >
                    Facebook Pages and Groups Policy <ExternalLink size={12} />
                  </a>
                </li>
              </ul>

              <div className="legal-callout legal-callout-warning">
                <AlertCircle size={18} className="legal-callout-icon text-amber-500" />
                <div className="legal-callout-text">
                  <strong>Zero-Tolerance Abuse Policy:</strong> You must not use OmniPulse to automate repetitive spam, deceptive
                  clickbait, coordinated inauthentic behavior, or violate Meta&apos;s anti-spam rules. Any violation will lead to immediate
                  account termination and revocation of API tokens.
                </div>
              </div>
            </section>

            {/* Section 4 */}
            <section id="user-accounts" className="legal-section">
              <h2 className="legal-section-title">4. User Accounts &amp; Security</h2>
              <p>
                When creating an OmniPulse account, you must provide accurate, complete, and current information.
                You are responsible for safeguarding your login credentials. If you suspect any unauthorized access,
                you must notify us immediately at <a href="mailto:security@omnipulse.ai" className="legal-link">security@omnipulse.ai</a>.
              </p>
            </section>

            {/* Section 5 */}
            <section id="acceptable-use" className="legal-section">
              <h2 className="legal-section-title">5. Acceptable Use Policy</h2>
              <p>You agree not to use the Service to:</p>
              <ul className="legal-list">
                <li>Publish content that is unlawful, defamatory, harassing, sexually explicit, abusive, or promoting hate speech.</li>
                <li>Infringe upon the copyright, trademark, patent, or proprietary rights of any third party.</li>
                <li>Distribute viruses, malware, trojans, or malicious payloads through media files.</li>
                <li>Attempt to reverse-engineer, decompile, or tamper with the OmniPulse API or infrastructure.</li>
                <li>Bypass social media platform rate limits, terms, or API quotas through automated abuse.</li>
              </ul>
            </section>

            {/* Section 6 */}
            <section id="content-ownership" className="legal-section">
              <h2 className="legal-section-title">6. User Content &amp; Intellectual Property</h2>
              <p>
                <strong>You retain 100% ownership</strong> of all post text, prompts, ideas, images, and creative assets that
                you submit to OmniPulse.
              </p>
              <p>
                By submitting content for distribution, you grant OmniPulse a non-exclusive, worldwide, royalty-free license solely
                to process, format, optimize, and transmit your content to the social platforms you have explicitly selected.
              </p>
            </section>

            {/* Section 7 */}
            <section id="ai-disclaimer" className="legal-section">
              <h2 className="legal-section-title">7. AI-Generated Content Disclaimer</h2>
              <p>
                OmniPulse provides AI-assisted content suggestions powered by Groq and large language models. While these tools
                strive to produce high-quality, relevant social copy:
              </p>
              <ul className="legal-list">
                <li>AI outputs are suggestions and drafts intended for human review and refinement.</li>
                <li>
                  <strong>You remain solely responsible</strong> for reviewing, editing, fact-checking, and verifying the legality,
                  suitability, and accuracy of any post before clicking <em>Publish Now</em> or scheduling.
                </li>
                <li>OmniPulse does not warrant that AI-generated copy will achieve specific follower growth, viral reach, or engagement metrics.</li>
              </ul>
            </section>

            {/* Section 8 */}
            <section id="availability" className="legal-section">
              <h2 className="legal-section-title">8. Service Availability &amp; Platform API Limits</h2>
              <p>
                OmniPulse relies on external social network APIs (e.g. Meta Graph API, LinkedIn REST API, AT Protocol).
                While we strive for continuous uptime and reliability:
              </p>
              <ul className="legal-list">
                <li>Social media platforms periodically enforce hourly or daily rate limits, security audits, and token expirations.</li>
                <li>We are not liable for publication delays caused by third-party API downtime, network outages, or platform policy suspensions.</li>
              </ul>
            </section>

            {/* Section 9 */}
            <section id="termination" className="legal-section">
              <h2 className="legal-section-title">9. Account Termination</h2>
              <p>
                You may close your account and delete your data at any time via the OmniPulse dashboard or by emailing{' '}
                <a href="mailto:support@omnipulse.ai" className="legal-link">support@omnipulse.ai</a>.
              </p>
              <p>
                We reserve the right to suspend or terminate accounts that breach these Terms, Meta Platform Terms, or applicable laws,
                without prior notice.
              </p>
            </section>

            {/* Section 10 */}
            <section id="liability" className="legal-section">
              <h2 className="legal-section-title">10. Limitation of Liability &amp; Disclaimers</h2>
              <p>
                THE SERVICE IS PROVIDED ON AN &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; BASIS WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS
                OR IMPLIED. IN NO EVENT SHALL OMNIPULSE, ITS FOUNDERS, OR OPERATORS BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
                CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING FROM YOUR USE OF THE SERVICE OR ANY CONTENT PUBLISHED THROUGH IT.
              </p>
            </section>

            {/* Section 11 */}
            <section id="contact" className="legal-section">
              <h2 className="legal-section-title">11. Governing Law &amp; Contact</h2>
              <p>
                These Terms shall be governed by and construed in accordance with the laws of the jurisdiction in which OmniPulse operates,
                without regard to its conflict of law principles.
              </p>
              <div className="legal-contact-card">
                <div className="legal-contact-item">
                  <Scale size={18} className="legal-contact-icon-violet" />
                  <div>
                    <span className="legal-contact-label">Legal Inquiries</span>
                    <a href="mailto:legal@omnipulse.ai" className="legal-contact-value">
                      legal@omnipulse.ai
                    </a>
                  </div>
                </div>
                <div className="legal-contact-item">
                  <CheckCircle2 size={18} className="legal-contact-icon-emerald" />
                  <div>
                    <span className="legal-contact-label">General Support</span>
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
              onClick={onNavigatePrivacy || (() => { window.location.href = '/privacy'; })}
              className="legal-footer-link"
            >
              Privacy Policy
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
export default TermsOfService;
