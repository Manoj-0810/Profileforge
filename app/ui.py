"""Web UI playground for interactive LinkedIn profile lookup and testing."""

HTML_PLAYGROUND = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ProfileForge — Live Profile Lookup Playground</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #111827;
      --card-border: #1f2937;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --text: #f9fafb;
      --text-muted: #9ca3af;
      --mono-font: 'JetBrains Mono', monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', -apple-system, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: #111827;
      border-bottom: 1px solid var(--card-border);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .logo {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-size: 1.25rem;
      font-weight: 700;
      color: #60a5fa;
    }
    .logo svg { width: 28px; height: 28px; fill: #3b82f6; }
    .header-links a {
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.875rem;
      margin-left: 1.5rem;
      transition: color 0.2s;
    }
    .header-links a:hover { color: #fff; }
    main {
      flex: 1;
      max-width: 1200px;
      width: 100%;
      margin: 2rem auto;
      padding: 0 1.5rem;
    }
    .hero {
      text-align: center;
      margin-bottom: 2rem;
    }
    .hero h1 { font-size: 2.25rem; font-weight: 700; margin-bottom: 0.5rem; }
    .hero p { color: var(--text-muted); font-size: 1.05rem; }
    .search-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
      margin-bottom: 2rem;
    }
    .input-row {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }
    .input-group {
      flex: 1;
      position: relative;
    }
    input[type="text"] {
      width: 100%;
      background: #1f2937;
      border: 1px solid #374151;
      color: #fff;
      padding: 0.875rem 1rem;
      border-radius: 8px;
      font-size: 1rem;
      outline: none;
      transition: border-color 0.2s;
    }
    input[type="text"]:focus {
      border-color: var(--primary);
    }
    .api-key-input {
      max-width: 250px;
    }
    button.btn-primary {
      background: var(--primary);
      color: #fff;
      border: none;
      padding: 0.875rem 1.75rem;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      transition: background 0.2s, transform 0.1s;
    }
    button.btn-primary:hover { background: var(--primary-hover); }
    button.btn-primary:active { transform: scale(0.98); }
    .sample-pills {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .pill {
      background: #1f2937;
      border: 1px solid #374151;
      color: #93c5fd;
      padding: 0.35rem 0.75rem;
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .pill:hover {
      background: #2563eb;
      color: #fff;
      border-color: #3b82f6;
    }
    .pill.warn { color: #fcd34d; }
    .pill.warn:hover { background: #d97706; color: #fff; }
    .results-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 900px) {
      .results-grid { grid-template-columns: 1fr; }
      .input-row { flex-direction: column; }
      .api-key-input { max-width: 100%; }
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--card-border);
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .profile-hero {
      display: flex;
      gap: 1rem;
      align-items: center;
      margin-bottom: 1.5rem;
    }
    .avatar {
      width: 72px;
      height: 72px;
      border-radius: 50%;
      background: #1e3a8a;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.75rem;
      font-weight: 700;
      color: #bfdbfe;
      border: 2px solid #3b82f6;
      object-fit: cover;
    }
    .profile-meta h2 { font-size: 1.35rem; font-weight: 700; }
    .profile-meta .headline { color: #93c5fd; font-size: 0.95rem; margin-top: 0.2rem; }
    .profile-meta .location { color: var(--text-muted); font-size: 0.85rem; margin-top: 0.2rem; }
    .metrics-bar {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.75rem;
      background: #1f2937;
      padding: 0.75rem;
      border-radius: 8px;
      margin-bottom: 1.5rem;
      text-align: center;
    }
    .metric-val { font-size: 1.1rem; font-weight: 700; color: #60a5fa; }
    .metric-lbl { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
    .section-title {
      font-size: 0.95rem;
      font-weight: 600;
      color: #d1d5db;
      margin: 1.25rem 0 0.75rem 0;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
    .timeline-item {
      padding: 0.75rem;
      background: #1f2937;
      border-radius: 8px;
      margin-bottom: 0.5rem;
      border-left: 3px solid #3b82f6;
    }
    .timeline-title { font-weight: 600; font-size: 0.95rem; }
    .timeline-sub { color: #93c5fd; font-size: 0.85rem; margin: 0.15rem 0; }
    .timeline-desc { color: var(--text-muted); font-size: 0.8rem; margin-top: 0.35rem; line-height: 1.4; }
    .badge-list { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .badge {
      background: #1f2937;
      color: #e5e7eb;
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
      font-size: 0.8rem;
      border: 1px solid #374151;
    }
    .badge.success { background: #064e3b; color: #6ee7b7; border-color: #047857; }
    .badge.warn { background: #78350f; color: #fde68a; border-color: #b45309; }
    pre.json-view {
      background: #030712;
      color: #34d399;
      font-family: var(--mono-font);
      font-size: 0.82rem;
      padding: 1rem;
      border-radius: 8px;
      overflow-x: auto;
      height: 520px;
      line-height: 1.45;
      border: 1px solid #1f2937;
    }
    .progress-track {
      background: #374151;
      height: 8px;
      border-radius: 4px;
      overflow: hidden;
      margin-top: 0.5rem;
    }
    .progress-fill {
      background: var(--accent);
      height: 100%;
      transition: width 0.4s ease;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.25rem 0.6rem;
      border-radius: 12px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .status-badge.hit { background: #064e3b; color: #6ee7b7; }
    .status-badge.miss { background: #1e3a8a; color: #93c5fd; }
    .error-box {
      background: #450a0a;
      border: 1px solid #991b1b;
      color: #fca5a5;
      padding: 1rem;
      border-radius: 8px;
      margin-top: 1rem;
      font-size: 0.9rem;
      display: none;
    }
    .spinner {
      display: none;
      width: 18px;
      height: 18px;
      border: 2px solid rgba(255,255,255,0.3);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <header>
    <div class="logo">
      <svg viewBox="0 0 24 24"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/></svg>
      ProfileForge Playground
    </div>
    <div class="header-links">
      <a href="/docs" target="_blank">Swagger OpenAPI Docs</a>
      <a href="/redoc" target="_blank">Redoc</a>
      <a href="/healthz" target="_blank">Health Check (/healthz)</a>
      <a href="/readyz" target="_blank">Readiness (/readyz)</a>
    </div>
  </header>

  <main>
    <div class="hero">
      <h1>LinkedIn Profile Lookup API</h1>
      <p>Paste any LinkedIn profile URL below or click a sample to see real-time parsing, caching, and data quality scoring.</p>
    </div>

    <div class="search-card">
      <div class="input-row">
        <div class="input-group">
          <input type="text" id="urlInput" placeholder="https://www.linkedin.com/in/username" value="https://www.linkedin.com/in/sarah-jenkins-dev">
        </div>
        <input type="text" id="apiKeyInput" class="api-key-input" placeholder="X-API-Key" value="test-api-key-123" title="API Key Header">
        <button class="btn-primary" id="fetchBtn" onclick="fetchProfile()">
          <span class="spinner" id="btnSpinner"></span>
          <span id="btnText">Fetch Profile</span>
        </button>
      </div>

      <div class="sample-pills">
        <span>Quick Samples:</span>
        <span class="pill" onclick="setSample('https://www.linkedin.com/in/sarah-jenkins-dev')">Sarah Jenkins (100% Complete)</span>
        <span class="pill" onclick="setSample('https://www.linkedin.com/in/alex-mercer')">Alex Mercer (Partial Profile)</span>
        <span class="pill" onclick="setSample('https://www.linkedin.com/in/dr-aris-thorne')">Dr. Aris Thorne (PhD / Multi-Edu)</span>
        <span class="pill" onclick="setSample('https://www.linkedin.com/in/jean-luc-dubois')">Jean-Luc Dubois (Polyglot)</span>
        <span class="pill" onclick="setSample('https://www.linkedin.com/in/kenta-tanaka')">田中 健太 (Unicode / CJK)</span>
        <span class="pill warn" onclick="setSample('https://www.linkedin.com/in/not-found-user')">Not Found Simulation (404)</span>
        <span class="pill warn" onclick="setSample('http://127.0.0.1/in/admin')">SSRF Block Test (400)</span>
      </div>

      <div class="error-box" id="errorBox"></div>
    </div>

    <div class="results-grid" id="resultsGrid">
      <!-- Formatted Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Normalized Profile View</div>
          <div id="cacheBadge" class="status-badge miss">Cache MISS</div>
        </div>

        <div class="profile-hero">
          <div class="avatar" id="avatarBox">SJ</div>
          <div class="profile-meta">
            <h2 id="fullName">Sarah Jenkins</h2>
            <div class="headline" id="headline">Staff Distributed Systems Engineer @ CloudScale</div>
            <div class="location" id="location">Seattle, Washington, United States</div>
          </div>
        </div>

        <div class="metrics-bar">
          <div>
            <div class="metric-val" id="metricLatency">1.8 ms</div>
            <div class="metric-lbl">Response Time</div>
          </div>
          <div>
            <div class="metric-val" id="metricQuality">100%</div>
            <div class="metric-lbl">Completeness</div>
          </div>
          <div>
            <div class="metric-val" id="metricFollowers">4,510</div>
            <div class="metric-lbl">Followers</div>
          </div>
        </div>

        <div class="section-title">Data Quality Assessment</div>
        <div style="font-size: 0.85rem; display:flex; justify-content:space-between;">
          <span id="dqScoreLabel">Score: 1.0 (7 of 7 sections present)</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="dqProgressBar" style="width: 100%;"></div>
        </div>

        <div class="section-title">Work Experience</div>
        <div id="experienceList">
          <div class="timeline-item">
            <div class="timeline-title">Staff Distributed Systems Engineer</div>
            <div class="timeline-sub">CloudScale Inc. &bull; Hybrid</div>
            <div class="timeline-desc">Architecting multi-region streaming pipelines handling 5M events/sec.</div>
          </div>
        </div>

        <div class="section-title">Education</div>
        <div id="educationList">
          <div class="timeline-item">
            <div class="timeline-title">University of Washington</div>
            <div class="timeline-sub">Master of Science in Computer Science & Engineering</div>
          </div>
        </div>

        <div class="section-title">Skills</div>
        <div class="badge-list" id="skillsList">
          <span class="badge">Distributed Systems</span>
          <span class="badge">Python</span>
          <span class="badge">Go</span>
          <span class="badge">Kubernetes</span>
        </div>

        <div class="section-title">Languages</div>
        <div class="badge-list" id="languagesList">
          <span class="badge">English (Native)</span>
          <span class="badge">German (Professional)</span>
        </div>
      </div>

      <!-- Raw JSON Viewer -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Structured API Response JSON</div>
          <button style="background:#374151; color:#fff; border:none; padding:0.3rem 0.6rem; border-radius:6px; font-size:0.75rem; cursor:pointer;" onclick="copyJson()">Copy JSON</button>
        </div>
        <pre class="json-view" id="rawJson">{
  "status": "Ready to query. Click 'Fetch Profile' or select a sample above."
}</pre>
      </div>
    </div>
  </main>

  <script>
    function setSample(url) {
      document.getElementById('urlInput').value = url;
      fetchProfile();
    }

    function copyJson() {
      const jsonText = document.getElementById('rawJson').innerText;
      navigator.clipboard.writeText(jsonText);
      alert('JSON copied to clipboard!');
    }

    async function fetchProfile() {
      const url = document.getElementById('urlInput').value.trim();
      const apiKey = document.getElementById('apiKeyInput').value.trim();
      const errorBox = document.getElementById('errorBox');
      const btnSpinner = document.getElementById('btnSpinner');
      const btnText = document.getElementById('btnText');
      const fetchBtn = document.getElementById('fetchBtn');

      errorBox.style.display = 'none';
      btnSpinner.style.display = 'inline-block';
      btnText.innerText = 'Fetching...';
      fetchBtn.disabled = true;

      const startTime = performance.now();

      try {
        const response = await fetch('/v1/profile', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': apiKey
          },
          body: JSON.stringify({ url: url })
        });

        const elapsedMs = Math.round(performance.now() - startTime);
        const data = await response.json();

        document.getElementById('rawJson').innerText = JSON.stringify(data, null, 2);

        if (!response.ok) {
          const errCode = data.error?.code || 'ERROR';
          const errMsg = data.error?.message || 'Failed to fetch profile';
          errorBox.innerText = `[${response.status} ${errCode}] ${errMsg}`;
          errorBox.style.display = 'block';
          return;
        }

        renderProfile(data, elapsedMs);

      } catch (err) {
        errorBox.innerText = `Network/Client Error: ${err.message}`;
        errorBox.style.display = 'block';
      } finally {
        btnSpinner.style.display = 'none';
        btnText.innerText = 'Fetch Profile';
        fetchBtn.disabled = false;
      }
    }

    function renderProfile(data, latencyMs) {
      const p = data.profile;
      const dq = data.data_quality;

      document.getElementById('fullName').innerText = p.full_name || 'N/A';
      document.getElementById('headline').innerText = p.headline || 'No headline available';
      document.getElementById('location').innerText = p.location || (p.country_code ? `Country: ${p.country_code}` : 'Location unlisted');
      document.getElementById('metricLatency').innerText = `${latencyMs} ms`;
      document.getElementById('metricQuality').innerText = `${Math.round(dq.completeness_score * 100)}%`;
      document.getElementById('metricFollowers').innerText = p.followers_count ? p.followers_count.toLocaleString() : '0';

      const cacheBadge = document.getElementById('cacheBadge');
      if (data.cache_hit) {
        cacheBadge.innerText = 'Cache HIT';
        cacheBadge.className = 'status-badge hit';
      } else {
        cacheBadge.innerText = 'Cache MISS';
        cacheBadge.className = 'status-badge miss';
      }

      // Avatar
      const avatarBox = document.getElementById('avatarBox');
      if (p.profile_image_url) {
        avatarBox.innerHTML = `<img src="${p.profile_image_url}" class="avatar" style="border:none;" onerror="this.outerHTML='${(p.full_name[0] || 'U')}'">`;
      } else {
        avatarBox.innerText = (p.full_name || 'U').split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase();
      }

      // Data Quality Progress
      const percent = Math.round(dq.completeness_score * 100);
      document.getElementById('dqProgressBar').style.width = `${percent}%`;
      document.getElementById('dqScoreLabel').innerText = `Score: ${dq.completeness_score} (${dq.available_sections.length} available, ${dq.missing_sections.length} missing)`;

      // Experiences
      const expContainer = document.getElementById('experienceList');
      if (p.experience && p.experience.length > 0) {
        expContainer.innerHTML = p.experience.map(e => `
          <div class="timeline-item">
            <div class="timeline-title">${e.title}</div>
            <div class="timeline-sub">${e.company} ${e.location_type ? '&bull; ' + e.location_type : ''} ${e.location ? '&bull; ' + e.location : ''}</div>
            ${e.description ? `<div class="timeline-desc">${e.description}</div>` : ''}
          </div>
        `).join('');
      } else {
        expContainer.innerHTML = '<div style="color:#6b7280; font-size:0.85rem;">No experience entries listed.</div>';
      }

      // Education
      const eduContainer = document.getElementById('educationList');
      if (p.education && p.education.length > 0) {
        eduContainer.innerHTML = p.education.map(ed => `
          <div class="timeline-item">
            <div class="timeline-title">${ed.school}</div>
            <div class="timeline-sub">${ed.degree || ''} ${ed.field_of_study ? 'in ' + ed.field_of_study : ''} ${ed.details && !ed.degree ? ed.details : ''}</div>
          </div>
        `).join('');
      } else {
        eduContainer.innerHTML = '<div style="color:#6b7280; font-size:0.85rem;">No education records listed.</div>';
      }

      // Skills
      const skillsContainer = document.getElementById('skillsList');
      if (p.skills && p.skills.length > 0) {
        skillsContainer.innerHTML = p.skills.map(s => `<span class="badge">${s}</span>`).join('');
      } else {
        skillsContainer.innerHTML = '<div style="color:#6b7280; font-size:0.85rem;">No skills listed.</div>';
      }

      // Languages
      const langContainer = document.getElementById('languagesList');
      if (p.languages && p.languages.length > 0) {
        langContainer.innerHTML = p.languages.map(l => `<span class="badge success">${l.name} ${l.proficiency ? '(' + l.proficiency + ')' : ''}</span>`).join('');
      } else {
        langContainer.innerHTML = '<div style="color:#6b7280; font-size:0.85rem;">No language records listed.</div>';
      }
    }

    // Auto-fetch on page load
    window.addEventListener('DOMContentLoaded', fetchProfile);
  </script>
</body>
</html>
"""
