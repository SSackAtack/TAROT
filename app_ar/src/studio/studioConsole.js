import { appState } from '../core/appState'
import { studioState, updateStudioStateFromPayload, saveStudioVolumeSettings } from './studioState'
import { sendControlMessage } from '../transport/wsClient'
import { startStudioRecording, stopStudioRecording } from './mediaRecorderController'
import { startStudioMicrophone, updateAudioMixerValues } from './audioMixer'
import { addTimelineMarker, formatMsToTime } from './timeline'
import { processDirectorDecision } from './director'

// Globalne referencje do elementów DOM konsoli
let sidebarEl = null
let topbarEl = null
let bottombarEl = null
let previousCards = []

let isDecksInitialized = false
let loadedDecksList = []
let activeDecksState = []
let isDecksApplying = false

const studioCameraLabels = {
    CAP_PROP_FOCUS: 'Ostrość',
    CAP_PROP_AUTOFOCUS: 'Autofokus',
    CAP_PROP_EXPOSURE: 'Ekspozycja',
    CAP_PROP_AUTO_EXPOSURE: 'Auto ekspozycja',
    CAP_PROP_BRIGHTNESS: 'Jasność',
    CAP_PROP_CONTRAST: 'Kontrast'
}

const studioCameraRanges = {
    CAP_PROP_FOCUS: { min: 0, max: 1023, step: 5 },
    CAP_PROP_AUTOFOCUS: { min: 0, max: 1, step: 1 },
    CAP_PROP_EXPOSURE: { min: -13, max: 1000, step: 1 },
    CAP_PROP_AUTO_EXPOSURE: { min: 0, max: 3, step: 1 },
    CAP_PROP_BRIGHTNESS: { min: 0, max: 255, step: 1 },
    CAP_PROP_CONTRAST: { min: 0, max: 255, step: 1 }
}

function clampCameraValue(value, range) {
    const numericValue = Number(value)
    if (!Number.isFinite(numericValue)) return Number(range.min)
    return Math.min(Number(range.max), Math.max(Number(range.min), numericValue))
}

function formatCameraValue(value, step) {
    const numericStep = Number(step)
    if (!Number.isFinite(numericStep) || !String(step).includes('.')) {
        return String(Number(value))
    }
    const decimals = String(step).split('.')[1].length
    return Number(value).toFixed(decimals)
}

function applyStudioCameraControlValue(input, rawValue, shouldSend = false) {
    const cameraParam = input.dataset.cameraParam
    if (!cameraParam) return

    const control = input.closest('.studio-camera-control')
    if (!control) return

    const range = studioCameraRanges[cameraParam] || { min: 0, max: 255, step: 1 }
    const value = clampCameraValue(rawValue, range)
    const formattedValue = formatCameraValue(value, range.step)

    control.querySelectorAll(`input[data-camera-param="${cameraParam}"]`).forEach((field) => {
        field.value = formattedValue
    })

    const output = control.querySelector('output')
    if (output) output.textContent = formattedValue

    if (shouldSend) {
        sendControlMessage({
            type: 'camera_set',
            param: cameraParam,
            value
        })
    }
}

function getStudioDeckDisplayName(deckId) {
    const deck = loadedDecksList.find(item => item.id === deckId)
    return deck?.display_name || deckId
}

function updateStudioActiveDecksStatus(selectedIds = activeDecksState) {
    if (!sidebarEl) return
    const statusEl = sidebarEl.querySelector('#studio-active-decks-status')
    if (!statusEl) return

    if (!Array.isArray(selectedIds) || selectedIds.length < 1) {
        statusEl.textContent = 'Wybierz 1-3 talie przed kalibracją'
        statusEl.classList.add('studio-active-decks-status--warning')
        return
    }

    const names = selectedIds.map(getStudioDeckDisplayName).join(', ')
    statusEl.textContent = `Aktywne teraz: ${names}`
    statusEl.classList.remove('studio-active-decks-status--warning')
}

function getCvExplainabilityFallback(data) {
    const activeDecks = data.operator?.active_decks || activeDecksState || []
    const layoutState = data.layout?.state || 'unknown'
    const cardCount = Array.isArray(data.cards) ? data.cards.length : 0
    const lastWarning = Array.isArray(data.warnings) && data.warnings.length > 0
        ? data.warnings[data.warnings.length - 1]
        : ''

    let severity = cardCount > 0 ? 'ok' : 'warn'
    let nextAction = cardCount > 0 ? 'Mozna prowadzic sesje.' : 'Zostaw mate nieruchomo przez kilka sekund.'

    if (activeDecks.length < 1) {
        severity = 'error'
        nextAction = 'Wybierz 1-3 talie w Studio.'
    } else if (layoutState === 'no_camera') {
        severity = 'error'
        nextAction = 'Sprawdz kamere i launcher CV.'
    } else if (lastWarning) {
        nextAction = lastWarning
    }

    return {
        severity,
        next_action: nextAction,
        steps: [
            {
                id: 'decks',
                label: 'Aktywne talie',
                state: activeDecks.length > 0 ? 'ok' : 'error',
                value: String(activeDecks.length),
                message: activeDecks.length > 0 ? activeDecks.join(', ') : 'Brak aktywnej talii'
            },
            {
                id: 'snapshot',
                label: 'Snapshot',
                state: ['settling', 'sampling_snapshots', 'analyzing_snapshot'].includes(layoutState) ? 'wait' : 'ok',
                value: layoutState,
                message: layoutState
            },
            {
                id: 'recognition',
                label: 'Rozpoznanie',
                state: cardCount > 0 ? 'ok' : 'wait',
                value: String(cardCount),
                message: cardCount > 0 ? 'Karty zaakceptowane' : 'Czeka na rozpoznanie'
            }
        ]
    }
}

function getCvExplainabilityBadge(severity) {
    if (severity === 'ok') return 'OK'
    if (severity === 'error') return 'BLAD'
    if (severity === 'wait') return 'WAIT'
    return 'UWAGA'
}

function getCvExplainabilityIcon(state) {
    if (state === 'ok') return '✓'
    if (state === 'error') return '×'
    if (state === 'warn') return '!'
    return '•'
}

function renderCvExplainability(data) {
    if (!sidebarEl) return
    const explain = data.operator?.explainability || getCvExplainabilityFallback(data)
    const panel = sidebarEl.querySelector('#studio-cv-explain-panel')
    const badge = sidebarEl.querySelector('#studio-cv-explain-badge')
    const stepsEl = sidebarEl.querySelector('#studio-cv-explain-steps')
    const nextEl = sidebarEl.querySelector('#studio-cv-explain-next')
    if (!panel || !badge || !stepsEl || !nextEl) return

    const severity = explain.severity || 'warn'
    panel.dataset.severity = severity
    badge.textContent = getCvExplainabilityBadge(severity)
    badge.className = `studio-cv-explain-badge studio-cv-explain-badge--${severity}`

    stepsEl.innerHTML = ''
    const steps = Array.isArray(explain.steps) ? explain.steps : []
    steps.forEach((step) => {
        const row = document.createElement('div')
        const state = step.state || 'wait'
        row.className = `studio-cv-explain-step studio-cv-explain-step--${state}`
        row.innerHTML = `
            <span class="studio-cv-explain-step__icon">${getCvExplainabilityIcon(state)}</span>
            <span class="studio-cv-explain-step__label">${step.label || step.id || 'Status'}</span>
            <span class="studio-cv-explain-step__value">${step.value || ''}</span>
            <span class="studio-cv-explain-step__message">${step.message || ''}</span>
        `
        stepsEl.appendChild(row)
    })

    nextEl.textContent = explain.next_action || 'Sprawdz diagnostyke CV.'
}

function formatAutotuneNumber(value) {
    const numberValue = Number(value)
    if (!Number.isFinite(numberValue)) return '-'
    return numberValue.toFixed(2)
}

function renderStudioAutotune(data) {
    if (!sidebarEl) return
    const autotune = data.operator?.calibration?.autotune || {}
    const panel = sidebarEl.querySelector('#studio-autotune-panel')
    const stateEl = sidebarEl.querySelector('#studio-autotune-state')
    const resultEl = sidebarEl.querySelector('#studio-autotune-result')
    if (!panel || !stateEl || !resultEl) return

    const state = autotune.state || 'idle'
    const recommendation = autotune.recommendation || null
    const progress = autotune.progress || {}
    panel.dataset.state = state
    stateEl.textContent = String(state).toUpperCase()

    if (!recommendation) {
        const scenarioProgress = Object.entries(progress)
            .map(([scenario, value]) => `${scenario}: ${value}`)
            .join(' | ')
        const collected = progress.samples_collected ?? progress.sample_count ?? 0
        const target = progress.samples_target ?? progress.target_samples ?? '-'
        resultEl.textContent = state === 'idle'
            ? 'Brak rekomendacji.'
            : `Zbieranie probek: ${scenarioProgress || `${collected}/${target}`}`
        return
    }

    const profile = recommendation.profile || {}
    const profileName = recommendation.profile_name || recommendation.name || 'kandydat'
    const score = recommendation.score ?? recommendation.confidence ?? recommendation.value
    const confidence = recommendation.confidence
    const profileSummary = Object.entries(profile)
        .slice(0, 3)
        .map(([key, value]) => `${key}=${value}`)
        .join(', ')
    const details = [
        `Profil: ${profileName}`,
        `Score: ${formatAutotuneNumber(score)}`,
        confidence !== undefined ? `Pewnosc: ${formatAutotuneNumber(confidence)}` : '',
        profileSummary
    ].filter(Boolean)

    resultEl.textContent = details.join(' | ')
}

function initStudioDecksPanel() {
    if (isDecksInitialized || !sidebarEl) return
    isDecksInitialized = true

    const listEl = sidebarEl.querySelector('#studio-decks-list')
    const applyBtn = sidebarEl.querySelector('#studio-decks-apply-btn')

    if (!listEl) return

    // 1. Pobierz manifest talii
    fetch('/decks_manifest.json')
        .then(res => res.json())
        .then(manifest => {
            loadedDecksList = manifest.decks || []
            
            // Pobierz aktualne aktywne talie z active_decks.json na starcie w celu synchronizacji początkowej
            fetch('/active_decks.json')
                .then(res => res.json())
                .then(activeData => {
                    activeDecksState = activeData.active_decks || []
                    updateStudioActiveDecksStatus(activeDecksState)
                    renderDecksCheckboxes(listEl, applyBtn)
                })
                .catch(() => {
                    updateStudioActiveDecksStatus([])
                    renderDecksCheckboxes(listEl, applyBtn)
                })
        })
        .catch(err => {
            listEl.innerHTML = `<div style="font-size: 11px; color: #f87171; text-align: center; padding: 8px;">Błąd pobierania manifestu: ${err}</div>`
            updateStudioActiveDecksStatus([])
        })
}

function renderDecksCheckboxes(listEl, applyBtn) {
    if (!listEl) return
    listEl.innerHTML = ''

    loadedDecksList.forEach(deck => {
        const isChecked = activeDecksState.includes(deck.id)
        
        const row = document.createElement('div')
        row.className = 'studio-deck-row'
        row.style.display = 'flex'
        row.style.alignItems = 'center'
        row.style.justifyContent = 'space-between'
        row.style.padding = '6px 10px'
        row.style.background = 'rgba(30, 41, 59, 0.4)'
        row.style.border = '1px solid rgba(255,255,255,0.05)'
        row.style.borderRadius = '4px'
        row.style.transition = 'all 0.2s ease'
        row.style.marginBottom = '2px'

        row.innerHTML = `
            <span style="font-size: 12px; font-weight: 500; color: #cbd5e1;">${deck.display_name}</span>
            <input type="checkbox" class="studio-deck-checkbox" data-deck-id="${deck.id}" ${isChecked ? 'checked' : ''} style="accent-color: #d67d3e; cursor: pointer; width: 15px; height: 15px;">
        `
        listEl.appendChild(row)
    })

    // Logika przycisków i checkboxów
    const checkboxes = listEl.querySelectorAll('.studio-deck-checkbox')
    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            const checkedBoxes = Array.from(checkboxes).filter(c => c.checked)
            const count = checkedBoxes.length

            // Limit 1-3 aktywnych talii
            if (count >= 3) {
                checkboxes.forEach(c => {
                    if (!c.checked) c.disabled = true
                })
            } else {
                checkboxes.forEach(c => c.disabled = false)
            }

            // Jeśli jest tylko 1 zaznaczona talia, zabraniamy jej odznaczenia (żeby nie było 0)
            if (count <= 1) {
                checkedBoxes.forEach(c => c.disabled = true)
            } else {
                checkedBoxes.forEach(c => {
                    if (count < 3) c.disabled = false
                })
            }

            // Sprawdzamy czy zaszła zmiana w stosunku do stanu activeDecksState
            const currentSelected = checkedBoxes.map(c => c.getAttribute('data-deck-id'))
            updateStudioActiveDecksStatus(currentSelected)
            const hasChanged = currentSelected.length !== activeDecksState.length || 
                               !currentSelected.every(id => activeDecksState.includes(id))

            if (applyBtn) {
                if (isDecksApplying) {
                    applyBtn.setAttribute('disabled', 'true')
                } else if (hasChanged && currentSelected.length >= 1 && currentSelected.length <= 3) {
                    applyBtn.removeAttribute('disabled')
                } else {
                    applyBtn.setAttribute('disabled', 'true')
                }
            }
        })
    })

    // Pierwsze uruchomienie walidacji stanu checkboxów
    const initialChecked = Array.from(checkboxes).filter(c => c.checked)
    if (initialChecked.length >= 3) {
        checkboxes.forEach(c => {
            if (!c.checked) c.disabled = true
        })
    } else if (initialChecked.length <= 1) {
        initialChecked.forEach(c => c.disabled = true)
    }

    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            const selected = Array.from(checkboxes)
                .filter(c => c.checked)
                .map(c => c.getAttribute('data-deck-id'))

            if (selected.length >= 1 && selected.length <= 3 && !isDecksApplying) {
                isDecksApplying = true
                applyBtn.setAttribute('disabled', 'true')
                applyBtn.textContent = 'Trwa wdrażanie...'
                checkboxes.forEach(c => c.disabled = true)
                
                sendControlMessage({
                    type: "studio_set_active_decks",
                    active_decks: selected
                })
            }
        })
    }
}

export function createStudioConsole() {
    if (!appState.studioMode) return

    // 1. Aktywuj klasę trybu studio w body
    document.body.classList.add('studio-mode-active')

    // 2. Usuń starszy operator-panel i wow-controls jeśli istnieją
    const oldOp = document.querySelector('.operator-panel')
    if (oldOp) oldOp.remove()
    const oldWow = document.querySelector('.wow-controls')
    if (oldWow) oldWow.remove()

    // 3. Stwórz główny kontener HUD wstrzykiwany na wierzch strony
    const hudContainer = document.createElement('div')
    hudContainer.className = 'studio-hud'
    document.body.appendChild(hudContainer)

    // 4. Stwórz górny pasek statusu (Topbar)
    const topbar = document.createElement('div')
    topbar.className = 'studio-topbar'
    topbar.innerHTML = `
        <div class="studio-logo">
            <div class="studio-logo__indicator"></div>
            <div class="studio-logo__text">TAROTVISION STUDIO</div>
            <div class="studio-logo__badge">Console v1</div>
        </div>
        <div class="studio-indicators">
            <button type="button" class="studio-operator-link" id="btn-open-operator" title="Otwórz Panel Operatora w nowej karcie">
                Operator
            </button>
            <div class="studio-indicator studio-indicator--active" id="indicator-ws">
                <div class="dot"></div> WS
            </div>
            <div class="studio-indicator" id="indicator-cv">
                <div class="dot"></div> CV
            </div>
            <div class="studio-indicator" id="indicator-cam">
                <div class="dot"></div> CAMERA
            </div>
            <div class="studio-indicator" id="indicator-audio">
                <div class="dot"></div> AUDIO
            </div>
            <div class="studio-indicator" id="indicator-rec">
                <div class="dot"></div> REC
            </div>
        </div>
    `
    hudContainer.appendChild(topbar)
    topbarEl = topbar

    // 5. Stwórz centralny preview overlay z safe guides
    const previewOverlay = document.createElement('div')
    previewOverlay.className = 'studio-preview-overlay'
    previewOverlay.innerHTML = `
        <div class="studio-preview-label">LIVE CAMERA PREVIEW</div>
        <div class="studio-camera-preview">
            <img id="studio-camera-preview-img" src="http://localhost:8766/video_feed.mjpg" alt="Podgląd kamery CV">
        </div>
        <div class="studio-safe-guides">
            <div class="studio-safe-guides-inner"></div>
        </div>
    `
    hudContainer.appendChild(previewOverlay)

    // 6. Stwórz prawy pasek boczny (Sidebar) z sekcjami
    const sidebar = document.createElement('div')
    sidebar.className = 'studio-sidebar'
    sidebar.innerHTML = `
        <!-- Sekcja 1: Nagrywanie -->
        <div class="studio-card">
            <div class="studio-card__header">
                <div class="studio-card__title">Transport i Nagrywanie</div>
                <div class="studio-card__subtitle" id="studio-rec-state">OFFLINE</div>
            </div>
            <div class="studio-rec-info">
                <div class="studio-rec-item">
                    <div class="studio-rec-item__label">Elapsed Time</div>
                    <div class="studio-rec-item__value studio-rec-item__value--time" id="studio-time-val">00:00:00</div>
                </div>
                <div class="studio-rec-item">
                    <div class="studio-rec-item__label">Dropped Frames</div>
                    <div class="studio-rec-item__value" id="studio-dropped-val">0</div>
                </div>
            </div>
            <div class="studio-path-box">
                <div class="studio-rec-item__label">Katalog zapisu (Backend Path)</div>
                <div class="studio-path-input-group">
                    <input type="text" class="studio-path-input" id="studio-path-input" placeholder="./recordings" value="./recordings">
                    <button class="studio-btn-action" id="studio-path-btn">Ustaw</button>
                </div>
                <div class="studio-path-status" id="studio-path-status">Stan: Brak walidacji</div>
            </div>
        </div>

        <!-- Sekcja 1b: Kamera sprzętowa -->
        <div class="studio-card">
            <div class="studio-card__header">
                <div class="studio-card__title">Kamera sprzętowo</div>
                <div class="studio-card__subtitle">Focus / Exposure</div>
            </div>
            <div class="studio-camera-controls" id="studio-camera-controls">
                Brak danych z kamery. Kliknij odczyt.
            </div>
            <button class="studio-btn-action" id="studio-camera-probe-btn" style="width: 100%; justify-content: center; height: 32px;">
                Odczyt kamery
            </button>
        </div>

        <!-- Sekcja 2: Reżyser / Sceny -->
        <div class="studio-card">
            <div class="studio-card__header">
                <div class="studio-card__title">Tryb Reżysera i Kadr</div>
                <div class="studio-card__subtitle">Director Mode</div>
            </div>
            <div class="studio-scenes-grid">
                <button class="studio-scene-btn studio-scene-btn--active" data-scene="table">
                    <span class="icon">🎴</span><span>Stół</span>
                </button>
                <button class="studio-scene-btn" data-scene="wow">
                    <span class="icon">✨</span><span>WOW Mode</span>
                </button>
                <button class="studio-scene-btn" data-scene="portrait_pip" disabled title="Kamera portretowa niedostępna w tej wersji">
                    <span class="icon">👤</span><span>PiP (Portret)</span>
                </button>
                <button class="studio-scene-btn" data-scene="title_card" disabled title="Intro/Outro niedostępne w tej wersji">
                    <span class="icon">🎬</span><span>Intro/Outro</span>
                </button>
                <button class="studio-scene-btn" data-scene="auto" id="btn-studio-auto" style="grid-column: 1 / -1; margin-top: 4px;">
                    <span class="icon">🤖</span><span>Automatyczny Reżyser (Auto)</span>
                </button>
            </div>
        </div>

        <!-- Sekcja 3: Mikser Audio -->
        <div class="studio-card">
            <div class="studio-card__header">
                <div class="studio-card__title">Mikser Audio (Offline Mixer)</div>
                <div class="studio-card__subtitle">Audio Levels</div>
            </div>
            <div class="studio-audio-mixer">
                <!-- Kanał Mic -->
                <div class="studio-audio-channel">
                    <div class="studio-audio-channel__name">Mic</div>
                    <input type="range" min="0" max="1" step="0.01" class="studio-audio-channel__slider" id="slider-mic" value="1.0">
                    <div class="studio-audio-channel__val" id="val-mic">100%</div>
                    <button class="studio-audio-channel__mute-btn" id="mute-mic">🔊</button>
                </div>
                <!-- Kanał BGM -->
                <div class="studio-audio-channel">
                    <div class="studio-audio-channel__name">BGM</div>
                    <input type="range" min="0" max="1" step="0.01" class="studio-audio-channel__slider" id="slider-bgm" value="0.5">
                    <div class="studio-audio-channel__val" id="val-bgm">50%</div>
                    <button class="studio-audio-channel__mute-btn" id="mute-bgm">🔊</button>
                </div>
                <!-- Kanał SFX -->
                <div class="studio-audio-channel">
                    <div class="studio-audio-channel__name">SFX</div>
                    <input type="range" min="0" max="1" step="0.01" class="studio-audio-channel__slider" id="slider-sfx" value="0.8">
                    <div class="studio-audio-channel__val" id="val-sfx">80%</div>
                    <button class="studio-audio-channel__mute-btn" id="mute-sfx">🔊</button>
                </div>
                <!-- Kanał Master -->
                <div class="studio-audio-channel" style="border-top: 1px solid rgba(139, 92, 246, 0.15); padding-top: 8px;">
                    <div class="studio-audio-channel__name" style="color: #d67d3e;">Master</div>
                    <input type="range" min="0" max="1" step="0.01" class="studio-audio-channel__slider" id="slider-master" value="1.0">
                    <div class="studio-audio-channel__val" id="val-master" style="color: #d67d3e;">100%</div>
                    <button class="studio-audio-channel__mute-btn" id="mute-master">🔊</button>
                </div>
            </div>
        </div>
 
        <!-- Sekcja 4: Aktywne Talie (Active Decks Selection) -->
        <div class="studio-card">
            <div class="studio-card__header">
                <div class="studio-card__title">Aktywne Talie (Active Decks)</div>
                <div class="studio-card__subtitle" id="studio-decks-count">Wybierz 1-3 talie</div>
            </div>
            <div class="studio-active-decks-status studio-active-decks-status--warning" id="studio-active-decks-status">
                Wybierz 1-3 talie przed kalibracją
            </div>
            <div class="studio-autotune-panel" id="studio-autotune-panel" data-state="idle">
                <div class="studio-autotune-header">
                    <span class="studio-autotune-title">Auto Tune</span>
                    <span class="studio-autotune-state" id="studio-autotune-state">IDLE</span>
                </div>
                <div class="studio-autotune-actions">
                    <button type="button" data-studio-action="autotune_start" data-scenario="empty">Pusta mata</button>
                    <button type="button" data-studio-action="autotune_start" data-scenario="one_card">1 karta</button>
                    <button type="button" data-studio-action="autotune_start" data-scenario="three_cards">3 karty</button>
                    <button type="button" data-studio-action="autotune_apply">Apply</button>
                    <button type="button" data-studio-action="autotune_cancel">Cancel</button>
                </div>
                <div class="studio-autotune-result" id="studio-autotune-result">Brak rekomendacji.</div>
            </div>
            <div class="studio-decks-list" id="studio-decks-list" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;">
                <div style="font-size: 11px; color: rgba(255,255,255,0.4); text-align: center; padding: 8px;">Ładowanie listy talii...</div>
            </div>
            <button class="studio-btn-action" id="studio-decks-apply-btn" style="width: 100%; justify-content: center; height: 32px;" disabled>
                Zastosuj Wybór (Apply)
            </button>
        </div>

        <!-- Sekcja 5: Diagnostyka CV -->
        <div class="studio-card">
            <div class="studio-card__header">
                <div class="studio-card__title">Diagnostyka CV Health</div>
                <div class="studio-card__subtitle">Engine status</div>
            </div>
            <div class="studio-cv-grid">
                <div class="studio-cv-item">
                    <span class="studio-cv-item__label">FPS:</span>
                    <span class="studio-cv-item__value" id="cv-fps-val">0.0</span>
                </div>
                <div class="studio-cv-item">
                    <span class="studio-cv-item__label">Cards:</span>
                    <span class="studio-cv-item__value" id="cv-cards-val">0</span>
                </div>
                <div class="studio-cv-item">
                    <span class="studio-cv-item__label">Stable Ms:</span>
                    <span class="studio-cv-item__value" id="cv-stable-val">0</span>
                </div>
                <div class="studio-cv-item">
                    <span class="studio-cv-item__label">Snapshot:</span>
                    <span class="studio-cv-item__value" id="cv-snap-val">holding</span>
                </div>
            </div>
            <div class="studio-cv-warning-box" id="cv-warning-box" style="display: none; margin-top: 10px;">
                <span class="studio-cv-warning-title">⚠️ Ostrzeżenie CV</span>
                <span class="studio-cv-warning-text" id="cv-warning-text"></span>
            </div>
            <div class="studio-cv-explain-panel" id="studio-cv-explain-panel" data-severity="wait">
                <div class="studio-cv-explain-header">
                    <span class="studio-cv-explain-title">CV Explain</span>
                    <span class="studio-cv-explain-badge studio-cv-explain-badge--wait" id="studio-cv-explain-badge">WAIT</span>
                </div>
                <div class="studio-cv-explain-steps" id="studio-cv-explain-steps"></div>
                <div class="studio-cv-explain-next-box">
                    <span class="studio-cv-explain-next-label">Następny krok</span>
                    <span class="studio-cv-explain-next" id="studio-cv-explain-next">Czekam na dane CV.</span>
                </div>
            </div>
        </div>
    `
    hudContainer.appendChild(sidebar)
    sidebarEl = sidebar

    // 7. Stwórz dolny pasek transportu (Bottombar)
    const bottombar = document.createElement('div')
    bottombar.className = 'studio-bottombar'
    bottombar.innerHTML = `
        <div class="studio-transport-group">
            <button class="studio-btn-transport" id="btn-studio-rec" disabled title="Nagrywanie niedostępne w tej wersji (Oczekuje na integrację)">
                <span class="indicator-rec" style="display:none;"></span>
                <span>ARM RECORDING</span>
            </button>
            <button class="studio-btn-transport" id="btn-studio-marker" disabled title="Wymagane aktywne nagrywanie">
                <span>➕</span><span>ADD MARKER</span>
            </button>
        </div>
        
        <div class="studio-timeline-box" style="flex: 1; margin: 0 24px; padding: 6px 12px; background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(214, 125, 62, 0.25); border-radius: 6px; display: flex; flex-direction: column; justify-content: center; gap: 6px; min-width: 250px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: 500; color: #d67d3e; letter-spacing: 0.5px;">
                <span>STUDIO TIMELINE TRACKER</span>
                <span id="studio-timeline-counter" style="color: #cbd5e1;">0 markers</span>
            </div>
            <div class="studio-timeline-track" id="studio-timeline-track" style="height: 8px; background: rgba(30, 41, 59, 0.8); border-radius: 4px; position: relative; overflow: visible; border: 1px solid rgba(255,255,255,0.05);">
                <div class="studio-timeline-playhead" id="studio-timeline-playhead" style="position: absolute; left: 0%; top: -2px; width: 4px; height: 12px; background: #d67d3e; border-radius: 2px; transition: left 0.1s linear; display: none;"></div>
            </div>
            <div id="studio-timeline-latest-marker" style="font-size: 10px; color: rgba(255,255,255,0.4); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center; font-family: monospace;">Timeline idle</div>
        </div>

        <div class="studio-transport-group">
            <button class="studio-btn-transport" id="btn-studio-intro" disabled title="Odtwarzanie intro niedostępne w tej wersji">
                <span>🎬</span><span>PLAY INTRO</span>
            </button>
            <button class="studio-btn-transport" id="btn-studio-outro" disabled title="Odtwarzanie outro niedostępne w tej wersji">
                <span>🏁</span><span>PLAY OUTRO</span>
            </button>
        </div>
    `
    hudContainer.appendChild(bottombar)
    bottombarEl = bottombar

    // Zainicjalizuj eventy
    initStudioConsoleEvents()
}

// Inicjalizacja nasłuchu na interakcje w Konsoli Studio
function initStudioConsoleEvents() {
    if (!sidebarEl) return

    // Inicjalizacja panelu aktywnych talii
    initStudioDecksPanel()

    // Automatyczna inicjalizacja mikrofonu i miksera audio w tle
    startStudioMicrophone().catch(err => console.warn('Deferred microphone authorization:', err))

    const operatorBtn = topbarEl ? topbarEl.querySelector('#btn-open-operator') : null
    if (operatorBtn) {
        operatorBtn.addEventListener('click', () => {
            window.open(`${window.location.origin}${window.location.pathname}?operator=1`, '_blank', 'noopener')
        })
    }

    const cameraProbeBtn = sidebarEl.querySelector('#studio-camera-probe-btn')
    if (cameraProbeBtn) {
        cameraProbeBtn.addEventListener('click', () => {
            sendControlMessage({ type: 'camera_probe' })
        })
    }

    const autotunePanel = sidebarEl.querySelector('#studio-autotune-panel')
    if (autotunePanel) {
        autotunePanel.addEventListener('click', (event) => {
            const button = event.target.closest('[data-studio-action]')
            if (!button) return
            const action = button.dataset.studioAction
            if (action === 'autotune_start') {
                sendControlMessage({
                    type: 'autotune_start',
                    scenario: button.dataset.scenario || 'empty'
                })
                return
            }
            if (action === 'autotune_apply' || action === 'autotune_cancel') {
                sendControlMessage({ type: action })
            }
        })
    }

    const cameraControls = sidebarEl.querySelector('#studio-camera-controls')
    if (cameraControls) {
        cameraControls.addEventListener('input', (event) => {
            const input = event.target
            if (!(input instanceof HTMLInputElement)) return
            if (!input.dataset.cameraParam) return
            if (input.dataset.cameraRole === 'number' && input.value === '') return
            applyStudioCameraControlValue(input, input.value)
        })
        cameraControls.addEventListener('change', (event) => {
            const input = event.target
            if (!(input instanceof HTMLInputElement)) return
            const cameraParam = input.dataset.cameraParam
            if (!cameraParam) return
            applyStudioCameraControlValue(input, input.value, true)
        })
        cameraControls.addEventListener('click', (event) => {
            const button = event.target
            if (!(button instanceof HTMLButtonElement)) return
            const direction = Number(button.dataset.cameraStepDirection)
            if (!Number.isFinite(direction)) return

            const control = button.closest('.studio-camera-control')
            const input = control?.querySelector('input[data-camera-role="range"]')
            if (!(input instanceof HTMLInputElement)) return

            const step = Number(input.step || '1')
            const nextValue = Number(input.value) + direction * (Number.isFinite(step) ? step : 1)
            applyStudioCameraControlValue(input, nextValue, true)
        })
    }

    // 1. Zmiana katalogu zapisu (Wysyła komendę konfiguracji zapisu)
    const pathBtn = sidebarEl.querySelector('#studio-path-btn')
    const pathInput = sidebarEl.querySelector('#studio-path-input')
    const pathStatus = sidebarEl.querySelector('#studio-path-status')
    if (pathBtn && pathInput) {
        pathBtn.addEventListener('click', () => {
            const path = pathInput.value.trim()
            if (!path) {
                pathStatus.textContent = "Stan: Ścieżka nie może być pusta!"
                pathStatus.style.color = "#f87171"
                return
            }
            // Wyślij control message na backend (Obsługa w Task Studio Console 2)
            sendControlMessage({
                type: "studio_set_recording_dir",
                path: path
            })
            pathStatus.textContent = "Stan: Weryfikacja..."
            pathStatus.style.color = "#a78bfa"
        })
    }

    // 2. Zmiana Scen Reżysera i trybu Auto/Manual
    const sceneButtons = sidebarEl.querySelectorAll('.studio-scene-btn')
    sceneButtons.forEach(btn => {
        if (btn.disabled) return
        btn.addEventListener('click', () => {
            const scene = btn.getAttribute('data-scene')
            
            if (scene === 'auto') {
                // Włączenie trybu automatycznego
                sendControlMessage({
                    type: "studio_set_director_mode",
                    mode: "auto"
                })
            } else {
                // Wyłączenie trybu automatycznego (nadpisanie ręczne)
                if (studioState.directorMode === 'auto') {
                    sendControlMessage({
                        type: "studio_set_director_mode",
                        mode: "manual"
                    })
                }
                
                studioState.activeScene = scene
                
                // Specjalna interakcja: Jeśli kliknięto WOW, włączamy WOW mode we frontendzie
                if (scene === 'wow') {
                    appState.wowMode = true
                    document.body.classList.add('wow-mode-active')
                } else if (scene === 'table') {
                    appState.wowMode = false
                    document.body.classList.remove('wow-mode-active')
                }
                
                // Dodajemy marker zmiany sceny
                if (studioState.recordingState === 'recording') {
                    addTimelineMarker('scene_changed', { scene: scene, mode: 'manual' })
                }

                // Wysyłamy zmianę sceny na backend
                sendControlMessage({
                    type: "studio_set_director_scene",
                    scene: scene
                })
            }
        })
    })

    // 3. Obsługa Miksera Audio (wysyła komendy WebSocket na backend)
    const channels = ['mic', 'bgm', 'sfx', 'master']
    channels.forEach(ch => {
        const slider = sidebarEl.querySelector(`#slider-${ch}`)
        const valLabel = sidebarEl.querySelector(`#val-${ch}`)
        const muteBtn = sidebarEl.querySelector(`#mute-${ch}`)

        if (slider && valLabel) {
            slider.addEventListener('input', () => {
                const val = parseFloat(slider.value)
                valLabel.textContent = `${Math.round(val * 100)}%`
                
                sendControlMessage({
                    type: "studio_set_audio_volume",
                    channel: ch,
                    volume: val
                })
            })
        }

        if (muteBtn) {
            muteBtn.addEventListener('click', () => {
                const muted = !studioState[`${ch}Muted`]
                
                sendControlMessage({
                    type: "studio_set_audio_mute",
                    channel: ch,
                    muted: muted
                })
            })
        }
    })

    // 3b. Obsługa przycisku markera ręcznego
    const markerBtn = bottombarEl ? bottombarEl.querySelector('#btn-studio-marker') : null
    if (markerBtn) {
        markerBtn.addEventListener('click', () => {
            if (studioState.recordingState === 'recording') {
                addTimelineMarker('operator_marker')
            }
        })
    }

    // 3c. Dynamiczne nasłuchiwanie i rysowanie osi czasu
    window.addEventListener('studio-timeline-update', (e) => {
        const { marker, markers } = e.detail
        const counter = bottombarEl ? bottombarEl.querySelector('#studio-timeline-counter') : null
        const latestLabel = bottombarEl ? bottombarEl.querySelector('#studio-timeline-latest-marker') : null
        const track = bottombarEl ? bottombarEl.querySelector('#studio-timeline-track') : null
        
        if (counter) {
            counter.textContent = `${markers.length} markers`
        }
        
        if (latestLabel) {
            latestLabel.textContent = `Latest: [${formatMsToTime(marker.timestamp_ms)}] ${marker.type.toUpperCase()}${marker.scene ? ' -> ' + marker.scene.toUpperCase() : ''}`
        }
        
        if (track) {
            if (marker.type === 'recording_started') {
                // Czyścimy stare kropki przy nowym nagraniu
                track.querySelectorAll('.studio-timeline-dot').forEach(el => el.remove())
            }
            
            if (marker.type !== 'recording_stopped') {
                const maxDuration = Math.max(30000, studioState.elapsedMs)
                const pct = (marker.timestamp_ms / maxDuration) * 100
                
                const dot = document.createElement('div')
                dot.className = 'studio-timeline-dot'
                dot.style.position = 'absolute'
                dot.style.left = `${Math.min(99, pct)}%`
                dot.style.top = '1px'
                dot.style.width = '6px'
                dot.style.height = '6px'
                dot.style.borderRadius = '50%'
                
                if (marker.type === 'recording_started') dot.style.background = '#10b981'
                else if (marker.type === 'scene_changed') dot.style.background = '#8b5cf6'
                else if (marker.type === 'card_revealed') dot.style.background = '#d67d3e'
                else if (marker.type === 'operator_marker') dot.style.background = '#ef4444'
                else dot.style.background = '#ffffff'
                
                dot.style.boxShadow = '0 0 6px rgba(255,255,255,0.8)'
                dot.title = `[${formatMsToTime(marker.timestamp_ms)}] ${marker.type}`
                track.appendChild(dot)
            }
        }
    })

    // 4. Obsługa przycisku nagrywania (ARM RECORDING / STOP RECORDING)
    const recBtn = bottombarEl ? bottombarEl.querySelector('#btn-studio-rec') : null
    if (recBtn) {
        recBtn.addEventListener('click', () => {
            if (studioState.recordingState === 'recording') {
                stopStudioRecording()
            } else {
                startStudioRecording()
            }
        })
    }
}

// Pomocnicza funkcja formatowania czasu
function formatTime(ms) {
    const totalSecs = Math.floor(ms / 1000)
    const secs = totalSecs % 60
    const mins = Math.floor(totalSecs / 60) % 60
    const hrs = Math.floor(totalSecs / 3600)
    
    return [hrs, mins, secs]
        .map(v => v < 10 ? "0" + v : v)
        .join(":")
}

function updateStudioCameraControls(supportedControls) {
    if (!sidebarEl) return
    const container = sidebarEl.querySelector('#studio-camera-controls')
    if (!container) return

    if (!supportedControls || Object.keys(supportedControls).length === 0) {
        container.textContent = 'Brak danych z kamery. Kliknij odczyt.'
        return
    }

    const existingInputs = container.querySelectorAll('input[data-camera-param]')
    if (existingInputs.length > 0) {
        Object.entries(supportedControls).forEach(([name, data]) => {
            if (data.readback_value === -1.0) return
            const control = container.querySelector(`.studio-camera-control[data-camera-control="${name}"]`)
            if (control && !control.contains(document.activeElement)) {
                const input = control.querySelector('input[data-camera-role="range"]')
                if (input) applyStudioCameraControlValue(input, data.readback_value)
            }
        })
        return
    }

    const html = Object.entries(supportedControls).map(([name, data]) => {
        if (data.readback_value === -1.0) return ''
        const range = studioCameraRanges[name] || { min: 0, max: 255, step: 1 }
        const label = studioCameraLabels[name] || name
        const value = formatCameraValue(clampCameraValue(data.readback_value, range), range.step)
        return `
            <label class="studio-camera-control" data-camera-control="${name}">
                <span title="${name}">${label}</span>
                <button type="button" class="studio-camera-step" data-camera-step-direction="-1" title="Zmniejsz o ${range.step}">-</button>
                <input
                    type="range"
                    min="${range.min}"
                    max="${range.max}"
                    step="${range.step}"
                    value="${value}"
                    data-camera-param="${name}"
                    data-camera-role="range"
                />
                <button type="button" class="studio-camera-step" data-camera-step-direction="1" title="Zwiększ o ${range.step}">+</button>
                <input
                    type="number"
                    min="${range.min}"
                    max="${range.max}"
                    step="${range.step}"
                    value="${value}"
                    data-camera-param="${name}"
                    data-camera-role="number"
                    aria-label="${label}: dokładna wartość"
                />
                <output>${value}</output>
            </label>
        `
    }).join('')

    container.innerHTML = html || 'Brak aktywnych sprzętowych funkcji kamery w tym systemie.'
}

// Funkcja aktualizująca UI Konsoli Studio nowym payloadem WebSocket
export function updateStudioConsole(data) {
    if (!appState.studioMode || !sidebarEl) return

    // 1. Zsynchronizuj status studia z payloadu
    updateStudioStateFromPayload(data.studio)

    const isRecording = studioState.recordingState === 'recording'

    // Zdarzenie card_revealed przy nagrywaniu
    if (isRecording) {
        const currentCards = data.cards || []
        const currentCardNames = currentCards.map(c => c.name || c).sort().join(',')
        const prevCardNames = previousCards.map(c => c.name || c).sort().join(',')
        
        if (currentCardNames !== prevCardNames && currentCards.length > previousCards.length) {
            // Dodano kartę - zarejestruj marker na osi czasu
            const newCards = currentCards.filter(c => !previousCards.some(pc => (pc.name || pc) === (c.name || c)))
            newCards.forEach(c => {
                addTimelineMarker('card_revealed', { card: c.name || c })
            })
        }
    }
    previousCards = data.cards || []

    // Decyzje automatycznego reżysera
    if (studioState.directorMode === 'auto') {
        processDirectorDecision(data)
    }

    // Synchronizacja wizualna Segmented Control (przyciski scen i auto)
    const sceneButtons = sidebarEl.querySelectorAll('.studio-scene-btn')
    sceneButtons.forEach(btn => {
        const scene = btn.getAttribute('data-scene')
        
        if (studioState.directorMode === 'auto') {
            if (scene === 'auto') {
                btn.classList.add('studio-scene-btn--active')
            } else {
                btn.classList.remove('studio-scene-btn--active')
                // Jeśli to scena wybrana aktualnie przez automat, nadajemy specjalną ramkę
                if (scene === studioState.activeScene) {
                    btn.classList.add('studio-scene-btn--auto-active')
                } else {
                    btn.classList.remove('studio-scene-btn--auto-active')
                }
            }
        } else {
            // Tryb manualny
            if (scene === 'auto') {
                btn.classList.remove('studio-scene-btn--active')
            } else {
                btn.classList.remove('studio-scene-btn--auto-active')
                if (scene === studioState.activeScene) {
                    btn.classList.add('studio-scene-btn--active')
                } else {
                    btn.classList.remove('studio-scene-btn--active')
                }
            }
        }
    })

    // 1b. Synchronizacja suwaków i wyciszeń Miksera Audio z WebSocketu
    const audioChannels = ['mic', 'bgm', 'sfx', 'master']
    audioChannels.forEach(ch => {
        const slider = sidebarEl.querySelector(`#slider-${ch}`)
        const valLabel = sidebarEl.querySelector(`#val-${ch}`)
        const muteBtn = sidebarEl.querySelector(`#mute-${ch}`)
        
        const vol = studioState[`${ch}Volume`]
        const muted = studioState[`${ch}Muted`]
        
        // Zaktualizuj suwak tylko gdy operator go nie przeciąga
        if (slider && document.activeElement !== slider) {
            slider.value = vol.toString()
        }
        if (valLabel) {
            valLabel.textContent = `${Math.round(vol * 100)}%`
        }
        if (muteBtn) {
            if (muted) {
                muteBtn.textContent = '🔇'
                muteBtn.classList.add('studio-audio-channel__mute-btn--muted')
            } else {
                muteBtn.textContent = '🔊'
                muteBtn.classList.remove('studio-audio-channel__mute-btn--muted')
            }
        }
    })
    saveStudioVolumeSettings()
    updateAudioMixerValues()
    updateStudioCameraControls(data.operator?.supported_camera_controls)

    // 2. Górny Topbar statusu systemowego
    const wsInd = topbarEl.querySelector('#indicator-ws')
    if (wsInd) {
        const isConnected = appState.controlSocket !== null && appState.controlSocket.readyState === WebSocket.OPEN
        wsInd.classList.toggle('studio-indicator--active', isConnected)
    }

    const cvInd = topbarEl.querySelector('#indicator-cv')
    if (cvInd) {
        const cvOk = data.detected || (data.layout && data.layout.state !== 'no_camera')
        cvInd.classList.toggle('studio-indicator--active', !!cvOk)
    }

    const camInd = topbarEl.querySelector('#indicator-cam')
    if (camInd) {
        const camActive = data.runtime && data.runtime.camera_index !== undefined
        camInd.classList.toggle('studio-indicator--active', !!camActive)
    }

    const audioInd = topbarEl.querySelector('#indicator-audio')
    if (audioInd) {
        // Zintegrowane z offline stanem miksera audio
        const audioActive = !studioState.masterMuted && studioState.masterVolume > 0
        audioInd.classList.toggle('studio-indicator--active', audioActive)
    }

    const recInd = topbarEl.querySelector('#indicator-rec')
    if (recInd) {
        recInd.classList.toggle('studio-indicator--rec', isRecording)
        recInd.classList.toggle('studio-indicator--active', isRecording)
    }

    // Weryfikacja ścieżki i status przycisku nagrywania w Bottombarze
    const recBtn = bottombarEl ? bottombarEl.querySelector('#btn-studio-rec') : null
    const recordingDirValid = data.studio && data.studio.recording_dir_status && data.studio.recording_dir_status.valid
    
    if (recBtn) {
        const recTextSpan = recBtn.querySelector('span:not(.indicator-rec)')
        const recIndicator = recBtn.querySelector('.indicator-rec')
        
        if (!recordingDirValid) {
            recBtn.setAttribute('disabled', 'true')
            recBtn.setAttribute('title', 'Wymagany poprawnie zweryfikowany katalog zapisu na backendzie')
            if (recTextSpan) recTextSpan.textContent = 'ARM RECORDING'
            if (recIndicator) recIndicator.style.display = 'none'
            recBtn.classList.remove('studio-btn-transport--rec')
            recBtn.classList.remove('studio-btn-transport--stopping')
        } else {
            recBtn.removeAttribute('disabled')
            recBtn.removeAttribute('title')
            
            if (studioState.recordingState === 'recording') {
                recBtn.classList.add('studio-btn-transport--rec')
                recBtn.classList.remove('studio-btn-transport--stopping')
                if (recTextSpan) recTextSpan.textContent = 'STOP RECORDING'
                if (recIndicator) recIndicator.style.display = 'inline-block'
            } else if (studioState.recordingState === 'stopping') {
                recBtn.setAttribute('disabled', 'true')
                recBtn.classList.remove('studio-btn-transport--rec')
                recBtn.classList.add('studio-btn-transport--stopping')
                if (recTextSpan) recTextSpan.textContent = 'SAVING...'
                if (recIndicator) recIndicator.style.display = 'none'
            } else {
                recBtn.classList.remove('studio-btn-transport--rec')
                recBtn.classList.remove('studio-btn-transport--stopping')
                if (recTextSpan) recTextSpan.textContent = 'START RECORDING'
                if (recIndicator) recIndicator.style.display = 'none'
            }
        }
    }

    // Aktualizacja statusu przycisku markera i playheadu osi czasu
    const markerBtn = bottombarEl ? bottombarEl.querySelector('#btn-studio-marker') : null
    const playhead = bottombarEl ? bottombarEl.querySelector('#studio-timeline-playhead') : null
    
    if (markerBtn) {
        if (isRecording) {
            markerBtn.removeAttribute('disabled')
            markerBtn.removeAttribute('title')
        } else {
            markerBtn.setAttribute('disabled', 'true')
            markerBtn.setAttribute('title', 'Wymagane aktywne nagrywanie')
        }
    }
    
    if (playhead) {
        if (isRecording) {
            playhead.style.display = 'block'
            const maxDuration = Math.max(30000, studioState.elapsedMs)
            const pct = (studioState.elapsedMs / maxDuration) * 100
            playhead.style.left = `${Math.min(99.5, pct)}%`
        } else {
            playhead.style.display = 'none'
            const counter = bottombarEl ? bottombarEl.querySelector('#studio-timeline-counter') : null
            const latestLabel = bottombarEl ? bottombarEl.querySelector('#studio-timeline-latest-marker') : null
            if (counter && studioState.recordingState === 'idle') {
                counter.textContent = '0 markers'
            }
            if (latestLabel && studioState.recordingState === 'idle') {
                latestLabel.textContent = 'Timeline idle'
            }
        }
    }

    // 3. Sekcja Nagrywanie w Sidebarze
    const recStateLabel = sidebarEl.querySelector('#studio-rec-state')
    if (recStateLabel) {
        recStateLabel.textContent = studioState.recordingState.toUpperCase()
        recStateLabel.style.color = isRecording ? '#f87171' : '#94a3b8'
    }

    const timeVal = sidebarEl.querySelector('#studio-time-val')
    if (timeVal) {
        timeVal.textContent = formatTime(studioState.elapsedMs)
    }

    const droppedVal = sidebarEl.querySelector('#studio-dropped-val')
    if (droppedVal) {
        droppedVal.textContent = studioState.droppedFrames.toString()
    }

    // Aktualizacja statusu ścieżki zapisu w UI
    const pathStatus = sidebarEl.querySelector('#studio-path-status')
    if (pathStatus && data.studio && data.studio.recording_dir_status) {
        const status = data.studio.recording_dir_status
        pathStatus.textContent = `Stan: ${status.message}`
        pathStatus.style.color = status.valid ? "#34d399" : "#f87171"
        
        // Zaktualizujmy wartość inputu tylko gdy nie ma focusa
        const pathInput = sidebarEl.querySelector('#studio-path-input')
        if (pathInput && document.activeElement !== pathInput && status.path) {
            pathInput.value = status.path
        }
    }

    // 4. Diagnostyka CV Health
    const cvFps = sidebarEl.querySelector('#cv-fps-val')
    if (cvFps && data.metrics && data.metrics.fps !== undefined) {
        cvFps.textContent = parseFloat(data.metrics.fps).toFixed(1)
    }

    const cvCards = sidebarEl.querySelector('#cv-cards-val')
    if (cvCards && data.cards) {
        cvCards.textContent = data.cards.length.toString()
    }

    const cvStable = sidebarEl.querySelector('#cv-stable-val')
    if (cvStable && data.layout && data.layout.stable_for_ms !== undefined) {
        cvStable.textContent = data.layout.stable_for_ms.toString()
    }

    const cvSnap = sidebarEl.querySelector('#cv-snap-val')
    if (cvSnap && data.layout && data.layout.state !== undefined) {
        cvSnap.textContent = data.layout.state
    }

    renderCvExplainability(data)
    renderStudioAutotune(data)

    // 4b. Ostrzeżenia operatora w Studio HUD
    const cvWarningBox = sidebarEl.querySelector('#cv-warning-box')
    const cvWarningText = sidebarEl.querySelector('#cv-warning-text')
    if (cvWarningBox && cvWarningText) {
        if (data.warnings && data.warnings.length > 0) {
            const lastWarning = data.warnings[data.warnings.length - 1]
            cvWarningText.textContent = lastWarning
            cvWarningBox.style.display = 'block'
        } else {
            cvWarningText.textContent = ''
            cvWarningBox.style.display = 'none'
        }
    }

    // 5. Synchronizacja stanu aktywnych talii z WebSocketu (data.operator.active_decks)
    if (data.operator && data.operator.active_decks) {
        const remoteDecks = data.operator.active_decks
        const equals = remoteDecks.length === activeDecksState.length &&
                       remoteDecks.every(id => activeDecksState.includes(id))
        
        if (!equals) {
            activeDecksState = [...remoteDecks]
            updateStudioActiveDecksStatus(activeDecksState)
            
            // Asynchroniczne doładowanie tekstur w locie do cache w silniku 3D Three.js
            import('../renderer/textureCache').then(module => {
                module.dynamicPreloadDecks(activeDecksState)
            })
            
            // Reaktywna aktualizacja zaznaczenia bez burzenia DOM
            if (sidebarEl) {
                const listEl = sidebarEl.querySelector('#studio-decks-list')
                const checkboxes = listEl ? listEl.querySelectorAll('.studio-deck-checkbox') : []
                if (checkboxes.length > 0) {
                    checkboxes.forEach(cb => {
                        const deckId = cb.getAttribute('data-deck-id')
                        const isChecked = activeDecksState.includes(deckId)
                        cb.checked = isChecked
                    })
                }
            }
        }

        // Zabezpieczenie Apply: jeśli oczekujemy na wdrożenie, sprawdzamy czy stan się zgadza z żądaniem
        if (isDecksApplying && sidebarEl) {
            const listEl = sidebarEl.querySelector('#studio-decks-list')
            const checkboxes = listEl ? listEl.querySelectorAll('.studio-deck-checkbox') : []
            if (checkboxes.length > 0) {
                const checkedIds = Array.from(checkboxes).filter(c => c.checked).map(c => c.getAttribute('data-deck-id'))
                const matchesRequest = remoteDecks.length === checkedIds.length &&
                                       remoteDecks.every(id => checkedIds.includes(id))
                
                if (matchesRequest) {
                    isDecksApplying = false
                    const applyBtn = sidebarEl.querySelector('#studio-decks-apply-btn')
                    if (applyBtn) {
                        applyBtn.textContent = 'Zastosuj Wybór (Apply)'
                        applyBtn.setAttribute('disabled', 'true')
                    }
                    
                    // Przywracamy limity dla checkboxów i je odblokowujemy
                    const count = checkedIds.length
                    checkboxes.forEach(c => {
                        c.disabled = false
                        if (count >= 3 && !c.checked) c.disabled = true
                        if (count <= 1 && c.checked) c.disabled = true
                    })
                }
            }
        } else if (!isDecksApplying && sidebarEl) {
            // Standardowa aktualizacja checkboxów gdy nie trwa proces Apply
            const listEl = sidebarEl.querySelector('#studio-decks-list')
            const checkboxes = listEl ? listEl.querySelectorAll('.studio-deck-checkbox') : []
            if (checkboxes.length > 0) {
                const checkedBoxes = Array.from(checkboxes).filter(c => c.checked)
                const count = checkedBoxes.length
                checkboxes.forEach(c => {
                    c.disabled = false
                    if (count >= 3 && !c.checked) c.disabled = true
                    if (count <= 1 && c.checked) c.disabled = true
                })
            }
        }
    }
}
