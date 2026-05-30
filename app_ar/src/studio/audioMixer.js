import { studioState } from './studioState'
import { sendControlMessage } from '../transport/wsClient'

let audioContext = null
let masterGain = null
let monitorGain = null
let mediaStreamDestination = null
let analyserNode = null

const channels = {
    mic: { gainNode: null, sourceNode: null, active: false },
    bgm: { gainNode: null, sourceNode: null, audioElement: null, active: false },
    sfx: { gainNode: null, active: false }
}

let peakInterval = null

/**
 * Inicjalizuje graf Web Audio API miksera.
 * Wywoływane przy pierwszej interakcji użytkownika (np. zmiana suwaka, kliknięcie arm).
 */
export function initAudioMixer() {
    if (audioContext) return audioContext

    try {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext
        audioContext = new AudioContextClass()
        
        // Master Gain dla nagrywania (łączy wszystkie kanały)
        masterGain = audioContext.createGain()
        masterGain.gain.value = studioState.masterMuted ? 0 : studioState.masterVolume
        
        // Monitor Gain dla głośników operatora (podsłuch tła i SFX bez mikrofonu, by uniknąć sprzężeń)
        monitorGain = audioContext.createGain()
        monitorGain.gain.value = studioState.masterMuted ? 0 : studioState.masterVolume
        monitorGain.connect(audioContext.destination)

        // Analizator Peak (dB) podpięty pod master nagrywania
        analyserNode = audioContext.createAnalyser()
        analyserNode.fftSize = 256
        masterGain.connect(analyserNode)

        // Wyjście strumienia dla MediaRecorder
        mediaStreamDestination = audioContext.createMediaStreamDestination()
        masterGain.connect(mediaStreamDestination)

        // Inicjalizacja poszczególnych kanałów gain
        const chNames = ['mic', 'bgm', 'sfx']
        chNames.forEach(name => {
            const gainNode = audioContext.createGain()
            
            // Pobranie domyślnych wartości ze stanu studia
            const vol = studioState[`${name}Volume`]
            const muted = studioState[`${name}Muted`]
            gainNode.gain.value = muted ? 0 : vol
            
            channels[name].gainNode = gainNode
            
            // Podłączenie kanałów do master (do nagrania)
            gainNode.connect(masterGain)
            
            // Podłączenie BGM i SFX również do monitora (słyszalne w głośnikach)
            if (name !== 'mic') {
                gainNode.connect(monitorGain)
            }
        })

        console.log('Studio Audio Mixer initialized successfully.')
        
        // Rozpoczęcie monitorowania wskaźnika poziomu Peak
        startPeakMonitoring()

        // Załadujmy domyślny podkład muzyczny offline (syntetyczny generator lub pusty odtwarzacz w MVP)
        setupBgmPlayer()

        return audioContext
    } catch (err) {
        console.error('Failed to initialize Audio Mixer:', err)
        return null
    }
}

/**
 * Uruchamia pobieranie strumienia mikrofonu operatora.
 */
export async function startStudioMicrophone() {
    initAudioMixer()
    if (!audioContext) return false

    if (audioContext.state === 'suspended') {
        await audioContext.resume()
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        })

        if (channels.mic.sourceNode) {
            channels.mic.sourceNode.disconnect()
        }

        const source = audioContext.createMediaStreamSource(stream)
        source.connect(channels.mic.gainNode)
        
        channels.mic.sourceNode = source
        channels.mic.active = true
        
        console.log('Microphone capture started successfully.')
        return true
    } catch (err) {
        console.warn('Could not capture microphone (Recording will proceed video-only or BGM-only):', err)
        
        // Zasygnalizuj ostrzeżenie w UI
        const pathStatus = document.querySelector('#studio-path-status')
        if (pathStatus) {
            pathStatus.textContent = 'Ostrzeżenie: Brak dostępu do mikrofonu (Nagrywanie wideo-only)'
            pathStatus.style.color = '#fbbf24'
        }
        
        channels.mic.active = false
        return false
    }
}

/**
 * Zwraca ścieżkę dźwiękową miksu master w celu dołączenia do nagrania.
 */
export function getStudioAudioTrack() {
    if (!mediaStreamDestination) return null
    const tracks = mediaStreamDestination.stream.getAudioTracks()
    return tracks.length > 0 ? tracks[0] : null
}

/**
 * Ustawia odtwarzacz muzyki w tle (BGM).
 */
function setupBgmPlayer() {
    // W MVP używamy elementu audio. Możemy załadować plik lokalny lub zaimplementować generator szumu / tła.
    const audio = new Audio()
    audio.loop = true
    audio.crossOrigin = 'anonymous'
    
    // Przykładowa licencjonowana premium pętla ambientowa offline (opcjonalny pusty element w MVP)
    channels.bgm.audioElement = audio
    
    try {
        const source = audioContext.createMediaElementSource(audio)
        source.connect(channels.bgm.gainNode)
        channels.bgm.sourceNode = source
        channels.bgm.active = true
    } catch (err) {
        console.warn('BGM source setup failed:', err)
    }
}

/**
 * Zmienia utwór lub pętlę muzyki w tle (BGM).
 */
export function playBgmUrl(url) {
    initAudioMixer()
    const audio = channels.bgm.audioElement
    if (!audio) return

    try {
        audio.src = url
        // Uruchamiamy odtwarzanie po interakcji
        if (audioContext && audioContext.state !== 'suspended') {
            audio.play().catch(err => console.log('BGM play deferred until user interaction:', err))
        }
    } catch (err) {
        console.error('Failed to play BGM:', err)
    }
}

/**
 * Aktualizuje parametry głośności i wyciszenia w grafie audio na podstawie studioState.
 */
export function updateAudioMixerValues() {
    if (!audioContext) return

    // 1. Aktualizacja suwaków kanałów
    const chNames = ['mic', 'bgm', 'sfx']
    chNames.forEach(name => {
        const gainNode = channels[name].gainNode
        if (gainNode) {
            const vol = studioState[`${name}Volume`]
            const muted = studioState[`${name}Muted`]
            
            // Płynna zmiana głośności (LinearRamp) w celu uniknięcia trzasków dźwiękowych
            gainNode.gain.setTargetAtTime(muted ? 0 : vol, audioContext.currentTime, 0.05)
        }
    })

    // 2. Aktualizacja Master Volume
    if (masterGain && monitorGain) {
        const vol = studioState.masterVolume
        const muted = studioState.masterMuted
        
        masterGain.gain.setTargetAtTime(muted ? 0 : vol, audioContext.currentTime, 0.05)
        monitorGain.gain.setTargetAtTime(muted ? 0 : vol, audioContext.currentTime, 0.05)
    }
}

/**
 * Odtwarza syntetyczny efekt dźwiękowy offline (generowany na żywo).
 * Gwarantuje działanie w 100% offline bez zależności plikowych w MVP!
 * Daje rewelacyjny efekt dźwiękowy premium.
 */
export function playSyntheticSFX(type = 'snapshot') {
    initAudioMixer()
    if (!audioContext) return

    if (audioContext.state === 'suspended') {
        audioContext.resume()
    }

    const osc = audioContext.createOscillator()
    const gain = audioContext.createGain()
    
    osc.connect(gain)
    gain.connect(channels.sfx.gainNode)

    const now = audioContext.currentTime

    if (type === 'snapshot') {
        // Futurystyczny, czysty, krótki dźwięk 'chirp'
        osc.type = 'sine'
        osc.frequency.setValueAtTime(600, now)
        osc.frequency.exponentialRampToValueAtTime(1200, now + 0.12)
        
        gain.gain.setValueAtTime(0.3, now)
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15)
        
        osc.start(now)
        osc.stop(now + 0.16)
    } else if (type === 'start_rec') {
        // Podwójny narastający ton oznajmiający start nagrywania
        osc.type = 'triangle'
        osc.frequency.setValueAtTime(440, now)
        osc.frequency.setValueAtTime(554.37, now + 0.08)
        osc.frequency.setValueAtTime(659.25, now + 0.16)
        
        gain.gain.setValueAtTime(0.25, now)
        gain.gain.setValueAtTime(0.25, now + 0.16)
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35)
        
        osc.start(now)
        osc.stop(now + 0.36)
    } else if (type === 'stop_rec') {
        // Opadający, ciepły dźwięk zakończenia nagrywania
        osc.type = 'sine'
        osc.frequency.setValueAtTime(523.25, now) // C5
        osc.frequency.exponentialRampToValueAtTime(261.63, now + 0.25) // C4
        
        gain.gain.setValueAtTime(0.28, now)
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3)
        
        osc.start(now)
        osc.stop(now + 0.31)
    }
}

/**
 * Uruchamia pętlę monitorowania poziomów Peak (dB).
 * Oblicza RMS i Peak z próbek czasowych w master nagrania.
 */
function startPeakMonitoring() {
    if (peakInterval) clearInterval(peakInterval)

    const bufferLength = analyserNode.frequencyBinCount
    const dataArray = new Float32Array(bufferLength)

    peakInterval = setInterval(() => {
        if (!analyserNode || !audioContext) return

        analyserNode.getFloatTimeDomainData(dataArray)

        // Obliczenie wartości szczytowej (Peak) w próbce klatki czasowej
        let maxVal = 0
        for (let i = 0; i < bufferLength; i++) {
            const val = Math.abs(dataArray[i])
            if (val > maxVal) maxVal = val
        }

        // Konwersja amplitudy na decybele (dBFS)
        let peakDb = -96 // minimalny próg
        if (maxVal > 0.00001) {
            peakDb = 20 * Math.log10(maxVal)
        }

        // Zaokrąglenie i ograniczenie
        peakDb = Math.max(-96, Math.min(0, parseFloat(peakDb.toFixed(1))))
        
        // Zapis do stanu studia
        studioState.audioPeakDb = peakDb

        // Wyślij poziom Peak do backendu za pomocą WebSocket, aby zapisać w plikach sesji i diagnostics
        sendControlMessage({
            type: 'studio_update_audio_peak',
            peak_db: peakDb
        })

        // Rysuj mierniki audio w interfejsie konsoli
        drawAudioVisualizer(peakDb)
    }, 150)
}

/**
 * Pomocnicza funkcja rysująca miernik głośności na suwaku Master lub dedykowanym pasku.
 */
function drawAudioVisualizer(peakDb) {
    const channels = ['mic', 'bgm', 'sfx', 'master']
    
    // Wizualizujemy poziom master na dedykowanym mierniku peak w Master kanale
    const masterChannelEl = document.querySelector('.studio-audio-channel:last-child')
    if (!masterChannelEl) return

    // Jeśli nie ma paska wizualnego, stwórzmy go dynamicznie dla premium wyglądu!
    let meterBar = masterChannelEl.querySelector('.studio-audio-meter-bar')
    if (!meterBar) {
        meterBar = document.createElement('div')
        meterBar.className = 'studio-audio-meter-bar'
        meterBar.style.cssText = `
            grid-column: 1 / -1;
            height: 4px;
            background: rgba(15, 23, 42, 0.8);
            border-radius: 2px;
            margin-top: 4px;
            overflow: hidden;
            position: relative;
        `
        const fill = document.createElement('div')
        fill.className = 'studio-audio-meter-fill'
        fill.style.cssText = `
            height: 100%;
            width: 0%;
            background: linear-gradient(to right, #34d399 60%, #fbbf24 85%, #f87171 100%);
            box-shadow: 0 0 6px #34d399;
            transition: width 0.1s ease;
        `
        meterBar.appendChild(fill)
        masterChannelEl.appendChild(meterBar)
    }

    const fill = meterBar.querySelector('.studio-audio-meter-fill')
    if (fill) {
        // Skalowanie dB [-60, 0] na procenty [0, 100]%
        const minDb = -60
        let percent = 0
        if (peakDb > minDb) {
            percent = ((peakDb - minDb) / (0 - minDb)) * 100
        }
        fill.style.width = `${percent}%`
        
        // Zmiana koloru cienia przy wysokim sygnale (przesterowanie/clip)
        if (peakDb > -3) {
            fill.style.boxShadow = '0 0 8px #f87171'
        } else if (peakDb > -12) {
            fill.style.boxShadow = '0 0 6px #fbbf24'
        } else {
            fill.style.boxShadow = '0 0 6px #34d399'
        }
    }
}
