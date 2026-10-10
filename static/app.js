// SteamSeparator - Lean & Bilingual Frontend
let currentLang = localStorage.getItem('lang') || 'en';
let currentC = 350.0;
let currentStatus = null;
let currentPreview = null;
let scanPollInterval = null;
let debounceTimer = null;
let activeFilter = 'assigned'; // Default: only assigned games!

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
    confidencePopover: "Gewichtet die Review-Anzahl: Verhindert Top-Einstufungen bei geringer Stimmenanzahl.",
    levelLow: "Niedrig",
    levelMed: "Mittel",
    levelHigh: "Hoch",
    levelDescLow: "Tolerant: Benötigt ca. 800 Reviews für Top-Wertungen",
    levelDescMed: "Ausgewogen: Benötigt ca. 1.900 Reviews für Top-Wertungen (Standard)",
    levelDescHigh: "Streng: Benötigt ca. 3.800 Reviews für Top-Wertungen",
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
    confidencePopover: "Weights review count: Prevents top rankings with low vote counts.",
    levelLow: "Low",
    levelMed: "Medium",
    levelHigh: "High",
    levelDescLow: "Tolerant: Requires ~800 reviews for top ratings",
    levelDescMed: "Balanced: Requires ~1,900 reviews for top ratings (Default)",
    levelDescHigh: "Strict: Requires ~3,800 reviews for top ratings",
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

// Level Buttons
const btnLevelLow = document.getElementById('btn-level-low');
const btnLevelMed = document.getElementById('btn-level-med');
const btnLevelHigh = document.getElementById('btn-level-high');

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

  const thScore = document.getElementById('th-score');
  if (thScore) {
    thScore.textContent = t('thScore');
    thScore.title = t('tooltipScore');
  }

  const thStatus = document.getElementById('th-status');
  if (thStatus) thStatus.textContent = t('thStatus');

  if (btnLevelLow) {
    btnLevelLow.textContent = t('levelLow');
    btnLevelLow.title = t('levelDescLow');
  }
  if (btnLevelMed) {
    btnLevelMed.textContent = t('levelMed');
    btnLevelMed.title = t('levelDescMed');
  }
  if (btnLevelHigh) {
    btnLevelHigh.textContent = t('levelHigh');
    btnLevelHigh.title = t('levelDescHigh');
  }

  if (currentLang === 'de') {
    btnLangDe.classList.add('active');
    btnLangEn.classList.remove('active');
  } else {
    btnLangEn.classList.add('active');
    btnLangDe.classList.remove('active');
  }

  if (currentStatus) renderStatus();
  if (currentPreview) {
    renderStats();
    renderTable();
  }
}

// Language switch listeners
btnLangDe.addEventListener('click', () => {
  currentLang = 'de';
  localStorage.setItem('lang', 'de');
  applyLanguage();
});

btnLangEn.addEventListener('click', () => {
  currentLang = 'en';
  localStorage.setItem('lang', 'en');
  applyLanguage();
});

// Level selector listeners
[btnLevelLow, btnLevelMed, btnLevelHigh].forEach(btn => {
  btn.addEventListener('click', (e) => {
    [btnLevelLow, btnLevelMed, btnLevelHigh].forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentC = parseFloat(btn.getAttribute('data-c'));
    fetchPreview();
  });
});

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
    currentStatus = await res.json();
    renderStatus();
    renderTiersList();
    await fetchPreview();
    checkScanProgress();
  } catch (err) {
    showToast('Error loading status: ' + err.message, 'error');
  }
}

function renderStatus() {
  if (currentStatus.is_steam_running) {
    steamStatusBadge.className = 'status-badge running';
    steamStatusText.textContent = t('steamRunning');
  } else {
    steamStatusBadge.className = 'status-badge stopped';
    steamStatusText.textContent = t('steamStopped');
  }

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

  accountSelect.addEventListener('change', () => {
    fetchPreview();
  });
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
    checkbox.addEventListener('change', () => fetchPreview());

    const span = document.createElement('span');
    span.className = 'tier-item-label';
    span.innerHTML = `<span class="tier-color-dot" style="background-color: ${info.badge_color || '#66c0f4'};"></span><span>${escapeHtml(tierName)}</span>`;

    label.appendChild(checkbox);
    label.appendChild(span);
    tiersCheckboxList.appendChild(label);
  }
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
  const accountId = accountSelect.value;
  if (!accountId) return;

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
    currentPreview = await res.json();

    if (currentPreview.is_steam_running) {
      steamStatusBadge.className = 'status-badge running';
      steamStatusText.textContent = t('steamRunning');
    } else {
      steamStatusBadge.className = 'status-badge stopped';
      steamStatusText.textContent = t('steamStopped');
    }

    renderStats();
    renderTable();
  } catch (err) {
    console.error('Preview error:', err);
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

  const bScore = g.total_reviews > 0 ? `${g.bayesian_score}%` : '-';

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
      <td style="text-align: right; color: var(--steam-blue);" class="num-cell">${bScore}</td>
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
  if (!currentPreview || !currentPreview.games) {
    gamesTableBody.innerHTML = `<tr><td colspan="5" class="table-loading">${t('loading')}</td></tr>`;
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
    gamesTableBody.innerHTML = `<tr><td colspan="5" class="table-loading">${t('noGames')}</td></tr>`;
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
            <td colspan="5">
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
            <td colspan="5">
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
