import './style.css'
import * as THREE from 'three'

// 1. Inicjalizacja sceny (z pelna przezroczystoscia pod nakladke OBS)
const container = document.getElementById('app')
const scene = new THREE.Scene()
const operatorMode = new URLSearchParams(window.location.search).get('operator') === '1'
let controlSocket = null
let latestStatus = null

// Ustawienia kamery — widok z gory (90 stopni, prostopadle do stolu)
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000)
camera.position.set(0, 35, 0.001) // Y = gora, Z = mikro-offset zeby lookAt nie zwariowal
camera.lookAt(0, 0, 0)

// Renderer z kanalem Alpha (cienie WYLACZONE)
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
renderer.setSize(window.innerWidth, window.innerHeight)
renderer.setPixelRatio(window.devicePixelRatio)
renderer.shadowMap.enabled = false
container.appendChild(renderer.domElement)

// 2. Oswietlenie — proste, rownomierne (bez cieni)
const ambientLight = new THREE.AmbientLight(0xffffff, 2.0)
scene.add(ambientLight)

const dirLight = new THREE.DirectionalLight(0xffffff, 1.5)
dirLight.position.set(0, 20, 5)
dirLight.castShadow = false
scene.add(dirLight)

// 4. Preload tekstur z Promise.all + flaga gotowosci
const textureLoader = new THREE.TextureLoader()
const texturesCache = {}
let texturesReady = false  // Flaga blokujaca tworzenie kart przed zakonczeniem preloadu
let latestFrameData = null // Bufor na dane z WebSocketu przed zakonczeniem preloadu

// Opcje wirtualnej siatki pozycjonującej (Grid Snapping)
const GRID_SNAP_ENABLED = false
const GRID_SIZE_X = 3.8  // Odstęp między kolumnami (szerokość karty ~3.2 + przerwa ~0.6)
const GRID_SIZE_Y = 6.0  // Odstęp między rzędami (wysokość karty ~5.5 + przerwa ~0.5)

// Parametry pozycjonowania i skali wirtualnych kart (nakładki AR)
const arSettings = {
    cardScale: parseFloat(localStorage.getItem('ar_cardScale') || '1.0'),
    spacingX: parseFloat(localStorage.getItem('ar_spacingX') || '1.0'),
    spacingY: parseFloat(localStorage.getItem('ar_spacingY') || '1.0'),
    offsetX: parseFloat(localStorage.getItem('ar_offsetX') || '0.0'),
    offsetY: parseFloat(localStorage.getItem('ar_offsetY') || '0.0'),
}

function saveArSettings() {
    localStorage.setItem('ar_cardScale', arSettings.cardScale.toString())
    localStorage.setItem('ar_spacingX', arSettings.spacingX.toString())
    localStorage.setItem('ar_spacingY', arSettings.spacingY.toString())
    localStorage.setItem('ar_offsetX', arSettings.offsetX.toString())
    localStorage.setItem('ar_offsetY', arSettings.offsetY.toString())
}

const cardNames = [
    "00_fool", "01_magician", "02_high_priestess", "03_empress", "04_emperor",
    "05_hierophant", "06_lovers", "07_chariot", "08_strength", "09_hermit",
    "10_wheel_of_fortune", "11_justice", "12_hanged_man", "13_death", "14_temperance",
    "15_devil", "16_tower", "17_star", "18_moon", "19_sun", "20_judgement", "21_world"
]

console.log("[PRELOAD] Rozpoczynam wczytywanie 22 tekstur tarota do pamieci...")

// Promise-based preloading — gwarantuje, ze texturesReady = true dopiero gdy WSZYSTKIE 22 sa gotowe
const preloadPromises = cardNames.map((name) => {
    return new Promise((resolve) => {
        const path = `/karty/${name}.webp`
        textureLoader.load(path, (texture) => {
            texturesCache[name] = texture
            texture.minFilter = THREE.LinearMipmapLinearFilter
            texture.magFilter = THREE.LinearFilter
            texture.colorSpace = THREE.SRGBColorSpace  // Poprawne odwzorowanie kolorow (wymagane od Three.js r152+)
            console.log(`[PRELOAD] Zaladowano: ${name}`)
            resolve()
        }, undefined, (err) => {
            console.error(`[PRELOAD BLAD] Nie udalo sie zaladowac: ${name}`, err)
            resolve() // Rozwiazujemy mimo bledu, zeby nie blokowac reszty
        })
    })
})

Promise.all(preloadPromises).then(() => {
    texturesReady = true
    console.log(`[PRELOAD] Wszystkie ${Object.keys(texturesCache).length} tekstur zaladowane i gotowe!`)
    
    // Jeśli otrzymaliśmy dane z WebSocketu przed załadowaniem tekstur — przetwarzamy je teraz!
    if (latestFrameData) {
        console.log("[PRELOAD] Przetwarzam zapamiętane dane WebSocket po załadowaniu tekstur...")
        handleCardData(latestFrameData)
    }
})

// 5. Wspoldzielona geometria karty — tworzona RAZ i reuzywana przez wszystkie instancje
// Eliminuje zbedne alokacje GPU (audit: kazda karta tworzyla wlasna kopie geometrii)
let sharedGeometry = null
let sharedCardWidth = 0
let sharedCardHeight = 0

function getSharedGeometry(aspect) {
    if (sharedGeometry) return sharedGeometry

    sharedCardHeight = 5.5
    sharedCardWidth = sharedCardHeight * aspect

    const shape = new THREE.Shape()
    const radius = 0.24
    const x = -sharedCardWidth / 2
    const y = -sharedCardHeight / 2

    shape.moveTo(x, y + radius)
    shape.lineTo(x, y + sharedCardHeight - radius)
    shape.quadraticCurveTo(x, y + sharedCardHeight, x + radius, y + sharedCardHeight)
    shape.lineTo(x + sharedCardWidth - radius, y + sharedCardHeight)
    shape.quadraticCurveTo(x + sharedCardWidth, y + sharedCardHeight, x + sharedCardWidth, y + sharedCardHeight - radius)
    shape.lineTo(x + sharedCardWidth, y + radius)
    shape.quadraticCurveTo(x + sharedCardWidth, y, x + sharedCardWidth - radius, y)
    shape.lineTo(x + radius, y)
    shape.quadraticCurveTo(x, y, x, y + radius)

    const extrudeSettings = {
        steps: 1,
        depth: 0.08,
        bevelEnabled: true,
        bevelThickness: 0.02,
        bevelSize: 0.015,
        bevelSegments: 4
    }

    sharedGeometry = new THREE.ExtrudeGeometry(shape, extrudeSettings)
    sharedGeometry.center()

    // Reczna korekta UV — wykonana RAZ, nie przy kazdej karcie
    const pos = sharedGeometry.attributes.position
    const uvs = sharedGeometry.attributes.uv
    for (let i = 0; i < pos.count; i++) {
        const u = (pos.getX(i) + sharedCardWidth / 2) / sharedCardWidth
        const v = (pos.getY(i) + sharedCardHeight / 2) / sharedCardHeight
        uvs.setXY(i, u, v)
    }
    uvs.needsUpdate = true

    console.log(`[AR] Wspoldzielona geometria utworzona (${sharedCardWidth.toFixed(2)} x ${sharedCardHeight})`)
    return sharedGeometry
}

// 6. Zarzadzanie instancjami kart 3D
const activeCards = {}

const operatorMetricNames = [
    'fps',
    'matching_ms',
    'cards_checked',
    'orb_skipped_locked',
    'locked_tracked_count',
    'available_card_count',
    'tracked_card_count',
    'stable_for_ms',
    'snapshot_quality_score',
    'snapshot_analysis_ms',
    'time_from_motion_to_publish_ms'
]

const metricLabels = {
    fps: 'FPS',
    matching_ms: 'Czas rozpoznawania',
    cards_checked: 'Sprawdzane karty',
    orb_skipped_locked: 'Pominiete ORB',
    locked_tracked_count: 'Sledzone konturem',
    available_card_count: 'Karty w puli',
    tracked_card_count: 'Karty na stole',
    stable_for_ms: 'Stabilnosc',
    snapshot_quality_score: 'Jakosc snapshotu',
    snapshot_analysis_ms: 'Analiza snapshotu',
    time_from_motion_to_publish_ms: 'Ruch -> publikacja'
}

const parameterLabels = {
    SNAPSHOT_SETTLE_SECONDS: 'Czas stabilizacji (s)',
    MOTION_CHANGED_RATIO: 'Czułość ruchu (detektor)',
    MIN_MATCH_COUNT: 'Min. punkty ORB',
    RATIO_THRESH: 'Próg Ratio (Lowe)',
    MIN_INLIER_RATIO: 'Zgodność RANSAC',
    WORKSPACE_INFLATE_PERCENT: 'Poszerzenie obszaru (%)'
}

const parameterHints = {
    SNAPSHOT_SETTLE_SECONDS: 'Czas stabilizacji stołu przed zrobieniem snapshotu.',
    MOTION_CHANGED_RATIO: 'Próg procentowy pikseli decydujący o wykryciu ruchu.',
    MIN_MATCH_COUNT: 'Minimalna wymagana liczba dopasowań cech ORB.',
    RATIO_THRESH: 'Test Lowe\'a. Niższy = bardziej unikalne punkty.',
    MIN_INLIER_RATIO: 'Poprawność ułożenia geometrycznego RANSAC.',
    WORKSPACE_INFLATE_PERCENT: 'Poszerzenie wirtualnego obszaru stołu na zewnątrz od ArUco.'
}

function formatMetricValue(value) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '-'
    if (Math.abs(value) >= 100) return value.toFixed(0)
    return value.toFixed(2)
}

function createOperatorPanel() {
    if (!operatorMode) return null

    const panel = document.createElement('aside')
    panel.className = 'operator-panel'
    panel.innerHTML = `
        <div class="operator-panel__header">
            <span class="operator-panel__title">Panel Operatora</span>
            <span class="operator-panel__status" data-role="connection">offline</span>
        </div>
        <div class="operator-panel__section">
            <div class="operator-panel__section-title">Stan systemu</div>
            <div class="operator-grid" data-role="runtime"></div>
        </div>
        <div class="operator-panel__section">
            <div class="operator-panel__section-title">Metryki</div>
            <div class="operator-grid" data-role="metrics"></div>
        </div>
        <div class="operator-panel__section">
            <div class="operator-panel__section-title">Parametry bezpieczne</div>
            <div class="operator-controls" data-role="safe-parameters"></div>
        </div>
        <details class="operator-panel__section operator-advanced">
            <summary class="operator-panel__section-title">Zaawansowane</summary>
            <div class="operator-controls" data-role="advanced-parameters"></div>
        </details>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Wizualia i rozstaw (AR)</summary>
            <div class="operator-controls">
                <label class="operator-control">
                    <span>Skala kart wirtualnych</span>
                    <input type="range" min="0.5" max="2.0" step="0.05" value="${arSettings.cardScale}" data-ar-param="cardScale" />
                    <output>${arSettings.cardScale.toFixed(2)}</output>
                </label>
                <label class="operator-control">
                    <span>Rozstaw poziomy (X)</span>
                    <input type="range" min="0.5" max="2.0" step="0.05" value="${arSettings.spacingX}" data-ar-param="spacingX" />
                    <output>${arSettings.spacingX.toFixed(2)}</output>
                </label>
                <label class="operator-control">
                    <span>Rozstaw pionowy (Y)</span>
                    <input type="range" min="0.5" max="2.0" step="0.05" value="${arSettings.spacingY}" data-ar-param="spacingY" />
                    <output>${arSettings.spacingY.toFixed(2)}</output>
                </label>
                <label class="operator-control">
                    <span>Przesunięcie poziome (X)</span>
                    <input type="range" min="-10.0" max="10.0" step="0.1" value="${arSettings.offsetX}" data-ar-param="offsetX" />
                    <output>${arSettings.offsetX.toFixed(1)}</output>
                </label>
                <label class="operator-control">
                    <span>Przesunięcie pionowe (Y)</span>
                    <input type="range" min="-10.0" max="10.0" step="0.1" value="${arSettings.offsetY}" data-ar-param="offsetY" />
                    <output>${arSettings.offsetY.toFixed(1)}</output>
                </label>
            </div>
        </details>
        <div class="operator-panel__section">
            <div class="operator-panel__section-title">Akcje</div>
            <div class="operator-help">Odczyt kamery niczego nie ustawia. To bezpieczny odczyt-only.</div>
            <div class="operator-actions">
                <input class="operator-profile-name" data-role="profile-name" value="studio_day" aria-label="Nazwa profilu" />
                <button type="button" data-action="profile_save">Zapisz</button>
                <button type="button" data-action="profile_apply">Wczytaj</button>
                <button type="button" data-action="tuning_rollback">Cofnij</button>
                <button type="button" data-action="camera_probe">Odczyt kamery</button>
                <button type="button" data-action="calibration_start">Kalibracja</button>
            </div>
        </div>
        <div class="operator-panel__section">
            <div class="operator-panel__section-title">Komunikaty</div>
            <div class="operator-warnings" data-role="warnings">-</div>
        </div>
    `
    document.body.appendChild(panel)
    return panel
}

const operatorPanel = createOperatorPanel()

function sendControlMessage(payload) {
    if (!controlSocket || controlSocket.readyState !== WebSocket.OPEN) return
    controlSocket.send(JSON.stringify(payload))
}

function updateOperatorGrid(container, entries) {
    if (!container) return
    container.innerHTML = entries.map(([label, value]) => `
        <div class="operator-grid__label">${label}</div>
        <div class="operator-grid__value">${value}</div>
    `).join('')
}

function updateOperatorParameters(operator) {
    if (!operatorPanel) return
    const safeContainer = operatorPanel.querySelector('[data-role="safe-parameters"]')
    const advancedContainer = operatorPanel.querySelector('[data-role="advanced-parameters"]')
    if (!safeContainer || !advancedContainer) return

    const parameters = operator?.parameters || {}
    const metadata = operator?.parameter_metadata || {}
    const names = Object.keys(metadata)
    if (names.length === 0) {
        safeContainer.textContent = '-'
        advancedContainer.textContent = '-'
        return
    }

    const renderControls = (filteredNames) => {
        if (filteredNames.length === 0) return '-'
        return filteredNames.map((name) => {
        const meta = metadata[name]
        const value = parameters[name] ?? meta.default
        return `
            <label class="operator-control">
                <span title="${name}">${parameterLabels[name] || name}</span>
                <input
                    type="range"
                    min="${meta.minimum}"
                    max="${meta.maximum}"
                    step="${name === 'MIN_MATCH_COUNT' || name === 'WORKSPACE_INFLATE_PERCENT' ? '1' : name === 'SNAPSHOT_SETTLE_SECONDS' ? '0.1' : name === 'MOTION_CHANGED_RATIO' || name === 'RATIO_THRESH' || name === 'MIN_INLIER_RATIO' ? '0.005' : '0.01'}"
                    value="${value}"
                    data-param="${name}"
                    ${meta.live_safe ? '' : 'data-unsafe="1"'}
                />
                <output>${formatMetricValue(Number(value))}</output>
                <small>${parameterHints[name] || name}</small>
            </label>
        `
        }).join('')
    }

    safeContainer.innerHTML = renderControls(names.filter((name) => metadata[name].live_safe))
    advancedContainer.innerHTML = renderControls(names.filter((name) => !metadata[name].live_safe))
}

function updateOperatorPanel(data) {
    if (!operatorPanel) return
    latestStatus = data

    const connection = operatorPanel.querySelector('[data-role="connection"]')
    if (connection) connection.textContent = controlSocket?.readyState === WebSocket.OPEN ? 'online' : 'offline'

    const metrics = data.metrics || {}
    const runtime = data.runtime || {}
    const operator = data.operator || {}
    const layout = data.layout || {}

    updateOperatorGrid(operatorPanel.querySelector('[data-role="runtime"]'), [
        ['Tryb CV', runtime.profile || '-'],
        ['Profil strojenia', operator.active_profile || '-'],
        ['Harmonogram', runtime.schedule_mode || '-'],
        ['Snapshot', layout.state || '-'],
        ['Layout', layout.layout_id ?? '-'],
        ['Boost', runtime.boost_frames_remaining ?? '-'],
        ['Kamera', runtime.camera_index ?? '-'],
        ['Obraz', runtime.capture_width && runtime.capture_height ? `${runtime.capture_width}x${runtime.capture_height}` : '-']
    ])

    updateOperatorGrid(
        operatorPanel.querySelector('[data-role="metrics"]'),
        operatorMetricNames.map((name) => [metricLabels[name] || name, formatMetricValue(metrics[name] ?? runtime[name])])
    )

    updateOperatorParameters(operator)

    const warnings = operatorPanel.querySelector('[data-role="warnings"]')
    const warningItems = operator.warnings || []
    if (warnings) warnings.textContent = warningItems.length ? warningItems.join(' | ') : '-'
}

// Wspoldzielony material zlotych krawedzi — identyczny dla wszystkich kart (audit: tworzony byl od nowa per karta)
const sharedEdgeMaterial = new THREE.MeshStandardMaterial({
    color: 0xd4af37,
    roughness: 0.22,
    metalness: 0.85,
    transparent: true,
    opacity: 0.0
})

function createVirtualCard(name) {
    if (!texturesReady) {
        console.warn(`[WARN] Preload jeszcze nie zakonczony — pomijam karte ${name}`)
        return
    }

    const texture = texturesCache[name]
    if (!texture) {
        console.warn(`[WARN] Tekstura dla karty ${name} nie istnieje w Cache!`)
        return
    }

    const aspect = texture.image ? (texture.image.width / texture.image.height) : (70 / 120)
    const geometry = getSharedGeometry(aspect) // Reuzywamy wspoldzielona geometrie

    // Kazda karta potrzebuje wlasnego materialu face (inna tekstura), ale klonujemy edge material
    const faceMaterial = new THREE.MeshStandardMaterial({ 
        map: texture,
        transparent: true,
        opacity: 0.0,
        roughness: 0.55,
        metalness: 0.05,
        side: THREE.DoubleSide
    })

    // Klonujemy edge material (potrzebne bo kazda karta ma niezalezna opacity)
    const edgeMaterial = sharedEdgeMaterial.clone()

    const mesh = new THREE.Mesh(geometry, [faceMaterial, edgeMaterial])
    // Cienie WYLACZONE
    
    const cardInstanceGroup = new THREE.Group()
    cardInstanceGroup.add(mesh)
    
    // Karta lezaca plasko na stole (90 stopni)
    cardInstanceGroup.rotation.x = -Math.PI / 2
    cardInstanceGroup.position.set(0, 0, 0)
    scene.add(cardInstanceGroup)

    activeCards[name] = {
        group: cardInstanceGroup,
        faceMaterial: faceMaterial,
        edgeMaterial: edgeMaterial,
        currentOpacity: 0.0,
        targetOpacity: 1.0,
        targetX: 0.0,
        targetY: 0.0,
        targetAngle: 0.0
    }
    
    console.log(`[AR] Utworzono karte 3D: ${name}`)
}

// 7. Wspólna funkcja przetwarzania danych o kartach (zapobiega wyścigom)
function handleCardData(detectedCards) {
    if (!texturesReady) {
        latestFrameData = detectedCards
        console.log("[PRELOAD] Dane o kartach z WebSocketu dotarły przed ukończeniem wczytywania grafik. Buforuję dane.")
        return
    }

    const detectedNames = detectedCards.map(c => c.name)
    
    Object.keys(activeCards).forEach((name) => {
        if (detectedNames.includes(name)) {
            activeCards[name].targetOpacity = 1.0
        } else {
            activeCards[name].targetOpacity = 0.0
        }
    })

    detectedCards.forEach((cardData) => {
        const name = cardData.name
        
        // Walidacja danych WebSocket — chroni przed NaN/undefined
        if (!cardNames.includes(name)) return
        if (typeof cardData.x !== 'number' || typeof cardData.y !== 'number') return
        
        if (!activeCards[name]) {
            createVirtualCard(name)
        }
        
        if (activeCards[name]) {
            activeCards[name].targetOpacity = 1.0
            
            // Przyciąganie współrzędnych do wirtualnej siatki (Grid Snapping)
            const rawX = cardData.x
            const rawY = cardData.y
            if (GRID_SNAP_ENABLED) {
                activeCards[name].targetX = Math.round(rawX / GRID_SIZE_X) * GRID_SIZE_X
                activeCards[name].targetY = Math.round(rawY / GRID_SIZE_Y) * GRID_SIZE_Y
            } else {
                activeCards[name].targetX = rawX
                activeCards[name].targetY = rawY
            }

            // Przyciąganie kąta (Angle Snapping) — wyłączone w trybie swobodnym dla naturalnego obrotu
            const rawAngle = cardData.angle || 0
            if (GRID_SNAP_ENABLED) {
                activeCards[name].targetAngle = Math.round(rawAngle / (Math.PI / 2)) * (Math.PI / 2)
            } else {
                activeCards[name].targetAngle = rawAngle
            }
        }
    })
}

// 8. WebSocket z exponential backoff
let wsReconnectDelay = 1000 // Start: 1s, max: 15s
const WS_MAX_DELAY = 15000

function connectWebSocket() {
    console.log("[WEBSOCKET] Laczenie z TarotVision CV...")
    const ws = new WebSocket("ws://localhost:8765")

    ws.onopen = () => {
        console.log("[WEBSOCKET] Polaczono! Oczekiwanie na rozklady kart...")
        controlSocket = ws
        updateOperatorPanel(latestStatus || { metrics: {}, runtime: {}, operator: {} })
        wsReconnectDelay = 1000 // Reset delay po udanym polaczeniu
    }

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data)
            const layout = data.layout || {}
            const detectedCards = data.cards || []
            updateOperatorPanel(data)
            const layoutState = layout.state || ''
            const isWatcherOnlyState = ['settling', 'sampling_snapshots', 'analyzing_snapshot'].includes(layoutState)
            if (!isWatcherOnlyState) {
                handleCardData(detectedCards)
            }
        } catch (e) {
            console.error("[WEBSOCKET ERROR] Blad przetwarzania danych:", e)
        }
    }

    ws.onclose = () => {
        console.warn(`[WEBSOCKET] Polaczenie utracone. Ponowna proba za ${(wsReconnectDelay / 1000).toFixed(1)}s...`)
        Object.keys(activeCards).forEach((name) => {
            activeCards[name].targetOpacity = 0.0
        })
        if (controlSocket === ws) controlSocket = null
        updateOperatorPanel(latestStatus || { metrics: {}, runtime: {}, operator: {} })
        setTimeout(connectWebSocket, wsReconnectDelay)
        // Exponential backoff — kazda nieudana proba podwaja delay (max 15s)
        wsReconnectDelay = Math.min(wsReconnectDelay * 2, WS_MAX_DELAY)
    }

    ws.onerror = () => {
        ws.close()
    }
}

connectWebSocket()

if (operatorPanel) {
    operatorPanel.addEventListener('input', (event) => {
        const input = event.target
        if (!(input instanceof HTMLInputElement)) return
        
        const arParam = input.dataset.arParam
        if (arParam) {
            arSettings[arParam] = parseFloat(input.value)
            saveArSettings()
            const output = input.parentElement?.querySelector('output')
            if (output) {
                output.textContent = arSettings[arParam].toFixed(arParam.startsWith('offset') ? 1 : 2)
            }
            return
        }

        const param = input.dataset.param
        if (!param) return
        const output = input.parentElement?.querySelector('output')
        if (output) output.textContent = formatMetricValue(Number(input.value))
    })

    operatorPanel.addEventListener('change', (event) => {
        const input = event.target
        if (!(input instanceof HTMLInputElement)) return
        const param = input.dataset.param
        if (!param) return
        sendControlMessage({
            type: 'tuning_update',
            param,
            value: Number(input.value)
        })
    })

    operatorPanel.addEventListener('click', (event) => {
        const button = event.target
        if (!(button instanceof HTMLButtonElement)) return
        const action = button.dataset.action
        if (!action) return
        const profileName = operatorPanel.querySelector('[data-role="profile-name"]')?.value || 'studio_day'
        if (action === 'profile_save' || action === 'profile_apply') {
            sendControlMessage({ type: action, name: profileName })
            return
        }
        sendControlMessage({ type: action })
    })
}

// 9. Główna pętla renderowania (bez zbędnego zegara THREE.Clock)
function animate() {
    requestAnimationFrame(animate)

    const visibleCardNames = Object.keys(activeCards)
        .filter((name) => activeCards[name].currentOpacity > 0.01 || activeCards[name].targetOpacity > 0.0)
        .sort()

    visibleCardNames.forEach((name, index) => {
        const cardObj = activeCards[name]

        // Natychmiastowa zmiana przezroczystosci (bez LERP)
        if (cardObj.targetOpacity > 0.5) {
            cardObj.currentOpacity = 1.0
        } else {
            cardObj.currentOpacity -= 0.05 // Szybkie wygaszanie
            if (cardObj.currentOpacity < 0) cardObj.currentOpacity = 0
        }
        cardObj.faceMaterial.opacity = cardObj.currentOpacity
        cardObj.edgeMaterial.opacity = cardObj.currentOpacity

        // Czyszczenie pamieci po pelnym wygaszeniu (NIE disposujemy wspoldzielonej geometrii!)
        if (cardObj.targetOpacity === 0.0 && cardObj.currentOpacity <= 0.01) {
            scene.remove(cardObj.group)
            cardObj.group.traverse((child) => {
                if (child.isMesh) {
                    // Geometria jest wspoldzielona — NIE disposujemy jej!
                    if (Array.isArray(child.material)) {
                        child.material.forEach((m) => m.dispose())
                    } else {
                        child.material.dispose()
                    }
                }
            })
            delete activeCards[name]
            console.log(`[AR] Usunieto i wyczyszczono karte: ${name}`)
            return
        }

        // Stosujemy lokalną skalę wirtualnej karty w Three.js
        cardObj.group.scale.set(arSettings.cardScale, arSettings.cardScale, arSettings.cardScale)

        // BEZPOSREDNIE ustawianie pozycji z uwzględnieniem lokalnego rozstawu i przesunięcia
        cardObj.group.position.x = cardObj.targetX * arSettings.spacingX + arSettings.offsetX
        cardObj.group.position.z = -(cardObj.targetY * arSettings.spacingY + arSettings.offsetY) // Z bo kamera patrzy z gory (Y->Z mapping)

        // Bezposrednie ustawienie kata obrotu
        cardObj.group.rotation.z = cardObj.targetAngle
    })

    renderer.render(scene, camera)
}

// Resizing
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
})

animate()
