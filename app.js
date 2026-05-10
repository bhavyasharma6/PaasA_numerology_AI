/**
 * app.js - PaasA Numerology AI Frontend Logic
 * Author: Bhavya Sharma | Enrollment: 2450850380 | MCSP-232
 *
 * Handles:
 *   - Form validation and submission (input page)
 *   - Dashboard rendering (Lo Shu Grid, Numbers, Chat tabs)
 *   - API communication via Fetch API
 *   - Session management in JavaScript variables
 *   - Real-time chat interface
 */

'use strict';

// ─────────────────────────────────────────────────────────────────────────────
// Configuration
// ─────────────────────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8000';
const CHAT_COOLDOWN_MS = 1000;   // 1 second between messages
const MAX_CHAT_LENGTH  = 500;    // max chars per message (client)

// ─────────────────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────────────────
let currentSessionId = null;
let numerologyData   = null;
let lastChatTime     = 0;
let isChatWaiting    = false;
let activeTab        = 'grid';

// ─────────────────────────────────────────────────────────────────────────────
// Utility Functions
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Make an API call with error handling.
 * @param {string} endpoint - API path (e.g. '/api/setup')
 * @param {string} method   - HTTP method
 * @param {Object} body     - Request body (for POST)
 * @returns {Promise<Object>} Parsed JSON response
 */
async function apiCall(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) options.body = JSON.stringify(body);

  const response = await fetch(`${API_BASE}${endpoint}`, options);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return data;
}

/**
 * Show/hide the loading overlay.
 * @param {boolean} show  - Whether to show
 * @param {string}  text  - Loading message
 */
function setLoading(show, text = 'Consulting the cosmos...') {
  const overlay = document.getElementById('loadingOverlay');
  const textEl  = document.getElementById('loadingText');
  if (!overlay) return;
  overlay.style.display = show ? 'flex' : 'none';
  if (textEl && text) textEl.textContent = text;
}

/**
 * Display an error toast notification.
 * @param {string} message - Error message
 */
function showError(message) {
  const toast = document.createElement('div');
  toast.className = 'error-toast';
  toast.innerHTML = `<span>⚠</span> ${message}`;
  toast.style.cssText = `
    position:fixed; bottom:2rem; right:2rem; z-index:9999;
    background:rgba(231,76,60,0.9); color:white; padding:1rem 1.5rem;
    border-radius:12px; font-size:0.9rem; animation:slideIn 0.3s ease;
    max-width:350px; backdrop-filter:blur(10px);
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

/**
 * Show a success toast.
 * @param {string} message - Success message
 */
function showSuccess(message) {
  const toast = document.createElement('div');
  toast.className = 'success-toast';
  toast.innerHTML = `<span>✓</span> ${message}`;
  toast.style.cssText = `
    position:fixed; bottom:2rem; right:2rem; z-index:9999;
    background:rgba(46,204,113,0.9); color:white; padding:1rem 1.5rem;
    border-radius:12px; font-size:0.9rem; animation:slideIn 0.3s ease;
    max-width:350px; backdrop-filter:blur(10px);
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ─────────────────────────────────────────────────────────────────────────────
// Input Page Logic
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Validate the user input form.
 * @returns {boolean} True if all fields are valid
 */
function validateForm() {
  const name   = document.getElementById('fullName')?.value?.trim();
  const dob    = document.getElementById('dob')?.value?.trim();
  const gender = document.querySelector('input[name="gender"]:checked')?.value;
  let valid    = true;

  // Clear previous errors
  document.querySelectorAll('.form-error').forEach(el => el.classList.remove('visible'));
  document.querySelectorAll('.form-control').forEach(el => el.classList.remove('error'));

  // Name validation
  if (!name || name.length < 2 || name.length > 100) {
    showFieldError('nameError', 'Name must be 2-100 characters');
    document.getElementById('fullName')?.classList.add('error');
    valid = false;
  } else if (!/^[A-Za-z\s]+$/.test(name)) {
    showFieldError('nameError', 'Name must contain only letters and spaces');
    document.getElementById('fullName')?.classList.add('error');
    valid = false;
  }

  // DOB validation
  const dobPattern = /^\d{2}-\d{2}-\d{4}$/;
  if (!dob || !dobPattern.test(dob)) {
    showFieldError('dobError', 'Date must be in DD-MM-YYYY format');
    document.getElementById('dob')?.classList.add('error');
    valid = false;
  } else {
    const [day, month, year] = dob.split('-').map(Number);
    if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1900 || year > 2025) {
      showFieldError('dobError', 'Please enter a valid date');
      document.getElementById('dob')?.classList.add('error');
      valid = false;
    }
  }

  // Gender validation
  if (!gender) {
    showFieldError('genderError', 'Please select your gender');
    valid = false;
  }

  return valid;
}

function showFieldError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) { el.textContent = message; el.classList.add('visible'); }
}

/**
 * Handle input form submission.
 * Validates, calls API, stores session, redirects to dashboard.
 */
async function submitNumerologyForm(event) {
  event.preventDefault();
  if (!validateForm()) return;

  const name   = document.getElementById('fullName').value.trim();
  const dob    = document.getElementById('dob').value.trim();
  const gender = document.querySelector('input[name="gender"]:checked').value;

  setLoading(true, 'Calculating your cosmic blueprint...');

  try {
    const data = await apiCall('/api/setup', 'POST', {
      full_name: name,
      dob: dob,
      gender: gender,
    });

    // Store session data in sessionStorage
    sessionStorage.setItem('paasaSession', JSON.stringify(data));
    sessionStorage.setItem('paasaSessionId', data.session_id);

    setLoading(false);
    showSuccess('Your cosmic reading is ready!');

    // Redirect to dashboard
    setTimeout(() => { window.location.href = '/dashboard'; }, 800);

  } catch (error) {
    setLoading(false);
    showError(error.message || 'Failed to calculate numerology. Please try again.');
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Dashboard Initialization
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Initialize the dashboard with session data.
 * Loads data from sessionStorage or fetches from API.
 */
async function initDashboard() {
  const storedData = sessionStorage.getItem('paasaSession');
  const storedId   = sessionStorage.getItem('paasaSessionId');

  if (storedData) {
    numerologyData   = JSON.parse(storedData);
    currentSessionId = numerologyData.session_id;
    renderDashboard(numerologyData);
  } else if (storedId) {
    // Fetch from API if not cached
    setLoading(true, 'Loading your reading...');
    try {
      const data = await apiCall(`/api/session/${storedId}`);
      numerologyData   = data;
      currentSessionId = storedId;
      renderDashboard(data);
    } catch (e) {
      showError('Session not found. Please start a new reading.');
      setTimeout(() => { window.location.href = '/input'; }, 2000);
    } finally {
      setLoading(false);
    }
  } else {
    window.location.href = '/input';
  }
}

/**
 * Render the full dashboard with all tab content.
 * @param {Object} data - Complete numerology session data
 */
function renderDashboard(data) {
  const greetingEl = document.getElementById('userGreeting');
  if (greetingEl) {
    const firstName = data.user_name.split(' ')[0];
    greetingEl.innerHTML =
      `✦ ${firstName}'s Cosmic Blueprint<span>${data.dob} &nbsp;·&nbsp; ${data.gender}</span>`;
  }
  renderLoShuGrid(data.loshu_grid, data.planes);
  renderCoreNumbers(data.numbers, data.insights);
  renderInsights(data.insights, data.planes);
  initChatInterface(data);
  switchTab('grid');
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 1: Lo Shu Grid
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Render the interactive Lo Shu Grid visualization.
 * @param {Object} gridData  - Grid data (grid, present, missing, frequencies)
 * @param {Object} planesData - Plane analysis data
 */
function renderLoShuGrid(gridData, planesData) {
  const { grid, present_numbers, missing_numbers, frequencies } = gridData;

  // Render grid cells
  const gridEl = document.getElementById('loshuGrid');
  if (gridEl) {
    gridEl.innerHTML = grid.flat().map(num => {
      const isPresent = num > 0 && present_numbers.includes(num);
      const freq = num > 0 ? (frequencies[num] || 0) : 0;
      return `<div class="grid-cell ${isPresent ? 'present' : 'missing'}"
                   title="${num > 0 ? 'Number ' + num + ' × ' + freq : 'Missing'}">
                <span class="number">${num > 0 ? num : '·'}</span>
                ${freq > 1 ? `<span class="freq-badge">×${freq}</span>` : ''}
              </div>`;
    }).join('');
  }

  // Present / missing tags
  const tagsEl = document.getElementById('numTags');
  if (tagsEl) {
    const presentTags = present_numbers.map(n =>
      `<span class="num-tag present">${n}</span>`).join('');
    const missingTags = missing_numbers.map(n =>
      `<span class="num-tag missing">${n}</span>`).join('');
    tagsEl.innerHTML =
      `<span style="font-size:0.7rem;color:var(--color-text-muted);align-self:center;">Present:</span>${presentTags}
       <span style="font-size:0.7rem;color:var(--color-text-muted);align-self:center;margin-left:0.5rem;">Missing:</span>${missingTags}`;
  }

  // Planes
  const planesEl = document.getElementById('planesGrid');
  if (planesEl) {
    planesEl.innerHTML = Object.entries(planesData)
      .filter(([k]) => k !== 'strongest_plane')
      .map(([name, info]) =>
        `<div class="plane-badge ${info.status?.toLowerCase()}">
           <span class="plane-name">${name.charAt(0).toUpperCase()+name.slice(1)}</span>
           <span class="plane-status">${info.status}</span>
         </div>`
      ).join('');
  }

  // Strongest plane
  const strongEl = document.getElementById('strongestPlane');
  if (strongEl && planesData.strongest_plane) {
    const sp = planesData.strongest_plane;
    const info = planesData[sp];
    strongEl.innerHTML =
      `${sp.charAt(0).toUpperCase()+sp.slice(1)} Plane
       <div style="font-family:var(--font-body);font-size:0.8rem;color:var(--color-text-muted);margin-top:4px;">
         ${info?.meaning || ''}
       </div>`;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 2: Core Numbers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Render the four core number cards.
 */
function renderCoreNumbers(numbers, insights) {
  const gridEl = document.getElementById('numbersGrid');
  if (!gridEl) return;

  const cards = [
    { key:'name_number', icon:'✦', label:'NAME NUMBER', name:'Chaldean Expression', theme:'gold',   desc:'Vibrational energy of your name in the ancient Chaldean system' },
    { key:'mulank',      icon:'🌙', label:'MULANK',      name:'Driver / Birth Number', theme:'purple', desc:'Core personality, natural instincts, and birth energy' },
    { key:'bhagyank',    icon:'⭐', label:'BHAGYANK',    name:'Life Path Number',      theme:'cyan',   desc:'Your destiny, life purpose, and the path your soul chose' },
    { key:'kua_number',  icon:'☯',  label:'KUA NUMBER',  name:'Feng Shui Personal',   theme:'pink',   desc:'Auspicious directions and elemental energy alignment' },
  ];

  const colors = { gold:'#ffd700', purple:'#9b59b6', cyan:'#00e5ff', pink:'#e91e8c' };

  gridEl.innerHTML = cards.map(c => {
    const col = colors[c.theme];
    return `<div class="number-card ${c.theme}">
              <div class="card-icon">${c.icon}</div>
              <div class="card-label" style="color:${col}">${c.label}</div>
              <div class="card-name">${c.name}</div>
              <div class="card-number" style="color:${col};text-shadow:0 0 24px ${col}55">
                ${numbers[c.key] ?? '?'}
              </div>
              <div class="card-desc">${c.desc}</div>
            </div>`;
  }).join('');
}

// ─────────────────────────────────────────────────────────────────────────────
// Insights Panel
// ─────────────────────────────────────────────────────────────────────────────

function renderInsights(insights, planes) {
  if (!insights) return;
  const el = document.getElementById('insightsPanel');
  if (!el) return;

  el.innerHTML = `
    <div class="insights-title">🔮 AI Cosmic Insights</div>

    <div class="insight-item" style="margin-bottom:1rem;">
      <div class="insight-label">✦ Personality Snapshot</div>
      <div class="insight-text" style="font-size:0.95rem; color:var(--color-text-primary);">
        ${insights.personality_snapshot || ''}
      </div>
    </div>

    <div class="insight-row">
      <div class="insight-item">
        <div class="insight-label" style="color:#2ed573;">💪 Key Strength</div>
        <div class="insight-text">${insights.key_strength || ''}</div>
      </div>
      <div class="insight-item purple">
        <div class="insight-label" style="color:#a29bfe;">⚡ Key Challenge</div>
        <div class="insight-text">${insights.key_challenge || ''}</div>
      </div>
      <div class="insight-item cyan">
        <div class="insight-label" style="color:#00e5ff;">🌟 Strongest Plane</div>
        <div class="insight-text">${insights.strongest_plane_meaning || insights.strongest_plane || ''}</div>
      </div>
      <div class="insight-item pink">
        <div class="insight-label" style="color:#fd79a8;">🔮 Remedy</div>
        <div class="insight-text">${insights.remedy_suggestion || ''}</div>
      </div>
    </div>

    ${insights.message ? `
      <div class="affirmation-box">"${insights.message}"</div>
    ` : ''}`;
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 3: AI Chat Interface
// ─────────────────────────────────────────────────────────────────────────────

function initChatInterface(data) {
  const chatHistory = data.chat_history || [];
  const messagesEl  = document.getElementById('chatMessages');
  if (!messagesEl) return;

  // Show existing history
  if (chatHistory.length === 0) {
    addChatBubble(
      'assistant',
      `Namaste! I am PaasA, your AI numerologist. I have your complete cosmic blueprint. ` +
      `Ask me anything about your destiny, relationships, career, or what your numbers reveal. ✨`
    );
  } else {
    chatHistory.forEach(msg => addChatBubble(msg.role, msg.message));
  }

  // Attach submit listener
  const input   = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');

  if (sendBtn) sendBtn.addEventListener('click', sendChatMessage);
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
    });
    input.addEventListener('input', () => {
      sendBtn.disabled = input.value.trim().length === 0 || isChatWaiting;
    });
  }
}

function addChatBubble(role, message) {
  const messagesEl = document.getElementById('chatMessages');
  if (!messagesEl) return;

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;

  if (role === 'assistant') {
    bubble.innerHTML = `<div class="bubble-header">✦ PaasA Numerologist</div>${message}`;
  } else {
    bubble.textContent = message;
  }

  messagesEl.appendChild(bubble);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTypingIndicator() {
  const messagesEl = document.getElementById('chatMessages');
  if (!messagesEl) return;
  const indicator = document.createElement('div');
  indicator.className = 'chat-bubble assistant';
  indicator.id = 'typingIndicator';
  indicator.innerHTML = `
    <div class="bubble-header">✦ PaasA Oracle</div>
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
  messagesEl.appendChild(indicator);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function removeTypingIndicator() {
  document.getElementById('typingIndicator')?.remove();
}

async function sendChatMessage() {
  const input   = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  if (!input || !currentSessionId) return;

  const message = input.value.trim();
  if (!message || message.length > MAX_CHAT_LENGTH) return;

  // Cooldown check
  const now = Date.now();
  if (now - lastChatTime < CHAT_COOLDOWN_MS) return;
  lastChatTime = now;

  // UI updates
  input.value   = '';
  isChatWaiting = true;
  if (sendBtn) sendBtn.disabled = true;

  addChatBubble('user', message);
  showTypingIndicator();

  try {
    const response = await apiCall('/api/chat', 'POST', {
      session_id: currentSessionId,
      message: message,
    });

    removeTypingIndicator();
    addChatBubble('assistant', response.response);

  } catch (error) {
    removeTypingIndicator();
    addChatBubble('assistant',
      'The cosmic oracle is momentarily unavailable. Please try again. 🌙'
    );
    showError(error.message || 'Chat error occurred');
  } finally {
    isChatWaiting = false;
    if (sendBtn) sendBtn.disabled = false;
    input.focus();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab Navigation
// ─────────────────────────────────────────────────────────────────────────────

function switchTab(tabName) {
  activeTab = tabName;
  document.querySelectorAll('.tab-btn').forEach(btn =>
    btn.classList.toggle('active', btn.dataset.tab === tabName));
  document.querySelectorAll('.tab-content').forEach(panel =>
    panel.classList.toggle('active', panel.id === `tab-${tabName}`));
}

// ─────────────────────────────────────────────────────────────────────────────
// History Page
// ─────────────────────────────────────────────────────────────────────────────

async function loadHistory(query = '') {
  const container = document.getElementById('sessionsList');
  if (!container) return;

  container.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><p>Loading...</p></div>';

  try {
    const url = query ? `/api/history?name=${encodeURIComponent(query)}` : '/api/history';
    const data = await apiCall(url);

    if (!data.sessions || data.sessions.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🌌</div>
          <p>No readings found. <a href="/input" style="color:var(--color-accent-gold);">Start your first reading →</a></p>
        </div>`;
      return;
    }

    container.innerHTML = data.sessions.map(s => `
      <div class="session-card">
        <div>
          <div class="session-name">${escapeHtml(s.full_name)}</div>
          <div class="session-meta">
            DOB: ${s.dob} &nbsp;|&nbsp; ${s.gender} &nbsp;|&nbsp;
            ${new Date(s.created_at).toLocaleDateString('en-IN', {day:'2-digit', month:'short', year:'numeric'})}
          </div>
        </div>
        <div class="session-actions">
          <button class="btn btn-primary btn-sm" onclick="loadSession('${s.session_id}')">Load ✦</button>
          <button class="btn btn-secondary btn-sm" onclick="deleteSessionCard('${s.session_id}', this)">Delete</button>
        </div>
      </div>
    `).join('');

  } catch (error) {
    container.innerHTML = `<div style="color:#e74c3c; text-align:center; padding:2rem;">Error: ${escapeHtml(error.message)}</div>`;
  }
}

function searchHistory() {
  const query = document.getElementById('searchInput')?.value?.trim() || '';
  clearTimeout(window._searchTimer);
  window._searchTimer = setTimeout(() => loadHistory(query), 350);
}

async function deleteSessionCard(sessionId, btnEl) {
  if (!confirm('Delete this reading permanently?')) return;
  try {
    await apiCall(`/api/session/${sessionId}`, 'DELETE');
    // Remove the card from DOM
    btnEl.closest('.session-card').remove();
    const list = document.getElementById('sessionsList');
    if (list && !list.querySelector('.session-card')) {
      list.innerHTML = '<div class="empty-state"><div class="empty-icon">🌌</div><p>No readings yet.</p></div>';
    }
  } catch (e) {
    showError('Could not delete session: ' + e.message);
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function loadSession(sessionId) {
  setLoading(true, 'Loading reading...');
  try {
    const data = await apiCall(`/api/session/${sessionId}`);
    sessionStorage.setItem('paasaSession', JSON.stringify(data));
    sessionStorage.setItem('paasaSessionId', sessionId);
    window.location.href = '/dashboard';
  } catch (e) {
    setLoading(false);
    showError('Could not load session');
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Page Detection & Bootstrap
// ─────────────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  if (path === '/input' || path === '/input.html') {
    // Attach form submission
    const form = document.getElementById('numerologyForm');
    if (form) form.addEventListener('submit', submitNumerologyForm);

  } else if (path === '/dashboard' || path === '/dashboard.html') {
    // Initialize dashboard
    initDashboard();
    // Tab button listeners
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

  } else if (path === '/history' || path === '/history.html') {
    loadHistory();
    const searchInput = document.getElementById('historySearch');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        clearTimeout(window._searchTimer);
        window._searchTimer = setTimeout(() => loadHistory(e.target.value), 400);
      });
    }
  }
});
