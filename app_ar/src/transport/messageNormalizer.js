/**
 * Normalizer wiadomości WebSocket dla TarotVision (Status Payload v1).
 * Gwarantuje stabilność działania frontendu poprzez wypełnianie brakujących pól domyślnymi wartościami.
 */

export function normalizeStatusPayload(rawPayload) {
    if (!rawPayload || typeof rawPayload !== 'object') {
        return createDefaultPayload()
    }

    const payload = { ...rawPayload }

    // Wersjonowanie i domyślne sekcje
    payload.schema_version = payload.schema_version || 1
    payload.detected = typeof payload.detected === 'boolean' ? payload.detected : false
    payload.cards = Array.isArray(payload.cards) ? payload.cards : []
    payload.metrics = payload.metrics || {}
    payload.warnings = Array.isArray(payload.warnings) ? payload.warnings : []
    payload.debug = payload.debug || {}
    payload.runtime = payload.runtime || {}
    
    // Normalizacja sekcji operatora
    payload.operator = {
        enabled: true,
        active_profile: 'default',
        parameters: {},
        parameter_metadata: {},
        pending_changes: {},
        supported_camera_controls: {},
        calibration: { state: 'idle', last_score: null },
        warnings: [],
        ...payload.operator
    }

    // Normalizacja sekcji table i layout
    payload.table = payload.table || {}
    payload.layout = payload.layout || {}

    // Normalizacja sekcji studio
    payload.studio = {
        recording_state: 'idle',
        recording_id: null,
        elapsed_ms: 0,
        dropped_frames: 0,
        audio_peak_db: null,
        director_scene: 'table',
        director_mode: 'manual',
        ...payload.studio
    }

    if (!payload.studio.audio) {
        payload.studio.audio = {
            channels: {
                mic: { volume: 1.0, muted: false },
                bgm: { volume: 0.5, muted: false },
                sfx: { volume: 0.8, muted: false },
                master: { volume: 1.0, muted: false }
            },
            peak_db: null
        }
    } else {
        payload.studio.audio = {
            channels: {
                mic: { volume: 1.0, muted: false },
                bgm: { volume: 0.5, muted: false },
                sfx: { volume: 0.8, muted: false },
                master: { volume: 1.0, muted: false },
                ...(payload.studio.audio.channels || {})
            },
            peak_db: payload.studio.audio.peak_db !== undefined ? payload.studio.audio.peak_db : null
        }
    }

    return payload
}

export function createDefaultPayload() {
    return {
        schema_version: 1,
        detected: false,
        cards: [],
        metrics: {},
        warnings: [],
        debug: {},
        runtime: {},
        operator: {
            enabled: true,
            active_profile: 'default',
            parameters: {},
            parameter_metadata: {},
            pending_changes: {},
            supported_camera_controls: {},
            calibration: { state: 'idle', last_score: null },
            warnings: []
        },
        table: {},
        layout: {},
        studio: {
            recording_state: 'idle',
            recording_id: null,
            elapsed_ms: 0,
            dropped_frames: 0,
            audio_peak_db: null,
            director_scene: 'table',
            director_mode: 'manual',
            audio: {
                channels: {
                    mic: { volume: 1.0, muted: false },
                    bgm: { volume: 0.5, muted: false },
                    sfx: { volume: 0.8, muted: false },
                    master: { volume: 1.0, muted: false }
                },
                peak_db: null
            }
        }
    }
}
