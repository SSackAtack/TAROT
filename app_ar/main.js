import './style.css'
import * as THREE from 'three'

// 1. Inicjalizacja sceny (z pelna przezroczystoscia pod nakladke OBS)
const container = document.getElementById('app')
const scene = new THREE.Scene()

// Ustawienia kamery — widok z gory (90 stopni, prostopadle do stolu)
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000)
camera.position.set(0, 35, 0.001) // Y = gora, Z = mikro-offset zeby lookAt nie zwariowal
camera.lookAt(0, 0, 0)

// Renderer z kanalem Alpha (cienie WYLACZONE)
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
renderer.setSize(window.innerWidth, window.innerHeight)
renderer.setPixelRatio(window.devicePixelRatio)
renderer.shadowMap.enabled = false
container.appendChild(renderer.domElement)

// 2. Oswietlenie — proste, rownomierne (bez cieni)
const ambientLight = new THREE.AmbientLight(0xffffff, 2.0)
scene.add(ambientLight)

const dirLight = new THREE.DirectionalLight(0xffffff, 1.5)
dirLight.position.set(0, 20, 5)
dirLight.castShadow = false
scene.add(dirLight)

// 4. Preload tekstur z Promise.all + flaga gotowosci
const textureLoader = new THREE.TextureLoader()
const texturesCache = {}
let texturesReady = false  // Flaga blokujaca tworzenie kart przed zakonczeniem preloadu
let latestFrameData = null // Bufor na dane z WebSocketu przed zakonczeniem preloadu

// Opcje wirtualnej siatki pozycjonującej (Grid Snapping)
const GRID_SNAP_ENABLED = true
const GRID_SIZE_X = 4.2  // Odstęp między kolumnami (szerokość karty ~3.2 + przerwa ~1.0)
const GRID_SIZE_Y = 6.0  // Odstęp między rzędami (wysokość karty ~5.5 + przerwa ~0.5)

const cardNames = [
    "00_fool", "01_magician", "02_high_priestess", "03_empress", "04_emperor",
    "05_hierophant", "06_lovers", "07_chariot", "08_strength", "09_hermit",
    "10_wheel_of_fortune", "11_justice", "12_hanged_man", "13_death", "14_temperance",
    "15_devil", "16_tower", "17_star", "18_moon", "19_sun", "20_judgement", "21_world"
]

console.log("[PRELOAD] Rozpoczynam wczytywanie 22 tekstur tarota do pamieci...")

// Promise-based preloading — gwarantuje, ze texturesReady = true dopiero gdy WSZYSTKIE 22 sa gotowe
const preloadPromises = cardNames.map((name) => {
    return new Promise((resolve) => {
        const path = `/karty/${name}.webp`
        textureLoader.load(path, (texture) => {
            texturesCache[name] = texture
            texture.minFilter = THREE.LinearMipmapLinearFilter
            texture.magFilter = THREE.LinearFilter
            texture.colorSpace = THREE.SRGBColorSpace  // Poprawne odwzorowanie kolorow (wymagane od Three.js r152+)
            console.log(`[PRELOAD] Zaladowano: ${name}`)
            resolve()
        }, undefined, (err) => {
            console.error(`[PRELOAD BLAD] Nie udalo sie zaladowac: ${name}`, err)
            resolve() // Rozwiazujemy mimo bledu, zeby nie blokowac reszty
        })
    })
})

Promise.all(preloadPromises).then(() => {
    texturesReady = true
    console.log(`[PRELOAD] Wszystkie ${Object.keys(texturesCache).length} tekstur zaladowane i gotowe!`)
    
    // Jeśli otrzymaliśmy dane z WebSocketu przed załadowaniem tekstur — przetwarzamy je teraz!
    if (latestFrameData) {
        console.log("[PRELOAD] Przetwarzam zapamiętane dane WebSocket po załadowaniu tekstur...")
        handleCardData(latestFrameData)
    }
})

// 5. Wspoldzielona geometria karty — tworzona RAZ i reuzywana przez wszystkie instancje
// Eliminuje zbedne alokacje GPU (audit: kazda karta tworzyla wlasna kopie geometrii)
let sharedGeometry = null
let sharedCardWidth = 0
let sharedCardHeight = 0

function getSharedGeometry(aspect) {
    if (sharedGeometry) return sharedGeometry

    sharedCardHeight = 5.5
    sharedCardWidth = sharedCardHeight * aspect

    const shape = new THREE.Shape()
    const radius = 0.24
    const x = -sharedCardWidth / 2
    const y = -sharedCardHeight / 2

    shape.moveTo(x, y + radius)
    shape.lineTo(x, y + sharedCardHeight - radius)
    shape.quadraticCurveTo(x, y + sharedCardHeight, x + radius, y + sharedCardHeight)
    shape.lineTo(x + sharedCardWidth - radius, y + sharedCardHeight)
    shape.quadraticCurveTo(x + sharedCardWidth, y + sharedCardHeight, x + sharedCardWidth, y + sharedCardHeight - radius)
    shape.lineTo(x + sharedCardWidth, y + radius)
    shape.quadraticCurveTo(x + sharedCardWidth, y, x + sharedCardWidth - radius, y)
    shape.lineTo(x + radius, y)
    shape.quadraticCurveTo(x, y, x, y + radius)

    const extrudeSettings = {
        steps: 1,
        depth: 0.08,
        bevelEnabled: true,
        bevelThickness: 0.02,
        bevelSize: 0.015,
        bevelSegments: 4
    }

    sharedGeometry = new THREE.ExtrudeGeometry(shape, extrudeSettings)
    sharedGeometry.center()

    // Reczna korekta UV — wykonana RAZ, nie przy kazdej karcie
    const pos = sharedGeometry.attributes.position
    const uvs = sharedGeometry.attributes.uv
    for (let i = 0; i < pos.count; i++) {
        const u = (pos.getX(i) + sharedCardWidth / 2) / sharedCardWidth
        const v = (pos.getY(i) + sharedCardHeight / 2) / sharedCardHeight
        uvs.setXY(i, u, v)
    }
    uvs.needsUpdate = true

    console.log(`[AR] Wspoldzielona geometria utworzona (${sharedCardWidth.toFixed(2)} x ${sharedCardHeight})`)
    return sharedGeometry
}

// 6. Zarzadzanie instancjami kart 3D
const activeCards = {}

// Wspoldzielony material zlotych krawedzi — identyczny dla wszystkich kart (audit: tworzony byl od nowa per karta)
const sharedEdgeMaterial = new THREE.MeshStandardMaterial({
    color: 0xd4af37,
    roughness: 0.22,
    metalness: 0.85,
    transparent: true,
    opacity: 0.0
})

function createVirtualCard(name) {
    if (!texturesReady) {
        console.warn(`[WARN] Preload jeszcze nie zakonczony — pomijam karte ${name}`)
        return
    }

    const texture = texturesCache[name]
    if (!texture) {
        console.warn(`[WARN] Tekstura dla karty ${name} nie istnieje w Cache!`)
        return
    }

    const aspect = texture.image ? (texture.image.width / texture.image.height) : (70 / 120)
    const geometry = getSharedGeometry(aspect) // Reuzywamy wspoldzielona geometrie

    // Kazda karta potrzebuje wlasnego materialu face (inna tekstura), ale klonujemy edge material
    const faceMaterial = new THREE.MeshStandardMaterial({ 
        map: texture,
        transparent: true,
        opacity: 0.0,
        roughness: 0.55,
        metalness: 0.05,
        side: THREE.DoubleSide
    })

    // Klonujemy edge material (potrzebne bo kazda karta ma niezalezna opacity)
    const edgeMaterial = sharedEdgeMaterial.clone()

    const mesh = new THREE.Mesh(geometry, [faceMaterial, edgeMaterial])
    // Cienie WYLACZONE
    
    const cardInstanceGroup = new THREE.Group()
    cardInstanceGroup.add(mesh)
    
    // Karta lezaca plasko na stole (90 stopni)
    cardInstanceGroup.rotation.x = -Math.PI / 2
    cardInstanceGroup.position.set(0, 0, 0)
    scene.add(cardInstanceGroup)

    activeCards[name] = {
        group: cardInstanceGroup,
        faceMaterial: faceMaterial,
        edgeMaterial: edgeMaterial,
        currentOpacity: 0.0,
        targetOpacity: 1.0,
        targetX: 0.0,
        targetY: 0.0,
        targetAngle: 0.0
    }
    
    console.log(`[AR] Utworzono karte 3D: ${name}`)
}

// 7. Wspólna funkcja przetwarzania danych o kartach (zapobiega wyścigom)
function handleCardData(detectedCards) {
    if (!texturesReady) {
        latestFrameData = detectedCards
        console.log("[PRELOAD] Dane o kartach z WebSocketu dotarły przed ukończeniem wczytywania grafik. Buforuję dane.")
        return
    }

    const detectedNames = detectedCards.map(c => c.name)
    
    Object.keys(activeCards).forEach((name) => {
        if (detectedNames.includes(name)) {
            activeCards[name].targetOpacity = 1.0
        } else {
            activeCards[name].targetOpacity = 0.0
        }
    })

    detectedCards.forEach((cardData) => {
        const name = cardData.name
        
        // Walidacja danych WebSocket — chroni przed NaN/undefined
        if (!cardNames.includes(name)) return
        if (typeof cardData.x !== 'number' || typeof cardData.y !== 'number') return
        
        if (!activeCards[name]) {
            createVirtualCard(name)
        }
        
        if (activeCards[name]) {
            activeCards[name].targetOpacity = 1.0
            
            // Przyciąganie współrzędnych do wirtualnej siatki (Grid Snapping)
            const rawX = cardData.x
            const rawY = cardData.y
            if (GRID_SNAP_ENABLED) {
                activeCards[name].targetX = Math.round(rawX / GRID_SIZE_X) * GRID_SIZE_X
                activeCards[name].targetY = Math.round(rawY / GRID_SIZE_Y) * GRID_SIZE_Y
            } else {
                activeCards[name].targetX = rawX
                activeCards[name].targetY = rawY
            }

            // Przyciąganie kąta (Angle Snapping) do najbliższej wielokrotności 90 stopni (Math.PI / 2)
            // Dzięki temu wirtualne karty trzymają zawsze idealny pion (0°, 180°) lub poziom (90°, 270°)
            const rawAngle = cardData.angle || 0
            activeCards[name].targetAngle = Math.round(rawAngle / (Math.PI / 2)) * (Math.PI / 2)
        }
    })
}

// 8. WebSocket z exponential backoff
let wsReconnectDelay = 1000 // Start: 1s, max: 15s
const WS_MAX_DELAY = 15000

function connectWebSocket() {
    console.log("[WEBSOCKET] Laczenie z TarotVision CV...")
    const ws = new WebSocket("ws://localhost:8765")

    ws.onopen = () => {
        console.log("[WEBSOCKET] Polaczono! Oczekiwanie na rozklady kart...")
        wsReconnectDelay = 1000 // Reset delay po udanym polaczeniu
    }

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data)
            const detectedCards = data.cards || []
            handleCardData(detectedCards)
        } catch (e) {
            console.error("[WEBSOCKET ERROR] Blad przetwarzania danych:", e)
        }
    }

    ws.onclose = () => {
        console.warn(`[WEBSOCKET] Polaczenie utracone. Ponowna proba za ${(wsReconnectDelay / 1000).toFixed(1)}s...`)
        Object.keys(activeCards).forEach((name) => {
            activeCards[name].targetOpacity = 0.0
        })
        setTimeout(connectWebSocket, wsReconnectDelay)
        // Exponential backoff — kazda nieudana proba podwaja delay (max 15s)
        wsReconnectDelay = Math.min(wsReconnectDelay * 2, WS_MAX_DELAY)
    }

    ws.onerror = () => {
        ws.close()
    }
}

connectWebSocket()

// 9. Główna pętla renderowania (bez zbędnego zegara THREE.Clock)
function animate() {
    requestAnimationFrame(animate)

    const visibleCardNames = Object.keys(activeCards)
        .filter((name) => activeCards[name].currentOpacity > 0.01 || activeCards[name].targetOpacity > 0.0)
        .sort()

    visibleCardNames.forEach((name, index) => {
        const cardObj = activeCards[name]

        // Natychmiastowa zmiana przezroczystosci (bez LERP)
        if (cardObj.targetOpacity > 0.5) {
            cardObj.currentOpacity = 1.0
        } else {
            cardObj.currentOpacity -= 0.05 // Szybkie wygaszanie
            if (cardObj.currentOpacity < 0) cardObj.currentOpacity = 0
        }
        cardObj.faceMaterial.opacity = cardObj.currentOpacity
        cardObj.edgeMaterial.opacity = cardObj.currentOpacity

        // Czyszczenie pamieci po pelnym wygaszeniu (NIE disposujemy wspoldzielonej geometrii!)
        if (cardObj.targetOpacity === 0.0 && cardObj.currentOpacity <= 0.01) {
            scene.remove(cardObj.group)
            cardObj.group.traverse((child) => {
                if (child.isMesh) {
                    // Geometria jest wspoldzielona — NIE disposujemy jej!
                    if (Array.isArray(child.material)) {
                        child.material.forEach((m) => m.dispose())
                    } else {
                        child.material.dispose()
                    }
                }
            })
            delete activeCards[name]
            console.log(`[AR] Usunieto i wyczyszczono karte: ${name}`)
            return
        }

        // BEZPOSREDNIE ustawianie pozycji (ZERO animacji, ZERO mikro-ruchow)
        cardObj.group.position.x = cardObj.targetX
        cardObj.group.position.z = -cardObj.targetY // Z bo kamera patrzy z gory (Y->Z mapping)

        // Bezposrednie ustawienie kata obrotu
        cardObj.group.rotation.z = cardObj.targetAngle
    })

    renderer.render(scene, camera)
}

// Resizing
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
})

animate()
