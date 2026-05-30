import { studioState } from './studioState'
import { sendControlMessage } from '../transport/wsClient'
import { renderer } from '../renderer/arRenderer'
import { getStudioAudioTrack, playSyntheticSFX } from './audioMixer'
import { initTimeline, finalizeTimeline, downloadTimelineFile } from './timeline'

let mediaRecorder = null
let recordedChunks = []
let recordingStartTime = 0
let timerInterval = null

/**
 * Inicjalizuje i sprawdza dostępne formaty MIME dla nagrywania w wideo.
 */
export function getSupportedMimeType() {
    const types = [
        'video/webm;codecs=vp9,opus',
        'video/webm;codecs=vp8,opus',
        'video/webm',
        'video/mp4'
    ]
    for (const type of types) {
        if (MediaRecorder.isTypeSupported(type)) {
            return type
        }
    }
    return ''
}

/**
 * Rozpoczyna nagrywanie live streamu z canvasu Three.js.
 */
export async function startStudioRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        console.warn('Recording is already in progress')
        return
    }

    if (!renderer || !renderer.domElement) {
        console.error('Canvas renderer is not initialized yet')
        studioState.recordingState = 'error'
        return
    }

    const canvas = renderer.domElement
    const mimeType = getSupportedMimeType()
    if (!mimeType) {
        console.error('No supported MediaRecorder MIME types found in this browser')
        studioState.recordingState = 'error'
        return
    }

    recordedChunks = []
    
    // Przechwycenie strumienia z canvasu (30 FPS)
    const canvasStream = canvas.captureStream(30)
    const videoTrack = canvasStream.getVideoTracks()[0]
    
    // Przechwycenie ścieżki audio z miksera master
    const audioTrack = getStudioAudioTrack()
    const tracks = [videoTrack]
    if (audioTrack) {
        tracks.push(audioTrack)
        console.log('Audio track successfully attached to MediaRecorder.')
    } else {
        console.warn('No active audio track found. Recording will proceed video-only.')
    }
    
    const combinedStream = new MediaStream(tracks)
    
    // Przygotowanie opcji
    const options = { mimeType }
    
    try {
        mediaRecorder = new MediaRecorder(combinedStream, options)
    } catch (err) {
        console.error('Failed to create MediaRecorder:', err)
        studioState.recordingState = 'error'
        return
    }

    // Odtwórz dźwięk startu nagrywania
    playSyntheticSFX('start_rec')

    // Rejestracja zdarzeń MediaRecorder
    mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
            recordedChunks.push(event.data)
        }
    }

    mediaRecorder.onstop = () => {
        finalizeRecording()
    }

    // Wygenerowanie unikalnego ID nagrania
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const recordingId = `rec_${timestamp}`

    // Ustawienie lokalnego stanu nagrywania
    studioState.recordingState = 'recording'
    studioState.recordingId = recordingId
    
    // Inicjalizacja osi czasu
    initTimeline()
    
    studioState.elapsedMs = 0
    studioState.droppedFrames = 0
    recordingStartTime = Date.now()

    // Rozpoczęcie nagrywania w chunkach 1-sekundowych
    mediaRecorder.start(1000)

    // Powiadomienie backendu o rozpoczęciu nagrywania
    sendControlMessage({
        type: 'studio_start_recording',
        recording_id: recordingId
    })

    // Uruchomienie licznika czasu
    timerInterval = setInterval(() => {
        studioState.elapsedMs = Date.now() - recordingStartTime
        
        // Wyślij okresową aktualizację stanu do backendu, aby zsynchronizować diagnostykę
        sendControlMessage({
            type: 'studio_update_recording_status',
            recording_state: 'recording',
            recording_id: recordingId,
            elapsed_ms: studioState.elapsedMs,
            dropped_frames: studioState.droppedFrames
        })
    }, 250)

    console.log(`Studio recording started. ID: ${recordingId}, MIME: ${mimeType}`)
}

/**
 * Zatrzymuje aktualne nagrywanie.
 */
export function stopStudioRecording() {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        console.warn('No active recording to stop')
        return
    }

    studioState.recordingState = 'stopping'
    
    // Odtwórz dźwięk zakończenia nagrywania
    playSyntheticSFX('stop_rec')
    
    if (timerInterval) {
        clearInterval(timerInterval)
        timerInterval = null
    }

    mediaRecorder.stop()

    // Powiadomienie backendu o zatrzymaniu nagrywania
    sendControlMessage({
        type: 'studio_stop_recording'
    })
}

/**
 * Finalizuje nagranie, scala chunky i wyzwala pobieranie pliku (MVP A).
 */
function finalizeRecording() {
    console.log('Finalizing recording...')
    
    // Zakończenie i eksport timeline
    const recId = studioState.recordingId
    const markers = finalizeTimeline()
    if (markers && markers.length > 0) {
        downloadTimelineFile(recId, markers)
    }

    if (recordedChunks.length === 0) {
        console.error('No recorded chunks available')
        studioState.recordingState = 'error'
        return
    }

    const mimeType = getSupportedMimeType()
    const blob = new Blob(recordedChunks, { type: mimeType })
    const url = URL.createObjectURL(blob)
    
    const filename = `${recId || 'tarotvision_recording'}.webm`
    
    // MVP A: Lokalny download pliku w przeglądarce
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

    console.log(`Recording file saved: ${filename}`)
    
    // Powrót do stanu bezczynności
    studioState.recordingState = 'idle'
    studioState.recordingId = null
    studioState.elapsedMs = 0
    studioState.droppedFrames = 0
}
