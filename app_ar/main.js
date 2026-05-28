import './style.css'
import * as THREE from 'three'

// 1. Inicjalizacja sceny (z pełną przezroczystością pod nakładkę OBS)
const container = document.getElementById('app')
const scene = new THREE.Scene()

// Ustawienia kamery
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000)
camera.position.z = 20 // Nieco dalej, by zmieścić cały rozkład wielu kart
camera.position.y = 7  
camera.lookAt(0, 3, 0) 

// Renderer z kanałem Alpha i cieniami
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
renderer.setSize(window.innerWidth, window.innerHeight)
renderer.setPixelRatio(window.devicePixelRatio)
renderer.shadowMap.enabled = true
renderer.shadowMap.type = THREE.PCFShadowMap
container.appendChild(renderer.domElement)

// 2. Oświetlenie
const ambientLight = new THREE.AmbientLight(0xffffff, 1.4) 
scene.add(ambientLight)

const dirLight = new THREE.DirectionalLight(0xffffff, 2.5) 
dirLight.position.set(5, 12, 5)
dirLight.castShadow = true
dirLight.shadow.camera.top = 12
dirLight.shadow.camera.bottom = -12
dirLight.shadow.camera.left = -15
dirLight.shadow.camera.right = 15
dirLight.shadow.mapSize.width = 2048
dirLight.shadow.mapSize.height = 2048
scene.add(dirLight)

// 3. Stół/Shadow Catcher (Łapacz cieni)
const shadowPlaneGeo = new THREE.PlaneGeometry(150, 150)
const shadowPlaneMat = new THREE.ShadowMaterial({ opacity: 0.55 })
const shadowPlane = new THREE.Mesh(shadowPlaneGeo, shadowPlaneMat)
shadowPlane.rotation.x = -Math.PI / 2
shadowPlane.position.y = -0.1
shadowPlane.receiveShadow = true
scene.add(shadowPlane)

// 4. Inicjalizacja mechanizmu Preloadu Tekstur
const textureLoader = new THREE.TextureLoader()
const texturesCache = {}

const cardNames = [
    "00_fool", "01_magician", "02_high_priestess", "03_empress", "04_emperor",
    "05_hierophant", "06_lovers", "07_chariot", "08_strength", "09_hermit",
    "10_wheel_of_fortune", "11_justice", "12_hanged_man", "13_death", "14_temperance",
    "15_devil", "16_tower", "17_star", "18_moon", "19_sun", "20_judgement", "21_world"
]

console.log("[PRELOAD] Rozpoczynam wczytywanie 22 tekstur tarota do pamięci...")

cardNames.forEach((name) => {
    const path = `/karty/${name}.webp`
    textureLoader.load(path, (texture) => {
        texturesCache[name] = texture
        // Konserwatywne ustawienia filtrowania dla maksymalnej ostrości tekstu i grafik
        texture.minFilter = THREE.LinearMipmapLinearFilter
        texture.magFilter = THREE.LinearFilter
        console.log(`[PRELOAD] Załadowano pomyślnie: ${name}`)
    }, undefined, (err) => {
        console.error(`[PRELOAD BŁĄD] Nie udało się załadować: ${name}`, err)
    })
})

// 5. Zarządzanie instancjami kart 3D na stole
const activeCards = {} // Słownik aktywnych kart: { "nazwa": { group, material, currentOpacity, targetOpacity } }

// Funkcja tworzenia i inicjalizacji wirtualnej karty 3D o zaokrąglonych rogach i pozłacanych brzegi
function createVirtualCard(name) {
    const texture = texturesCache[name]
    if (!texture) {
        console.warn(`[WARN] Tekstura dla karty ${name} nie jest jeszcze gotowa w Cache!`)
        return
    }

    const aspect = texture.image ? (texture.image.width / texture.image.height) : (70 / 120)
    const cardHeight = 5.5
    const cardWidth = cardHeight * aspect

    // 1. Tworzymy kształt 2D zaokrąglonego prostokąta (Rounded Rectangle)
    const shape = new THREE.Shape()
    const radius = 0.24 // Promień zaokrąglenia rogu dostosowany proporcjonalnie
    const x = -cardWidth / 2
    const y = -cardHeight / 2

    shape.moveTo(x, y + radius)
    shape.lineTo(x, y + cardHeight - radius)
    shape.quadraticCurveTo(x, y + cardHeight, x + radius, y + cardHeight)
    shape.lineTo(x + cardWidth - radius, y + cardHeight)
    shape.quadraticCurveTo(x + cardWidth, y + cardHeight, x + cardWidth, y + cardHeight - radius)
    shape.lineTo(x + cardWidth, y + radius)
    shape.quadraticCurveTo(x + cardWidth, y, x + cardWidth - radius, y)
    shape.lineTo(x + radius, y)
    shape.quadraticCurveTo(x, y, x, y + radius)

    // 2. Wyciskamy kształt w 3D (Extrude) nadając mu grubość papieru i ścięcia krawędzi (bevel)
    const extrudeSettings = {
        steps: 1,
        depth: 0.08, // Grubość karty (ok. 0.8mm w skali sceny)
        bevelEnabled: true,
        bevelThickness: 0.02, // Płaskie, lśniące ścięcie na brzegu
        bevelSize: 0.015,
        bevelSegments: 4
    }

    const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings)
    geometry.center() // Środkujemy układ współrzędnych geometrii

    // Ręczna korekta i mapowanie współrzędnych UV na zakres [0, 1] dla idealnego rozłożenia tekstury na zaokrąglonym prostokącie
    const pos = geometry.attributes.position
    const uvs = geometry.attributes.uv
    for (let i = 0; i < pos.count; i++) {
        const u = (pos.getX(i) + cardWidth / 2) / cardWidth
        const v = (pos.getY(i) + cardHeight / 2) / cardHeight
        uvs.setXY(i, u, v)
    }
    uvs.needsUpdate = true

    // 3. Definiujemy materiały (Przód/Tył z grafiką oraz metaliczne złote brzegi!)
    const faceMaterial = new THREE.MeshStandardMaterial({ 
        map: texture,
        transparent: true,
        opacity: 0.0,
        roughness: 0.55,
        metalness: 0.05,
        side: THREE.DoubleSide
    })

    const edgeMaterial = new THREE.MeshStandardMaterial({
        color: 0xd4af37, // Przepiękny, głęboki odcień złota (Metallic Gold Leaf)
        roughness: 0.22,
        metalness: 0.85,  // Bardzo wysoka metaliczność dla lśnienia w świetle lampy!
        transparent: true,
        opacity: 0.0
    })

    // Mesh obsługuje tablicę materiałów (index 0: przód/tył, index 1: boczna krawędź extrude)
    const mesh = new THREE.Mesh(geometry, [faceMaterial, edgeMaterial])
    mesh.castShadow = true
    
    const cardInstanceGroup = new THREE.Group()
    cardInstanceGroup.add(mesh)
    
    // Pozycjonujemy początkowo na środku (X=0)
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
    
    console.log(`[AR] Utworzono zaokrągloną kartę 3D o złotych brzegach: ${name}`)
}

// 6. Integracja WebSocket (Odbiór rozkładu wielu kart)
function connectWebSocket() {
    console.log("[WEBSOCKET] Łączenie z TarotVision CV...")
    const ws = new WebSocket("ws://localhost:8765")

    ws.onopen = () => {
        console.log("[WEBSOCKET] Połączono! Oczekiwanie na rozkłady kart...")
    }

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data)
            const detectedCards = data.cards || [] // Lista obiektów { name, x, y, angle }
            const detectedNames = detectedCards.map(c => c.name)
            
            // Oznaczamy wszystkie załadowane karty jako nieaktywne (do wygaszenia),
            // chyba że znajdują się na nowej liście wykrytych kart.
            Object.keys(activeCards).forEach((name) => {
                if (detectedNames.includes(name)) {
                    activeCards[name].targetOpacity = 1.0
                } else {
                    activeCards[name].targetOpacity = 0.0
                }
            })

            // Dla każdej nowo wykrytej karty: tworzymy instancję i aktualizujemy jej docelową pozycję
            detectedCards.forEach((cardData) => {
                const name = cardData.name
                if (!activeCards[name]) {
                    createVirtualCard(name)
                }
                
                if (activeCards[name]) {
                    activeCards[name].targetOpacity = 1.0
                    activeCards[name].targetX = cardData.x
                    activeCards[name].targetY = cardData.y
                    activeCards[name].targetAngle = cardData.angle
                }
            })
        } catch (e) {
            console.error("[WEBSOCKET ERROR] Błąd przetwarzania danych:", e)
        }
    }

    ws.onclose = () => {
        console.warn("[WEBSOCKET] Połączenie utracone. Próba wznowienia za 3s...")
        // Wygaszamy wszystkie karty przy braku sygnału z backendu
        Object.keys(activeCards).forEach((name) => {
            activeCards[name].targetOpacity = 0.0
        })
        setTimeout(connectWebSocket, 3000)
    }

    ws.onerror = (err) => {
        ws.close()
    }
}

connectWebSocket()

// 7. Pętla animacji z dynamicznym układem łukowym i płynnymi przejściami
const startTime = Date.now()

function animate() {
    requestAnimationFrame(animate)

    const t = (Date.now() - startTime) * 0.001

    // Pobieramy i sortujemy alfabetycznie nazwy wszystkich widocznych kart
    // Sortowanie gwarantuje, że karty nie zamieniają się miejscami na ekranie!
    const visibleCardNames = Object.keys(activeCards)
        .filter((name) => activeCards[name].currentOpacity > 0.01 || activeCards[name].targetOpacity > 0.0)
        .sort()

    const numCards = visibleCardNames.length
    const step = 4.2 // Elegancki odstęp dostosowany do mniejszego rozmiaru kart
    const totalWidth = (numCards - 1) * step

    visibleCardNames.forEach((name, index) => {
        const cardObj = activeCards[name]

        // Płynna zmiana przezroczystości (LERP) dla obu materiałów
        cardObj.currentOpacity += (cardObj.targetOpacity - cardObj.currentOpacity) * 0.07
        cardObj.faceMaterial.opacity = cardObj.currentOpacity * 0.95
        cardObj.edgeMaterial.opacity = cardObj.currentOpacity * 0.95

        // Czyszczenie pamięci (Garbage Collector) po pełnym wygaszeniu
        if (cardObj.targetOpacity === 0.0 && cardObj.currentOpacity <= 0.01) {
            scene.remove(cardObj.group)
            cardObj.group.traverse((child) => {
                if (child.isMesh) {
                    child.geometry.dispose()
                    
                    // Wsparcie dla czyszczenia tablicy materiałów (face + edge)
                    if (Array.isArray(child.material)) {
                        child.material.forEach((m) => m.dispose())
                    } else {
                        child.material.dispose()
                    }
                }
            })
            delete activeCards[name]
            console.log(`[AR] Usunięto i wyczyszczono z pamięci kartę: ${name}`)
            return
        }

        // Płynne podążanie (LERP) za pozycją X z kamery
        cardObj.group.position.x += (cardObj.targetX - cardObj.group.position.x) * 0.08

        // Płynne podążanie (LERP) za pozycją Y z kamery (łączymy pozycję Y z organiczną lewitacją)
        const organicLevitation = Math.sin(t * 1.5 + index * 0.8) * 0.25
        const targetYWithLevitation = cardObj.targetY + organicLevitation
        cardObj.group.position.y += (targetYWithLevitation - cardObj.group.position.y) * 0.08

        // Płynne podążanie (LERP) za kątem obrotu (rotacja na płaszczyźnie ekranu Z)
        cardObj.group.rotation.z += (cardObj.targetAngle - cardObj.group.rotation.z) * 0.08

        // Delikatne kołysanie w osi Y (3D depth feeling)
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
