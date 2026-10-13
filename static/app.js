// SteamSeparator - Lean & Bilingual Frontend
let currentLang = localStorage.getItem('lang') || 'en';
let currentLevel = 5;
let currentC = 700.0;
let currentStatus = null;
let currentPreview = null;
let scanPollInterval = null;
let debounceTimer = null;
let activeFilter = 'assigned'; // Default: only assigned games!

// 10 Stepped Filter Levels for Unified Quality Gate
const FILTER_LEVELS = [
  { level: 1, c: 150.0, opHint: "180", vpHint: "530", en: "Very Lenient", de: "Sehr locker" },
  { level: 2, c: 250.0, opHint: "300", vpHint: "890", en: "Lenient", de: "Locker" },
  { level: 3, c: 350.0, opHint: "440", vpHint: "1.2k", en: "Light", de: "Leicht" },
  { level: 4, c: 500.0, opHint: "625", vpHint: "1.8k", en: "Moderate", de: "Moderat" },
  { level: 5, c: 700.0, opHint: "875", vpHint: "2.5k", en: "Balanced", de: "Ausgewogen" },
  { level: 6, c: 950.0, opHint: "1.2k", vpHint: "3.4k", en: "Firm", de: "Bestimmt" },
  { level: 7, c: 1300.0, opHint: "1.6k", vpHint: "4.6k", en: "Strict", de: "Streng" },
  { level: 8, c: 1800.0, opHint: "2.2k", vpHint: "6.4k", en: "Very Strict", de: "Sehr streng" },
  { level: 9, c: 2500.0, opHint: "3.1k", vpHint: "8.9k", en: "High Confidence", de: "Hohe Relevanz" },
  { level: 10, c: 3500.0, opHint: "4.4k", vpHint: "12.5k", en: "Bestsellers Only", de: "Nur Bestseller" },
];

// Translations
const i18n = {
  de: {
    title: "SteamSeparator",
    account: "Account:",
    checkingSteam: "Prüfe Steam-Status...",
    steamRunning: "⚠️ Steam läuft (vor Speichern beenden)",
    steamStopped: "✅ Steam beendet (bereit zum Speichern)",
    tuningTitle: "Feinjustierung",
    confidenceLabel: "Review-Filter",
    confidencePopover: "Sortiert Nischen-Spiele mit zu wenigen Reviews aus. Spiele mit 95%+ benötigen weniger Reviews, während mittelmäßig bewertete Spiele (80-85%) deutlich mehr Stimmen brauchen.",
    noTiersSelected: "Mindestens eine Collection auswählen",
    thresholdMinSuffix: "+ Reviews",
    grpLowConf: "Zu wenige Reviews",
    grpUnavailable: "Nicht im Land verfügbar",
    grpDelisted: "Delistet / Nicht mehr im Shop",
    grpNoReviews: "Keine Reviews / Nicht gescannt",
    collectionsLabel: "Collections in Steam erstellen:",
    btnScan: "Bewertungen scannen",
    btnSave: "In Steam anwenden",
    btnSaving: "Speichere...",
    statLowConf: "Ausgeschlossen",
    statTotal: "Spiele in Bibliothek",
    searchPlaceholder: "🔍 Spiel suchen...",
    pillAll: "Alle",
    pillAssigned: "Zugeordnet",
    pillExcluded: "Ausgeschlossen",
    thCover: "Cover",
    thGame: "Spiel",
    thRaw: "Positiv %",
    thScore: "Gewichteter Score",
    thStatus: "Steam-Collection",
    tooltipRaw: "Prozentsatz positiver Bewertungen (Positive / Gesamt)",
    tooltipScore: "Gewichtet die Review-Anzahl: Verhindert Top-Einstufungen bei geringer Stimmenanzahl.",
    loading: "Lade Bibliothek...",
    noGames: "Keine passenden Spiele in dieser Ansicht.",
    scanStarted: "Scan gestartet! Frage Reviews ab...",
    scanDone: "Scan abgeschlossen!",
    saveConfirm: "Möchtest du die Collections jetzt in Steam anwenden?\n\n(Ein automatisches Sicherheits-Backup wird im Hintergrund erstellt).",
    saveSuccess: "Erfolgreich in Steam gespeichert! Du kannst Steam jetzt starten.",
    steamMustClose: "Steam läuft noch! Bitte beende Steam vollständig vor dem Speichern.",
    selectTierError: "Bitte wähle mindestens eine Collection aus.",
    gamesCountLabel: "Spiele",
    scanAllUpToDate: "Alle Spiele sind bereits erfasst (0 neue Spiele).",
    lblForceRefresh: "Voll-Scan erzwingen",
    tooltipForceRefresh: "Ignoriert den lokalen Cache und fragt alle Titel frisch bei Steam ab",
    openInSteam: "Im Steam Shop öffnen",
    refreshGame: "Dieses Spiel einzeln von Steam neu abfragen",
    gameUpdated: "erfolgreich aktualisiert",
    refreshGroup: "Alle Spiele in dieser Gruppe von Steam neu prüfen",
    refreshGroupBtn: "Gruppe prüfen",
    batchScanStarted: "Prüfung im Hintergrund gestartet...",
    noGamesInGroup: "Keine Spiele in dieser Gruppe.",
    scanInProgress: "Ein Scan läuft bereits. Fortschritt wird angezeigt...",
    scanError: "Fehler beim Starten des Scans",
  },
  en: {
    title: "SteamSeparator",
    account: "Account:",
    checkingSteam: "Checking Steam status...",
    steamRunning: "⚠️ Steam is running (exit before saving)",
    steamStopped: "✅ Steam is closed (ready to apply)",
    tuningTitle: "Fine Tuning",
    confidenceLabel: "Review Filter",
    confidencePopover: "Filters out niche games with too few reviews. Masterpieces (95%+) need fewer reviews to qualify, while mid-rated games (80-85%) require significantly more votes.",
    noTiersSelected: "Select at least one collection",
    thresholdMinSuffix: "+ reviews",
    grpLowConf: "Few reviews",
    grpUnavailable: "Not available in country",
    grpDelisted: "Delisted / No longer in store",
    grpNoReviews: "No reviews / Not scanned",
    collectionsLabel: "Collections to create in Steam:",
    btnScan: "Scan Reviews",
    btnSave: "Apply to Steam",
    btnSaving: "Saving...",
    statLowConf: "Excluded",
    statTotal: "Games in Library",
    searchPlaceholder: "🔍 Search game...",
    pillAll: "All",
    pillAssigned: "Assigned",
    pillExcluded: "Excluded",
    thCover: "Cover",
    thGame: "Game",
    thRaw: "Positive %",
    thScore: "Weighted Score",
    thStatus: "Steam Collection",
    tooltipRaw: "Percentage of positive reviews (Positive / Total)",
    tooltipScore: "Weights review count: Prevents top rankings with low vote counts.",
    loading: "Loading library...",
    noGames: "No matching games in this view.",
    scanStarted: "Scan started! Fetching reviews...",
    scanDone: "Scan finished!",
    scanAllUpToDate: "All games are already up to date (0 new games).",
    saveConfirm: "Apply collections to Steam now?\n\n(An automatic backup will be created in the background).",
    saveSuccess: "Successfully saved to Steam! You can start Steam now.",
    steamMustClose: "Steam is currently running! Please completely close Steam before saving.",
    selectTierError: "Please select at least one collection tier.",
    gamesCountLabel: "games",
    lblForceRefresh: "Force full scan",
    tooltipForceRefresh: "Bypasses local cache and re-queries all games freshly from Steam",
    openInSteam: "Open in Steam Store",
    refreshGame: "Re-fetch this single game from Steam",
    gameUpdated: "successfully updated",
    refreshGroup: "Re-check all games in this group from Steam",
    refreshGroupBtn: "Check group",
    batchScanStarted: "Checking games in background...",
    noGamesInGroup: "No games in this group.",
    scanInProgress: "A scan is already in progress. Showing progress...",
    scanError: "Error starting scan",
  }
};

// DOM Elements
const accountSelect = document.getElementById('account-select');
const steamStatusBadge = document.getElementById('steam-status-badge');
const steamStatusText = document.getElementById('steam-status-text');
const tiersCheckboxList = document.getElementById('tiers-checkbox-list');
const btnScan = document.getElementById('btn-scan');
const btnSave = document.getElementById('btn-save');
const searchInput = document.getElementById('search-input');
const gamesTableBody = document.getElementById('games-table-body');
const toastEl = document.getElementById('toast');
const scanProgressCard = document.getElementById('scan-progress-card');
const scanProgressFill = document.getElementById('scan-progress-fill');
const scanPercent = document.getElementById('scan-percent');
const scanMessage = document.getElementById('scan-message');
const statsGrid = document.getElementById('stats-grid');

// Lang Buttons
const btnLangDe = document.getElementById('btn-lang-de');
const btnLangEn = document.getElementById('btn-lang-en');

// Stepped Slider & Dynamic Threshold Rows Elements
const filterLevelSlider = document.getElementById('filter-level-slider');
const filterLevelBadge = document.getElementById('filter-level-badge');
const thresholdCard = document.getElementById('threshold-card') || document.getElementById('threshold-chips-container');



function t(key) {
  return (i18n[currentLang] && i18n[currentLang][key]) || key;
}

function applyLanguage() {
  const elTitle = document.getElementById('i18n-title');
  if (elTitle) elTitle.textContent = t('title');

  const elAccount = document.getElementById('i18n-lbl-account');
  if (elAccount) elAccount.textContent = t('account');

  const elTuningTitle = document.getElementById('i18n-tuning-title');
  if (elTuningTitle) elTuningTitle.textContent = t('tuningTitle');

  const elConfLabel = document.getElementById('i18n-confidence-label');
  if (elConfLabel) elConfLabel.textContent = t('confidenceLabel');

  const elConfPopover = document.getElementById('i18n-confidence-popover-text');
  if (elConfPopover) elConfPopover.textContent = t('confidencePopover');

  const elColLabel = document.getElementById('i18n-collections-label');
  if (elColLabel) elColLabel.textContent = t('collectionsLabel');

  const elBtnScan = document.getElementById('i18n-btn-scan');
  if (elBtnScan) elBtnScan.textContent = t('btnScan');

  const elBtnSave = document.getElementById('i18n-btn-save');
  if (elBtnSave) elBtnSave.textContent = t('btnSave');

  const lblForce = document.getElementById('i18n-lbl-force-refresh');
  if (lblForce) lblForce.textContent = t('lblForceRefresh');

  const toggleForce = document.getElementById('toggle-force-refresh-label');
  if (toggleForce) toggleForce.title = t('tooltipForceRefresh');

  if (searchInput) searchInput.placeholder = t('searchPlaceholder');

  const pillAssigned = document.getElementById('pill-assigned');
  if (pillAssigned) pillAssigned.textContent = t('pillAssigned');

  const pillExcluded = document.getElementById('pill-excluded');
  if (pillExcluded) pillExcluded.textContent = t('pillExcluded');

  const thCover = document.getElementById('th-cover');
  if (thCover) thCover.textContent = t('thCover');

  const thGame = document.getElementById('th-game');
  if (thGame) thGame.textContent = t('thGame');

  const thRaw = document.getElementById('th-raw');
  if (thRaw) {
    thRaw.textContent = t('thRaw');
    thRaw.title = t('tooltipRaw');
  }

  const thStatus = document.getElementById('th-status');
  if (thStatus) thStatus.textContent = t('thStatus');

  // Update slider badge and hint with active language
  updateLevelDisplay(currentLevel);

  if (btnLangDe && btnLangEn) {
    if (currentLang === 'de') {
      btnLangDe.classList.add('active');
      btnLangEn.classList.remove('active');
    } else {
      btnLangEn.classList.add('active');
      btnLangDe.classList.remove('active');
    }
  }

  if (currentStatus) renderStatus();
  if (currentPreview) {
    renderStats();
    renderTable();
  }
}

// Language switch listeners
if (btnLangDe) {
  btnLangDe.addEventListener('click', () => {
    currentLang = 'de';
    localStorage.setItem('lang', 'de');
    applyLanguage();
  });
}

if (btnLangEn) {
  btnLangEn.addEventListener('click', () => {
    currentLang = 'en';
    localStorage.setItem('lang', 'en');
    applyLanguage();
  });
}

// Graceful fallback for legacy 3-button selectors if cached by any client
const legacyButtons = [
  document.getElementById('btn-level-low'),
  document.getElementById('btn-level-med'),
  document.getElementById('btn-level-high')
].filter(Boolean);

legacyButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    legacyButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentC = parseFloat(btn.getAttribute('data-c') || '700');
    fetchPreview();
  });
});

// Level Display & Slider logic
let previewDebounceTimer = null;

function formatReviewCount(num) {
  if (num >= 10000) {
    return `${(num / 1000).toFixed(1).replace('.0', '')}k`;
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(1).replace('.0', '')}k`;
  }
  return String(Math.round(num));
}

function getTierReviewThreshold(tierName, cVal) {
  switch (tierName) {
    case 'Overwhelmingly Positive':
      return formatReviewCount(Math.round(cVal * 1.25));
    case 'Very Positive':
      return formatReviewCount(Math.round(cVal * 3.57));
    case 'Mostly Positive':
      return formatReviewCount(Math.round(cVal * 5.7));
    case 'Mixed':
      return '50';
    case 'Mostly Negative':
      return '50';
    case 'Overwhelmingly Negative':
      return '500';
    default:
      return '50';
  }
}

function renderThresholdChips() {
  const container = thresholdCard || document.getElementById('threshold-card') || document.getElementById('threshold-chips-container');
  if (!container) return;
  const tiers = (currentStatus && currentStatus.tiers) || {};
  const selectedTiers = getSelectedTiers();

  container.innerHTML = '';

  if (selectedTiers.length === 0) {
    const emptySpan = document.createElement('div');
    emptySpan.className = 'threshold-empty-hint';
    emptySpan.textContent = t('noTiersSelected');
    container.appendChild(emptySpan);
    return;
  }

  for (const [tierName, info] of Object.entries(tiers)) {
    if (!selectedTiers.includes(tierName)) continue;

    const countStr = getTierReviewThreshold(tierName, currentC);
    const isBaseline = ['Mixed', 'Mostly Negative', 'Overwhelmingly Negative'].includes(tierName);
    const prefix = isBaseline ? '' : '~';
    const row = document.createElement('div');
    row.className = 'threshold-row';
    row.innerHTML = `
      <div class="threshold-row-left">
        <span class="threshold-row-dot" style="background-color: ${info.badge_color || '#66c0f4'};"></span>
        <span class="threshold-row-title">${escapeHtml(tierName)}</span>
      </div>
      <div class="threshold-pill">
        <span class="threshold-pill-num">${prefix}${countStr}+</span>
        <span class="threshold-pill-unit">${currentLang === 'de' ? 'Reviews' : 'reviews'}</span>
      </div>
    `;
    container.appendChild(row);
  }
}

function updateLevelDisplay(levelNum) {
  currentLevel = Math.max(1, Math.min(10, levelNum || 5));
  const lvlData = FILTER_LEVELS[currentLevel - 1];
  currentC = lvlData.c;

  if (filterLevelBadge) {
    const label = currentLang === 'de' ? lvlData.de : lvlData.en;
    filterLevelBadge.textContent = `Level ${currentLevel} · ${label}`;
  }

  renderThresholdChips();

  if (filterLevelSlider && parseInt(filterLevelSlider.value, 10) !== currentLevel) {
    filterLevelSlider.value = currentLevel;
  }
}

if (filterLevelSlider) {
  filterLevelSlider.addEventListener('input', (e) => {
    const lvl = parseInt(e.target.value, 10);
    updateLevelDisplay(lvl);

    if (previewDebounceTimer) clearTimeout(previewDebounceTimer);
    previewDebounceTimer = setTimeout(() => {
      fetchPreview();
    }, 150);
  });
}

// Info Popover listeners
const btnConfInfo = document.getElementById('btn-confidence-info');
const confPopover = document.getElementById('confidence-popover');

if (btnConfInfo && confPopover) {
  btnConfInfo.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = confPopover.classList.contains('open');
    if (isOpen) {
      confPopover.classList.remove('open');
      btnConfInfo.classList.remove('active');
    } else {
      confPopover.classList.add('open');
      btnConfInfo.classList.add('active');
    }
  });

  document.addEventListener('click', (e) => {
    if (!confPopover.contains(e.target) && e.target !== btnConfInfo) {
      confPopover.classList.remove('open');
      btnConfInfo.classList.remove('active');
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      confPopover.classList.remove('open');
      btnConfInfo.classList.remove('active');
    }
  });
}

async function init() {
  applyLanguage();
  try {
    const res = await fetch('/api/status');
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    currentStatus = await res.json();
    renderStatus();
    renderTiersList();
    await fetchPreview();
    checkScanProgress();
  } catch (err) {
    showToast('Error loading status: ' + err.message, 'error');
    if (gamesTableBody) {
      const isDe = currentLang === 'de';
      gamesTableBody.innerHTML = `
        <tr>
          <td colspan="4" class="table-loading">
            <div style="margin-bottom: 12px; color: #ef5350;">⚠️ ${isDe ? 'Fehler beim Verbinden mit dem Server' : 'Error connecting to server'}: ${escapeHtml(err.message)}</div>
            <button onclick="init()" class="btn btn-secondary" style="margin: 0 auto; display: inline-flex;">🔄 ${isDe ? 'Erneut versuchen' : 'Retry'}</button>
          </td>
        </tr>
      `;
    }
  }
}

function renderStatus() {
  if (!currentStatus) return;

  if (steamStatusBadge && steamStatusText) {
    if (currentStatus.is_steam_running) {
      steamStatusBadge.className = 'status-badge running';
      steamStatusText.textContent = t('steamRunning');
    } else {
      steamStatusBadge.className = 'status-badge stopped';
      steamStatusText.textContent = t('steamStopped');
    }
  }

  if (accountSelect) {
    accountSelect.innerHTML = '';
    if (currentStatus.users && currentStatus.users.length > 0) {
      currentStatus.users.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.account_id;
        opt.textContent = `${u.persona_name} (${u.account_id})`;
        if (u.account_id === currentStatus.selected_account_id) {
          opt.selected = true;
        }
        accountSelect.appendChild(opt);
      });
    } else {
      accountSelect.innerHTML = '<option value="">No account found</option>';
    }

    accountSelect.onchange = () => {
      fetchPreview();
    };
  }
}

function renderTiersList() {
  tiersCheckboxList.innerHTML = '';
  const tiers = currentStatus.tiers || {};

  for (const [tierName, info] of Object.entries(tiers)) {
    const label = document.createElement('label');
    label.className = 'checkbox-item';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = tierName;
    checkbox.checked = info.default_active || false;
    checkbox.addEventListener('change', () => {
      renderThresholdChips();
      fetchPreview();
    });

    const span = document.createElement('span');
    span.className = 'tier-item-label';
    span.innerHTML = `<span class="tier-color-dot" style="background-color: ${info.badge_color || '#66c0f4'};"></span><span>${escapeHtml(tierName)}</span>`;

    label.appendChild(checkbox);
    label.appendChild(span);
    tiersCheckboxList.appendChild(label);
  }
  renderThresholdChips();
}

function getSelectedTiers() {
  const checked = [];
  tiersCheckboxList.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
    checked.push(cb.value);
  });
  return checked;
}

// Filter pills
document.querySelectorAll('.filter-pills .pill').forEach(pill => {
  pill.addEventListener('click', (e) => {
    document.querySelectorAll('.filter-pills .pill').forEach(p => p.classList.remove('active'));
    e.target.classList.add('active');
    activeFilter = e.target.getAttribute('data-filter');
    renderTable();
  });
});

searchInput.addEventListener('input', () => {
  renderTable();
});

btnScan.addEventListener('click', async () => {
  try {
    btnScan.disabled = true;
    const accountId = accountSelect.value;
    const checkForce = document.getElementById('check-force-refresh');
    const forceRefresh = checkForce ? checkForce.checked : false;

    const res = await fetch('/api/scan/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account_id: accountId, force_refresh: forceRefresh })
    });
    const data = await res.json();
    if (data.status === 'started') {
      showToast(t('scanStarted'), 'success');
      startScanPolling();
      if (checkForce) checkForce.checked = false; // Reset after starting
    } else {
      showToast(data.message || 'Scan in progress', 'error');
    }
  } catch (err) {
    showToast('Error starting scan: ' + err.message, 'error');
  } finally {
    btnScan.disabled = false;
  }
});

function startScanPolling() {
  scanProgressCard.classList.remove('hidden');
  if (scanPollInterval) clearInterval(scanPollInterval);

  scanPollInterval = setInterval(async () => {
    try {
      const res = await fetch('/api/scan/progress');
      const prog = await res.json();

      scanProgressFill.style.width = prog.percent + '%';
      scanPercent.textContent = prog.percent + '%';
      scanMessage.textContent = prog.message;

      if (!prog.is_scanning) {
        clearInterval(scanPollInterval);
        setTimeout(() => {
          scanProgressCard.classList.add('hidden');
        }, 2500);
        if (prog.total === 0) {
          showToast(t('scanAllUpToDate'), 'success');
        } else {
          showToast(t('scanDone'), 'success');
        }
        fetchPreview();
      }
    } catch (err) {
      clearInterval(scanPollInterval);
    }
  }, 500);
}

async function checkScanProgress() {
  try {
    const res = await fetch('/api/scan/progress');
    const prog = await res.json();
    if (prog.is_scanning) {
      startScanPolling();
    }
  } catch (err) {}
}

async function fetchPreview() {
  const accountId = accountSelect ? accountSelect.value : null;
  if (!accountId) {
    if (gamesTableBody) {
      const isDe = currentLang === 'de';
      gamesTableBody.innerHTML = `
        <tr>
          <td colspan="4" class="table-loading">
            <div style="margin-bottom: 8px;">${isDe ? 'Kein Steam-Account gefunden.' : 'No Steam account detected.'}</div>
            <div style="font-size: 13px; color: var(--steam-text-muted);">${isDe ? 'Bitte stelle sicher, dass Steam auf diesem PC installiert ist.' : 'Please ensure Steam is installed and you are logged in on this PC.'}</div>
          </td>
        </tr>
      `;
    }
    return;
  }

  const payload = {
    account_id: accountId,
    c: currentC,
    m: 0.50,
    active_tiers: getSelectedTiers()
  };

  try {
    const res = await fetch('/api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      const msg = errData.detail || (currentLang === 'de' ? 'Fehler beim Laden der Vorschau' : 'Error loading library preview');
      showToast(msg, 'error');
      if (gamesTableBody) {
        gamesTableBody.innerHTML = `
          <tr>
            <td colspan="4" class="table-loading">
              <div style="margin-bottom: 12px; color: #ef5350;">⚠️ ${escapeHtml(msg)}</div>
              <button onclick="fetchPreview()" class="btn btn-secondary" style="margin: 0 auto; display: inline-flex;">🔄 ${currentLang === 'de' ? 'Erneut versuchen' : 'Retry'}</button>
            </td>
          </tr>
        `;
      }
      return;
    }

    currentPreview = await res.json();

    if (steamStatusBadge && steamStatusText) {
      if (currentPreview.is_steam_running) {
        steamStatusBadge.className = 'status-badge running';
        steamStatusText.textContent = t('steamRunning');
      } else {
        steamStatusBadge.className = 'status-badge stopped';
        steamStatusText.textContent = t('steamStopped');
      }
    }

    renderStats();
    renderTable();
  } catch (err) {
    console.error('Preview error:', err);
    const msg = (currentLang === 'de' ? 'Verbindungsfehler: ' : 'Connection error: ') + err.message;
    showToast(msg, 'error');
    if (gamesTableBody) {
      gamesTableBody.innerHTML = `
        <tr>
          <td colspan="4" class="table-loading">
            <div style="margin-bottom: 12px; color: #ef5350;">⚠️ ${escapeHtml(msg)}</div>
            <button onclick="fetchPreview()" class="btn btn-secondary" style="margin: 0 auto; display: inline-flex;">🔄 ${currentLang === 'de' ? 'Erneut versuchen' : 'Retry'}</button>
          </td>
        </tr>
      `;
    }
  }
}

function renderStats() {
  if (!currentPreview || !currentPreview.stats || !statsGrid) return;
  const s = currentPreview.stats;
  const tiers = (currentStatus && currentStatus.tiers) || {};
  const selectedTiers = getSelectedTiers();

  const excludedCount = (s.low_confidence || 0) + (s.delisted || 0) + (s.unavailable || 0) + (s.unscanned || 0) + (s.no_reviews || 0);

  statsGrid.innerHTML = '';

  // 1. Dynamic card for each selected active tier
  for (const [tierName, info] of Object.entries(tiers)) {
    if (selectedTiers.includes(tierName)) {
      const count = s.tier_counts[tierName] || 0;
      const card = document.createElement('div');
      card.className = 'stat-card';
      card.style.borderTop = `3px solid ${info.badge_color || '#66c0f4'}`;
      card.innerHTML = `
        <div class="stat-num">${count.toLocaleString()}</div>
        <div class="stat-label">
          <span class="tier-color-dot" style="background-color: ${info.badge_color || '#66c0f4'};"></span>
          <span>${escapeHtml(tierName)}</span>
        </div>
      `;
      statsGrid.appendChild(card);
    }
  }

  // 2. Excluded card (true exclusions only)
  const cardEx = document.createElement('div');
  cardEx.className = 'stat-card';
  cardEx.style.borderTop = '3px solid #7e8d9c';
  cardEx.innerHTML = `
    <div class="stat-num">${excludedCount.toLocaleString()}</div>
    <div class="stat-label">
      <span class="tier-color-dot" style="background-color: #7e8d9c;"></span>
      <span>${t('statLowConf')}</span>
    </div>
  `;
  statsGrid.appendChild(cardEx);

  // 3. Total Owned card
  const cardTot = document.createElement('div');
  cardTot.className = 'stat-card';
  cardTot.style.borderTop = '3px solid #4a6177';
  cardTot.innerHTML = `
    <div class="stat-num">${(s.total_owned || 0).toLocaleString()}</div>
    <div class="stat-label">
      <span class="tier-color-dot" style="background-color: #4a6177;"></span>
      <span>${t('statTotal')}</span>
    </div>
  `;
  statsGrid.appendChild(cardTot);

  // Update table toolbar filter pills
  const pillAssigned = document.getElementById('pill-assigned');
  const pillExcluded = document.getElementById('pill-excluded');
  if (pillAssigned) {
    pillAssigned.textContent = `${t('pillAssigned')} (${(s.assigned || 0).toLocaleString()})`;
  }
  if (pillExcluded) {
    pillExcluded.textContent = `${t('pillExcluded')} (${excludedCount.toLocaleString()})`;
  }
}

function renderGameRow(g) {
  const storeUrl = `https://store.steampowered.com/app/${g.appid}/`;
  const headerUrl = `https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/${g.appid}/header.jpg`;
  let statusBadgeClass = 'badge-unassigned';
  let label = currentLang === 'de' ? g.status_label_de : g.status_label_en;

  if (g.status === 'assigned') {
    statusBadgeClass = 'badge-assigned';
  } else if (g.status === 'unavailable') {
    statusBadgeClass = 'badge-unavailable';
  } else if (g.status === 'delisted') {
    statusBadgeClass = 'badge-delisted';
  } else if (g.status === 'low_confidence') {
    statusBadgeClass = 'badge-low-conf';
  } else if (g.status === 'unscanned' || g.status === 'no_reviews') {
    statusBadgeClass = 'badge-unscanned';
  }

  const pctDisplay = g.total_reviews > 0 ? `${g.raw_percent}%` : '-';
  const reviewsSubline = g.total_reviews > 0
    ? `<span class="pct-sub">${g.total_positive.toLocaleString()} / ${g.total_reviews.toLocaleString()}</span>`
    : '';

  return `
    <tr>
      <td>
        <a href="${storeUrl}" target="_blank" rel="noopener noreferrer" class="game-cover-link" title="${t('openInSteam')}">
          <img src="${headerUrl}" class="game-cover" onerror="this.src='https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/${g.appid}/capsule_231x87.jpg'; this.onerror=function(){this.style.opacity='0.2';}" alt="">
        </a>
      </td>
      <td>
        <div class="game-title-cell">
          <div class="game-title-row">
            <a href="${storeUrl}" target="_blank" rel="noopener noreferrer" class="game-title-link" title="AppID: ${g.appid} - ${t('openInSteam')}">
              <span class="game-title">${escapeHtml(g.name)}</span>
              <span class="external-icon">↗</span>
            </a>
            <button class="btn-single-refresh" onclick="refreshSingleGame(${g.appid}, this, event)" title="${t('refreshGame')}">
              <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
              </svg>
            </button>
          </div>
          <span class="game-appid">AppID: ${g.appid}</span>
        </div>
      </td>
      <td style="text-align: right;" class="num-cell">
        <div class="pct-cell">
          <span class="pct-main">${pctDisplay}</span>
          ${reviewsSubline}
        </div>
      </td>
      <td>
        <span class="score-badge ${statusBadgeClass}">${escapeHtml(label)}</span>
      </td>
    </tr>
  `;
}

async function refreshSingleGame(appid, btnElement, event) {
  if (event) event.stopPropagation();
  if (!btnElement || btnElement.classList.contains('spinning')) return;

  btnElement.classList.add('spinning');
  try {
    const res = await fetch(`/api/scan/single/${appid}`, { method: 'POST' });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`${data.info.name} ${t('gameUpdated')}: ${data.info.total_positive.toLocaleString()} / ${data.info.total_reviews.toLocaleString()} (${data.info.review_score_desc})`, 'info');
      await fetchPreview();
    } else {
      showToast(data.detail || 'Fehler beim Abrufen der Reviews', 'error');
    }
  } catch (err) {
    showToast('Fehler: ' + err.message, 'error');
  } finally {
    btnElement.classList.remove('spinning');
  }
}

async function refreshGroupGames(groupKey, event) {
  if (event) event.stopPropagation();
  const btn = event ? (event.currentTarget || (event.target && event.target.closest('button'))) : null;
  if (btn && btn.classList.contains('spinning')) return;
  if (!currentPreview || !currentPreview.games) return;

  const targetFilter = {
    'low_confidence': g => g.status === 'low_confidence',
    'unavailable': g => g.status === 'unavailable',
    'delisted': g => g.status === 'delisted',
    'unscanned': g => g.status === 'unscanned' || g.status === 'no_reviews'
  }[groupKey];

  if (!targetFilter) return;

  const targetGames = currentPreview.games.filter(targetFilter);
  if (targetGames.length === 0) {
    showToast(t('noGamesInGroup'), 'info');
    return;
  }

  const appids = targetGames.map(g => g.appid);
  if (btn) btn.classList.add('spinning');

  try {
    const res = await fetch('/api/scan/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appids })
    });
    const data = await res.json();
    if (res.ok && data.status === 'started') {
      showToast(`${appids.length} ${t('batchScanStarted')}`, 'info');
      startScanPolling();
    } else if (res.ok && data.status === 'already_scanning') {
      showToast(data.message || t('scanInProgress'), 'info');
      startScanPolling();
    } else {
      const errDetail = (data && data.detail) ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : '';
      const errMsg = (data && data.message) || errDetail || t('scanError');
      showToast(errMsg, 'error');
    }
  } catch (err) {
    showToast('Fehler: ' + err.message, 'error');
  } finally {
    if (btn) btn.classList.remove('spinning');
  }
}

function renderTable() {
  if (!gamesTableBody) return;

  if (!currentPreview || !currentPreview.games) {
    const isDe = currentLang === 'de';
    gamesTableBody.innerHTML = `
      <tr>
        <td colspan="4" class="table-loading">
          <div style="margin-bottom: 12px;">${t('loading')}</div>
          <button onclick="fetchPreview()" class="btn btn-secondary" style="margin: 0 auto; display: inline-flex;">🔄 ${isDe ? 'Neu laden' : 'Reload'}</button>
        </td>
      </tr>
    `;
    return;
  }

  const query = searchInput.value.toLowerCase().trim();
  const allFilteredGames = currentPreview.games.filter(g => {
    if (query && !g.name.toLowerCase().includes(query) && !String(g.appid).includes(query)) {
      return false;
    }
    // Completely hide games whose tier was unselected by the user
    if (g.status === 'unassigned') return false;
    // Tab filter
    if (activeFilter === 'assigned' && g.status !== 'assigned') return false;
    if (activeFilter === 'excluded' && g.status === 'assigned') return false;
    return true;
  });

  if (allFilteredGames.length === 0) {
    gamesTableBody.innerHTML = `<tr><td colspan="4" class="table-loading">${t('noGames')}</td></tr>`;
    return;
  }

  let rowsHtml = '';

  if (activeFilter === 'assigned') {
    const tiers = (currentStatus && currentStatus.tiers) || {};
    const selectedTiers = getSelectedTiers();

    for (const tier of Object.keys(tiers)) {
      if (!selectedTiers.includes(tier)) continue;
      const tierGames = allFilteredGames.filter(g => g.assigned_tier === tier);
      if (tierGames.length > 0) {
        const dotColor = tiers[tier]?.badge_color || '#66c0f4';
        rowsHtml += `
          <tr class="group-header-row">
            <td colspan="4">
              <div class="group-header-title">
                <span class="group-header-title-text">
                  <span class="tier-color-dot" style="background-color: ${dotColor};"></span>
                  <span>${escapeHtml(tier)}</span>
                </span>
                <span class="group-header-count">${tierGames.length} ${t('gamesCountLabel')}</span>
              </div>
            </td>
          </tr>
        `;
        tierGames.forEach(g => {
          rowsHtml += renderGameRow(g);
        });
      }
    }
  } else {
    // Excluded games view - grouped by status
    const excludedSections = [
      {
        key: 'low_confidence',
        color: '#92a4b8',
        label: t('grpLowConf'),
        filter: g => g.status === 'low_confidence'
      },
      {
        key: 'unavailable',
        color: '#f1a94e',
        label: t('grpUnavailable'),
        filter: g => g.status === 'unavailable'
      },
      {
        key: 'delisted',
        color: '#ef5350',
        label: t('grpDelisted'),
        filter: g => g.status === 'delisted'
      },
      {
        key: 'unscanned',
        color: '#5d6d7e',
        label: t('grpNoReviews'),
        filter: g => g.status === 'unscanned' || g.status === 'no_reviews'
      }
    ];

    excludedSections.forEach(sec => {
      const secGames = allFilteredGames.filter(sec.filter);
      if (secGames.length > 0) {
        rowsHtml += `
          <tr class="group-header-row group-header-${sec.key}">
            <td colspan="4">
              <div class="group-header-title">
                <span class="group-header-title-text">
                  <span class="tier-color-dot" style="background-color: ${sec.color};"></span>
                  <span>${escapeHtml(sec.label)}</span>
                </span>
                <span class="group-header-count">${secGames.length} ${t('gamesCountLabel')}</span>
                <button class="btn-group-refresh" onclick="refreshGroupGames('${sec.key}', event)" title="${t('refreshGroup')}">
                  <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
                  </svg>
                  <span>${t('refreshGroupBtn')}</span>
                </button>
              </div>
            </td>
          </tr>
        `;
        secGames.forEach(g => {
          rowsHtml += renderGameRow(g);
        });
      }
    });
  }

  gamesTableBody.innerHTML = rowsHtml;
}

if (btnSave) {
  btnSave.addEventListener('click', async () => {
  const statusRes = await fetch('/api/status');
  const freshStatus = await statusRes.json();

  if (freshStatus.is_steam_running) {
    showToast(t('steamMustClose'), 'error');
    steamStatusBadge.className = 'status-badge running';
    steamStatusText.textContent = t('steamRunning');
    return;
  }

  const selectedTiers = getSelectedTiers();
  if (selectedTiers.length === 0) {
    showToast(t('selectTierError'), 'error');
    return;
  }

  const confirmed = confirm(t('saveConfirm'));
  if (!confirmed) return;

  btnSave.disabled = true;
  document.getElementById('i18n-btn-save').textContent = t('btnSaving');

  try {
    const payload = {
      account_id: accountSelect.value,
      c: currentC,
      m: 0.50,
      active_tiers: selectedTiers
    };

    const res = await fetch('/api/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Save failed');
    }

    showToast(t('saveSuccess'), 'success');
  } catch (err) {
    showToast('Error: ' + err.message, 'error');
  } finally {
    btnSave.disabled = false;
    document.getElementById('i18n-btn-save').textContent = t('btnSave');
  }
});
}

function showToast(msg, type = 'success') {
  toastEl.textContent = msg;
  toastEl.className = `toast ${type}`;
  toastEl.classList.remove('hidden');
  setTimeout(() => {
    toastEl.classList.add('hidden');
  }, 4000);
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[m]);
}

// Start
init();
