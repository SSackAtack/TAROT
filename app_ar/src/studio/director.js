import { studioState } from './studioState'
import { appState } from '../core/appState'
import { sendControlMessage } from '../transport/wsClient'

let hysteresisTimeout = null
let currentPendingScene = null

/**
 * Przetwarza bieżący status z WebSocketu pod kątem decyzji automatycznego reżysera.
 * 
 * @param {object} payload Znormalizowany status payload v1 nadesłany z serwera
 */
export function processDirectorDecision(payload) {
    if (studioState.directorMode !== 'auto') {
        // Jeśli jesteśmy w trybie manualnym, nic nie robimy
        return
    }

    const cardsOnTable = payload.cards && payload.cards.length > 0
    const currentScene = studioState.activeScene

    if (cardsOnTable) {
        // Są karty na stole - przełącz na WOW mode
        if (hysteresisTimeout) {
            clearTimeout(hysteresisTimeout)
            hysteresisTimeout = null
        }
        currentPendingScene = null

        if (currentScene !== 'wow') {
            console.log('Director Auto-Switch: Cards detected, switching to WOW scene.')
            setDirectorScene('wow')
        }
    } else {
        // Brak kart na stole - chcemy powrócić do widoku standardowego stołu (table)
        if (currentScene !== 'table' && currentScene !== 'title_card') {
            if (currentPendingScene !== 'table') {
                if (hysteresisTimeout) {
                    clearTimeout(hysteresisTimeout)
                }
                
                currentPendingScene = 'table'
                // Ustawiamy histerezę 1.5 sekundy (1500 ms) w celu stabilizacji
                hysteresisTimeout = setTimeout(() => {
                    console.log('Director Auto-Switch: No cards detected (hysteresis ended), returning to table scene.')
                    setDirectorScene('table')
                    hysteresisTimeout = null
                    currentPendingScene = null
                }, 1500)
            }
        } else {
            // Jesteśmy już w scenie stołu lub intro, czyścimy ewentualne timery
            if (hysteresisTimeout) {
                clearTimeout(hysteresisTimeout)
                hysteresisTimeout = null
            }
            currentPendingScene = null
        }
    }
}

/**
 * Uruchamia fizyczną zmianę sceny w systemie reżyserskim.
 * 
 * @param {string} scene Nowa wybrana scena
 */
function setDirectorScene(scene) {
    studioState.activeScene = scene

    // Specjalna interakcja lokalna we frontendzie
    if (scene === 'wow') {
        appState.wowMode = true
        document.body.classList.add('wow-mode-active')
    } else if (scene === 'table') {
        appState.wowMode = false
        document.body.classList.remove('wow-mode-active')
    }

    // Wyślij zmianę na backend
    sendControlMessage({
        type: 'studio_set_director_scene',
        scene: scene
    })
}
