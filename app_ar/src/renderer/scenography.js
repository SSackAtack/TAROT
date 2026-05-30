import * as THREE from 'three'

// Oświetlenie i obiekty sceny
export let ambientLight = null
export let dirLight = null
export let candleLight = null
export let mysticLight = null
export let glowLight = null

export let deskMesh = null
export let candlesGroup = null
export const candleFlames = []
export let currentScenographyOpacity = 0.0

// System iskierek (Star Dust)
export const particleCount = 140
export const particleVelocities = []
export let particleSystem = null

// Generator klimatycznej, proceduralnej tekstury starego biurka mahoniowego
export function createDeskTexture() {
    const canvas = document.createElement('canvas')
    canvas.width = 1024
    canvas.height = 1024
    const ctx = canvas.getContext('2d')

    // 1. Tło - bogaty, ciepły brąz starego dębu mahoniowego
    ctx.fillStyle = '#3a2014'
    ctx.fillRect(0, 0, 1024, 1024)

    // 2. Rysowanie słojów drewna
    for (let i = 0; i < 180; i++) {
        const yCoord = (i / 180) * 1024
        const isDark = Math.random() > 0.4
        ctx.strokeStyle = isDark 
            ? `rgba(18, 8, 4, ${Math.random() * 0.18 + 0.08})` 
            : `rgba(88, 52, 34, ${Math.random() * 0.15 + 0.05})`
        
        ctx.lineWidth = Math.random() * 1.5 + 1.0
        ctx.beginPath()
        ctx.moveTo(0, yCoord)
        
        for (let x = 0; x <= 1024; x += 16) {
            const dx = x - 512
            const dy = yCoord - 512
            const dist = Math.sqrt(dx * dx + dy * dy)
            
            let wave = Math.sin(x * 0.005) * 16
            if (dist < 360) {
                const strength = (1.0 - dist / 360)
                wave += (dy > 0 ? 1 : -1) * Math.sin(dx * 0.01) * 90 * strength
            }
            
            ctx.lineTo(x, yCoord + wave)
        }
        ctx.stroke()
    }

    // Przebarwienia stołu
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

    // 3. Centralny krąg astrologiczny
    const cx = 512
    const cy = 512

    drawGoldenPath(() => {
        ctx.arc(cx, cy, 230, 0, Math.PI * 2)
    }, 2, 0.32)

    drawGoldenPath(() => {
        ctx.arc(cx, cy, 240, 0, Math.PI * 2)
    }, 0.8, 0.25)

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

    drawGoldenPath(() => {
        ctx.arc(cx, cy, 180, 0, Math.PI * 2)
    }, 1, 0.28)

    // 4. Runy i symbole astrologiczne
    const symbols = [
        (c) => {
            c.arc(0, 0, 16, 0, Math.PI * 2)
            c.moveTo(0, 0)
            c.arc(0, 0, 1.5, 0, Math.PI * 2)
        },
        (c) => {
            c.moveTo(-10, -15)
            c.bezierCurveTo(15, -15, 15, 15, -10, 15)
            c.bezierCurveTo(2, 8, 2, -8, -10, -15)
        },
        (c) => {
            c.arc(0, 5, 10, 0, Math.PI * 2)
            c.moveTo(0, 15)
            c.lineTo(0, 26)
            c.moveTo(-8, 20)
            c.lineTo(8, 20)
            c.moveTo(-12, -8)
            c.quadraticCurveTo(0, 0, 12, -8)
        },
        (c) => {
            c.arc(0, -6, 11, 0, Math.PI * 2)
            c.moveTo(0, 5)
            c.lineTo(0, 22)
            c.moveTo(-7, 13)
            c.lineTo(7, 13)
        },
        (c) => {
            c.arc(0, 0, 14, 0, Math.PI * 2)
            c.moveTo(-14, 0)
            c.lineTo(14, 0)
            c.moveTo(0, -14)
            c.lineTo(0, 14)
        },
        (c) => {
            c.arc(-5, 6, 10, 0, Math.PI * 2)
            c.moveTo(2, -1)
            c.lineTo(16, -15)
            c.moveTo(6, -15)
            c.lineTo(16, -15)
            c.lineTo(16, -5)
        },
        (c) => {
            c.moveTo(-10, -12)
            c.quadraticCurveTo(2, -12, 2, 2)
            c.lineTo(-12, 2)
            c.moveTo(2, -15)
            c.lineTo(2, 20)
            c.moveTo(-5, 12)
            c.lineTo(9, 12)
        },
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
        ctx.rotate(angle + Math.PI / 2)
        drawGoldenPath(() => {
            symFn(ctx)
        }, 1.5, 0.3)
        ctx.restore()
    })

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

export function initLights(scene) {
    ambientLight = new THREE.AmbientLight(0xffffff, 2.0)
    scene.add(ambientLight)

    dirLight = new THREE.DirectionalLight(0xffffff, 1.5)
    dirLight.position.set(0, 20, 5)
    dirLight.castShadow = false
    scene.add(dirLight)

    // Dynamiczne oświetlenie WOW
    candleLight = new THREE.PointLight(0xffb85c, 0, 50)
    candleLight.position.set(0, 8, 0)
    candleLight.visible = false
    scene.add(candleLight)

    mysticLight = new THREE.PointLight(0x8a2be2, 0, 50)
    mysticLight.position.set(0, 6, 0)
    mysticLight.visible = false
    scene.add(mysticLight)

    glowLight = new THREE.PointLight(0xff69b4, 0, 30)
    glowLight.position.set(0, 10, 0)
    glowLight.visible = false
    scene.add(glowLight)
}

export function initScenography(scene) {
    // 1. Blat stołu
    const deskGeom = new THREE.PlaneGeometry(60, 40)
    const deskTexture = createDeskTexture()
    const deskMat = new THREE.MeshStandardMaterial({
        map: deskTexture,
        roughness: 0.65,
        metalness: 0.05,
        transparent: true,
        opacity: 0.0
    })
    deskMesh = new THREE.Mesh(deskGeom, deskMat)
    deskMesh.rotation.x = -Math.PI / 2
    deskMesh.position.y = -0.06
    deskMesh.visible = false
    scene.add(deskMesh)

    // 2. Świece
    candlesGroup = new THREE.Group()
    candlesGroup.visible = false
    scene.add(candlesGroup)

    function createCandle(x, z, scaleHeight = 1.0) {
        const candleContainer = new THREE.Group()
        candleContainer.position.set(x, 0, z)

        const candleH = 2.8 * scaleHeight

        // Korpus woskowy
        const bodyGeom = new THREE.CylinderGeometry(0.42, 0.46, candleH, 16)
        const bodyMat = new THREE.MeshStandardMaterial({
            color: 0x421c54,
            roughness: 0.45,
            metalness: 0.08,
            transparent: true,
            opacity: 0.0
        })
        const bodyMesh = new THREE.Mesh(bodyGeom, bodyMat)
        bodyMesh.position.y = -0.06 + candleH / 2
        candleContainer.add(bodyMesh)

        // Knot
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

        // Płomień
        const flameGeom = new THREE.ConeGeometry(0.18, 0.60, 16)
        flameGeom.translate(0, 0.30, 0)
        const flameMat = new THREE.MeshBasicMaterial({
            color: 0xffa834,
            transparent: true,
            opacity: 0.0,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        })
        const flameMesh = new THREE.Mesh(flameGeom, flameMat)
        flameMesh.position.y = -0.06 + candleH + 0.20
        candleContainer.add(flameMesh)

        // Jądro płomienia
        const coreGeom = new THREE.ConeGeometry(0.09, 0.32, 16)
        coreGeom.translate(0, 0.16, 0)
        const coreMat = new THREE.MeshBasicMaterial({
            color: 0x00a2ff,
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

    createCandle(-8.2, -4.0, 1.1)
    createCandle(8.2, -4.0, 0.95)

    // 3. System złotej mgławicy (Star Dust)
    const particlesGeometry = new THREE.BufferGeometry()
    const positions = new Float32Array(particleCount * 3)
    
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
        size: 0.08,
        transparent: true,
        opacity: 0.35,
        blending: THREE.AdditiveBlending,
        depthWrite: false
    })

    particleSystem = new THREE.Points(particlesGeometry, particlesMaterial)
    particleSystem.visible = false
    scene.add(particleSystem)
}

export function updateScenographyAnimation(wowMode, arSettings) {
    // Płynna przezroczystość scenografii
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

    if (wowMode) {
        const time = Date.now() * 0.0006
        const animTime = Date.now() * 0.003
        
        // Płomienie świec
        if (candlesGroup && candlesGroup.visible) {
            candleFlames.forEach((c, i) => {
                const flameWobbleX = Math.sin(animTime + i * 20) * 0.07 + (Math.random() - 0.5) * 0.03
                const flameWobbleZ = Math.cos(animTime * 0.8 + i * 10) * 0.07 + (Math.random() - 0.5) * 0.03
                
                c.flame.rotation.x = flameWobbleX
                c.flame.rotation.z = flameWobbleZ
                c.core.rotation.x = flameWobbleX
                c.core.rotation.z = flameWobbleZ
                
                const flameScaleY = 1.0 + Math.sin(animTime * 2.5 + i * 5) * 0.14 + (Math.random() - 0.5) * 0.05
                c.flame.scale.set(1.0, flameScaleY, 1.0)
                c.core.scale.set(1.0, flameScaleY, 1.0)
            })
        }

        // Migotanie PointLights
        const leftCandle = candleFlames[0]
        if (leftCandle) {
            const flicker = 6.5 + Math.sin(animTime * 2.0) * 1.5 + (Math.random() - 0.5) * 0.4
            candleLight.intensity = flicker * currentScenographyOpacity
            candleLight.position.x = leftCandle.baseX + Math.sin(animTime) * 0.08
            candleLight.position.z = leftCandle.baseZ + Math.cos(animTime) * 0.08
            candleLight.position.y = 2.8 * leftCandle.scaleHeight + 0.3 + Math.sin(animTime * 3) * 0.03
        }

        const rightCandle = candleFlames[1]
        if (rightCandle) {
            const flicker = 3.5 + Math.sin(animTime * 1.7 + 10) * 1.0 + (Math.random() - 0.5) * 0.3
            glowLight.intensity = flicker * currentScenographyOpacity
            glowLight.position.x = rightCandle.baseX + Math.sin(animTime * 0.9) * 0.08
            glowLight.position.z = rightCandle.baseZ + Math.cos(animTime * 0.9) * 0.08
            glowLight.position.y = 2.8 * rightCandle.scaleHeight + 0.3 + Math.cos(animTime * 3.2) * 0.03
        }
        
        // Fioletowe światło obrotowe
        mysticLight.position.x = Math.cos(time * 0.7) * -9
        mysticLight.position.z = Math.sin(time * 0.7) * -9
        mysticLight.position.y = 5 + Math.sin(time * 1.2) * 1.0
        mysticLight.intensity = 5.0 * currentScenographyOpacity
    }

    // Animacja Star Dust
    if (wowMode && particleSystem && particleSystem.visible) {
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
}
