import * as THREE from 'three'

export const scene = new THREE.Scene()
export let camera = null
export let renderer = null

export const targetCameraPos = new THREE.Vector3(0, 35, 0.001)
export const targetCameraLookAt = new THREE.Vector3(0, 0, 0)
export const currentCameraLookAt = new THREE.Vector3(0, 0, 0)

export function initRenderer(container) {
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000)
    camera.position.copy(targetCameraPos)
    camera.lookAt(currentCameraLookAt)

    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(window.devicePixelRatio)
    renderer.shadowMap.enabled = false
    
    container.appendChild(renderer.domElement)

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight
        camera.updateProjectionMatrix()
        renderer.setSize(window.innerWidth, window.innerHeight)
    })
}

export function updateCameraAnimation(wowMode, arSettings) {
    if (wowMode) {
        const time = Date.now() * 0.00025  // Bardzo wolny okres falowania (około 25 sekund na cykl)
        const breathing = Math.sin(time) * 0.8  // Zmiana pozycji o maksymalnie 0.8 jednostki
        
        targetCameraPos.x = 0  
        targetCameraPos.z = arSettings.cameraDistance + breathing * 0.6  
        targetCameraPos.y = arSettings.cameraHeight + breathing * 0.4    
        targetCameraLookAt.set(0, -0.4, -0.6)  
    } else {
        targetCameraPos.set(0, 35, 0.001)
        targetCameraLookAt.set(0, 0, 0)
    }

    camera.position.lerp(targetCameraPos, 0.04)
    currentCameraLookAt.lerp(targetCameraLookAt, 0.04)
    camera.lookAt(currentCameraLookAt)
}
