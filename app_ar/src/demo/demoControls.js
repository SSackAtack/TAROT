import { appState, arSettings } from '../core/appState'
import { handleCardData } from '../renderer/cardFactory'
import { cardNames } from '../renderer/textureCache'
import { scene } from '../renderer/arRenderer'
import { 
    particleSystem, candleLight, mysticLight, glowLight, 
    ambientLight, dirLight, deskMesh, candlesGroup 
} from '../renderer/scenography'
import { operatorPanel, toggleOperatorPanel } from '../operator/operatorPanel'

const GRID_SNAP_ENABLED = false
const GRID_SIZE_X = 3.8
const GRID_SIZE_Y = 6.0

export let wowControlsPanel = null

export function toggleWowMode() {
    appState.wowMode = !appState.wowMode
    const body = document.body
    const btn = document.getElementById('toggle-wow-btn')
    
    if (appState.wowMode) {
        body.classList.add('wow-mode-active')
        if (btn) {
            btn.textContent = '✨ Wyłącz Tryb Kinowy'
            btn.classList.add('wow-btn--active')
        }
        
        if (particleSystem) particleSystem.visible = true
        if (candleLight) candleLight.visible = true
        if (mysticLight) mysticLight.visible = true
        if (glowLight) glowLight.visible = true
        
        if (deskMesh) deskMesh.visible = true
        if (candlesGroup) candlesGroup.visible = true
        
        candleLight.intensity = 8.0
        mysticLight.intensity = 5.0
        glowLight.intensity = 3.0
        
        ambientLight.intensity = 0.4
        dirLight.intensity = 0.2
    } else {
        body.classList.remove('wow-mode-active')
        if (btn) {
            btn.textContent = '✨ Włącz Tryb Kinowy'
            btn.classList.remove('wow-btn--active')
        }
        
        if (particleSystem) particleSystem.visible = false
        if (candleLight) candleLight.visible = false
        if (mysticLight) mysticLight.visible = false
        if (glowLight) glowLight.visible = false
        
        candleLight.intensity = 0
        mysticLight.intensity = 0
        glowLight.intensity = 0
        
        ambientLight.intensity = 2.0
        dirLight.intensity = 1.5
    }
}

export function dealDemoSpread() {
    clearDemoSpread()
    setTimeout(() => {
        const shuffled = [...cardNames].sort(() => 0.5 - Math.random())
        const selected = shuffled.slice(0, 3)
        const spread = [
            { name: selected[0], x: -4.2, y: 0.0, angle: (Math.random() - 0.5) * 0.1 },
            { name: selected[1], x: 0.0, y: 0.0, angle: (Math.random() - 0.5) * 0.08 },
            { name: selected[2], x: 4.2, y: 0.0, angle: (Math.random() - 0.5) * 0.1 }
        ]
        handleCardData(spread, scene, arSettings, GRID_SNAP_ENABLED, GRID_SIZE_X, GRID_SIZE_Y, cardNames)
    }, 150)
}

export function clearDemoSpread() {
    handleCardData([], scene, arSettings, GRID_SNAP_ENABLED, GRID_SIZE_X, GRID_SIZE_Y, cardNames)
}

export function toggleWowControlsPanel() {
    if (!wowControlsPanel) return
    wowControlsPanel.classList.toggle('wow-controls--collapsed')
    const toggleBtn = wowControlsPanel.querySelector('#wow-controls-toggle')
    if (toggleBtn) {
        if (wowControlsPanel.classList.contains('wow-controls--collapsed')) {
            toggleBtn.innerHTML = '▲'
            toggleBtn.title = "Pokaż panel kontrolny"
        } else {
            toggleBtn.innerHTML = '▼'
            toggleBtn.title = "Ukryj panel kontrolny"
        }
    }
}

export function toggleAllPanels() {
    const panels = [
        { el: operatorPanel, collapsedClass: 'operator-panel--collapsed', toggleId: '#operator-panel-toggle', openSym: '▶', closedSym: '⚙️', titleOpen: 'Ukryj panel', titleClosed: 'Pokaż panel' },
        { el: wowControlsPanel, collapsedClass: 'wow-controls--collapsed', toggleId: '#wow-controls-toggle', openSym: '▼', closedSym: '▲', titleOpen: 'Ukryj panel kontrolny', titleClosed: 'Pokaż panel kontrolny' }
    ]
    
    if (wowControlsPanel) {
        const shouldCollapse = !wowControlsPanel.classList.contains('wow-controls--collapsed')
        panels.forEach(p => {
            if (!p.el) return
            if (shouldCollapse) {
                p.el.classList.add(p.collapsedClass)
            } else {
                p.el.classList.remove(p.collapsedClass)
            }
            const btn = p.el.querySelector(p.toggleId)
            if (btn) {
                btn.innerHTML = shouldCollapse ? p.closedSym : p.openSym
                btn.title = shouldCollapse ? p.titleClosed : p.titleOpen
            }
        })
    }
}

export function createWowControls() {
    const controls = document.createElement('div')
    controls.className = 'wow-controls'
    controls.id = 'wow-controls-panel'
    controls.innerHTML = `
        <button type="button" class="wow-controls__toggle-btn" id="wow-controls-toggle" title="Ukryj panel kontrolny">▼</button>
        <div class="wow-controls__title">🔮 TarotVision Live</div>
        <div class="wow-controls__buttons">
            <button id="toggle-wow-btn" class="wow-btn wow-btn--primary">✨ Włącz Tryb Kinowy</button>
            <button id="demo-deal-btn" class="wow-btn">🃏 Rozdaj Karty (Demo)</button>
            <button id="demo-clear-btn" class="wow-btn wow-btn--danger">Sweep (Wyczyść)</button>
        </div>
        <div class="wow-controls__info">Skróty: <strong>W</strong> (Tryb Kinowy) | <strong>D</strong> (Rozdaj) | <strong>C</strong> (Wyczyść) | <strong>H</strong> (Ukryj Panele)</div>
    `
    document.body.appendChild(controls)
    wowControlsPanel = controls
    
    const toggleWowBtn = controls.querySelector('#toggle-wow-btn')
    const demoDealBtn = controls.querySelector('#demo-deal-btn')
    const demoClearBtn = controls.querySelector('#demo-clear-btn')
    const togglePanelBtn = controls.querySelector('#wow-controls-toggle')
    
    toggleWowBtn.addEventListener('click', toggleWowMode)
    demoDealBtn.addEventListener('click', dealDemoSpread)
    demoClearBtn.addEventListener('click', clearDemoSpread)
    togglePanelBtn.addEventListener('click', toggleWowControlsPanel)
    
    window.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
        const key = e.key.toLowerCase()
        if (key === 'w') {
            toggleWowMode()
        } else if (key === 'd') {
            dealDemoSpread()
        } else if (key === 'c') {
            clearDemoSpread()
        } else if (key === 'h') {
            toggleAllPanels()
        }
    })
}
