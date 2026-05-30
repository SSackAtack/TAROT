import { appState } from '../core/appState'
import { updateOperatorPanel } from '../operator/operatorPanel'
import { handleCardData } from '../renderer/cardFactory'
import { cardNames } from '../renderer/textureCache'
import { scene, renderer } from '../renderer/arRenderer'

const GRID_SNAP_ENABLED = false
const GRID_SIZE_X = 3.8
const GRID_SIZE_Y = 6.0

let wsReconnectDelay = 1000 
const WS_MAX_DELAY = 15000

export function sendControlMessage(payload) {
    if (!appState.controlSocket || appState.controlSocket.readyState !== WebSocket.OPEN) return
    appState.controlSocket.send(JSON.stringify(payload))
}

export function connectWebSocket(arSettings) {
    const ws = new WebSocket("ws://localhost:8765")

    ws.onopen = () => {
        appState.controlSocket = ws
        updateOperatorPanel(appState.latestStatus || { metrics: {}, runtime: {}, operator: {} })
        wsReconnectDelay = 1000 
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
                handleCardData(detectedCards, scene, arSettings, GRID_SNAP_ENABLED, GRID_SIZE_X, GRID_SIZE_Y, cardNames)
            }
        } catch (e) {
            console.error("[WEBSOCKET ERROR] Błąd przetwarzania danych:", e)
        }
    }

    ws.onclose = () => {
        Object.keys(appState.activeCards).forEach((name) => {
            appState.activeCards[name].targetOpacity = 0.0
        })
        if (appState.controlSocket === ws) appState.controlSocket = null
        updateOperatorPanel(appState.latestStatus || { metrics: {}, runtime: {}, operator: {} })
        setTimeout(() => connectWebSocket(arSettings), wsReconnectDelay)
        wsReconnectDelay = Math.min(wsReconnectDelay * 2, WS_MAX_DELAY)
    }

    ws.onerror = () => {
        ws.close()
    }
}
