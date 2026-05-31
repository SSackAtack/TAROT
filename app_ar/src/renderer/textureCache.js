import * as THREE from 'three'
import { appState } from '../core/appState'

export const cardNames = [
    ...Array.from({ length: 78 }, (_, i) => `RWS_${String(i).padStart(2, '0')}`),
    ...Array.from({ length: 78 }, (_, i) => `Zodiak_${String(i).padStart(2, '0')}`),
    ...Array.from({ length: 78 }, (_, i) => `Magic_${String(i).padStart(2, '0')}`),
    ...Array.from({ length: 78 }, (_, i) => `Gilded_${String(i).padStart(2, '0')}`),
    ...Array.from({ length: 78 }, (_, i) => `Marchetti_${String(i).padStart(2, '0')}`),
    ...Array.from({ length: 78 }, (_, i) => `Boski_${String(i).padStart(2, '0')}`)
]

const textureLoader = new THREE.TextureLoader()

export function loadTextures(onComplete, handleCardDataFn) {
    console.log(`[PRELOAD] Rozpoczynam wczytywanie ${cardNames.length} tekstur tarota...`)
    
    const preloadPromises = cardNames.map((name) => {
        return new Promise((resolve) => {
            const path = `/karty/${name}.webp`
            textureLoader.load(path, (texture) => {
                appState.texturesCache[name] = texture
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
        appState.texturesReady = true
        console.log(`[PRELOAD] Wszystkie ${Object.keys(appState.texturesCache).length} tekstur gotowe!`)
        
        if (onComplete) onComplete()
        
        if (appState.latestFrameData && handleCardDataFn) {
            handleCardDataFn(appState.latestFrameData)
        }
    })
}

// Generator mistycznego rewersu karty tarot w locie na Canvasie
export function createCardBackTexture() {
    const canvas = document.createElement('canvas')
    canvas.width = 512
    canvas.height = 880
    const ctx = canvas.getContext('2d')

    // 1. Tło - aksamitny radialny gradient
    const grad = ctx.createRadialGradient(256, 440, 50, 256, 440, 500)
    grad.addColorStop(0, '#161036')
    grad.addColorStop(0.5, '#0b071e')
    grad.addColorStop(1, '#030208')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, 512, 880)

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

    // 2. Gruba zewnętrzna ramka
    drawGoldenPath(() => {
        ctx.roundRect(24, 24, 512 - 48, 880 - 48, 20)
    }, 6)

    // Cienka wewnętrzna ramka
    drawGoldenPath(() => {
        ctx.roundRect(38, 38, 512 - 76, 880 - 76, 14)
    }, 2)

    // 3. Narożne ornamenty
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

    // 4. Mistyczny Star Dust
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

    // Gwiazda
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

    const centralGrad = ctx.createRadialGradient(cx, cy, 2, cx, cy, 14)
    centralGrad.addColorStop(0, '#ffffff')
    centralGrad.addColorStop(0.3, '#fff3a8')
    centralGrad.addColorStop(0.8, '#d4af37')
    centralGrad.addColorStop(1, 'transparent')
    ctx.fillStyle = centralGrad
    ctx.beginPath()
    ctx.arc(cx, cy, 14, 0, Math.PI * 2)
    ctx.fill()

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
