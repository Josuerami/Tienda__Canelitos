# Script para descargar imágenes usadas por la app (PowerShell)
# Ejecútalo desde la carpeta del proyecto: `cd C:\Users\LENOVO\ProyectoModulo\tienda_canelitos` y luego `.\	ools\download_images.ps1` o `.\
esources\download_images.ps1` según dónde lo pongas.
# Crea la carpeta static/img si no existe y descarga las imágenes.

$imgDir = Join-Path -Path $PSScriptRoot -ChildPath "..\static\img" | Resolve-Path -Relative
if (-not (Test-Path $imgDir)) {
    New-Item -ItemType Directory -Force -Path $imgDir | Out-Null
}

$files = @(
    @{ url = 'https://upload.wikimedia.org/wikipedia/commons/5/59/Coca-Cola_355ml_can.png'; out = 'coca_cola_355ml.png' },
    @{ url = 'https://upload.wikimedia.org/wikipedia/commons/0/0b/Water_Bottle.png'; out = 'agua_1l.png' },
    @{ url = 'https://upload.wikimedia.org/wikipedia/commons/6/67/Bread_2007.jpg'; out = 'pan_blanco.jpg' },
    @{ url = 'https://upload.wikimedia.org/wikipedia/commons/0/0c/Milk_glass.jpg'; out = 'leche_1l.jpg' },
    @{ url = 'https://upload.wikimedia.org/wikipedia/commons/7/79/Chips_bag.png'; out = 'papas_fritas.png' },
    @{ url = 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Rice_Bag.png'; out = 'arroz_1kg.png' },
    @{ url = 'https://upload.wikimedia.org/wikipedia/commons/1/1a/Napkins.png'; out = 'servilletas.png' },
    @{ url = 'https://upload.wikimedia.org/wikipedia/commons/8/81/Liquid_soap_dispenser.png'; out = 'jabon_liquido.png' },
    @{ url = 'https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg'; out = 'placeholder.svg' }
)

Write-Host "Descargando imágenes a: $imgDir"
$wc = New-Object System.Net.WebClient
foreach ($f in $files) {
    $dest = Join-Path $imgDir $f.out
    try {
        Write-Host "-> $($f.url) -> $dest"
        $wc.DownloadFile($f.url, $dest)
    }
    catch {
        Write-Host "  [!] No se pudo descargar $($f.url). Se mantendrá (o creará) placeholder si falta. Error: $_" -ForegroundColor Yellow
    }
}
$wc.Dispose()
Write-Host "Hecho. Si faltan archivos, ejecuta 'python download_images.py' para generar placeholders."