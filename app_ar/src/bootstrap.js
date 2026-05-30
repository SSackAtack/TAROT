import '../style.css'
import { appState, arSettings } from './core/appState'
import { scene, camera, renderer, initRenderer, updateCameraAnimation } from './renderer/arRenderer'
import { initLights, initScenography, updateScenographyAnimation } from './renderer/scenography'
import { loadTextures, cardNames } from './renderer/textureCache'
import { animateCards, handleCardData } from './renderer/cardFactory'
import { createOperatorPanel, initOperatorListeners } from './operator/operatorPanel'
import { connectWebSocket } from './transport/wsClient'
import { createWowControls } from './demo/demoControls'

import { createStudioConsole } from './studio/studioConsole'

const GRID_SNAP_ENABLED = false
const GRID_SIZE_X = 3.8
const GRID_SIZE_Y = 6.0

const container = document.getElementById('app')

// 1. Inicjalizacja Three.js (scena, kamera, renderer, światła i stół)
initRenderer(container)
initLights(scene)
initScenography(scene)

// 2. Inicjalizacja UI (Panel operatora / Konsola Studio i przyciski kontrolne WOW)
if (appState.studioMode) {
    createStudioConsole()
} else {
    createOperatorPanel()
    initOperatorListeners()
    createWowControls()
}

// 3. Połączenie WebSocket i asynchroniczne wczytywanie tekstur tarota
connectWebSocket(arSettings)
loadTextures(null, (detected) => handleCardData(detected, scene, arSettings, GRID_SNAP_ENABLED, GRID_SIZE_X, GRID_SIZE_Y, cardNames))

// 4. Główna pętla animacji i renderingu
function animate() {
    requestAnimationFrame(animate)

    // Animacja kamery, świec, oświetlenia oraz Star Dust
    updateCameraAnimation(appState.wowMode, arSettings)
    updateScenographyAnimation(appState.wowMode, arSettings)
    
    // Animacje fizyczne i transformacje kart 3D
    animateCards(scene, arSettings, appState.wowMode, GRID_SNAP_ENABLED, GRID_SIZE_X, GRID_SIZE_Y)

    renderer.render(scene, camera)
}

animate()
