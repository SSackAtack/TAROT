import './style.css'
import * as THREE from 'three'

// 1. Inicjalizacja sceny (z pelna przezroczystoscia pod nakladke OBS)
const container = document.getElementById('app')
const scene = new THREE.Scene()

// Ustawienia kamery
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000)
camera.position.z = 20
camera.position.y = 7  
camera.lookAt(0, 3, 0) 

// Renderer z kanalem Alpha i cieniami
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
renderer.setSize(window.innerWidth, window.innerHeight)
renderer.setPixelRatio(window.devicePixelRatio)
renderer.shadowMap.enabled = true
renderer.shadowMap.type = THREE.PCFShadowMap
container.appendChild(renderer.domElement)

// 2. Oswietlenie
const ambientLight = new THREE.AmbientLight(0xffffff, 1.4) 
scene.add(ambientLight)

const dirLight = new THREE.DirectionalLight(0xffffff, 2.5) 
dirLight.position.set(5, 12, 5)
dirLight.castShadow = true
dirLight.shadow.camera.top = 12
dirLight.shadow.camera.bottom = -12
dirLight.shadow.camera.left = -15
dirLight.shadow.camera.right = 15
dirLight.shadow.mapSize.width = 1024
dirLight.shadow.mapSize.height = 1024
scene.add(dirLight)

// 3. Shadow Catcher (Lapacz cieni)
const shadowPlaneGeo = new THREE.PlaneGeometry(150, 150)
const shadowPlaneMat = new THREE.ShadowMaterial({ opacity: 0.55 })
const shadowPlane = new THREE.Mesh(shadowPlaneGeo, shadowPlaneMat)
shadowPlane.rotation.x = -Math.PI / 2
shadowPlane.position.y = -0.1
shadowPlane.receiveShadow = true
scene.add(shadowPlane)

// 4. Preload tekstur z Promise.all + flaga gotowosci
const textureLoader = new THREE.TextureLoader()
const texturesCache = {}
let texturesReady = false  // Flaga blokujaca tworzenie kart przed zakonczeniem preloadu

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
    mesh.castShadow = true
    
    const cardInstanceGroup = new THREE.Group()
    cardInstanceGroup.add(mesh)
    
    cardInstanceGroup.position.set(0, 4.5, 0)
    scene.add(cardInstanceGroup)

    activeCards[name] = {
        group: cardInstanceGroup,
        faceMaterial: faceMaterial,
        edgeMaterial: edgeMaterial,
        currentOpacity: 0.0,
        targetOpacity: 1.0,
        targetX: 0.0,
        targetY: 4.5,
        targetAngle: 0.0
    }
    
    console.log(`[AR] Utworzono karte 3D: ${name}`)
}

// 7. WebSocket z exponential backoff
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
                    activeCards[name].targetX = cardData.x
                    activeCards[name].targetY = cardData.y
                    activeCards[name].targetAngle = cardData.angle || 0
                }
            })
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

// 8. Petla animacji z frame-rate independent LERP (THREE.Clock zamiast Date.now)
const clock = new THREE.Clock()

function animate() {
    requestAnimationFrame(animate)

    const delta = clock.getDelta()       // Czas miedzy klatkami w sekundach (frame-rate independent!)
    const t = clock.getElapsedTime()     // Calkowity czas od startu (precyzyjniejszy niz Date.now)

    const visibleCardNames = Object.keys(activeCards)
        .filter((name) => activeCards[name].currentOpacity > 0.01 || activeCards[name].targetOpacity > 0.0)
        .sort()

    visibleCardNames.forEach((name, index) => {
        const cardObj = activeCards[name]

        // Frame-rate independent LERP — identyczna predkosc animacji na 30Hz, 60Hz i 144Hz
        const opacitySmooth = 1 - Math.pow(1 - 0.07, delta * 60)
        const posSmooth = 1 - Math.pow(1 - 0.08, delta * 60)

        // Plynna zmiana przezroczystosci
        cardObj.currentOpacity += (cardObj.targetOpacity - cardObj.currentOpacity) * opacitySmooth
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

        // Plynne podazanie za pozycja X (frame-rate independent)
        cardObj.group.position.x += (cardObj.targetX - cardObj.group.position.x) * posSmooth

        // Plynne podazanie za pozycja Y + organiczna lewitacja
        const organicLevitation = Math.sin(t * 1.5 + index * 0.8) * 0.25
        const targetYWithLevitation = cardObj.targetY + organicLevitation
        cardObj.group.position.y += (targetYWithLevitation - cardObj.group.position.y) * posSmooth

        // Plynne podazanie za katem obrotu Z (frame-rate independent)
        cardObj.group.rotation.z += (cardObj.targetAngle - cardObj.group.rotation.z) * posSmooth

        // Delikatne kolysanie w osi Y (3D depth feeling)
        cardObj.group.rotation.y = Math.sin(t * 0.8 + index * 0.5) * 0.06
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
