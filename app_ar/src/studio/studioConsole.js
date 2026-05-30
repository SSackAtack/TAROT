import { appState } from '../core/appState'
import { studioState, updateStudioStateFromPayload, saveStudioVolumeSettings } from './studioState'
import { sendControlMessage } from '../transport/wsClient'
import { startStudioRecording, stopStudioRecording } from './mediaRecorderController'
import { startStudioMicrophone, updateAudioMixerValues } from './audioMixer'

// Globalne referencje do elementów DOM konsoli
let sidebarEl = null
let topbarEl = null
let bottombarEl = null

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
        <div class="studio-preview-label">LIVE FEED COMPOSITOR</div>
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
                <button class="studio-scene-btn" data-scene="auto" style="grid-column: 1 / -1; margin-top: 4px;" disabled title="Automatyczny reżyser niedostępny w tej wersji">
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
                    <div class="studio-audio-channel__name" style="color: #ffd700;">Master</div>
                    <input type="range" min="0" max="1" step="0.01" class="studio-audio-channel__slider" id="slider-master" value="1.0">
                    <div class="studio-audio-channel__val" id="val-master" style="color: #ffd700;">100%</div>
                    <button class="studio-audio-channel__mute-btn" id="mute-master">🔊</button>
                </div>
            </div>
        </div>

        <!-- Sekcja 4: Diagnostyka CV -->
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
            <button class="studio-btn-transport" id="btn-studio-marker" disabled title="Dodawanie markerów niedostępne w tej wersji">
                <span>➕</span><span>ADD TIMELINE MARKER</span>
            </button>
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

    // Automatyczna inicjalizacja mikrofonu i miksera audio w tle
    startStudioMicrophone().catch(err => console.warn('Deferred microphone authorization:', err))

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

    // 2. Zmiana Scen Reżysera (Tylko sceny stołowe i WOW są aktywne lokalnie)
    const sceneButtons = sidebarEl.querySelectorAll('.studio-scene-btn')
    sceneButtons.forEach(btn => {
        if (btn.disabled) return
        btn.addEventListener('click', () => {
            sceneButtons.forEach(b => b.classList.remove('studio-scene-btn--active'))
            btn.classList.add('studio-scene-btn--active')
            
            const scene = btn.getAttribute('data-scene')
            studioState.activeScene = scene

            // Specjalna interakcja: Jeśli kliknięto WOW, włączamy WOW mode we frontendzie
            if (scene === 'wow') {
                appState.wowMode = true
                document.body.classList.add('wow-mode-active')
            } else if (scene === 'table') {
                appState.wowMode = false
                document.body.classList.remove('wow-mode-active')
            }

            // Wysyłamy wiadomość reżysera na backend (kontrakt)
            sendControlMessage({
                type: "studio_set_director_scene",
                scene: scene
            })
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

// Funkcja aktualizująca UI Konsoli Studio nowym payloadem WebSocket
export function updateStudioConsole(data) {
    if (!appState.studioMode || !sidebarEl) return

    // 1. Zsynchronizuj status studia z payloadu
    updateStudioStateFromPayload(data.studio)

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
    const isRecording = studioState.recordingState === 'recording'
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
}
