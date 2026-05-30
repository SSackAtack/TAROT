import { appState, arSettings, saveArSettings } from '../core/appState'
import { sendControlMessage } from '../transport/wsClient'

const operatorMetricNames = [
    'fps', 'matching_ms', 'cards_checked', 'orb_skipped_locked',
    'locked_tracked_count', 'available_card_count', 'tracked_card_count',
    'stable_for_ms', 'snapshot_quality_score', 'snapshot_analysis_ms',
    'time_from_motion_to_publish_ms'
]

const metricLabels = {
    fps: 'FPS',
    matching_ms: 'Czas rozpoznawania',
    cards_checked: 'Sprawdzane karty',
    orb_skipped_locked: 'Pominięte ORB',
    locked_tracked_count: 'Śledzone konturem',
    available_card_count: 'Karty w puli',
    tracked_card_count: 'Karty na stole',
    stable_for_ms: 'Stabilność',
    snapshot_quality_score: 'Jakość snapshotu',
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

export let operatorPanel = null

export function formatMetricValue(value) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '-'
    if (Math.abs(value) >= 100) return value.toFixed(0)
    return value.toFixed(2)
}

export function createOperatorPanel() {
    if (!appState.operatorMode) return null

    const panel = document.createElement('aside')
    panel.className = 'operator-panel'
    panel.innerHTML = `
        <button type="button" class="operator-panel__toggle-btn" id="operator-panel-toggle" title="Ukryj/Pokaż Panel">⚙️</button>
        <div class="operator-panel__header">
            <span class="operator-panel__title">Panel Operatora</span>
            <span class="operator-panel__status" data-role="connection">offline</span>
        </div>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Stan systemu</summary>
            <div class="operator-grid" data-role="runtime"></div>
        </details>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Metryki</summary>
            <div class="operator-grid" data-role="metrics"></div>
        </details>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Parametry bezpieczne</summary>
            <div class="operator-controls" data-role="safe-parameters"></div>
        </details>
        <details class="operator-panel__section operator-advanced">
            <summary class="operator-panel__section-title">Zaawansowane</summary>
            <div class="operator-controls" data-role="advanced-parameters"></div>
        </details>
        <details class="operator-panel__section" data-role="camera-controls-section">
            <summary class="operator-panel__section-title">Kamera sprzętowo (Focus/Exposure)</summary>
            <div class="operator-controls" data-role="camera-controls">
                Brak danych z kamery (kliknij "Odczyt kamery")
            </div>
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
                <label class="operator-control">
                    <span>Wysokość kamery (WOW)</span>
                    <input type="range" min="5.0" max="30.0" step="0.5" value="${arSettings.cameraHeight}" data-ar-param="cameraHeight" />
                    <output>${arSettings.cameraHeight.toFixed(1)}</output>
                </label>
                <label class="operator-control">
                    <span>Kąt / Odległość (WOW)</span>
                    <input type="range" min="5.0" max="25.0" step="0.5" value="${arSettings.cameraDistance}" data-ar-param="cameraDistance" />
                    <output>${arSettings.cameraDistance.toFixed(1)}</output>
                </label>
            </div>
        </details>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Akcje i profile</summary>
            <div class="operator-help">Odczyt kamery niczego nie ustawia. To bezpieczny odczyt-only.</div>
            <div class="operator-actions">
                <input class="operator-profile-name" data-role="profile-name" value="studio_day" aria-label="Nazwa profilu" />
                <button type="button" data-action="profile_save">Zapisz</button>
                <button type="button" data-action="profile_apply">Wczytaj</button>
                <button type="button" data-action="tuning_rollback">Cofnij</button>
                <button type="button" data-action="camera_probe">Odczyt kamery</button>
                <button type="button" data-action="calibration_start">Kalibracja</button>
            </div>
        </details>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Komunikaty systemowe</summary>
            <div class="operator-warnings" data-role="warnings">-</div>
        </details>
    `
    document.body.appendChild(panel)
    operatorPanel = panel

    const toggleBtn = panel.querySelector('#operator-panel-toggle')
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleOperatorPanel)
    }

    return panel
}

export function toggleOperatorPanel() {
    if (!operatorPanel) return
    operatorPanel.classList.toggle('operator-panel--collapsed')
    const toggleBtn = operatorPanel.querySelector('#operator-panel-toggle')
    if (toggleBtn) {
        if (operatorPanel.classList.contains('operator-panel--collapsed')) {
            toggleBtn.innerHTML = '⚙️'
            toggleBtn.title = "Pokaż panel"
        } else {
            toggleBtn.innerHTML = '▶'
            toggleBtn.title = "Ukryj panel"
        }
    }
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

    const existingInputs = safeContainer.querySelectorAll('input[data-param]')
    if (existingInputs.length > 0) {
        names.forEach((name) => {
            const val = parameters[name] ?? metadata[name].default
            const input = operatorPanel.querySelector(`input[data-param="${name}"]`)
            if (input) {
                const output = input.parentElement?.querySelector('output')
                if (document.activeElement !== input) {
                    input.value = val
                    if (output) output.textContent = formatMetricValue(Number(val))
                }
            }
        })
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

function updateCameraControlsUI(supportedControls) {
    if (!operatorPanel) return
    const container = operatorPanel.querySelector('[data-role="camera-controls"]')
    if (!container) return

    if (!supportedControls || Object.keys(supportedControls).length === 0) {
        container.textContent = 'Brak danych z kamery (kliknij "Odczyt kamery")'
        return
    }

    const labels = {
        CAP_PROP_FOCUS: 'Ostrość (Focus)',
        CAP_PROP_AUTOFOCUS: 'Autofokus (0=Wył, 1=Wł)',
        CAP_PROP_EXPOSURE: 'Ekspozycja (Exposure)',
        CAP_PROP_AUTO_EXPOSURE: 'Auto Ekspozycja',
        CAP_PROP_BRIGHTNESS: 'Jasność (Brightness)',
        CAP_PROP_CONTRAST: 'Kontrast (Contrast)'
    }

    const ranges = {
        CAP_PROP_FOCUS: { min: 0, max: 1023, step: 5 },
        CAP_PROP_AUTOFOCUS: { min: 0, max: 1, step: 1 },
        CAP_PROP_EXPOSURE: { min: -13, max: 1000, step: 1 },
        CAP_PROP_AUTO_EXPOSURE: { min: 0, max: 3, step: 1 },
        CAP_PROP_BRIGHTNESS: { min: 0, max: 255, step: 1 },
        CAP_PROP_CONTRAST: { min: 0, max: 255, step: 1 }
    }

    const existingInputs = container.querySelectorAll('input[data-camera-param]')
    if (existingInputs.length > 0) {
        Object.entries(supportedControls).forEach(([name, data]) => {
            if (data.readback_value === -1.0) return
            const input = container.querySelector(`input[data-camera-param="${name}"]`)
            if (input) {
                const output = input.parentElement?.querySelector('output')
                if (document.activeElement !== input) {
                    input.value = data.readback_value
                    if (output) output.textContent = data.readback_value
                }
            }
        })
        return
    }

    const html = Object.entries(supportedControls)
        .map(([name, data]) => {
            if (data.readback_value === -1.0) return ''
            const range = ranges[name] || { min: 0, max: 255, step: 1 }
            const label = labels[name] || name
            return `
                <label class="operator-control">
                    <span title="${name}">${label}</span>
                    <input
                        type="range"
                        min="${range.min}"
                        max="${range.max}"
                        step="${range.step}"
                        value="${data.readback_value}"
                        data-camera-param="${name}"
                    />
                    <output>${data.readback_value}</output>
                </label>
            `
        })
        .join('')

    container.innerHTML = html || 'Brak aktywnych sprzętowych funkcji kamery w tym systemie.'
}

export function updateOperatorPanel(data) {
    if (!operatorPanel) return
    appState.latestStatus = data

    const connection = operatorPanel.querySelector('[data-role="connection"]')
    if (connection) connection.textContent = appState.controlSocket?.readyState === WebSocket.OPEN ? 'online' : 'offline'

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
    updateCameraControlsUI(operator.supported_camera_controls)

    const warnings = operatorPanel.querySelector('[data-role="warnings"]')
    const warningItems = operator.warnings || []
    if (warnings) warnings.textContent = warningItems.length ? warningItems.join(' | ') : '-'
}

export function initOperatorListeners() {
    if (!operatorPanel) return

    operatorPanel.addEventListener('input', (event) => {
        const input = event.target
        if (!(input instanceof HTMLInputElement)) return
        
        const arParam = input.dataset.arParam
        if (arParam) {
            arSettings[arParam] = parseFloat(input.value)
            saveArSettings()
            const output = input.parentElement?.querySelector('output')
            if (output) {
                output.textContent = arSettings[arParam].toFixed((arParam.startsWith('offset') || arParam.startsWith('camera')) ? 1 : 2)
            }
            return
        }

        const cameraParam = input.dataset.cameraParam
        if (cameraParam) {
            const output = input.parentElement?.querySelector('output')
            if (output) {
                output.textContent = input.value
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
        
        const cameraParam = input.dataset.cameraParam
        if (cameraParam) {
            sendControlMessage({
                type: 'camera_set',
                param: cameraParam,
                value: Number(input.value)
            })
            return
        }

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
