# OmniPulse Frontend — AI Social Media Agent

OmniPulse is an autonomous, high-performance social media management and AI post orchestration interface built with **React 18**, **TypeScript**, and **Vite**.

## 🌟 Key Features

- **Omni-Channel Creation Studio**: Craft and schedule posts with live character counters, dynamic previews, and tone customization.
- **AI-Powered Multi-Platform Synthesis**: Generate tailored post variants optimized for Bluesky, LinkedIn, Facebook, and Instagram.
- **Dedicated Platform Dashboards**:
  - 🦋 **Bluesky**: AT Protocol feed monitor, character validation (≤ 300 chars).
  - 💼 **LinkedIn**: Professional narrative formatting, hashtags, and preview cards.
  - 📘 **Facebook**: Page post publisher and feed engagement metrics.
  - 📸 **Instagram**: Media container requirements validation and visual preview.
- **Interactive Calendar & Scheduler**: Full-featured visual timeline and schedule manager.
- **Real-Time Analytics & Logs**: Monitor post performance, delivery status, and scheduling queues.

---

## 🛠 Tech Stack

- **Framework**: [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Bundler & Dev Server**: [Vite](https://vitejs.dev/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **State & Backend Connectivity**: REST API integration with FastAPI backend & optional Supabase client.

---

## 🚀 Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (v18.x or newer recommended)
- `npm` or `yarn` / `pnpm`

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Vaishnavik-droid/Ai-social-media-agent-.git
   cd Ai-social-media-agent-
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```
   Configure your backend API URL (default: `http://localhost:8000`).

### Running Locally

Start the Vite development server:
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) (or the port specified in terminal) in your browser.

### Building for Production

Compile TypeScript and build the optimized production assets:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

---

## 📂 Project Structure

```
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable UI components & layouts
│   ├── pages/           # Route views (Dashboard, PostStudio, Calendar, Platforms, Settings)
│   ├── services/        # API client and Supabase service integration
│   ├── types/           # TypeScript interfaces & domain types
│   ├── App.tsx          # Main application router and state
│   ├── main.tsx         # Application entrypoint
│   └── index.css        # Global design system & utility styles
├── docs/                # Architecture context and reference
├── package.json         # Scripts and project dependencies
├── tsconfig.json        # TypeScript configuration
└── vite.config.ts       # Vite configuration
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
