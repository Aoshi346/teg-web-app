# TesisFar — parte de Windows. Ejecutar UNA vez en PowerShell COMO ADMINISTRADOR:
#   powershell -ExecutionPolicy Bypass -File install-windows.ps1
#
# Hace cuatro cosas (la 0: memoria de WSL 4 GB + 4 GB de swap si no hay .wslconfig):
#   1. El PC no se suspende ni hiberna (un servidor dormido no responde).
#   2. Al iniciar sesión en Windows arranca Ubuntu (WSL) en segundo plano y lo mantiene encendido;
#      dentro de Ubuntu, systemd arranca TesisFar solo.
#   3. Bloquea la pantalla justo después, para poder usar el inicio de sesión automático sin dejar
#      el escritorio abierto.
param(
    [string]$Distro = "Ubuntu"
)
$ErrorActionPreference = "Stop"

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Abre PowerShell con 'Ejecutar como administrador' y vuelve a lanzarlo." -ForegroundColor Red
    exit 1
}

# wsl.exe -l escribe en UTF-16: sin esto, los nombres salen con caracteres nulos.
[Console]::OutputEncoding = [System.Text.Encoding]::Unicode
$distros = (wsl.exe -l -q) | ForEach-Object { $_.Trim() } | Where-Object { $_ }
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
if ($distros -notcontains $Distro) {
    Write-Host "No encuentro la distribución '$Distro' en WSL. Hay: $($distros -join ', ')" -ForegroundColor Red
    Write-Host "Vuelve a lanzarlo con:  -Distro <nombre>" -ForegroundColor Red
    exit 1
}

Write-Host "1/3 Sin suspensión ni hibernación (con corriente)..." -ForegroundColor Cyan
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /hibernate off   # apaga también el «inicio rápido», que da arranques raros con WSL

Write-Host "     Memoria de WSL (PC de 8 GB): 4 GB + 4 GB de swap..." -ForegroundColor Cyan
$wslConfig = Join-Path $env:USERPROFILE ".wslconfig"
if (Test-Path $wslConfig) {
    Write-Host "     Ya existe $wslConfig; no lo toco. Recomendado: [wsl2] memory=4GB swap=4GB" -ForegroundColor Yellow
} else {
    Set-Content -Path $wslConfig -Encoding ASCII -Value "[wsl2]`r`nmemory=4GB`r`nswap=4GB`r`n"
    wsl.exe --shutdown   # se aplica al volver a arrancar (paso 3)
}

Write-Host "2/3 Tarea programada: arrancar TesisFar al iniciar sesión..." -ForegroundColor Cyan
$user = "$env:USERDOMAIN\$env:USERNAME"
$keepAlive = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -Command `"wsl.exe -d $Distro --exec /bin/sleep infinity`""
$lock = New-ScheduledTaskAction -Execute "rundll32.exe" -Argument "user32.dll,LockWorkStation"
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "TesisFar - servidor" -Force `
    -Action $keepAlive -Trigger $trigger -Settings $settings -User $user -RunLevel Limited | Out-Null

$lockTrigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$lockTrigger.Delay = "PT1M"
Register-ScheduledTask -TaskName "TesisFar - bloquear pantalla" -Force `
    -Action $lock -Trigger $lockTrigger -User $user -RunLevel Limited | Out-Null

Write-Host "3/3 Arrancando ahora..." -ForegroundColor Cyan
Start-ScheduledTask -TaskName "TesisFar - servidor"

Write-Host ""
Write-Host "Listo." -ForegroundColor Green
Write-Host "Falta un paso a mano para que TesisFar vuelva solo tras un reinicio (Windows Update, apagón):"
Write-Host "  Inicio de sesión automático: pulsa Win+R, escribe  netplwiz  y desmarca"
Write-Host "  'Los usuarios deben escribir su nombre y contraseña para usar el equipo' (ver la guía)."
