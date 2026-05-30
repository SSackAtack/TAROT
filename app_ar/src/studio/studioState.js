import { appState } from '../core/appState'

export const studioState = {
    // Lokalne ustawienia konsoli studio
    activeScene: 'table', // table, wow, portrait_pip, title_card
    directorMode: 'manual', // manual, auto
    micVolume: parseFloat(localStorage.getItem('studio_micVolume') || '1.0'),
    bgmVolume: parseFloat(localStorage.getItem('studio_bgmVolume') || '0.5'),
    sfxVolume: parseFloat(localStorage.getItem('studio_sfxVolume') || '0.8'),
    masterVolume: parseFloat(localStorage.getItem('studio_masterVolume') || '1.0'),
    micMuted: localStorage.getItem('studio_micMuted') === 'true',
    bgmMuted: localStorage.getItem('studio_bgmMuted') === 'true',
    sfxMuted: localStorage.getItem('studio_sfxMuted') === 'true',
    masterMuted: localStorage.getItem('studio_masterMuted') === 'true',
    
    // Status nagrywania synchronizowany z WebSocket / MediaRecorder
    recordingState: 'idle', // idle, armed, recording, stopping, error
    recordingId: null,
    elapsedMs: 0,
    droppedFrames: 0,
    audioPeakDb: null,
}

export function saveStudioVolumeSettings() {
    localStorage.setItem('studio_micVolume', studioState.micVolume.toString())
    localStorage.setItem('studio_bgmVolume', studioState.bgmVolume.toString())
    localStorage.setItem('studio_sfxVolume', studioState.sfxVolume.toString())
    localStorage.setItem('studio_masterVolume', studioState.masterVolume.toString())
    localStorage.setItem('studio_micMuted', studioState.micMuted.toString())
    localStorage.setItem('studio_bgmMuted', studioState.bgmMuted.toString())
    localStorage.setItem('studio_sfxMuted', studioState.sfxMuted.toString())
    localStorage.setItem('studio_masterMuted', studioState.masterMuted.toString())
}

export function updateStudioStateFromPayload(studioPayload) {
    if (!studioPayload) return
    studioState.recordingState = studioPayload.recording_state || 'idle'
    studioState.recordingId = studioPayload.recording_id || null
    studioState.elapsedMs = studioPayload.elapsed_ms || 0
    studioState.droppedFrames = studioPayload.dropped_frames || 0
    studioState.audioPeakDb = studioPayload.audio_peak_db !== undefined ? studioPayload.audio_peak_db : null
    studioState.activeScene = studioPayload.director_scene || 'table'
    studioState.directorMode = studioPayload.director_mode || 'manual'

    if (studioPayload.audio && studioPayload.audio.channels) {
        const channels = ['mic', 'bgm', 'sfx', 'master']
        channels.forEach(ch => {
            if (studioPayload.audio.channels[ch]) {
                studioState[`${ch}Volume`] = studioPayload.audio.channels[ch].volume
                studioState[`${ch}Muted`] = studioPayload.audio.channels[ch].muted
            }
        })
        if (studioPayload.audio.peak_db !== undefined) {
            studioState.audioPeakDb = studioPayload.audio.peak_db
        }
    }
}
