import { studioState } from './studioState'
import { sendControlMessage } from '../transport/wsClient'

let timelineMarkers = []
let recordingStartTime = 0
let isRecordingActive = false

/**
 * Inicjalizuje nową oś czasu na początku nagrania.
 */
export function initTimeline() {
    timelineMarkers = []
    recordingStartTime = Date.now()
    isRecordingActive = true
    
    // Dodaj pierwszy automatyczny marker startu
    addTimelineMarker('recording_started')
    console.log('Timeline initialized for recording:', studioState.recordingId)
}

/**
 * Zatrzymuje zbieranie markerów na osi czasu.
 */
export function finalizeTimeline() {
    if (!isRecordingActive) return null
    
    // Dodaj końcowy marker stopu
    addTimelineMarker('recording_stopped')
    isRecordingActive = false
    
    const finalMarkers = [...timelineMarkers]
    console.log(`Timeline finalized with ${finalMarkers.length} markers for recording:`, studioState.recordingId)
    
    return finalMarkers
}

/**
 * Dodaje nowy znacznik (marker) do aktywnej osi czasu.
 * 
 * @param {string} type Typ markera (recording_started, scene_changed, card_revealed, operator_marker, recording_stopped)
 * @param {object} metadata Dodatkowe informacje skojarzone z markerem
 */
export function addTimelineMarker(type, metadata = {}) {
    if (!isRecordingActive && type !== 'recording_started') {
        return
    }
    
    const timestampMs = type === 'recording_started' ? 0 : Date.now() - recordingStartTime
    
    const marker = {
        timestamp_ms: timestampMs,
        type: type,
        ...metadata
    }
    
    timelineMarkers.push(marker)
    console.log(`Timeline Marker [${formatMsToTime(timestampMs)}]: ${type}`, metadata)
    
    // Wyzwól zdarzenie w DOM, aby zaktualizować interfejs (np. narysować kropkę)
    const event = new CustomEvent('studio-timeline-update', { detail: { marker, markers: timelineMarkers } })
    window.dispatchEvent(event)
}

/**
 * Zwraca aktualną listę markerów.
 */
export function getTimelineMarkers() {
    return timelineMarkers
}

/**
 * Generuje i pobiera plik JSON z timeline w przeglądarce (offline-first).
 */
export function downloadTimelineFile(recordingId, markers) {
    if (!markers || markers.length === 0) return
    
    const payload = {
        recording_id: recordingId,
        exported_at: new Date().toISOString(),
        duration_ms: markers[markers.length - 1].timestamp_ms,
        markers: markers
    }
    
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const filename = `${recordingId || 'tarotvision_recording'}.json`
    
    const a = document.createElement('a')
    a.style.display = 'none'
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    
    setTimeout(() => {
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
    }, 100)
    
    console.log(`Timeline offline file saved: ${filename}`)
    
    // Wyślij timeline na serwer komendą WebSocket
    sendControlMessage({
        type: 'studio_save_timeline',
        recording_id: recordingId,
        markers: markers
    })
}

/**
 * Helper do formatowania milisekund do postaci MM:SS.mmm
 */
export function formatMsToTime(ms) {
    const totalSecs = Math.floor(ms / 1000)
    const mins = Math.floor(totalSecs / 60).toString().padStart(2, '0')
    const secs = (totalSecs % 60).toString().padStart(2, '0')
    const millis = (ms % 1000).toString().padStart(3, '0')
    return `${mins}:${secs}.${millis}`
}
