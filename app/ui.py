"""Web UI playground for interactive LinkedIn profile lookup and developer testing."""

HTML_PLAYGROUND = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ProfileForge — Profile Lookup API</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --space-1: 4px;
      --space-2: 8px;
      --space-3: 12px;
      --space-4: 16px;
      --space-5: 20px;
      --space-6: 24px;
      --space-8: 32px;
      --space-10: 40px;
      --space-12: 48px;

      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 16px;
      --radius-full: 9999px;

      --bg-canvas: #080c14;
      --bg-surface: #0e1422;
      --bg-card: rgba(14, 20, 34, 0.75);
      --bg-card-hover: rgba(22, 31, 51, 0.85);
      --bg-subtle: rgba(255, 255, 255, 0.03);
      --bg-input: rgba(10, 15, 26, 0.85);

      --border-subtle: rgba(255, 255, 255, 0.07);
      --border-default: rgba(255, 255, 255, 0.12);
      --border-focus: rgba(59, 130, 246, 0.5);

      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --text-dim: #475569;

      --accent-blue: #3b82f6;
      --accent-blue-hover: #2563eb;
      --accent-blue-subtle: rgba(59, 130, 246, 0.12);
      --accent-emerald: #10b981;
      --accent-emerald-subtle: rgba(16, 185, 129, 0.12);
      --accent-amber: #f59e0b;
      --accent-amber-subtle: rgba(245, 158, 11, 0.12);
      --accent-red: #ef4444;
      --accent-red-subtle: rgba(239, 68, 68, 0.12);

      --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', SFMono-Regular, Menlo, Monaco, Consolas, monospace;

      --shadow-card: 0 4px 20px -2px rgba(0, 0, 0, 0.5), 0 0 0 1px var(--border-subtle);
      --shadow-glow: 0 0 35px -5px rgba(59, 130, 246, 0.15);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-canvas);
      background-image:
        radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(16, 185, 129, 0.04) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(30, 58, 138, 0.05) 0px, transparent 60%);
      background-attachment: fixed;
      color: var(--text-primary);
      font-family: var(--font-sans);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }

    /* Top Navigation Header */
    header {
      background: rgba(8, 12, 20, 0.85);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-subtle);
      padding: var(--space-3) var(--space-8);
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 50;
    }

    .brand-group {
      display: flex;
      align-items: center;
      gap: var(--space-3);
    }

    .brand-link {
      display: flex;
      align-items: center;
      gap: var(--space-2);
      text-decoration: none;
    }

    .brand-icon {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
    }

    .brand-icon svg {
      width: 18px;
      height: 18px;
      fill: #ffffff;
    }

    .brand-name {
      font-size: 1.1rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #ffffff;
    }

    .brand-divider {
      color: var(--text-dim);
      font-weight: 300;
    }

    .brand-desc {
      font-size: 0.85rem;
      color: var(--text-secondary);
      font-weight: 500;
    }

    .status-badge {
      font-size: 0.75rem;
      font-weight: 600;
      padding: var(--space-1) var(--space-3);
      background: var(--accent-emerald-subtle);
      border: 1px solid rgba(16, 185, 129, 0.25);
      color: #34d399;
      border-radius: var(--radius-full);
      display: inline-flex;
      align-items: center;
      gap: var(--space-2);
    }

    .status-dot {
      width: 6px;
      height: 6px;
      background: var(--accent-emerald);
      border-radius: 50%;
      box-shadow: 0 0 6px var(--accent-emerald);
    }

    .nav-actions {
      display: flex;
      align-items: center;
      gap: var(--space-2);
    }

    .nav-link {
      color: var(--text-secondary);
      text-decoration: none;
      font-size: 0.85rem;
      font-weight: 600;
      padding: var(--space-2) var(--space-3);
      border-radius: var(--radius-sm);
      transition: all 0.15s ease;
    }

    .nav-link:hover {
      color: #ffffff;
      background: var(--bg-subtle);
    }

    /* Main Container */
    main {
      flex: 1;
      max-width: 1120px;
      width: 100%;
      margin: var(--space-8) auto;
      padding: 0 var(--space-6);
    }

    /* Hero Section */
    .hero-section {
      text-align: center;
      margin-bottom: var(--space-8);
    }

    .hero-eyebrow {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--accent-blue);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: var(--space-2);
    }

    .hero-title {
      font-size: 2.25rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      margin-bottom: var(--space-2);
      color: #ffffff;
    }

    .hero-subtitle {
      color: var(--text-secondary);
      font-size: 1rem;
      max-width: 580px;
      margin: 0 auto;
    }

    /* Search Card */
    .search-card {
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--border-default);
      border-radius: var(--radius-lg);
      padding: var(--space-5);
      box-shadow: var(--shadow-card), var(--shadow-glow);
      margin-bottom: var(--space-8);
      transition: border-color 0.2s ease;
    }

    .search-card:focus-within {
      border-color: var(--border-focus);
    }

    .search-form {
      display: flex;
      gap: var(--space-3);
      align-items: center;
      flex-wrap: wrap;
    }

    .input-group-url {
      position: relative;
      flex: 3;
      min-width: 280px;
    }

    .input-icon {
      position: absolute;
      left: var(--space-4);
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-dim);
      pointer-events: none;
      width: 16px;
      height: 16px;
    }

    .input-group-key {
      position: relative;
      flex: 1.2;
      min-width: 150px;
    }

    .input-control {
      width: 100%;
      background: var(--bg-input);
      border: 1px solid var(--border-default);
      color: #ffffff;
      padding: var(--space-3) var(--space-4);
      padding-left: var(--space-10);
      border-radius: var(--radius-md);
      font-size: 0.92rem;
      font-family: var(--font-sans);
      outline: none;
      transition: all 0.15s ease;
    }

    .input-control.no-icon {
      padding-left: var(--space-4);
    }

    .input-control:focus {
      border-color: var(--accent-blue);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-blue-hover) 100%);
      color: #ffffff;
      border: none;
      padding: var(--space-3) var(--space-6);
      border-radius: var(--radius-md);
      font-size: 0.92rem;
      font-weight: 600;
      font-family: var(--font-sans);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--space-2);
      transition: all 0.15s ease;
      white-space: nowrap;
      min-width: 140px;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }

    .btn-primary:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35);
    }

    .btn-primary:active {
      transform: translateY(0);
    }

    .btn-primary:disabled {
      opacity: 0.7;
      cursor: not-allowed;
      transform: none;
    }

    /* Sub-Controls */
    .subcontrols-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: var(--space-3);
      margin-top: var(--space-4);
      padding-top: var(--space-3);
      border-top: 1px solid var(--border-subtle);
      font-size: 0.82rem;
    }

    .samples-bar {
      display: flex;
      align-items: center;
      gap: var(--space-2);
      flex-wrap: wrap;
    }

    .samples-label {
      color: var(--text-dim);
      font-weight: 600;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .sample-pill {
      background: var(--bg-subtle);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      padding: 7px 12px;
      min-height: 36px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      font-size: 0.8rem;
      font-weight: 500;
      transition: all 0.15s ease;
    }

    .sample-pill:hover {
      background: var(--accent-blue-subtle);
      border-color: rgba(59, 130, 246, 0.3);
      color: #ffffff;
    }

    .options-toggle {
      background: transparent;
      border: 0;
      padding: 7px 0;
      min-height: 36px;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 0.8rem;
      font-family: inherit;
      user-select: none;
    }

    .options-toggle:hover {
      color: var(--text-secondary);
    }

    .empty-list-message {
      color: var(--text-dim);
      font-size: 0.88rem;
      padding: var(--space-4) 0;
    }

    .developer-drawer {
      margin-top: var(--space-3);
      padding: var(--space-3);
      background: var(--bg-subtle);
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-subtle);
      display: none;
    }

    .developer-drawer.open {
      display: flex;
      align-items: center;
      gap: var(--space-3);
    }

    .checkbox-label {
      display: flex;
      align-items: center;
      gap: var(--space-2);
      color: var(--text-secondary);
      font-size: 0.82rem;
      cursor: pointer;
    }

    .checkbox-label input {
      accent-color: var(--accent-blue);
    }

    /* Error / Alert Banner */
    .alert-banner {
      background: var(--accent-red-subtle);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #fca5a5;
      padding: var(--space-4);
      border-radius: var(--radius-md);
      margin-bottom: var(--space-6);
      display: none;
      font-size: 0.88rem;
    }

    .alert-banner-title {
      font-weight: 700;
      margin-bottom: var(--space-1);
      display: flex;
      align-items: center;
      gap: var(--space-2);
    }

    /* Empty State */
    .empty-state {
      background: var(--bg-card);
      border: 1px dashed var(--border-default);
      border-radius: var(--radius-lg);
      padding: var(--space-12) var(--space-6);
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }

    .empty-icon {
      width: 48px;
      height: 48px;
      background: var(--bg-subtle);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-dim);
      margin-bottom: var(--space-4);
    }

    .empty-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text-secondary);
      margin-bottom: var(--space-1);
    }

    .empty-desc {
      color: var(--text-muted);
      font-size: 0.88rem;
      max-width: 420px;
    }

    /* Results Container */
    .results-container {
      display: none;
      flex-direction: column;
      gap: var(--space-6);
    }

    /* Profile Hero Card */
    .profile-hero-card {
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--border-default);
      border-radius: var(--radius-lg);
      padding: var(--space-6);
      box-shadow: var(--shadow-card);
    }

    .hero-top-row {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: var(--space-4);
      flex-wrap: wrap;
    }

    .profile-identity {
      display: flex;
      gap: var(--space-4);
      align-items: flex-start;
    }

    .profile-avatar {
      width: 72px;
      height: 72px;
      border-radius: 50%;
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      border: 2px solid rgba(59, 130, 246, 0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
      font-weight: 800;
      color: #93c5fd;
      overflow: hidden;
      flex-shrink: 0;
    }

    .profile-avatar img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .profile-name {
      font-size: 1.5rem;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.02em;
    }

    .profile-headline {
      color: #cbd5e1;
      font-size: 0.95rem;
      font-weight: 500;
      margin-top: var(--space-1);
      max-width: 600px;
    }

    .profile-meta-row {
      display: flex;
      align-items: center;
      gap: var(--space-4);
      margin-top: var(--space-2);
      font-size: 0.82rem;
      color: var(--text-muted);
      flex-wrap: wrap;
    }

    .meta-item {
      display: flex;
      align-items: center;
      gap: var(--space-1);
    }

    .meta-link {
      color: var(--accent-blue);
      text-decoration: none;
    }

    .meta-link:hover {
      text-decoration: underline;
    }

    /* Compact Metrics Strip */
    .metrics-strip {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: var(--space-3);
      margin-top: var(--space-5);
      padding-top: var(--space-4);
      border-top: 1px solid var(--border-subtle);
    }

    @media (max-width: 768px) {
      .metrics-strip {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .metric-cell {
      background: var(--bg-subtle);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: var(--space-3);
    }

    .metric-label {
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: var(--space-1);
    }

    .metric-value {
      font-size: 1.15rem;
      font-weight: 700;
      color: #ffffff;
      font-family: var(--font-mono);
      display: flex;
      align-items: center;
      gap: var(--space-2);
    }

    .metric-badge {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: var(--radius-sm);
    }

    .metric-badge.hit {
      background: var(--accent-emerald-subtle);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .metric-badge.miss {
      background: var(--accent-amber-subtle);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.3);
    }

    /* Segmented Navigation Tabs */
    .tabs-nav {
      display: flex;
      gap: var(--space-1);
      background: rgba(14, 20, 34, 0.6);
      padding: var(--space-1);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      overflow-x: auto;
    }

    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-secondary);
      padding: var(--space-2) var(--space-4);
      border-radius: var(--radius-sm);
      font-size: 0.85rem;
      font-weight: 600;
      font-family: var(--font-sans);
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
    }

    .tab-btn:hover {
      color: #ffffff;
      background: var(--bg-subtle);
    }

    .tab-btn.active {
      background: var(--accent-blue);
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }

    /* Tab Content Cards */
    .tab-pane {
      display: none;
      background: var(--bg-card);
      border: 1px solid var(--border-default);
      border-radius: var(--radius-lg);
      padding: var(--space-6);
      box-shadow: var(--shadow-card);
    }

    .tab-pane.active {
      display: block;
    }

    .tab-pane-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: var(--space-4);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    /* Timeline Component */
    .timeline-stream {
      display: flex;
      flex-direction: column;
      gap: var(--space-5);
    }

    .timeline-item {
      position: relative;
      padding-left: var(--space-6);
      border-left: 2px solid rgba(59, 130, 246, 0.3);
    }

    .timeline-item::before {
      content: '';
      position: absolute;
      left: -5px;
      top: 4px;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-blue);
      box-shadow: 0 0 6px var(--accent-blue);
    }

    .item-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: var(--space-2);
    }

    .item-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: #ffffff;
    }

    .item-date {
      font-size: 0.8rem;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }

    .item-subtitle {
      color: var(--text-secondary);
      font-size: 0.85rem;
      margin-top: 2px;
    }

    .item-desc {
      color: var(--text-secondary);
      font-size: 0.85rem;
      margin-top: var(--space-2);
      line-height: 1.5;
    }

    /* Tag & Badges */
    .tag-cloud {
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-2);
    }

    .badge-tag {
      background: var(--bg-subtle);
      border: 1px solid var(--border-default);
      color: var(--text-secondary);
      padding: var(--space-1) var(--space-3);
      border-radius: var(--radius-sm);
      font-size: 0.82rem;
      font-weight: 500;
    }

    .badge-tag.blue {
      background: var(--accent-blue-subtle);
      border-color: rgba(59, 130, 246, 0.25);
      color: #93c5fd;
    }

    .badge-tag.green {
      background: var(--accent-emerald-subtle);
      border-color: rgba(16, 185, 129, 0.25);
      color: #6ee7b7;
    }

    /* Data Quality Overview Card */
    .dq-container {
      background: var(--bg-subtle);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: var(--space-4);
      margin-top: var(--space-4);
    }

    .dq-row {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      margin-bottom: var(--space-2);
      font-weight: 600;
    }

    .dq-track {
      height: 6px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: var(--radius-full);
      overflow: hidden;
      margin-bottom: var(--space-3);
    }

    .dq-bar {
      height: 100%;
      background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
      width: 0%;
      transition: width 0.4s ease;
    }

    /* JSON Viewer */
    .json-header-strip {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--space-3);
      font-size: 0.8rem;
      color: var(--text-muted);
    }

    .btn-copy {
      background: var(--bg-subtle);
      border: 1px solid var(--border-default);
      color: var(--text-secondary);
      padding: var(--space-1) var(--space-3);
      border-radius: var(--radius-sm);
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-copy:hover {
      background: rgba(255, 255, 255, 0.08);
      color: #ffffff;
    }

    pre.json-display {
      background: #050811;
      border: 1px solid var(--border-default);
      border-radius: var(--radius-md);
      padding: var(--space-4);
      font-family: var(--font-mono);
      font-size: 0.82rem;
      color: #38bdf8;
      overflow-x: auto;
      max-height: 520px;
      line-height: 1.5;
    }

    /* Spinner */
    .spinner-icon {
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: #ffffff;
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
      display: none;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    @media (max-width: 640px) {
      header {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: var(--space-2) var(--space-3);
        padding: var(--space-3) var(--space-4);
      }

      .brand-group {
        min-width: 0;
      }

      .brand-desc,
      .brand-divider {
        display: none;
      }

      .status-badge {
        justify-self: end;
      }

      .nav-actions {
        grid-column: 1 / -1;
        justify-content: flex-end;
        border-top: 1px solid var(--border-subtle);
        padding-top: var(--space-2);
      }

      main {
        margin: var(--space-6) auto;
        padding: 0 var(--space-4);
      }

      .hero-title {
        font-size: 1.8rem;
      }

      .search-card,
      .profile-hero-card,
      .tab-pane {
        padding: var(--space-4);
      }

      .search-form {
        align-items: stretch;
        flex-direction: column;
      }

      .input-group-url,
      .input-group-key {
        min-width: 0;
        width: 100%;
      }

      .btn-primary {
        width: 100%;
      }

      .subcontrols-row {
        align-items: flex-start;
      }

      .samples-bar {
        width: 100%;
      }

      .options-toggle {
        align-self: flex-start;
      }

      .profile-identity {
        gap: var(--space-3);
        width: 100%;
      }

      .profile-name {
        font-size: 1.25rem;
      }

      .profile-headline {
        overflow-wrap: anywhere;
      }

      .json-header-strip {
        align-items: flex-start;
        flex-wrap: wrap;
        gap: var(--space-2);
      }
    }

    @media (prefers-reduced-motion: reduce) {
      * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
      }
    }
  </style>
</head>
<body>

  <!-- Navigation Header -->
  <header>
    <div class="brand-group">
      <a href="/" class="brand-link" aria-label="ProfileForge Home">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        </div>
        <span class="brand-name">ProfileForge</span>
      </a>
      <span class="brand-divider">/</span>
      <span class="brand-desc">Profile Lookup API</span>
    </div>

    <div class="status-badge">
      <span class="status-dot"></span>
      <span>Operational</span>
    </div>

    <nav class="nav-actions" aria-label="Quick links">
      <a href="/docs" target="_blank" class="nav-link">Docs</a>
      <a href="/healthz" target="_blank" class="nav-link">Health</a>
    </nav>
  </header>

  <!-- Main Content -->
  <main>

    <!-- Hero Header -->
    <div class="hero-section">
      <div class="hero-eyebrow">Profile Lookup API</div>
      <h1 class="hero-title">Look up a profile. Get structured data.</h1>
      <p class="hero-subtitle">Direct acquisition with normalized schema extraction, in-memory caching, and data quality scoring.</p>
    </div>

    <!-- Search Card -->
    <section class="search-card" aria-label="Profile Search">
      <form class="search-form" onsubmit="event.preventDefault(); handleLookup();">

        <div class="input-group-url">
          <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" id="targetUrl" class="input-control" placeholder="https://www.linkedin.com/in/username" value="https://www.linkedin.com/in/sarah-jenkins-dev" required spellcheck="false">
        </div>

        <div class="input-group-key">
          <input type="password" id="clientApiKey" class="input-control no-icon" placeholder="Your ProfileForge API key" value="" aria-label="ProfileForge API Key" spellcheck="false">
        </div>

        <button type="submit" class="btn-primary" id="submitBtn">
          <span class="spinner-icon" id="loadingSpinner"></span>
          <span id="btnLabel">Fetch Profile</span>
        </button>

      </form>

      <!-- Subcontrols & Sample Chips -->
      <div class="subcontrols-row">
        <div class="samples-bar">
          <span class="samples-label">Sample Profiles:</span>
          <button type="button" class="sample-pill" onclick="loadSample('https://www.linkedin.com/in/sarah-jenkins-dev')">Sarah Jenkins</button>
          <button type="button" class="sample-pill" onclick="loadSample('https://www.linkedin.com/in/alex-mercer-tech')">Alex Mercer</button>
          <button type="button" class="sample-pill" onclick="loadSample('https://www.linkedin.com/in/maya-lin-ai')">Maya Lin</button>
        </div>

        <button type="button" class="options-toggle" onclick="toggleDevOptions()" id="devToggleText" aria-expanded="false" aria-controls="devDrawer">⚙️ Developer Options</button>
      </div>

      <div class="developer-drawer" id="devDrawer">
        <label class="checkbox-label">
          <input type="checkbox" id="bypassCacheOption">
          <span>Force live lookup (bypass cache)</span>
        </label>
      </div>
    </section>

    <!-- Error Alert Banner -->
    <div class="alert-banner" id="errorBanner" role="alert">
      <div class="alert-banner-title" id="errorTitle">Profile Lookup Failed</div>
      <div id="errorMessage">Please check the profile URL and try again.</div>
    </div>

    <!-- Empty State -->
    <div class="empty-state" id="emptyState">
      <div class="empty-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
      </div>
      <div class="empty-title">Ready for Profile Lookup</div>
      <div class="empty-desc">Enter a public LinkedIn profile URL above or select a sample profile to inspect normalized structured data.</div>
    </div>

    <!-- Results Display -->
    <div class="results-container" id="resultsContainer">

      <!-- Profile Hero Card -->
      <div class="profile-hero-card">
        <div class="hero-top-row">
          <div class="profile-identity">
            <div class="profile-avatar" id="resAvatar">SJ</div>
            <div>
              <h2 class="profile-name" id="resFullName">—</h2>
              <div class="profile-headline" id="resHeadline">—</div>
              <div class="profile-meta-row">
                <span class="meta-item" id="resLocationWrap">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="7" r="3"></circle></svg>
                  <span id="resLocation">—</span>
                </span>
                <span class="meta-item">
                  <a href="#" target="_blank" class="meta-link" id="resCanonicalLink">View on LinkedIn ↗</a>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Metrics Strip -->
        <div class="metrics-strip">
          <div class="metric-cell">
            <div class="metric-label">Latency</div>
            <div class="metric-value" id="resLatency">—</div>
          </div>
          <div class="metric-cell">
            <div class="metric-label">Cache Status</div>
            <div class="metric-value">
              <span class="metric-badge hit" id="resCacheBadge">Fresh Lookup</span>
            </div>
          </div>
          <div class="metric-cell">
            <div class="metric-label">Completeness</div>
            <div class="metric-value" id="resCompleteness">—</div>
          </div>
          <div class="metric-cell">
            <div class="metric-label">Followers</div>
            <div class="metric-value" id="resFollowers">—</div>
          </div>
        </div>
      </div>

      <!-- Segmented Tab Navigation -->
      <div class="tabs-nav" role="tablist">
        <button type="button" class="tab-btn active" role="tab" aria-selected="true" aria-controls="pane-overview" onclick="switchTab('overview', this)">Overview</button>
        <button type="button" class="tab-btn" role="tab" aria-selected="false" aria-controls="pane-experience" onclick="switchTab('experience', this)">Experience</button>
        <button type="button" class="tab-btn" role="tab" aria-selected="false" aria-controls="pane-education" onclick="switchTab('education', this)">Education</button>
        <button type="button" class="tab-btn" role="tab" aria-selected="false" aria-controls="pane-skills" onclick="switchTab('skills', this)">Skills</button>
        <button type="button" class="tab-btn" role="tab" aria-selected="false" aria-controls="pane-languages" onclick="switchTab('languages', this)">Languages & Certs</button>
        <button type="button" class="tab-btn" role="tab" aria-selected="false" aria-controls="pane-json" onclick="switchTab('json', this)">Raw JSON</button>
      </div>

      <!-- Tab Pane 1: Overview -->
      <div class="tab-pane active" id="pane-overview" role="tabpanel">
        <div class="tab-pane-title">Profile Overview</div>

        <div id="aboutSection" style="margin-bottom: var(--space-4);">
          <div style="font-size:0.8rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; margin-bottom:var(--space-1);">About</div>
          <p id="resAbout" style="color:#cbd5e1; font-size:0.9rem; line-height:1.6;">—</p>
        </div>

        <div class="dq-container">
          <div class="dq-row">
            <span>Data Quality Breakdown</span>
            <span id="resDqSummary">10 / 10 Sections</span>
          </div>
          <div class="dq-track">
            <div class="dq-bar" id="resDqBar"></div>
          </div>
          <div style="font-size:0.8rem; color:var(--text-muted);" id="resSectionsBreakdown">
            Available: Name, Headline, Location, About, Experience, Education, Skills, Languages
          </div>
        </div>
      </div>

      <!-- Tab Pane 2: Experience -->
      <div class="tab-pane" id="pane-experience" role="tabpanel">
        <div class="tab-pane-title">Professional Experience</div>
        <div class="timeline-stream" id="resExperienceList"></div>
      </div>

      <!-- Tab Pane 3: Education -->
      <div class="tab-pane" id="pane-education" role="tabpanel">
        <div class="tab-pane-title">Education History</div>
        <div class="timeline-stream" id="resEducationList"></div>
      </div>

      <!-- Tab Pane 4: Skills -->
      <div class="tab-pane" id="pane-skills" role="tabpanel">
        <div class="tab-pane-title">Skills & Proficiencies</div>
        <div class="tag-cloud" id="resSkillsList"></div>
      </div>

      <!-- Tab Pane 5: Languages & Certs -->
      <div class="tab-pane" id="pane-languages" role="tabpanel">
        <div class="tab-pane-title">Languages & Certifications</div>
        <div style="font-size:0.8rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; margin-bottom:var(--space-2);">Languages</div>
        <div class="tag-cloud" id="resLanguagesList" style="margin-bottom: var(--space-5);"></div>

        <div style="font-size:0.8rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; margin-bottom:var(--space-2);">Certifications</div>
        <div class="timeline-stream" id="resCertificationsList"></div>
      </div>

      <!-- Tab Pane 6: Raw JSON -->
      <div class="tab-pane" id="pane-json" role="tabpanel">
        <div class="json-header-strip">
          <span id="jsonMetaDetails">Source: linkedin · Request ID: —</span>
          <button type="button" class="btn-copy" id="copyJsonBtn" onclick="copyResponseJson()">Copy JSON</button>
        </div>
        <pre class="json-display" id="resRawJson">// JSON will be rendered here...</pre>
      </div>

    </div>

  </main>

  <script>
    let rawResponseData = null;

    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      }[character]));
    }

    function safeHttpUrl(value) {
      try {
        const parsed = new URL(String(value));
        return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? parsed.href : '';
      } catch (_) {
        return '';
      }
    }

    function initialsFor(name) {
      return String(name || 'U').trim().split(/\\s+/).map(part => part[0]).join('').substring(0, 2).toUpperCase() || 'U';
    }

    function setEmptyMessage(container, message) {
      container.innerHTML = `<div class="empty-list-message">${escapeHtml(message)}</div>`;
    }

    function toggleDevOptions() {
      const drawer = document.getElementById('devDrawer');
      drawer.classList.toggle('open');
      document.getElementById('devToggleText').setAttribute('aria-expanded', drawer.classList.contains('open'));
    }

    function loadSample(url) {
      document.getElementById('targetUrl').value = url;
      const apiKey = document.getElementById('clientApiKey').value.trim();
      if (apiKey) {
        handleLookup();
      }
    }

    function switchTab(tabId, btn) {
      document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      const pane = document.getElementById('pane-' + tabId);
      if (pane) pane.classList.add('active');
    }

    function copyResponseJson() {
      if (!rawResponseData) return;
      navigator.clipboard.writeText(JSON.stringify(rawResponseData, null, 2)).then(() => {
        const btn = document.getElementById('copyJsonBtn');
        btn.innerText = '✓ Copied!';
        setTimeout(() => { btn.innerText = 'Copy JSON'; }, 2000);
      });
    }

    async function handleLookup() {
      const url = document.getElementById('targetUrl').value.trim();
      const apiKey = document.getElementById('clientApiKey').value.trim();
      const bypassCache = document.getElementById('bypassCacheOption').checked;

      const submitBtn = document.getElementById('submitBtn');
      const btnLabel = document.getElementById('btnLabel');
      const spinner = document.getElementById('loadingSpinner');
      const errorBanner = document.getElementById('errorBanner');
      const emptyState = document.getElementById('emptyState');
      const resultsContainer = document.getElementById('resultsContainer');

      errorBanner.style.display = 'none';

      if (!apiKey) {
        document.getElementById('errorTitle').innerText = 'ProfileForge API Key Required';
        document.getElementById('errorMessage').innerText = 'Please enter your ProfileForge API Key to authenticate your request.';
        errorBanner.style.display = 'block';
        return;
      }

      submitBtn.disabled = true;
      spinner.style.display = 'inline-block';
      btnLabel.innerText = 'Fetching profile...';

      const startTime = performance.now();

      try {
        const response = await fetch('/v1/profile', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': apiKey
          },
          body: JSON.stringify({ url: url, bypass_cache: bypassCache })
        });

        const elapsedMs = Math.round(performance.now() - startTime);
      const data = await response.json().catch(() => ({}));
        rawResponseData = data;

        if (!response.ok) {
          const errCode = data.error?.code || 'ERROR';
          const errMsg = data.error?.message || 'Profile lookup failed. Please verify the URL and credentials.';
          if (response.status === 401) {
            document.getElementById('errorTitle').innerText = 'Authentication Failed (401 Unauthorized)';
            document.getElementById('errorMessage').innerText = 'The supplied ProfileForge API key was rejected. Please verify your X-API-Key credentials.';
          } else {
            document.getElementById('errorTitle').innerText = `Error (${response.status} ${errCode})`;
            document.getElementById('errorMessage').innerText = errMsg;
          }
          errorBanner.style.display = 'block';
          return;
        }

        renderResult(data, elapsedMs);
        emptyState.style.display = 'none';
        resultsContainer.style.display = 'flex';

      } catch (err) {
        document.getElementById('errorTitle').innerText = 'Network Connection Failed';
        document.getElementById('errorMessage').innerText = err.message || 'Unable to connect to the ProfileForge backend.';
        errorBanner.style.display = 'block';
      } finally {
        submitBtn.disabled = false;
        spinner.style.display = 'none';
        btnLabel.innerText = 'Fetch Profile';
      }
    }

    function renderResult(data, latencyMs) {
      const p = data.profile || {};
      const dq = data.data_quality || {};

      // Profile Identity
      document.getElementById('resFullName').innerText = p.full_name || 'Unnamed Profile';
      document.getElementById('resHeadline').innerText = p.headline || 'No headline specified';
      document.getElementById('resLocation').innerText = p.location || (p.country_code ? `Country: ${p.country_code}` : 'Location unlisted');

      const linkElem = document.getElementById('resCanonicalLink');
      if (p.canonical_url || p.profile_url) {
        linkElem.href = p.canonical_url || p.profile_url;
        linkElem.style.display = 'inline';
      } else {
        linkElem.style.display = 'none';
      }

      // Avatar
      const avatarElem = document.getElementById('resAvatar');
      avatarElem.replaceChildren();
      const fallbackInitials = initialsFor(p.full_name);
      const imageUrl = safeHttpUrl(p.profile_image_url);
      if (imageUrl) {
        const image = document.createElement('img');
        image.src = imageUrl;
        image.alt = p.full_name || 'Profile photo';
        image.referrerPolicy = 'no-referrer';
        image.addEventListener('error', () => { avatarElem.textContent = fallbackInitials; }, { once: true });
        avatarElem.appendChild(image);
      } else {
        avatarElem.textContent = fallbackInitials;
      }

      // Metrics
      document.getElementById('resLatency').innerText = `${latencyMs} ms`;

      const cacheBadge = document.getElementById('resCacheBadge');
      if (data.cache_hit) {
        cacheBadge.innerText = '✓ Cache hit';
        cacheBadge.className = 'metric-badge hit';
      } else {
        cacheBadge.innerText = '↗ Fresh lookup';
        cacheBadge.className = 'metric-badge miss';
      }

      const scorePercent = Math.round((dq.completeness_score || 0) * 100);
      document.getElementById('resCompleteness').innerText = `${scorePercent}%`;
      document.getElementById('resFollowers').innerText = p.followers_count ? p.followers_count.toLocaleString() : '—';

      // Overview Tab
      const aboutBox = document.getElementById('aboutSection');
      if (p.about) {
        document.getElementById('resAbout').innerText = p.about;
        aboutBox.style.display = 'block';
      } else {
        aboutBox.style.display = 'none';
      }

      document.getElementById('resDqBar').style.width = `${scorePercent}%`;
      const availCount = (dq.available_sections || []).length;
      document.getElementById('resDqSummary').innerText = `${availCount} Available Sections (${scorePercent}%)`;
      document.getElementById('resSectionsBreakdown').innerText = `Available: ${(dq.available_sections || []).join(', ') || 'None'}`;

      // Experience Tab
      const expList = document.getElementById('resExperienceList');
      if (p.experience && p.experience.length > 0) {
        expList.innerHTML = p.experience.map(e => `
          <div class="timeline-item">
            <div class="item-header">
              <span class="item-title">${escapeHtml(e.title)}</span>
              <span class="item-date">${escapeHtml(e.start_date || '')} — ${escapeHtml(e.end_date || 'Present')}</span>
            </div>
            <div class="item-subtitle">${escapeHtml(e.company)} ${e.location_type ? '&bull; ' + escapeHtml(e.location_type) : ''} ${e.location ? '&bull; ' + escapeHtml(e.location) : ''}</div>
            ${e.description ? `<div class="item-desc">${escapeHtml(e.description)}</div>` : ''}
          </div>
        `).join('');
      } else {
        setEmptyMessage(expList, 'No experience entries listed.');
      }

      // Education Tab
      const eduList = document.getElementById('resEducationList');
      if (p.education && p.education.length > 0) {
        eduList.innerHTML = p.education.map(ed => `
          <div class="timeline-item">
            <div class="item-header">
              <span class="item-title">${escapeHtml(ed.school)}</span>
              <span class="item-date">${escapeHtml(ed.start_date || '')} — ${escapeHtml(ed.end_date || '')}</span>
            </div>
            <div class="item-subtitle">${escapeHtml(ed.degree || '')} ${ed.field_of_study ? 'in ' + escapeHtml(ed.field_of_study) : ''}</div>
            ${ed.details ? `<div class="item-desc">${escapeHtml(ed.details)}</div>` : ''}
          </div>
        `).join('');
      } else {
        setEmptyMessage(eduList, 'No education entries listed.');
      }

      // Skills Tab
      const skillsList = document.getElementById('resSkillsList');
      if (p.skills && p.skills.length > 0) {
        skillsList.innerHTML = p.skills.map(s => `<span class="badge-tag blue">${escapeHtml(s)}</span>`).join('');
      } else {
        setEmptyMessage(skillsList, 'No skills listed.');
      }

      // Languages & Certs Tab
      const langList = document.getElementById('resLanguagesList');
      if (p.languages && p.languages.length > 0) {
        langList.innerHTML = p.languages.map(l => `<span class="badge-tag green">${escapeHtml(l.name)} ${l.proficiency ? '(' + escapeHtml(l.proficiency) + ')' : ''}</span>`).join('');
      } else {
        setEmptyMessage(langList, 'No languages listed.');
      }

      const certList = document.getElementById('resCertificationsList');
      if (p.certifications && p.certifications.length > 0) {
        certList.innerHTML = p.certifications.map(c => `
          <div class="timeline-item">
            <div class="item-header">
              <span class="item-title">${escapeHtml(c.name)}</span>
              <span class="item-date">${escapeHtml(c.issue_date || '')}</span>
            </div>
            <div class="item-subtitle">${escapeHtml(c.issuing_organization)} ${c.credential_id ? '&bull; ID: ' + escapeHtml(c.credential_id) : ''}</div>
          </div>
        `).join('');
      } else {
        setEmptyMessage(certList, 'No certifications listed.');
      }

      // Raw JSON Tab
      document.getElementById('jsonMetaDetails').innerText = `Source: ${data.source || 'linkedin'} · Request ID: ${data.request_id || '—'}`;
      document.getElementById('resRawJson').innerText = JSON.stringify(data, null, 2);
    }
  </script>
</body>
</html>
"""
