import * as THREE from 'three'
import { appState } from '../core/appState'
import { createCardBackTexture } from './textureCache'

export let sharedBackTexture = null
export let sharedBackMaterial = null

export function getSharedBackMaterial() {
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

// Współdzielona geometria karty
export let sharedGeometry = null
export let sharedCardWidth = 0
export let sharedCardHeight = 0

export function getSharedGeometry(aspect) {
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

export const sharedEdgeMaterial = new THREE.MeshStandardMaterial({
    color: 0xd4af37,
    roughness: 0.12,  
    metalness: 0.95,  
    transparent: true,
    opacity: 0.0
})

export function createVirtualCard(name, scene, arSettings) {
    if (!appState.texturesReady) {
        console.warn(`[WARN] Preload jeszcze nie skończony — pomijam kartę ${name}`)
        return
    }

    const texture = appState.texturesCache[name]
    if (!texture) {
        console.warn(`[WARN] Tekstura dla karty ${name} nie istnieje w Cache!`)
        return
    }

    const aspect = texture.image ? (texture.image.width / texture.image.height) : (70 / 120)
    const geometry = getSharedGeometry(aspect) 

    // Materiał awersu
    const faceMaterial = new THREE.MeshStandardMaterial({ 
        map: texture,
        transparent: true,
        opacity: 0.0,
        roughness: 0.35,  
        metalness: 0.10,
        side: THREE.FrontSide
    })

    const backMaterial = getSharedBackMaterial().clone()
    const edgeMaterial = sharedEdgeMaterial.clone()

    // Korpus karty 3D
    const bodyMesh = new THREE.Mesh(geometry, [backMaterial, edgeMaterial])

    // Panel przedni z obrazkiem karty
    const padding = 0.08
    const w = sharedCardWidth - padding
    const h = sharedCardHeight - padding
    const r = 0.20
    
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
    
    const pos = faceGeometry.attributes.position
    const uvs = faceGeometry.attributes.uv
    for (let i = 0; i < pos.count; i++) {
        const u = (pos.getX(i) + w / 2) / w
        const v = (pos.getY(i) + h / 2) / h
        uvs.setXY(i, u, v)
    }
    uvs.needsUpdate = true

    const faceMesh = new THREE.Mesh(faceGeometry, faceMaterial)
    faceMesh.position.z = 0.062

    const cardContainer = new THREE.Group()
    cardContainer.add(bodyMesh)
    cardContainer.add(faceMesh)

    const cardInstanceGroup = new THREE.Group()
    cardInstanceGroup.add(cardContainer)
    
    cardInstanceGroup.rotation.x = -Math.PI / 2
    cardInstanceGroup.position.set(0, 0, 0)
    scene.add(cardInstanceGroup)

    appState.activeCards[name] = {
        group: cardInstanceGroup,
        container: cardContainer,
        faceMaterial: faceMaterial,
        backMaterial: backMaterial,
        edgeMaterial: edgeMaterial,
        currentOpacity: 0.0,
        targetOpacity: 1.0,
        currentX: 0.0,
        currentY: 4.0,
        currentZ: 0.0,
        currentAngle: 0.0,
        currentFlip: Math.PI,
        targetFlip: 0.0,
        spinOffset: (Math.random() - 0.5) * 1.6,
        targetX: 0.0,
        targetY: 0.0,
        targetAngle: 0.0
    }
}

// Funkcja animacji kart 3D
export function animateCards(scene, arSettings, wowMode, GRID_SNAP_ENABLED, GRID_SIZE_X, GRID_SIZE_Y) {
    const visibleCardNames = Object.keys(appState.activeCards)
        .filter((name) => appState.activeCards[name].currentOpacity > 0.005 || appState.activeCards[name].targetOpacity > 0.0)
        .sort()

    visibleCardNames.forEach((name, index) => {
        const cardObj = appState.activeCards[name]

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
            delete appState.activeCards[name]
            return
        }

        cardObj.group.scale.set(arSettings.cardScale, arSettings.cardScale, arSettings.cardScale)

        const targetWorldX = cardObj.targetX * arSettings.spacingX + arSettings.offsetX
        const targetWorldZ = -(cardObj.targetY * arSettings.spacingY + arSettings.offsetY)
        
        cardObj.currentX += (targetWorldX - cardObj.currentX) * 0.08
        cardObj.currentZ += (targetWorldZ - cardObj.currentZ) * 0.08
        
        const hoverOffset = Math.sin(Date.now() * 0.0012 + index * 0.7) * 0.06 
        const targetWorldY = wowMode ? 0.25 + hoverOffset : 0.0 
        cardObj.currentY += (targetWorldY - cardObj.currentY) * 0.08

        cardObj.group.position.x = cardObj.currentX
        cardObj.group.position.z = cardObj.currentZ
        cardObj.group.position.y = cardObj.currentY

        const heightDelta = Math.max(0.0, cardObj.currentY - targetWorldY)

        cardObj.currentAngle += (cardObj.targetAngle - cardObj.currentAngle) * 0.08
        cardObj.group.rotation.z = cardObj.currentAngle + heightDelta * cardObj.spinOffset

        cardObj.currentFlip += (cardObj.targetFlip - cardObj.currentFlip) * 0.05
        cardObj.container.rotation.y = cardObj.currentFlip

        cardObj.container.rotation.x = heightDelta * 0.08

        if (wowMode) {
            cardObj.group.rotation.x = -Math.PI / 2 + Math.sin(Date.now() * 0.0008 + index) * 0.015 
            cardObj.group.rotation.y = Math.cos(Date.now() * 0.0008 + index) * 0.015 
        } else {
            cardObj.group.rotation.x = -Math.PI / 2
            cardObj.group.rotation.y = 0
        }
    })
}

// Obsługa pozycjonowania danych z detektora (zabezpieczona przed wyścigami)
export function handleCardData(detectedCards, scene, arSettings, GRID_SNAP_ENABLED, GRID_SIZE_X, GRID_SIZE_Y, cardNames) {
    if (!appState.texturesReady) {
        appState.latestFrameData = detectedCards
        return
    }

    const detectedNames = detectedCards.map(c => c.name)
    
    Object.keys(appState.activeCards).forEach((name) => {
        if (detectedNames.includes(name)) {
            appState.activeCards[name].targetOpacity = 1.0
        } else {
            appState.activeCards[name].targetOpacity = 0.0
        }
    })

    detectedCards.forEach((cardData) => {
        const name = cardData.name
        
        if (!cardNames.includes(name)) return
        if (typeof cardData.x !== 'number' || typeof cardData.y !== 'number') return
        
        if (!appState.activeCards[name]) {
            createVirtualCard(name, scene, arSettings)
            if (appState.activeCards[name]) {
                const targetX = GRID_SNAP_ENABLED ? Math.round(cardData.x / GRID_SIZE_X) * GRID_SIZE_X : cardData.x
                const targetY = GRID_SNAP_ENABLED ? Math.round(cardData.y / GRID_SIZE_Y) * GRID_SIZE_Y : cardData.y
                appState.activeCards[name].currentX = targetX * arSettings.spacingX + arSettings.offsetX
                appState.activeCards[name].currentZ = -(targetY * arSettings.spacingY + arSettings.offsetY)
                appState.activeCards[name].currentY = 4.0 
                appState.activeCards[name].currentAngle = (cardData.angle || 0) + (Math.random() - 0.5) * 0.4 
            }
        }
        
        if (appState.activeCards[name]) {
            appState.activeCards[name].targetOpacity = 1.0
            
            const rawX = cardData.x
            const rawY = cardData.y
            if (GRID_SNAP_ENABLED) {
                appState.activeCards[name].targetX = Math.round(rawX / GRID_SIZE_X) * GRID_SIZE_X
                appState.activeCards[name].targetY = Math.round(rawY / GRID_SIZE_Y) * GRID_SIZE_Y
            } else {
                appState.activeCards[name].targetX = rawX
                appState.activeCards[name].targetY = rawY
            }

            const rawAngle = cardData.angle || 0
            if (GRID_SNAP_ENABLED) {
                appState.activeCards[name].targetAngle = Math.round(rawAngle / (Math.PI / 2)) * (Math.PI / 2)
            } else {
                appState.activeCards[name].targetAngle = rawAngle
            }
        }
    })
}
