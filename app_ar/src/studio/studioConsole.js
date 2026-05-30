import { appState } from '../core/appState'
import { studioState, updateStudioStateFromPayload, saveStudioVolumeSettings } from './studioState'
import { sendControlMessage } from '../transport/wsClient'

// Dynamiczne wstrzyknięcie styli CSS dla premium Konsoli Studio
function injectStudioStyles() {
    if (document.getElementById('studio-styles')) return

    const style = document.createElement('style')
    style.id = 'studio-styles'
    style.innerHTML = `
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Share+Tech+Mono&display=swap');

        /* Reset i tło dla trybu Studio */
        body.studio-mode-active {
            background: radial-gradient(circle at 30% 30%, #0c0817 0%, #030206 100%) !important;
            font-family: 'Outfit', sans-serif;
            color: #f1f5f9;
        }

        /* Główny kontener HUD */
        .studio-hud {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            display: grid;
            grid-template-rows: 60px 1fr 70px;
            grid-template-columns: 1fr 380px;
            z-index: 9999;
            box-sizing: border-box;
        }

        .studio-hud * {
            pointer-events: auto;
            box-sizing: border-box;
        }

        /* Górny pasek statusu */
        .studio-topbar {
            grid-column: 1 / -1;
            background: linear-gradient(to bottom, rgba(8, 5, 18, 0.95) 0%, rgba(8, 5, 18, 0.7) 100%);
            border-bottom: 1px solid rgba(139, 92, 246, 0.25);
            backdrop-filter: blur(12px);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }

        .studio-logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .studio-logo__indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #8b5cf6;
            box-shadow: 0 0 10px #8b5cf6;
            animation: pulse-purple 2s infinite alternate;
        }

        .studio-logo__text {
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.05em;
            background: linear-gradient(135deg, #fff 0%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .studio-logo__badge {
            font-family: 'Share Tech Mono', monospace;
            background: rgba(139, 92, 246, 0.2);
            border: 1px solid rgba(139, 92, 246, 0.4);
            color: #c4b5fd;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .studio-indicators {
            display: flex;
            gap: 16px;
        }

        .studio-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.15);
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            color: #94a3b8;
        }

        .studio-indicator--active {
            color: #38bdf8;
            border-color: rgba(56, 189, 248, 0.35);
            background: rgba(56, 189, 248, 0.05);
        }

        .studio-indicator--active .dot {
            background-color: #38bdf8;
            box-shadow: 0 0 8px #38bdf8;
        }

        .studio-indicator--rec {
            color: #f87171;
            border-color: rgba(248, 113, 113, 0.4);
            background: rgba(248, 113, 113, 0.08);
            animation: pulse-red-border 1.5s infinite alternate;
        }

        .studio-indicator--rec .dot {
            background-color: #f87171;
            box-shadow: 0 0 10px #f87171;
            animation: blink-red 1s infinite steps(2);
        }

        .studio-indicator .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #475569;
        }

        /* Safe Guides (Overlay Preview) */
        .studio-preview-overlay {
            grid-row: 2 / 3;
            grid-column: 1 / 2;
            position: relative;
            pointer-events: none;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .studio-safe-guides {
            width: 85%;
            height: 80%;
            border: 1px dashed rgba(139, 92, 246, 0.15);
            position: relative;
        }

        /* Narożniki Safe Guides */
        .studio-safe-guides::before, .studio-safe-guides::after,
        .studio-safe-guides-inner::before, .studio-safe-guides-inner::after {
            content: "";
            position: absolute;
            width: 24px;
            height: 24px;
            border-color: rgba(167, 139, 250, 0.45);
            border-style: solid;
        }

        /* Top Left Corner */
        .studio-safe-guides::before {
            top: -2px; left: -2px; border-width: 2px 0 0 2px;
        }
        /* Top Right Corner */
        .studio-safe-guides::after {
            top: -2px; right: -2px; border-width: 2px 2px 0 0;
        }

        .studio-safe-guides-inner {
            position: absolute;
            top: 5%; left: 5%; width: 90%; height: 90%;
            border: 1px dashed rgba(56, 189, 248, 0.1);
        }

        /* Bottom Left Corner */
        .studio-safe-guides-inner::before {
            bottom: -2px; left: -2px; border-width: 0 0 2px 2px;
        }
        /* Bottom Right Corner */
        .studio-safe-guides-inner::after {
            bottom: -2px; right: -2px; border-width: 0 2px 2px 0;
        }

        .studio-preview-label {
            position: absolute;
            top: 24px;
            left: 24px;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(139, 92, 246, 0.3);
            backdrop-filter: blur(8px);
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 11px;
            font-family: 'Share Tech Mono', monospace;
            color: #c4b5fd;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        /* Prawy pasek boczny (Sidebar) */
        .studio-sidebar {
            grid-row: 2 / 3;
            grid-column: 2 / 3;
            background: rgba(10, 6, 22, 0.82);
            border-left: 1px solid rgba(139, 92, 246, 0.25);
            backdrop-filter: blur(20px);
            display: flex;
            flex-direction: column;
            padding: 20px;
            gap: 20px;
            overflow-y: auto;
            box-shadow: -10px 0 30px rgba(0, 0, 0, 0.5);
        }

        .studio-card {
            background: rgba(20, 15, 38, 0.65);
            border: 1px solid rgba(139, 92, 246, 0.18);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            box-shadow: inset 0 0 15px rgba(139, 92, 246, 0.05);
            transition: all 0.3s ease;
        }

        .studio-card:hover {
            border-color: rgba(139, 92, 246, 0.3);
            box-shadow: inset 0 0 20px rgba(139, 92, 246, 0.08), 0 4px 12px rgba(0,0,0,0.25);
        }

        .studio-card__header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(139, 92, 246, 0.15);
            padding-bottom: 8px;
        }

        .studio-card__title {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #a78bfa;
        }

        .studio-card__subtitle {
            font-family: 'Share Tech Mono', monospace;
            font-size: 11px;
            color: #94a3b8;
        }

        /* Sekcja nagrywania */
        .studio-rec-info {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }

        .studio-rec-item {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(148, 163, 184, 0.1);
            padding: 8px;
            border-radius: 6px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .studio-rec-item__label {
            font-size: 10px;
            color: #94a3b8;
            text-transform: uppercase;
        }

        .studio-rec-item__value {
            font-family: 'Share Tech Mono', monospace;
            font-size: 14px;
            font-weight: 600;
            color: #f1f5f9;
        }

        .studio-rec-item__value--time {
            font-size: 16px;
            color: #38bdf8;
        }

        /* Ścieżka zapisu */
        .studio-path-box {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .studio-path-input-group {
            display: flex;
            gap: 8px;
        }

        .studio-path-input {
            flex: 1;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 6px;
            padding: 6px 10px;
            color: #f1f5f9;
            font-family: 'Share Tech Mono', monospace;
            font-size: 11px;
            outline: none;
            transition: all 0.3s ease;
        }

        .studio-path-input:focus {
            border-color: #8b5cf6;
            box-shadow: 0 0 8px rgba(139, 92, 246, 0.3);
        }

        .studio-btn-action {
            background: rgba(139, 92, 246, 0.25);
            border: 1px solid rgba(139, 92, 246, 0.4);
            color: #c4b5fd;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .studio-btn-action:hover {
            background: rgba(139, 92, 246, 0.4);
            color: #fff;
        }

        .studio-path-status {
            font-size: 10px;
            font-weight: 600;
            color: #94a3b8;
        }

        /* Sekcja wyboru scen (Director) */
        .studio-scenes-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }

        .studio-scene-btn {
            background: rgba(30, 25, 55, 0.6);
            border: 1px solid rgba(139, 92, 246, 0.2);
            color: #cbd5e1;
            padding: 10px 8px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .studio-scene-btn:hover {
            background: rgba(139, 92, 246, 0.15);
            border-color: rgba(139, 92, 246, 0.4);
            color: #fff;
            transform: translateY(-1px);
        }

        .studio-scene-btn--active {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.8) 0%, rgba(109, 40, 217, 0.8) 100%);
            border-color: #a78bfa;
            color: #fff;
            box-shadow: 0 0 12px rgba(139, 92, 246, 0.4);
            font-weight: 700;
        }

        .studio-scene-btn .icon {
            font-size: 16px;
        }

        /* Mikser Audio */
        .studio-audio-mixer {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .studio-audio-channel {
            display: grid;
            grid-template-columns: 60px 1fr 40px 32px;
            align-items: center;
            gap: 10px;
        }

        .studio-audio-channel__name {
            font-size: 11px;
            font-weight: 600;
            color: #cbd5e1;
            text-transform: uppercase;
        }

        .studio-audio-channel__slider {
            -webkit-appearance: none;
            width: 100%;
            height: 4px;
            border-radius: 2px;
            background: rgba(139, 92, 246, 0.2);
            outline: none;
        }

        .studio-audio-channel__slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #a78bfa;
            cursor: pointer;
            box-shadow: 0 0 5px #a78bfa;
            transition: transform 0.1s ease;
        }

        .studio-audio-channel__slider::-webkit-slider-thumb:hover {
            transform: scale(1.3);
        }

        .studio-audio-channel__val {
            font-family: 'Share Tech Mono', monospace;
            font-size: 11px;
            color: #94a3b8;
            text-align: right;
        }

        .studio-audio-channel__mute-btn {
            background: transparent;
            border: none;
            color: #64748b;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0;
            transition: color 0.2s ease;
        }

        .studio-audio-channel__mute-btn:hover {
            color: #ffd700;
        }

        .studio-audio-channel__mute-btn--muted {
            color: #ef4444 !important;
            text-shadow: 0 0 5px rgba(239, 68, 68, 0.5);
        }

        /* CV Health */
        .studio-cv-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px 16px;
        }

        .studio-cv-item {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
        }

        .studio-cv-item__label {
            color: #94a3b8;
        }

        .studio-cv-item__value {
            font-family: 'Share Tech Mono', monospace;
            color: #cbd5e1;
            font-weight: 600;
        }

        /* Dolny panel transportu (Bottombar) */
        .studio-bottombar {
            grid-row: 3 / 4;
            grid-column: 1 / -1;
            background: linear-gradient(to top, rgba(8, 5, 18, 0.95) 0%, rgba(8, 5, 18, 0.75) 100%);
            border-top: 1px solid rgba(139, 92, 246, 0.25);
            backdrop-filter: blur(12px);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.4);
        }

        .studio-transport-group {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .studio-btn-transport {
            height: 38px;
            background: rgba(30, 20, 50, 0.7);
            border: 1px solid rgba(139, 92, 246, 0.35);
            color: #cbd5e1;
            border-radius: 8px;
            padding: 0 16px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.25s ease;
        }

        .studio-btn-transport:hover {
            background: rgba(139, 92, 246, 0.18);
            border-color: #8b5cf6;
            color: #fff;
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.2);
        }

        .studio-btn-transport--rec {
            background: linear-gradient(135deg, #ef4444 0%, #991b1b 100%);
            border-color: #f87171;
            color: #fff;
            font-weight: 700;
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
            animation: pulse-red-shadow 2s infinite ease-in-out;
        }

        .studio-btn-transport--rec:hover {
            background: linear-gradient(135deg, #f87171 0%, #b91c1c 100%);
            border-color: #fff;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
        }

        .studio-btn-transport .indicator-rec {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #fff;
            box-shadow: 0 0 5px #fff;
            animation: blink-rec-dot 1s infinite alternate;
        }

        /* Animacje */
        @keyframes pulse-purple {
            0% { transform: scale(1.0); opacity: 0.7; box-shadow: 0 0 5px #8b5cf6; }
            100% { transform: scale(1.2); opacity: 1.0; box-shadow: 0 0 12px #a78bfa; }
        }

        @keyframes pulse-red-border {
            0% { border-color: rgba(248, 113, 113, 0.3); }
            100% { border-color: rgba(248, 113, 113, 0.75); }
        }

        @keyframes pulse-red-shadow {
            0% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.3); }
            50% { box-shadow: 0 0 22px rgba(239, 68, 68, 0.7); }
            100% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.3); }
        }

        @keyframes blink-red {
            0% { opacity: 0.3; }
            100% { opacity: 1.0; }
        }

        @keyframes blink-rec-dot {
            0% { opacity: 0.2; }
            100% { opacity: 1.0; }
        }
    `
    document.head.appendChild(style)
}

// Globalne referencje do elementów DOM konsoli
let sidebarEl = null
let topbarEl = null
let bottombarEl = null

export function createStudioConsole() {
    if (!appState.studioMode) return

    // 1. Aktywuj klasę trybu studio w body i wstrzyknij style
    document.body.classList.add('studio-mode-active')
    injectStudioStyles()

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
                <button class="studio-scene-btn" data-scene="portrait_pip">
                    <span class="icon">👤</span><span>PiP (Portret)</span>
                </button>
                <button class="studio-scene-btn" data-scene="title_card">
                    <span class="icon">🎬</span><span>Intro/Outro</span>
                </button>
                <button class="studio-scene-btn" data-scene="auto" style="grid-column: 1 / -1; margin-top: 4px;">
                    <span class="icon">🤖</span><span>Automatyczny Reżyser (Auto)</span>
                </button>
            </div>
        </div>

        <!-- Sekcja 3: Mikser Audio -->
        <div class="studio-card">
            <div class="studio-card__header">
                <div class="studio-card__title">Mikser Audio</div>
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
            <button class="studio-btn-transport" id="btn-studio-rec">
                <span class="indicator-rec" style="display:none;"></span>
                <span>ARM RECORDING</span>
            </button>
            <button class="studio-btn-transport" id="btn-studio-marker">
                <span>➕</span><span>ADD TIMELINE MARKER</span>
            </button>
        </div>
        <div class="studio-transport-group">
            <button class="studio-btn-transport" id="btn-studio-intro">
                <span>🎬</span><span>PLAY INTRO</span>
            </button>
            <button class="studio-btn-transport" id="btn-studio-outro">
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

    // 1. Zmiana katalogu zapisu (na razie tylko lokalny mock do Task 2)
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
            // Wyślij control message na backend
            sendControlMessage({
                type: "studio_set_recording_dir",
                path: path
            })
            pathStatus.textContent = "Stan: Weryfikacja..."
            pathStatus.style.color = "#a78bfa"
        })
    }

    // 2. Zmiana Scen Reżysera
    const sceneButtons = sidebarEl.querySelectorAll('.studio-scene-btn')
    sceneButtons.forEach(btn => {
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

            // Wysyłamy wiadomość reżysera na backend
            sendControlMessage({
                type: "studio_set_director_scene",
                scene: scene
            })
        })
    })

    // 3. Obsługa Miksera Audio (suwaki i przyciski Mute)
    const channels = ['mic', 'bgm', 'sfx', 'master']
    channels.forEach(ch => {
        const slider = sidebarEl.querySelector(`#slider-${ch}`)
        const valLabel = sidebarEl.querySelector(`#val-${ch}`)
        const muteBtn = sidebarEl.querySelector(`#mute-${ch}`)

        if (slider && valLabel) {
            slider.addEventListener('input', () => {
                const val = parseFloat(slider.value)
                studioState[`${ch}Volume`] = val
                valLabel.textContent = `${Math.round(val * 100)}%`
                saveStudioVolumeSettings()
            })
        }

        if (muteBtn) {
            muteBtn.addEventListener('click', () => {
                const muted = !studioState[`${ch}Muted`]
                studioState[`${ch}Muted`] = muted
                
                if (muted) {
                    muteBtn.textContent = '🔇'
                    muteBtn.classList.add('studio-audio-channel__mute-btn--muted')
                } else {
                    muteBtn.textContent = '🔊'
                    muteBtn.classList.remove('studio-audio-channel__mute-btn--muted')
                }
                saveStudioVolumeSettings()
            })
        }
    })

    // 4. Dolny pasek (Przycisk RECORDING)
    const recBtn = bottombarEl.querySelector('#btn-studio-rec')
    if (recBtn) {
        recBtn.addEventListener('click', () => {
            const isRec = studioState.recordingState === 'recording'
            if (isRec) {
                // STOP recording
                sendControlMessage({ type: "studio_stop_recording" })
            } else {
                // START recording
                sendControlMessage({ type: "studio_start_recording" })
            }
        })
    }

    // 5. Dolny pasek (Przycisk TIMELINE MARKER)
    const markerBtn = bottombarEl.querySelector('#btn-studio-marker')
    if (markerBtn) {
        markerBtn.addEventListener('click', () => {
            sendControlMessage({
                type: "studio_add_marker",
                label: "operator_marker"
            })
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
        // Mock - w Task 7 będziemy czytać realne urządzenia audio
        audioInd.classList.add('studio-indicator--active')
    }

    const recInd = topbarEl.querySelector('#indicator-rec')
    const isRecording = studioState.recordingState === 'recording'
    if (recInd) {
        recInd.classList.toggle('studio-indicator--rec', isRecording)
        recInd.classList.toggle('studio-indicator--active', isRecording)
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
    }

    // 4. Uaktualnienie przycisku RECORDING na dolnym pasku
    const recBtn = bottombarEl.querySelector('#btn-studio-rec')
    if (recBtn) {
        const recDot = recBtn.querySelector('.indicator-rec')
        const recText = recBtn.querySelector('span:not(.indicator-rec)')
        
        if (isRecording) {
            recBtn.classList.add('studio-btn-transport--rec')
            if (recDot) recDot.style.display = 'inline-block'
            if (recText) recText.textContent = 'STOP RECORDING'
        } else {
            recBtn.classList.remove('studio-btn-transport--rec')
            if (recDot) recDot.style.display = 'none'
            if (recText) recText.textContent = studioState.recordingState === 'armed' ? 'START RECORDING' : 'ARM RECORDING'
        }
    }

    // 5. Diagnostyka CV Health
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
