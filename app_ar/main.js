import './style.css'
import * as THREE from 'three'

// 1. Inicjalizacja sceny (z pełną przezroczystością pod nakładkę OBS)
const container = document.getElementById('app')
const scene = new THREE.Scene()
const operatorMode = new URLSearchParams(window.location.search).get('operator') === '1'
let controlSocket = null
let latestStatus = null

// Stan klimatycznego efektu WOW
let wowMode = false

// Parametry do płynnego LERPowania kamery cinematic (delikatny ruch)
const targetCameraPos = new THREE.Vector3(0, 35, 0.001)
const targetCameraLookAt = new THREE.Vector3(0, 0, 0)
const currentCameraLookAt = new THREE.Vector3(0, 0, 0)

// Ustawienia kamery — widok początkowo od góry
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000)
camera.position.copy(targetCameraPos)
camera.lookAt(currentCameraLookAt)

// Renderer z kanałem Alpha i wysokim antialiasingiem
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
renderer.setSize(window.innerWidth, window.innerHeight)
renderer.setPixelRatio(window.devicePixelRatio)
renderer.shadowMap.enabled = false
container.appendChild(renderer.domElement)

// 2. Oświetlenie standardowe (równe, bez cieni dla OBS)
const ambientLight = new THREE.AmbientLight(0xffffff, 2.0)
scene.add(ambientLight)

const dirLight = new THREE.DirectionalLight(0xffffff, 1.5)
dirLight.position.set(0, 20, 5)
dirLight.castShadow = false
scene.add(dirLight)

// 3. Dynamiczne, nastrojowe oświetlenie dla trybu WOW (złagodzone intensywności)
const candleLight = new THREE.PointLight(0xffb85c, 0, 50) // Ciepły blask świecy
candleLight.position.set(0, 8, 0)
candleLight.visible = false
scene.add(candleLight)

const mysticLight = new THREE.PointLight(0x8a2be2, 0, 50) // Mistyczny fiolet/niebieski
mysticLight.position.set(0, 6, 0)
mysticLight.visible = false
scene.add(mysticLight)

const glowLight = new THREE.PointLight(0xff69b4, 0, 30) // Ciepły różowo-złoty akcent dopełniający
glowLight.position.set(0, 10, 0)
glowLight.visible = false
scene.add(glowLight)

// 4. System mistycznych, złotych iskierek (Star Dust) — złagodzony (mniej, mniejsze, mniejsza krycie)
const particleCount = 140
const particlesGeometry = new THREE.BufferGeometry()
const positions = new Float32Array(particleCount * 3)
const particleVelocities = []

for (let i = 0; i < particleCount; i++) {
    const idx = i * 3
    positions[idx] = (Math.random() - 0.5) * 26
    positions[idx+1] = Math.random() * 8 - 4
    positions[idx+2] = (Math.random() - 0.5) * 18
    
    particleVelocities.push({
        x: (Math.random() - 0.5) * 0.010,
        y: Math.random() * 0.008 + 0.004,
        z: (Math.random() - 0.5) * 0.010,
        oscSpeed: Math.random() * 0.008 + 0.003,
        oscWidth: Math.random() * 0.005
    })
}

particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))

const particlesMaterial = new THREE.PointsMaterial({
    color: 0xffd700,
    size: 0.08, // Mniejsze iskierki dla elegancji (było 0.12)
    transparent: true,
    opacity: 0.35, // Delikatniejsze krycie (było 0.6)
    blending: THREE.AdditiveBlending,
    depthWrite: false
})

const particleSystem = new THREE.Points(particlesGeometry, particlesMaterial)
particleSystem.visible = false
scene.add(particleSystem)

// Inicjalizacja mistycznej scenografii następuje na dole pliku, by zapobiec błędom inicjalizacji let

// 5. Preload tekstur z Promise.all
const textureLoader = new THREE.TextureLoader()
const texturesCache = {}
let texturesReady = false  
let latestFrameData = null 

const GRID_SNAP_ENABLED = false
const GRID_SIZE_X = 3.8  
const GRID_SIZE_Y = 6.0  

const arSettings = {
    cardScale: parseFloat(localStorage.getItem('ar_cardScale') || '1.0'),
    spacingX: parseFloat(localStorage.getItem('ar_spacingX') || '1.0'),
    spacingY: parseFloat(localStorage.getItem('ar_spacingY') || '1.0'),
    offsetX: parseFloat(localStorage.getItem('ar_offsetX') || '0.0'),
    offsetY: parseFloat(localStorage.getItem('ar_offsetY') || '0.0'),
    cameraHeight: parseFloat(localStorage.getItem('ar_cameraHeight') || '15.0'),
    cameraDistance: parseFloat(localStorage.getItem('ar_cameraDistance') || '10.5'),
}

function saveArSettings() {
    localStorage.setItem('ar_cardScale', arSettings.cardScale.toString())
    localStorage.setItem('ar_spacingX', arSettings.spacingX.toString())
    localStorage.setItem('ar_spacingY', arSettings.spacingY.toString())
    localStorage.setItem('ar_offsetX', arSettings.offsetX.toString())
    localStorage.setItem('ar_offsetY', arSettings.offsetY.toString())
    localStorage.setItem('ar_cameraHeight', arSettings.cameraHeight.toString())
    localStorage.setItem('ar_cameraDistance', arSettings.cameraDistance.toString())
}

const cardNames = [
    "00_fool", "01_magician", "02_high_priestess", "03_empress", "04_emperor",
    "05_hierophant", "06_lovers", "07_chariot", "08_strength", "09_hermit",
    "10_wheel_of_fortune", "11_justice", "12_hanged_man", "13_death", "14_temperance",
    "15_devil", "16_tower", "17_star", "18_moon", "19_sun", "20_judgement", "21_world"
]

console.log("[PRELOAD] Rozpoczynam wczytywanie 22 tekstur tarota...")

const preloadPromises = cardNames.map((name) => {
    return new Promise((resolve) => {
        const path = `/karty/${name}.webp`
        textureLoader.load(path, (texture) => {
            texturesCache[name] = texture
            texture.minFilter = THREE.LinearMipmapLinearFilter
            texture.magFilter = THREE.LinearFilter
            texture.colorSpace = THREE.SRGBColorSpace  
            resolve()
        }, undefined, (err) => {
            console.error(`[PRELOAD BŁĄD] Nie udało się załadować: ${name}`, err)
            resolve() 
        })
    })
})

Promise.all(preloadPromises).then(() => {
    texturesReady = true
    console.log(`[PRELOAD] Wszystkie ${Object.keys(texturesCache).length} tekstur gotowe!`)
    
    if (latestFrameData) {
        handleCardData(latestFrameData)
    }
})

// Generator mistycznego rewersu karty tarot w locie na Canvasie
function createCardBackTexture() {
    const canvas = document.createElement('canvas')
    canvas.width = 512
    canvas.height = 880
    const ctx = canvas.getContext('2d')

    // 1. Tło - głęboki, aksamitny radialny gradient
    const grad = ctx.createRadialGradient(256, 440, 50, 256, 440, 500)
    grad.addColorStop(0, '#161036') // Nocny indygo-fiolet
    grad.addColorStop(0.5, '#0b071e') // Ciemny granat
    grad.addColorStop(1, '#030208') // Aksamitna czerń sceniczna
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, 512, 880)

    // Pomocnicza funkcja do rysowania złotych linii z metalicznym cieniowaniem
    function drawGoldenPath(drawFn, strokeWidth = 2, isGlow = false) {
        ctx.save()
        if (isGlow) {
            ctx.shadowColor = '#d4af37'
            ctx.shadowBlur = 10
            ctx.strokeStyle = 'rgba(212, 175, 55, 0.4)'
        } else {
            const strokeGrad = ctx.createLinearGradient(0, 0, 512, 880)
            strokeGrad.addColorStop(0, '#aa7c11')
            strokeGrad.addColorStop(0.3, '#d4af37')
            strokeGrad.addColorStop(0.5, '#fff3a8')
            strokeGrad.addColorStop(0.7, '#d4af37')
            strokeGrad.addColorStop(1, '#aa7c11')
            ctx.strokeStyle = strokeGrad
        }
        ctx.lineWidth = strokeWidth
        ctx.lineJoin = 'round'
        ctx.lineCap = 'round'
        ctx.beginPath()
        drawFn()
        ctx.stroke()
        ctx.restore()
    }

    // 2. Gruba zewnętrzna ramka (cofnięta o 24px)
    drawGoldenPath(() => {
        ctx.roundRect(24, 24, 512 - 48, 880 - 48, 20)
    }, 6)

    // Cienka wewnętrzna ramka (cofnięta o 38px)
    drawGoldenPath(() => {
        ctx.roundRect(38, 38, 512 - 76, 880 - 76, 14)
    }, 2)

    // 3. Narożne ornamenty (delikatne złote łuki i punkty)
    const corners = [
        { x: 38, y: 38, rx: 1, ry: 1 },
        { x: 512 - 38, y: 38, rx: -1, ry: 1 },
        { x: 38, y: 880 - 38, rx: 1, ry: -1 },
        { x: 512 - 38, y: 880 - 38, rx: -1, ry: -1 }
    ]

    corners.forEach(c => {
        drawGoldenPath(() => {
            ctx.arc(c.x + c.rx * 25, c.y + c.ry * 25, 20, 0, Math.PI * 2)
        }, 1.5)
        ctx.fillStyle = '#fff3a8'
        ctx.beginPath()
        ctx.arc(c.x + c.rx * 25, c.y + c.ry * 25, 3, 0, Math.PI * 2)
        ctx.fill()
    })

    // 4. Mistyczny Star Dust (kosmiczne małe kropki w tle)
    for (let i = 0; i < 60; i++) {
        const px = Math.random() * (512 - 100) + 50
        const py = Math.random() * (880 - 100) + 50
        const size = Math.random() * 1.5 + 0.5
        const opacity = Math.random() * 0.7 + 0.3
        
        ctx.fillStyle = `rgba(255, 243, 168, ${opacity})`
        ctx.beginPath()
        ctx.arc(px, py, size, 0, Math.PI * 2)
        ctx.fill()
    }

    // 5. Centralna ozdoba astrologiczna
    const cx = 256
    const cy = 440

    drawGoldenPath(() => {
        ctx.arc(cx, cy, 80, 0, Math.PI * 2)
    }, 1.5)
    
    drawGoldenPath(() => {
        ctx.arc(cx, cy, 86, 0, Math.PI * 2)
    }, 0.8)

    drawGoldenPath(() => {
        ctx.arc(cx, cy, 54, 0, Math.PI * 2)
    }, 1)

    // Centralna 12-ramienna gwiazda
    drawGoldenPath(() => {
        const arms = 12
        const outerR = 48
        const innerR = 18
        
        for (let i = 0; i < arms * 2; i++) {
            const angle = (Math.PI / arms) * i
            const r = (i % 2 === 0) ? outerR : innerR
            const x = cx + Math.cos(angle) * r
            const y = cy + Math.sin(angle) * r
            if (i === 0) {
                ctx.moveTo(x, y)
            } else {
                ctx.lineTo(x, y)
            }
        }
        ctx.closePath()
    }, 2)

    // Blask słońca w samym środku
    const centralGrad = ctx.createRadialGradient(cx, cy, 2, cx, cy, 14)
    centralGrad.addColorStop(0, '#ffffff')
    centralGrad.addColorStop(0.3, '#fff3a8')
    centralGrad.addColorStop(0.8, '#d4af37')
    centralGrad.addColorStop(1, 'transparent')
    ctx.fillStyle = centralGrad
    ctx.beginPath()
    ctx.arc(cx, cy, 14, 0, Math.PI * 2)
    ctx.fill()

    // Delikatne dodatkowe promienie słoneczne wokół gwiazdy
    drawGoldenPath(() => {
        const rays = 24
        for (let i = 0; i < rays; i++) {
            const angle = (Math.PI * 2 / rays) * i
            const startR = 96
            const endR = 108 + (i % 2 === 0 ? 8 : 0)
            ctx.moveTo(cx + Math.cos(angle) * startR, cy + Math.sin(angle) * startR)
            ctx.lineTo(cx + Math.cos(angle) * endR, cy + Math.sin(angle) * endR)
        }
    }, 1)

    const texture = new THREE.CanvasTexture(canvas)
    texture.minFilter = THREE.LinearMipmapLinearFilter
    texture.magFilter = THREE.LinearFilter
    texture.colorSpace = THREE.SRGBColorSpace
    return texture
}

// Generator klimatycznej, proceduralnej tekstury starego biurka mahoniowego
function createDeskTexture() {
    const canvas = document.createElement('canvas')
    canvas.width = 1024
    canvas.height = 1024
    const ctx = canvas.getContext('2d')

    // 1. Tło - bogaty, ciepły brąz starego dębu mahoniowego
    ctx.fillStyle = '#3a2014'
    ctx.fillRect(0, 0, 1024, 1024)

    // 2. Rysowanie słojów drewna (wyrazistszych i bardziej trójwymiarowych)
    for (let i = 0; i < 180; i++) {
        const yCoord = (i / 180) * 1024
        // Używamy naprzemiennie jasnych i ciemnych włókien dla głębi drewna
        const isDark = Math.random() > 0.4
        ctx.strokeStyle = isDark 
            ? `rgba(18, 8, 4, ${Math.random() * 0.18 + 0.08})` 
            : `rgba(88, 52, 34, ${Math.random() * 0.15 + 0.05})`
        
        ctx.lineWidth = Math.random() * 1.5 + 1.0
        ctx.beginPath()
        ctx.moveTo(0, yCoord)
        
        // Fale słojów wokół centralnego sęka stołu
        for (let x = 0; x <= 1024; x += 16) {
            const dx = x - 512
            const dy = yCoord - 512
            const dist = Math.sqrt(dx * dx + dy * dy)
            
            let wave = Math.sin(x * 0.005) * 16
            // Zakrzywienie wokół sęka
            if (dist < 360) {
                const strength = (1.0 - dist / 360)
                wave += (dy > 0 ? 1 : -1) * Math.sin(dx * 0.01) * 90 * strength
            }
            
            ctx.lineTo(x, yCoord + wave)
        }
        ctx.stroke()
    }

    // Dodanie starzejących przebarwień i sęków
    for (let k = 0; k < 15; k++) {
        const px = Math.random() * 1024
        const py = Math.random() * 1024
        const r = Math.random() * 180 + 60
        const spotGrad = ctx.createRadialGradient(px, py, 5, px, py, r)
        spotGrad.addColorStop(0, 'rgba(12, 6, 3, 0.42)')
        spotGrad.addColorStop(1, 'transparent')
        ctx.fillStyle = spotGrad
        ctx.beginPath()
        ctx.arc(px, py, r, 0, Math.PI * 2)
        ctx.fill()
    }

    // Helper do rysowania wyrytych w drewnie złotych symboli i linii
    function drawGoldenPath(drawFn, strokeWidth = 2, opacity = 0.28) {
        ctx.save()
        ctx.shadowColor = '#d4af37'
        ctx.shadowBlur = 8
        ctx.strokeStyle = `rgba(212, 175, 55, ${opacity})`
        ctx.lineWidth = strokeWidth
        ctx.lineJoin = 'round'
        ctx.lineCap = 'round'
        ctx.beginPath()
        drawFn()
        ctx.stroke()
        ctx.restore()
    }

    // 3. CENTRALNY KRĄG ASTROLOGICZNY (Idealnie widoczny pod kartami!)
    const cx = 512
    const cy = 512

    // Okrąg zewnętrzny kręgu
    drawGoldenPath(() => {
        ctx.arc(cx, cy, 230, 0, Math.PI * 2)
    }, 2, 0.32)

    drawGoldenPath(() => {
        ctx.arc(cx, cy, 240, 0, Math.PI * 2)
    }, 0.8, 0.25)

    // Podziałki stopniowe na okręgu dla mistycznego wyglądu
    drawGoldenPath(() => {
        const steps = 72
        for (let i = 0; i < steps; i++) {
            const angle = (Math.PI * 2 / steps) * i
            const rStart = 230
            const rEnd = (i % 6 === 0) ? 218 : 224
            ctx.moveTo(cx + Math.cos(angle) * rStart, cy + Math.sin(angle) * rStart)
            ctx.lineTo(cx + Math.cos(angle) * rEnd, cy + Math.sin(angle) * rEnd)
        }
    }, 1.2, 0.25)

    // Okrąg wewnętrzny kręgu
    drawGoldenPath(() => {
        ctx.arc(cx, cy, 180, 0, Math.PI * 2)
    }, 1, 0.28)

    // 4. MISTYCZNE RUNY I SYMBOLE ASTROLOGICZNE WOKÓŁ CENTRALNEGO KRĘGU (W kadru kamery!)
    const symbols = [
        // Słońce (Góra)
        (c) => {
            c.arc(0, 0, 16, 0, Math.PI * 2)
            c.moveTo(0, 0)
            c.arc(0, 0, 1.5, 0, Math.PI * 2)
        },
        // Księżyc (Prawy górny skos)
        (c) => {
            c.moveTo(-10, -15)
            c.bezierCurveTo(15, -15, 15, 15, -10, 15)
            c.bezierCurveTo(2, 8, 2, -8, -10, -15)
        },
        // Merkury (Prawo)
        (c) => {
            c.arc(0, 5, 10, 0, Math.PI * 2)
            c.moveTo(0, 15)
            c.lineTo(0, 26)
            c.moveTo(-8, 20)
            c.lineTo(8, 20)
            c.moveTo(-12, -8)
            c.quadraticCurveTo(0, 0, 12, -8)
        },
        // Wenus (Prawy dolny skos)
        (c) => {
            c.arc(0, -6, 11, 0, Math.PI * 2)
            c.moveTo(0, 5)
            c.lineTo(0, 22)
            c.moveTo(-7, 13)
            c.lineTo(7, 13)
        },
        // Ziemia (Dół)
        (c) => {
            c.arc(0, 0, 14, 0, Math.PI * 2)
            c.moveTo(-14, 0)
            c.lineTo(14, 0)
            c.moveTo(0, -14)
            c.lineTo(0, 14)
        },
        // Mars (Lewy dolny skos)
        (c) => {
            c.arc(-5, 6, 10, 0, Math.PI * 2)
            c.moveTo(2, -1)
            c.lineTo(16, -15)
            c.moveTo(6, -15)
            c.lineTo(16, -15)
            c.lineTo(16, -5)
        },
        // Jowisz (Lewo)
        (c) => {
            c.moveTo(-10, -12)
            c.quadraticCurveTo(2, -12, 2, 2)
            c.lineTo(-12, 2)
            c.moveTo(2, -15)
            c.lineTo(2, 20)
            c.moveTo(-5, 12)
            c.lineTo(9, 12)
        },
        // Saturn (Lewy górny skos)
        (c) => {
            c.moveTo(-10, -15)
            c.lineTo(0, -15)
            c.moveTo(-5, -15)
            c.lineTo(-5, 5)
            c.quadraticCurveTo(8, 12, -6, 20)
            c.moveTo(-10, -7)
            c.lineTo(0, -7)
        }
    ]

    symbols.forEach((symFn, index) => {
        const angle = (Math.PI * 2 / 8) * index - Math.PI / 2
        const rx = cx + Math.cos(angle) * 206
        const ry = cy + Math.sin(angle) * 206
        
        ctx.save()
        ctx.translate(rx, ry)
        ctx.rotate(angle + Math.PI / 2) // Runy zorientowane w stronę środka!
        drawGoldenPath(() => {
            symFn(ctx)
        }, 1.5, 0.3)
        ctx.restore()
    })

    // 5. Łagodniejsza, kinowa winieta radialna (Jasne centrum z runami, ciemne obrzeża ze świecami)
    const vignette = ctx.createRadialGradient(cx, cy, 260, cx, cy, 620)
    vignette.addColorStop(0, 'transparent')
    vignette.addColorStop(0.55, 'rgba(0, 0, 0, 0.42)')
    vignette.addColorStop(1, 'rgba(0, 0, 0, 0.94)')
    ctx.fillStyle = vignette
    ctx.fillRect(0, 0, 1024, 1024)

    const texture = new THREE.CanvasTexture(canvas)
    texture.minFilter = THREE.LinearMipmapLinearFilter
    texture.magFilter = THREE.LinearFilter
    texture.colorSpace = THREE.SRGBColorSpace
    return texture
}

let deskMesh = null
let candlesGroup = null
const candleFlames = []
let currentScenographyOpacity = 0.0

function initScenography() {
    // 1. STÓŁ / BIURKO DĘBOWE (duża płaszczyzna)
    const deskGeom = new THREE.PlaneGeometry(60, 40)
    const deskTexture = createDeskTexture()
    const deskMat = new THREE.MeshStandardMaterial({
        map: deskTexture,
        roughness: 0.65, // Rozproszone, matowe, nastrojowe odbicia starego drewna
        metalness: 0.05,
        transparent: true,
        opacity: 0.0 // Płynne wyłanianie (fade-in) w trybie WOW
    })
    deskMesh = new THREE.Mesh(deskGeom, deskMat)
    deskMesh.rotation.x = -Math.PI / 2
    deskMesh.position.y = -0.06 // Lekko pod kartami, by zapobiec z-fightingowi
    deskMesh.visible = false
    scene.add(deskMesh)

    // 2. ŚWIECE 3D
    candlesGroup = new THREE.Group()
    candlesGroup.visible = false
    scene.add(candlesGroup)

    // Helper do tworzenia solidnych, trójwymiarowych świec
    function createCandle(x, z, scaleHeight = 1.0) {
        const candleContainer = new THREE.Group()
        candleContainer.position.set(x, 0, z)

        const candleH = 2.8 * scaleHeight

        // A. Korpus woskowy (gruba, luksusowa purpura świecy liturgicznej)
        const bodyGeom = new THREE.CylinderGeometry(0.42, 0.46, candleH, 16)
        const bodyMat = new THREE.MeshStandardMaterial({
            color: 0x421c54, // Purpurowy, nastrojowy wosk
            roughness: 0.45,
            metalness: 0.08,
            transparent: true,
            opacity: 0.0
        })
        const bodyMesh = new THREE.Mesh(bodyGeom, bodyMat)
        // Świeca stoi dokładnie na stole (Y = -0.06)
        bodyMesh.position.y = -0.06 + candleH / 2
        candleContainer.add(bodyMesh)

        // B. Knot (grubszy, ciemny knot)
        const wickGeom = new THREE.CylinderGeometry(0.025, 0.025, 0.22, 8)
        const wickMat = new THREE.MeshStandardMaterial({
            color: 0x181818,
            roughness: 0.9,
            transparent: true,
            opacity: 0.0
        })
        const wickMesh = new THREE.Mesh(wickGeom, wickMat)
        wickMesh.position.y = -0.06 + candleH + 0.11
        candleContainer.add(wickMesh)

        // C. Płomień (efektowny, żarzący się płomień o miękkich krawędziach)
        const flameGeom = new THREE.ConeGeometry(0.18, 0.60, 16)
        flameGeom.translate(0, 0.30, 0) // Przesuwamy piwot na dół płomienia dla pięknego kołysania
        const flameMat = new THREE.MeshBasicMaterial({
            color: 0xffa834,
            transparent: true,
            opacity: 0.0,
            blending: THREE.AdditiveBlending, // Efekt świetlistego ognia
            depthWrite: false
        })
        const flameMesh = new THREE.Mesh(flameGeom, flameMat)
        flameMesh.position.y = -0.06 + candleH + 0.20
        candleContainer.add(flameMesh)

        // D. Jądro płomienia (błękitny płomień u nasady knota)
        const coreGeom = new THREE.ConeGeometry(0.09, 0.32, 16)
        coreGeom.translate(0, 0.16, 0)
        const coreMat = new THREE.MeshBasicMaterial({
            color: 0x00a2ff, // Mistyczny, neonowy błękit
            transparent: true,
            opacity: 0.0,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        })
        const coreMesh = new THREE.Mesh(coreGeom, coreMat)
        coreMesh.position.y = -0.06 + candleH + 0.18
        candleContainer.add(coreMesh)

        candlesGroup.add(candleContainer)

        candleFlames.push({
            container: candleContainer,
            flame: flameMesh,
            core: coreMesh,
            body: bodyMesh,
            wick: wickMesh,
            baseX: x,
            baseZ: z,
            scaleHeight: scaleHeight
        })
    }

    // Ustawiamy dwie nastrojowe świece bliżej kart, by były doskonale widoczne w kadrze
    createCandle(-8.2, -4.0, 1.1)
    createCandle(8.2, -4.0, 0.95)
}

let sharedBackTexture = null
let sharedBackMaterial = null

function getSharedBackMaterial() {
    if (sharedBackMaterial) return sharedBackMaterial
    
    sharedBackTexture = createCardBackTexture()
    sharedBackMaterial = new THREE.MeshStandardMaterial({
        map: sharedBackTexture,
        roughness: 0.3,
        metalness: 0.12,
        transparent: true,
        opacity: 0.0
    })
    return sharedBackMaterial
}

// 6. Współdzielona geometria karty (zoptymalizowana)
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

    const pos = sharedGeometry.attributes.position
    const uvs = sharedGeometry.attributes.uv
    for (let i = 0; i < pos.count; i++) {
        const u = (pos.getX(i) + sharedCardWidth / 2) / sharedCardWidth
        const v = (pos.getY(i) + sharedCardHeight / 2) / sharedCardHeight
        uvs.setXY(i, u, v)
    }
    uvs.needsUpdate = true

    return sharedGeometry
}

// Zarządzanie instancjami kart 3D
const activeCards = {}

const operatorMetricNames = [
    'fps', 'matching_ms', 'cards_checked', 'orb_skipped_locked',
    'locked_tracked_count', 'available_card_count', 'tracked_card_count',
    'stable_for_ms', 'snapshot_quality_score', 'snapshot_analysis_ms',
    'time_from_motion_to_publish_ms'
]

const metricLabels = {
    fps: 'FPS',
    matching_ms: 'Czas rozpoznawania',
    cards_checked: 'Sprawdzane karty',
    orb_skipped_locked: 'Pominięte ORB',
    locked_tracked_count: 'Śledzone konturem',
    available_card_count: 'Karty w puli',
    tracked_card_count: 'Karty na stole',
    stable_for_ms: 'Stabilność',
    snapshot_quality_score: 'Jakość snapshotu',
    snapshot_analysis_ms: 'Analiza snapshotu',
    time_from_motion_to_publish_ms: 'Ruch -> publikacja'
}

const parameterLabels = {
    SNAPSHOT_SETTLE_SECONDS: 'Czas stabilizacji (s)',
    MOTION_CHANGED_RATIO: 'Czułość ruchu (detektor)',
    MIN_MATCH_COUNT: 'Min. punkty ORB',
    RATIO_THRESH: 'Próg Ratio (Lowe)',
    MIN_INLIER_RATIO: 'Zgodność RANSAC',
    WORKSPACE_INFLATE_PERCENT: 'Poszerzenie obszaru (%)'
}

const parameterHints = {
    SNAPSHOT_SETTLE_SECONDS: 'Czas stabilizacji stołu przed zrobieniem snapshotu.',
    MOTION_CHANGED_RATIO: 'Próg procentowy pikseli decydujący o wykryciu ruchu.',
    MIN_MATCH_COUNT: 'Minimalna wymagana liczba dopasowań cech ORB.',
    RATIO_THRESH: 'Test Lowe\'a. Niższy = bardziej unikalne punkty.',
    MIN_INLIER_RATIO: 'Poprawność ułożenia geometrycznego RANSAC.',
    WORKSPACE_INFLATE_PERCENT: 'Poszerzenie wirtualnego obszaru stołu na zewnątrz od ArUco.'
}

function formatMetricValue(value) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '-'
    if (Math.abs(value) >= 100) return value.toFixed(0)
    return value.toFixed(2)
}

function createOperatorPanel() {
    if (!operatorMode) return null

    const panel = document.createElement('aside')
    panel.className = 'operator-panel'
    panel.innerHTML = `
        <button type="button" class="operator-panel__toggle-btn" id="operator-panel-toggle" title="Ukryj/Pokaż Panel">⚙️</button>
        <div class="operator-panel__header">
            <span class="operator-panel__title">Panel Operatora</span>
            <span class="operator-panel__status" data-role="connection">offline</span>
        </div>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Stan systemu</summary>
            <div class="operator-grid" data-role="runtime"></div>
        </details>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Metryki</summary>
            <div class="operator-grid" data-role="metrics"></div>
        </details>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Parametry bezpieczne</summary>
            <div class="operator-controls" data-role="safe-parameters"></div>
        </details>
        <details class="operator-panel__section operator-advanced">
            <summary class="operator-panel__section-title">Zaawansowane</summary>
            <div class="operator-controls" data-role="advanced-parameters"></div>
        </details>
        <details class="operator-panel__section" data-role="camera-controls-section">
            <summary class="operator-panel__section-title">Kamera sprzętowo (Focus/Exposure)</summary>
            <div class="operator-controls" data-role="camera-controls">
                Brak danych z kamery (kliknij "Odczyt kamery")
            </div>
        </details>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Wizualia i rozstaw (AR)</summary>
            <div class="operator-controls">
                <label class="operator-control">
                    <span>Skala kart wirtualnych</span>
                    <input type="range" min="0.5" max="2.0" step="0.05" value="${arSettings.cardScale}" data-ar-param="cardScale" />
                    <output>${arSettings.cardScale.toFixed(2)}</output>
                </label>
                <label class="operator-control">
                    <span>Rozstaw poziomy (X)</span>
                    <input type="range" min="0.5" max="2.0" step="0.05" value="${arSettings.spacingX}" data-ar-param="spacingX" />
                    <output>${arSettings.spacingX.toFixed(2)}</output>
                </label>
                <label class="operator-control">
                    <span>Rozstaw pionowy (Y)</span>
                    <input type="range" min="0.5" max="2.0" step="0.05" value="${arSettings.spacingY}" data-ar-param="spacingY" />
                    <output>${arSettings.spacingY.toFixed(2)}</output>
                </label>
                <label class="operator-control">
                    <span>Przesunięcie poziome (X)</span>
                    <input type="range" min="-10.0" max="10.0" step="0.1" value="${arSettings.offsetX}" data-ar-param="offsetX" />
                    <output>${arSettings.offsetX.toFixed(1)}</output>
                </label>
                <label class="operator-control">
                    <span>Przesunięcie pionowe (Y)</span>
                    <input type="range" min="-10.0" max="10.0" step="0.1" value="${arSettings.offsetY}" data-ar-param="offsetY" />
                    <output>${arSettings.offsetY.toFixed(1)}</output>
                </label>
                <label class="operator-control">
                    <span>Wysokość kamery (WOW)</span>
                    <input type="range" min="5.0" max="30.0" step="0.5" value="${arSettings.cameraHeight}" data-ar-param="cameraHeight" />
                    <output>${arSettings.cameraHeight.toFixed(1)}</output>
                </label>
                <label class="operator-control">
                    <span>Kąt / Odległość (WOW)</span>
                    <input type="range" min="5.0" max="25.0" step="0.5" value="${arSettings.cameraDistance}" data-ar-param="cameraDistance" />
                    <output>${arSettings.cameraDistance.toFixed(1)}</output>
                </label>
            </div>
        </details>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Akcje i profile</summary>
            <div class="operator-help">Odczyt kamery niczego nie ustawia. To bezpieczny odczyt-only.</div>
            <div class="operator-actions">
                <input class="operator-profile-name" data-role="profile-name" value="studio_day" aria-label="Nazwa profilu" />
                <button type="button" data-action="profile_save">Zapisz</button>
                <button type="button" data-action="profile_apply">Wczytaj</button>
                <button type="button" data-action="tuning_rollback">Cofnij</button>
                <button type="button" data-action="camera_probe">Odczyt kamery</button>
                <button type="button" data-action="calibration_start">Kalibracja</button>
            </div>
        </details>
        <details class="operator-panel__section">
            <summary class="operator-panel__section-title">Komunikaty systemowe</summary>
            <div class="operator-warnings" data-role="warnings">-</div>
        </details>
    `
    document.body.appendChild(panel)

    // Podpięcie wysuwania panelu
    const toggleBtn = panel.querySelector('#operator-panel-toggle')
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleOperatorPanel)
    }

    return panel
}

const operatorPanel = createOperatorPanel()

function toggleOperatorPanel() {
    if (!operatorPanel) return
    operatorPanel.classList.toggle('operator-panel--collapsed')
    const toggleBtn = operatorPanel.querySelector('#operator-panel-toggle')
    if (toggleBtn) {
        if (operatorPanel.classList.contains('operator-panel--collapsed')) {
            toggleBtn.innerHTML = '⚙️'
            toggleBtn.title = "Pokaż panel"
        } else {
            toggleBtn.innerHTML = '▶'
            toggleBtn.title = "Ukryj panel"
        }
    }
}

function sendControlMessage(payload) {
    if (!controlSocket || controlSocket.readyState !== WebSocket.OPEN) return
    controlSocket.send(JSON.stringify(payload))
}

function updateOperatorGrid(container, entries) {
    if (!container) return
    container.innerHTML = entries.map(([label, value]) => `
        <div class="operator-grid__label">${label}</div>
        <div class="operator-grid__value">${value}</div>
    `).join('')
}

function updateOperatorParameters(operator) {
    if (!operatorPanel) return
    const safeContainer = operatorPanel.querySelector('[data-role="safe-parameters"]')
    const advancedContainer = operatorPanel.querySelector('[data-role="advanced-parameters"]')
    if (!safeContainer || !advancedContainer) return

    const parameters = operator?.parameters || {}
    const metadata = operator?.parameter_metadata || {}
    const names = Object.keys(metadata)
    if (names.length === 0) {
        safeContainer.textContent = '-'
        advancedContainer.textContent = '-'
        return
    }

    const existingInputs = safeContainer.querySelectorAll('input[data-param]')
    if (existingInputs.length > 0) {
        names.forEach((name) => {
            const val = parameters[name] ?? metadata[name].default
            const input = operatorPanel.querySelector(`input[data-param="${name}"]`)
            if (input) {
                const output = input.parentElement?.querySelector('output')
                if (document.activeElement !== input) {
                    input.value = val
                    if (output) output.textContent = formatMetricValue(Number(val))
                }
            }
        })
        return
    }

    const renderControls = (filteredNames) => {
        if (filteredNames.length === 0) return '-'
        return filteredNames.map((name) => {
        const meta = metadata[name]
        const value = parameters[name] ?? meta.default
        return `
            <label class="operator-control">
                <span title="${name}">${parameterLabels[name] || name}</span>
                <input
                    type="range"
                    min="${meta.minimum}"
                    max="${meta.maximum}"
                    step="${name === 'MIN_MATCH_COUNT' || name === 'WORKSPACE_INFLATE_PERCENT' ? '1' : name === 'SNAPSHOT_SETTLE_SECONDS' ? '0.1' : name === 'MOTION_CHANGED_RATIO' || name === 'RATIO_THRESH' || name === 'MIN_INLIER_RATIO' ? '0.005' : '0.01'}"
                    value="${value}"
                    data-param="${name}"
                    ${meta.live_safe ? '' : 'data-unsafe="1"'}
                />
                <output>${formatMetricValue(Number(value))}</output>
                <small>${parameterHints[name] || name}</small>
            </label>
        `
        }).join('')
    }

    safeContainer.innerHTML = renderControls(names.filter((name) => metadata[name].live_safe))
    advancedContainer.innerHTML = renderControls(names.filter((name) => !metadata[name].live_safe))
}

function updateCameraControlsUI(supportedControls) {
    if (!operatorPanel) return
    const container = operatorPanel.querySelector('[data-role="camera-controls"]')
    if (!container) return

    if (!supportedControls || Object.keys(supportedControls).length === 0) {
        container.textContent = 'Brak danych z kamery (kliknij "Odczyt kamery")'
        return
    }

    const labels = {
        CAP_PROP_FOCUS: 'Ostrość (Focus)',
        CAP_PROP_AUTOFOCUS: 'Autofokus (0=Wył, 1=Wł)',
        CAP_PROP_EXPOSURE: 'Ekspozycja (Exposure)',
        CAP_PROP_AUTO_EXPOSURE: 'Auto Ekspozycja',
        CAP_PROP_BRIGHTNESS: 'Jasność (Brightness)',
        CAP_PROP_CONTRAST: 'Kontrast (Contrast)'
    }

    const ranges = {
        CAP_PROP_FOCUS: { min: 0, max: 1023, step: 5 },
        CAP_PROP_AUTOFOCUS: { min: 0, max: 1, step: 1 },
        CAP_PROP_EXPOSURE: { min: -13, max: 1000, step: 1 },
        CAP_PROP_AUTO_EXPOSURE: { min: 0, max: 3, step: 1 },
        CAP_PROP_BRIGHTNESS: { min: 0, max: 255, step: 1 },
        CAP_PROP_CONTRAST: { min: 0, max: 255, step: 1 }
    }

    const existingInputs = container.querySelectorAll('input[data-camera-param]')
    if (existingInputs.length > 0) {
        Object.entries(supportedControls).forEach(([name, data]) => {
            if (data.readback_value === -1.0) return
            const input = container.querySelector(`input[data-camera-param="${name}"]`)
            if (input) {
                const output = input.parentElement?.querySelector('output')
                if (document.activeElement !== input) {
                    input.value = data.readback_value
                    if (output) output.textContent = data.readback_value
                }
            }
        })
        return
    }

    const html = Object.entries(supportedControls)
        .map(([name, data]) => {
            if (data.readback_value === -1.0) return ''
            const range = ranges[name] || { min: 0, max: 255, step: 1 }
            const label = labels[name] || name
            return `
                <label class="operator-control">
                    <span title="${name}">${label}</span>
                    <input
                        type="range"
                        min="${range.min}"
                        max="${range.max}"
                        step="${range.step}"
                        value="${data.readback_value}"
                        data-camera-param="${name}"
                    />
                    <output>${data.readback_value}</output>
                </label>
            `
        })
        .join('')

    container.innerHTML = html || 'Brak aktywnych sprzętowych funkcji kamery w tym systemie.'
}

function updateOperatorPanel(data) {
    if (!operatorPanel) return
    latestStatus = data

    const connection = operatorPanel.querySelector('[data-role="connection"]')
    if (connection) connection.textContent = controlSocket?.readyState === WebSocket.OPEN ? 'online' : 'offline'

    const metrics = data.metrics || {}
    const runtime = data.runtime || {}
    const operator = data.operator || {}
    const layout = data.layout || {}

    updateOperatorGrid(operatorPanel.querySelector('[data-role="runtime"]'), [
        ['Tryb CV', runtime.profile || '-'],
        ['Profil strojenia', operator.active_profile || '-'],
        ['Harmonogram', runtime.schedule_mode || '-'],
        ['Snapshot', layout.state || '-'],
        ['Layout', layout.layout_id ?? '-'],
        ['Boost', runtime.boost_frames_remaining ?? '-'],
        ['Kamera', runtime.camera_index ?? '-'],
        ['Obraz', runtime.capture_width && runtime.capture_height ? `${runtime.capture_width}x${runtime.capture_height}` : '-']
    ])

    updateOperatorGrid(
        operatorPanel.querySelector('[data-role="metrics"]'),
        operatorMetricNames.map((name) => [metricLabels[name] || name, formatMetricValue(metrics[name] ?? runtime[name])])
    )

    updateOperatorParameters(operator)
    updateCameraControlsUI(operator.supported_camera_controls)

    const warnings = operatorPanel.querySelector('[data-role="warnings"]')
    const warningItems = operator.warnings || []
    if (warnings) warnings.textContent = warningItems.length ? warningItems.join(' | ') : '-'
}

// Współdzielony materiał złotych krawędzi (zoptymalizowany pod kątem pięknych odbić)
const sharedEdgeMaterial = new THREE.MeshStandardMaterial({
    color: 0xd4af37,
    roughness: 0.12,  
    metalness: 0.95,  
    transparent: true,
    opacity: 0.0
})

function createVirtualCard(name) {
    if (!texturesReady) {
        console.warn(`[WARN] Preload jeszcze nie skończony — pomijam kartę ${name}`)
        return
    }

    const texture = texturesCache[name]
    if (!texture) {
        console.warn(`[WARN] Tekstura dla karty ${name} nie istnieje w Cache!`)
        return
    }

    const aspect = texture.image ? (texture.image.width / texture.image.height) : (70 / 120)
    const geometry = getSharedGeometry(aspect) 

    // 1. Materiał awersu (obrazka karty)
    const faceMaterial = new THREE.MeshStandardMaterial({ 
        map: texture,
        transparent: true,
        opacity: 0.0,
        roughness: 0.35,  
        metalness: 0.10,
        side: THREE.FrontSide // Rysujemy tylko od przodu, bo to jest cieniutki panel awersu
    })

    // 2. Klonowane materiały rewersu i złotych krawędzi, by kontrolować krycie każdej karty z osobna
    const backMaterial = getSharedBackMaterial().clone()
    const edgeMaterial = sharedEdgeMaterial.clone()

    // 3. Korpus karty 3D (ExtrudeGeometry) - z przodu i z tyłu ma rewers (BackMaterial), a boki złote (EdgeMaterial)
    const bodyMesh = new THREE.Mesh(geometry, [backMaterial, edgeMaterial])

    // 4. Panel przedni z obrazkiem karty (zaokrąglony ShapeGeometry, co tworzy spójne, luksusowe zaokrąglone obramowanie)
    const padding = 0.08
    const w = sharedCardWidth - padding
    const h = sharedCardHeight - padding
    const r = 0.20 // Proporcjonalnie mniejszy promień zaokrąglenia dla mniejszego panelu ilustracji
    
    const faceShape = new THREE.Shape()
    const x = -w / 2
    const y = -h / 2
    
    faceShape.moveTo(x, y + r)
    faceShape.lineTo(x, y + h - r)
    faceShape.quadraticCurveTo(x, y + h, x + r, y + h)
    faceShape.lineTo(x + w - r, y + h)
    faceShape.quadraticCurveTo(x + w, y + h, x + w, y + h - r)
    faceShape.lineTo(x + w, y + r)
    faceShape.quadraticCurveTo(x + w, y, x + w - r, y)
    faceShape.lineTo(x + r, y)
    faceShape.quadraticCurveTo(x, y, x, y + r)
    
    const faceGeometry = new THREE.ShapeGeometry(faceShape)
    
    // Ręczne przeliczenie UV dla idealnego dopasowania ilustracji karty na zaokrąglonym kształcie
    const pos = faceGeometry.attributes.position
    const uvs = faceGeometry.attributes.uv
    for (let i = 0; i < pos.count; i++) {
        const u = (pos.getX(i) + w / 2) / w
        const v = (pos.getY(i) + h / 2) / h
        uvs.setXY(i, u, v)
    }
    uvs.needsUpdate = true

    const faceMesh = new THREE.Mesh(faceGeometry, faceMaterial)
    
    // Przesuwamy awers minimalnie w osi Z do przodu względem środka korpusu 3D, by uniknąć z-fighting
    faceMesh.position.z = 0.062

    // 5. Zagnieżdżona struktura grupowa do obsługi obrotów i animacji flip
    const cardContainer = new THREE.Group()
    cardContainer.add(bodyMesh)
    cardContainer.add(faceMesh)

    const cardInstanceGroup = new THREE.Group()
    cardInstanceGroup.add(cardContainer)
    
    // Ustawienie początkowe na płasko na stole
    cardInstanceGroup.rotation.x = -Math.PI / 2
    cardInstanceGroup.position.set(0, 0, 0)
    scene.add(cardInstanceGroup)

    activeCards[name] = {
        group: cardInstanceGroup,     // Główna grupa instancji (odpowiada za pozycję X, Y, Z na stole)
        container: cardContainer,     // Wewnętrzna grupa (odpowiada za lokalne obroty, np. flip)
        faceMaterial: faceMaterial,
        backMaterial: backMaterial,
        edgeMaterial: edgeMaterial,
        currentOpacity: 0.0,
        targetOpacity: 1.0,
        currentX: 0.0,
        currentY: 4.0,                // Start wysoko w powietrzu do spadania
        currentZ: 0.0,
        currentAngle: 0.0,
        currentFlip: Math.PI,         // Start w stanie odwróconym (pokazuje rewers)
        targetFlip: 0.0,              // Cel: obrócona twarzą do góry
        spinOffset: (Math.random() - 0.5) * 1.6, // Losowe lekkie podkręcenie podczas lotu
        targetX: 0.0,
        targetY: 0.0,
        targetAngle: 0.0
    }
}

// Funkcja przetwarzania danych o kartach (zabezpieczona przed wyścigami)
function handleCardData(detectedCards) {
    if (!texturesReady) {
        latestFrameData = detectedCards
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
        
        if (!cardNames.includes(name)) return
        if (typeof cardData.x !== 'number' || typeof cardData.y !== 'number') return
        
        if (!activeCards[name]) {
            createVirtualCard(name)
            if (activeCards[name]) {
                const targetX = GRID_SNAP_ENABLED ? Math.round(cardData.x / GRID_SIZE_X) * GRID_SIZE_X : cardData.x
                const targetY = GRID_SNAP_ENABLED ? Math.round(cardData.y / GRID_SIZE_Y) * GRID_SIZE_Y : cardData.y
                activeCards[name].currentX = targetX * arSettings.spacingX + arSettings.offsetX
                activeCards[name].currentZ = -(targetY * arSettings.spacingY + arSettings.offsetY)
                activeCards[name].currentY = 4.0 
                activeCards[name].currentAngle = (cardData.angle || 0) + (Math.random() - 0.5) * 0.4 
            }
        }
        
        if (activeCards[name]) {
            activeCards[name].targetOpacity = 1.0
            
            const rawX = cardData.x
            const rawY = cardData.y
            if (GRID_SNAP_ENABLED) {
                activeCards[name].targetX = Math.round(rawX / GRID_SIZE_X) * GRID_SIZE_X
                activeCards[name].targetY = Math.round(rawY / GRID_SIZE_Y) * GRID_SIZE_Y
            } else {
                activeCards[name].targetX = rawX
                activeCards[name].targetY = rawY
            }

            const rawAngle = cardData.angle || 0
            if (GRID_SNAP_ENABLED) {
                activeCards[name].targetAngle = Math.round(rawAngle / (Math.PI / 2)) * (Math.PI / 2)
            } else {
                activeCards[name].targetAngle = rawAngle
            }
        }
    })
}

// Logika Toggling WOW Mode & Demo Spread
function toggleWowMode() {
    wowMode = !wowMode
    const body = document.body
    const btn = document.getElementById('toggle-wow-btn')
    
    if (wowMode) {
        body.classList.add('wow-mode-active')
        if (btn) {
            btn.textContent = '✨ Wyłącz Tryb Kinowy'
            btn.classList.add('wow-btn--active')
        }
        
        particleSystem.visible = true
        candleLight.visible = true
        mysticLight.visible = true
        glowLight.visible = true
        
        if (deskMesh) deskMesh.visible = true
        if (candlesGroup) candlesGroup.visible = true
        
        // Złagodzone natężenie światła (było 15/10/5)
        candleLight.intensity = 8.0
        mysticLight.intensity = 5.0
        glowLight.intensity = 3.0
        
        // Zmniejszenie płaskich świateł
        ambientLight.intensity = 0.4
        dirLight.intensity = 0.2
    } else {
        body.classList.remove('wow-mode-active')
        if (btn) {
            btn.textContent = '✨ Włącz Tryb Kinowy'
            btn.classList.remove('wow-btn--active')
        }
        
        particleSystem.visible = false
        candleLight.visible = false
        mysticLight.visible = false
        glowLight.visible = false
        
        candleLight.intensity = 0
        mysticLight.intensity = 0
        glowLight.intensity = 0
        
        // Powrót do jasnego, produkcyjnego oświetlenia
        ambientLight.intensity = 2.0
        dirLight.intensity = 1.5
    }
}

function dealDemoSpread() {
    clearDemoSpread()
    setTimeout(() => {
        const shuffled = [...cardNames].sort(() => 0.5 - Math.random())
        const selected = shuffled.slice(0, 3)
        const spread = [
            { name: selected[0], x: -4.2, y: 0.0, angle: (Math.random() - 0.5) * 0.1 },
            { name: selected[1], x: 0.0, y: 0.0, angle: (Math.random() - 0.5) * 0.08 },
            { name: selected[2], x: 4.2, y: 0.0, angle: (Math.random() - 0.5) * 0.1 }
        ]
        handleCardData(spread)
    }, 150)
}

function clearDemoSpread() {
    handleCardData([])
}

let wowControlsPanel = null;

function toggleWowControlsPanel() {
    if (!wowControlsPanel) return
    wowControlsPanel.classList.toggle('wow-controls--collapsed')
    const toggleBtn = wowControlsPanel.querySelector('#wow-controls-toggle')
    if (toggleBtn) {
        if (wowControlsPanel.classList.contains('wow-controls--collapsed')) {
            toggleBtn.innerHTML = '▲'
            toggleBtn.title = "Pokaż panel kontrolny"
        } else {
            toggleBtn.innerHTML = '▼'
            toggleBtn.title = "Ukryj panel kontrolny"
        }
    }
}

function toggleAllPanels() {
    const panels = [
        { el: operatorPanel, collapsedClass: 'operator-panel--collapsed', toggleId: '#operator-panel-toggle', openSym: '▶', closedSym: '⚙️', titleOpen: 'Ukryj panel', titleClosed: 'Pokaż panel' },
        { el: wowControlsPanel, collapsedClass: 'wow-controls--collapsed', toggleId: '#wow-controls-toggle', openSym: '▼', closedSym: '▲', titleOpen: 'Ukryj panel kontrolny', titleClosed: 'Pokaż panel kontrolny' }
    ]
    
    if (wowControlsPanel) {
        const shouldCollapse = !wowControlsPanel.classList.contains('wow-controls--collapsed')
        panels.forEach(p => {
            if (!p.el) return
            if (shouldCollapse) {
                p.el.classList.add(p.collapsedClass)
            } else {
                p.el.classList.remove(p.collapsedClass)
            }
            const btn = p.el.querySelector(p.toggleId)
            if (btn) {
                btn.innerHTML = shouldCollapse ? p.closedSym : p.openSym
                btn.title = shouldCollapse ? p.titleClosed : p.titleOpen
            }
        })
    }
}

// Widget z przyciskami demo na dole (Tryb Kinowy)
function createWowControls() {
    const controls = document.createElement('div')
    controls.className = 'wow-controls'
    controls.id = 'wow-controls-panel'
    controls.innerHTML = `
        <button type="button" class="wow-controls__toggle-btn" id="wow-controls-toggle" title="Ukryj panel kontrolny">▼</button>
        <div class="wow-controls__title">🔮 TarotVision Live</div>
        <div class="wow-controls__buttons">
            <button id="toggle-wow-btn" class="wow-btn wow-btn--primary">✨ Włącz Tryb Kinowy</button>
            <button id="demo-deal-btn" class="wow-btn">🃏 Rozdaj Karty (Demo)</button>
            <button id="demo-clear-btn" class="wow-btn wow-btn--danger">Sweep (Wyczyść)</button>
        </div>
        <div class="wow-controls__info">Skróty: <strong>W</strong> (Tryb Kinowy) | <strong>D</strong> (Rozdaj) | <strong>C</strong> (Wyczyść) | <strong>H</strong> (Ukryj Panele)</div>
    `
    document.body.appendChild(controls)
    wowControlsPanel = controls
    
    const toggleWowBtn = controls.querySelector('#toggle-wow-btn')
    const demoDealBtn = controls.querySelector('#demo-deal-btn')
    const demoClearBtn = controls.querySelector('#demo-clear-btn')
    const togglePanelBtn = controls.querySelector('#wow-controls-toggle')
    
    toggleWowBtn.addEventListener('click', toggleWowMode)
    demoDealBtn.addEventListener('click', dealDemoSpread)
    demoClearBtn.addEventListener('click', clearDemoSpread)
    togglePanelBtn.addEventListener('click', toggleWowControlsPanel)
    
    window.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
        const key = e.key.toLowerCase()
        if (key === 'w') {
            toggleWowMode()
        } else if (key === 'd') {
            dealDemoSpread()
        } else if (key === 'c') {
            clearDemoSpread()
        } else if (key === 'h') {
            toggleAllPanels()
        }
    })
}

createWowControls()

// 8. WebSocket z exponential backoff
let wsReconnectDelay = 1000 
const WS_MAX_DELAY = 15000

function connectWebSocket() {
    const ws = new WebSocket("ws://localhost:8765")

    ws.onopen = () => {
        controlSocket = ws
        updateOperatorPanel(latestStatus || { metrics: {}, runtime: {}, operator: {} })
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
                handleCardData(detectedCards)
            }
        } catch (e) {
            console.error("[WEBSOCKET ERROR] Błąd przetwarzania danych:", e)
        }
    }

    ws.onclose = () => {
        Object.keys(activeCards).forEach((name) => {
            activeCards[name].targetOpacity = 0.0
        })
        if (controlSocket === ws) controlSocket = null
        updateOperatorPanel(latestStatus || { metrics: {}, runtime: {}, operator: {} })
        setTimeout(connectWebSocket, wsReconnectDelay)
        wsReconnectDelay = Math.min(wsReconnectDelay * 2, WS_MAX_DELAY)
    }

    ws.onerror = () => {
        ws.close()
    }
}

connectWebSocket()

if (operatorPanel) {
    operatorPanel.addEventListener('input', (event) => {
        const input = event.target
        if (!(input instanceof HTMLInputElement)) return
        
        const arParam = input.dataset.arParam
        if (arParam) {
            arSettings[arParam] = parseFloat(input.value)
            saveArSettings()
            const output = input.parentElement?.querySelector('output')
            if (output) {
                output.textContent = arSettings[arParam].toFixed((arParam.startsWith('offset') || arParam.startsWith('camera')) ? 1 : 2)
            }
            return
        }

        const cameraParam = input.dataset.cameraParam
        if (cameraParam) {
            const output = input.parentElement?.querySelector('output')
            if (output) {
                output.textContent = input.value
            }
            return
        }

        const param = input.dataset.param
        if (!param) return
        const output = input.parentElement?.querySelector('output')
        if (output) output.textContent = formatMetricValue(Number(input.value))
    })

    operatorPanel.addEventListener('change', (event) => {
        const input = event.target
        if (!(input instanceof HTMLInputElement)) return
        
        const cameraParam = input.dataset.cameraParam
        if (cameraParam) {
            sendControlMessage({
                type: 'camera_set',
                param: cameraParam,
                value: Number(input.value)
            })
            return
        }

        const param = input.dataset.param
        if (!param) return
        sendControlMessage({
            type: 'tuning_update',
            param,
            value: Number(input.value)
        })
    })

    operatorPanel.addEventListener('click', (event) => {
        const button = event.target
        if (!(button instanceof HTMLButtonElement)) return
        const action = button.dataset.action
        if (!action) return
        const profileName = operatorPanel.querySelector('[data-role="profile-name"]')?.value || 'studio_day'
        if (action === 'profile_save' || action === 'profile_apply') {
            sendControlMessage({ type: action, name: profileName })
            return
        }
        sendControlMessage({ type: action })
    })
}

// 9. Główna pętla renderowania (złagodzona, elegancka dynamika i nastrojowość)
function animate() {
    requestAnimationFrame(animate)

    // A. Całkowicie stabilna kamera kinowa w trybie WOW (bez wirowania/obracania stołu)
    // Wprowadzamy jedynie ultra-subtelne "oddychanie" kamery (powolny najazd i oddalenie)
    if (wowMode) {
        const time = Date.now() * 0.00025  // Bardzo wolny okres falowania (około 25 sekund na cykl)
        const breathing = Math.sin(time) * 0.8  // Zmiana pozycji o maksymalnie 0.8 jednostki
        
        targetCameraPos.x = 0  // Kamera wycentrowana w osi X, co całkowicie eliminuje wirowanie
        targetCameraPos.z = arSettings.cameraDistance + breathing * 0.6  // Kąt/odległość kamery ustawiana suwakiem z delikatnym oddychaniem
        targetCameraPos.y = arSettings.cameraHeight + breathing * 0.4    // Wysokość kamery ustawiana suwakiem z delikatnym oddychaniem
        targetCameraLookAt.set(0, -0.4, -0.6)  // Stały, stabilny punkt skupienia wzroku
    } else {
        targetCameraPos.set(0, 35, 0.001)
        targetCameraLookAt.set(0, 0, 0)
    }

    camera.position.lerp(targetCameraPos, 0.04)
    currentCameraLookAt.lerp(targetCameraLookAt, 0.04)
    camera.lookAt(currentCameraLookAt)

    // A2. Płynna przezroczystość scenografii (stół i świece)
    const targetScenographyOpacity = wowMode ? 1.0 : 0.0
    if (Math.abs(currentScenographyOpacity - targetScenographyOpacity) > 0.005) {
        currentScenographyOpacity += (targetScenographyOpacity - currentScenographyOpacity) * 0.05
        
        if (deskMesh && deskMesh.visible) {
            deskMesh.material.opacity = currentScenographyOpacity
        }
        
        candleFlames.forEach(c => {
            c.body.material.opacity = currentScenographyOpacity
            c.wick.material.opacity = currentScenographyOpacity
            c.flame.material.opacity = currentScenographyOpacity
            c.core.material.opacity = currentScenographyOpacity
        })
        
        if (currentScenographyOpacity <= 0.01) {
            if (deskMesh) deskMesh.visible = false
            if (candlesGroup) candlesGroup.visible = false
        }
    }

    // B. Animowanie dynamicznego oświetlenia PBR i świec 3D w trybie WOW
    if (wowMode) {
        const time = Date.now() * 0.0006
        const animTime = Date.now() * 0.003
        
        // 1. Animowanie płomieni i knotów świec (kołysanie płomienia i pulsowanie ognia)
        if (candlesGroup && candlesGroup.visible) {
            candleFlames.forEach((c, i) => {
                // Tańczenie na wietrze (rotacja płomienia wokół osi X i Z)
                const flameWobbleX = Math.sin(animTime + i * 20) * 0.07 + (Math.random() - 0.5) * 0.03
                const flameWobbleZ = Math.cos(animTime * 0.8 + i * 10) * 0.07 + (Math.random() - 0.5) * 0.03
                
                c.flame.rotation.x = flameWobbleX
                c.flame.rotation.z = flameWobbleZ
                c.core.rotation.x = flameWobbleX
                c.core.rotation.z = flameWobbleZ
                
                // Pulsowanie wielkości płomienia (skala pionowa Y)
                const flameScaleY = 1.0 + Math.sin(animTime * 2.5 + i * 5) * 0.14 + (Math.random() - 0.5) * 0.05
                c.flame.scale.set(1.0, flameScaleY, 1.0)
                c.core.scale.set(1.0, flameScaleY, 1.0)
            })
        }

        // 2. Synchronizacja światła lewej świecy (candleLight) z jej pozycją i migotaniem płomienia
        const leftCandle = candleFlames[0]
        if (leftCandle) {
            const flicker = 6.5 + Math.sin(animTime * 2.0) * 1.5 + (Math.random() - 0.5) * 0.4
            candleLight.intensity = flicker * currentScenographyOpacity
            candleLight.position.x = leftCandle.baseX + Math.sin(animTime) * 0.08
            candleLight.position.z = leftCandle.baseZ + Math.cos(animTime) * 0.08
            candleLight.position.y = 2.8 * leftCandle.scaleHeight + 0.3 + Math.sin(animTime * 3) * 0.03
        }

        // 3. Synchronizacja światła prawej świecy (glowLight) z jej pozycją i migotaniem
        const rightCandle = candleFlames[1]
        if (rightCandle) {
            const flicker = 3.5 + Math.sin(animTime * 1.7 + 10) * 1.0 + (Math.random() - 0.5) * 0.3
            glowLight.intensity = flicker * currentScenographyOpacity
            glowLight.position.x = rightCandle.baseX + Math.sin(animTime * 0.9) * 0.08
            glowLight.position.z = rightCandle.baseZ + Math.cos(animTime * 0.9) * 0.08
            glowLight.position.y = 2.8 * rightCandle.scaleHeight + 0.3 + Math.cos(animTime * 3.2) * 0.03
        }
        
        // 4. Orbita fioletowego, mistycznego światła (mysticLight) krążącego nad stołem
        mysticLight.position.x = Math.cos(time * 0.7) * -9
        mysticLight.position.z = Math.sin(time * 0.7) * -9
        mysticLight.position.y = 5 + Math.sin(time * 1.2) * 1.0
        mysticLight.intensity = 5.0 * currentScenographyOpacity
    }

    // C. Animowanie systemu złotej mgławicy (Star Dust) — powolniejszy dryf
    if (wowMode && particleSystem.visible) {
        const positions = particleSystem.geometry.attributes.position.array
        const time = Date.now()
        
        for (let i = 0; i < particleCount; i++) {
            const idx = i * 3
            const vel = particleVelocities[i]
            
            positions[idx+1] += vel.y
            positions[idx] += vel.x + Math.sin(time * vel.oscSpeed) * vel.oscWidth
            positions[idx+2] += vel.z
            
            if (positions[idx+1] > 6) {
                positions[idx] = (Math.random() - 0.5) * 26
                positions[idx+1] = -4
                positions[idx+2] = (Math.random() - 0.5) * 18
            }
        }
        particleSystem.geometry.attributes.position.needsUpdate = true
    }

    const visibleCardNames = Object.keys(activeCards)
        .filter((name) => activeCards[name].currentOpacity > 0.005 || activeCards[name].targetOpacity > 0.0)
        .sort()

    visibleCardNames.forEach((name, index) => {
        const cardObj = activeCards[name]

        cardObj.currentOpacity += (cardObj.targetOpacity - cardObj.currentOpacity) * 0.08
        cardObj.faceMaterial.opacity = cardObj.currentOpacity
        cardObj.backMaterial.opacity = cardObj.currentOpacity
        cardObj.edgeMaterial.opacity = cardObj.currentOpacity

        if (cardObj.targetOpacity === 0.0 && cardObj.currentOpacity <= 0.01) {
            scene.remove(cardObj.group)
            cardObj.group.traverse((child) => {
                if (child.isMesh) {
                    if (Array.isArray(child.material)) {
                        child.material.forEach((m) => m.dispose())
                    } else {
                        child.material.dispose()
                    }
                }
            })
            delete activeCards[name]
            return
        }

        cardObj.group.scale.set(arSettings.cardScale, arSettings.cardScale, arSettings.cardScale)

        const targetWorldX = cardObj.targetX * arSettings.spacingX + arSettings.offsetX
        const targetWorldZ = -(cardObj.targetY * arSettings.spacingY + arSettings.offsetY)
        
        cardObj.currentX += (targetWorldX - cardObj.currentX) * 0.08
        cardObj.currentZ += (targetWorldZ - cardObj.currentZ) * 0.08
        
        // Złagodzona, niższa lewitacja (było 0.4 + hover 0.12)
        const hoverOffset = Math.sin(Date.now() * 0.0012 + index * 0.7) * 0.06 
        const targetWorldY = wowMode ? 0.25 + hoverOffset : 0.0 
        cardObj.currentY += (targetWorldY - cardObj.currentY) * 0.08

        cardObj.group.position.x = cardObj.currentX
        cardObj.group.position.z = cardObj.currentZ
        cardObj.group.position.y = cardObj.currentY

        // 1. Wyznaczenie wysokości nad docelowym punktem lądowania do animacji podkręcenia (spin) i pochylenia
        const heightDelta = Math.max(0.0, cardObj.currentY - targetWorldY)

        // 2. Animacja kręcenia się karty w locie (spin) płynnie wygasająca przy stole
        cardObj.currentAngle += (cardObj.targetAngle - cardObj.currentAngle) * 0.08
        cardObj.group.rotation.z = cardObj.currentAngle + heightDelta * cardObj.spinOffset

        // 3. Animacja płynnego obracania (flip) z rewersu na awers (180 stopni wokół osi Y)
        cardObj.currentFlip += (cardObj.targetFlip - cardObj.currentFlip) * 0.05
        cardObj.container.rotation.y = cardObj.currentFlip

        // 4. Naturalny przechył aerodynamiczny w locie (dziób lekko w dół / w górę)
        cardObj.container.rotation.x = heightDelta * 0.08

        // Złagodzony, subtelniejszy przechył tilt (było 0.03) dla eleganckiej dyskrecji 3D leżąc na stole
        if (wowMode) {
            cardObj.group.rotation.x = -Math.PI / 2 + Math.sin(Date.now() * 0.0008 + index) * 0.015 
            cardObj.group.rotation.y = Math.cos(Date.now() * 0.0008 + index) * 0.015 
        } else {
            cardObj.group.rotation.x = -Math.PI / 2
            cardObj.group.rotation.y = 0
        }
    })

    renderer.render(scene, camera)
}

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
})

// Inicjalizacja mistycznej scenografii 3D (Biurko i Świece) przed startem renderowania
initScenography()

animate()
