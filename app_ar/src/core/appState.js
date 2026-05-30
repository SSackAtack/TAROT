export const arSettings = {
    cardScale: parseFloat(localStorage.getItem('ar_cardScale') || '1.0'),
    spacingX: parseFloat(localStorage.getItem('ar_spacingX') || '1.0'),
    spacingY: parseFloat(localStorage.getItem('ar_spacingY') || '1.0'),
    offsetX: parseFloat(localStorage.getItem('ar_offsetX') || '0.0'),
    offsetY: parseFloat(localStorage.getItem('ar_offsetY') || '0.0'),
    cameraHeight: parseFloat(localStorage.getItem('ar_cameraHeight') || '15.0'),
    cameraDistance: parseFloat(localStorage.getItem('ar_cameraDistance') || '10.5'),
}

export function saveArSettings() {
    localStorage.setItem('ar_cardScale', arSettings.cardScale.toString())
    localStorage.setItem('ar_spacingX', arSettings.spacingX.toString())
    localStorage.setItem('ar_spacingY', arSettings.spacingY.toString())
    localStorage.setItem('ar_offsetX', arSettings.offsetX.toString())
    localStorage.setItem('ar_offsetY', arSettings.offsetY.toString())
    localStorage.setItem('ar_cameraHeight', arSettings.cameraHeight.toString())
    localStorage.setItem('ar_cameraDistance', arSettings.cameraDistance.toString())
}

export const appState = {
    operatorMode: new URLSearchParams(window.location.search).get('operator') === '1',
    controlSocket: null,
    latestStatus: null,
    wowMode: false,
    texturesReady: false,
    latestFrameData: null,
    activeCards: {},
    texturesCache: {}
}
