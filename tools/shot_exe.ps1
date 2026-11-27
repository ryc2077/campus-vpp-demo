# Launch the built campus-vpp-demo.exe on a Windows runner, wait for the
# overview scene to load, screenshot the real running window, optionally
# click given screen coordinates (scene bar buttons) and screenshot each.
# Usage:
#   .\tools\shot_exe.ps1 -ExePath ".\exe-pkg\campus-vpp-demo.exe" `
#     -OutDir ".\shots" -Clicks "368,700;520,700" -ShotNames "pv;classroom"
param(
  [string]$ExePath,
  [string]$OutDir,
  [string]$Clicks = "",
  [string]$ShotNames = "",
  [int]$WaitSeconds = 150,
  [int]$AfterClickSeconds = 12
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class NativeMouse {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
}
"@

function Save-Screenshot([string]$Path) {
  $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
  $g.Dispose()
  $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
  # brightness probe: sample a grid to detect an all-black capture
  $sum = 0; $n = 0
  for ($x = 0; $x -lt $bounds.Width; $x += 64) {
    for ($y = 0; $y -lt $bounds.Height; $y += 64) {
      $c = $bmp.GetPixel($x, $y)
      $sum += ($c.R + $c.G + $c.B) / 3; $n++
    }
  }
  $mean = [math]::Round($sum / $n, 1)
  $size = (Get-Item $Path).Length
  Write-Output "SHOT $Path size=$size mean_brightness=$mean screen=$($bounds.Width)x$($bounds.Height)"
  if ($mean -lt 5) { Write-Output "WARN: screenshot looks all black" }
  $bmp.Dispose()
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
if (-not (Test-Path $ExePath)) { throw "exe not found: $ExePath" }
Write-Output "Launching $ExePath --resolution 1024x720"
$proc = Start-Process -FilePath $ExePath -ArgumentList "--resolution", "1024x720" -PassThru
Write-Output "PID=$($proc.Id) ProcessName=$($proc.ProcessName)"

# wait for the main window to appear (up to 90s)
$deadline = (Get-Date).AddSeconds(90)
while ($true) {
  $p = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
  if (-not $p) { throw "exe exited early" }
  if ($p.MainWindowHandle -ne 0) { break }
  if ((Get-Date) -gt $deadline) { Write-Output "WARN: no main window after 90s, continuing anyway"; break }
  Start-Sleep -Seconds 5
}
$p = Get-Process -Id $proc.Id
Write-Output "MainWindowTitle='$($p.MainWindowTitle)' HasExited=$($p.HasExited)"
Write-Output "Waiting $WaitSeconds s for the overview scene to load..."
Start-Sleep -Seconds $WaitSeconds
$p = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
if (-not $p -or $p.HasExited) { throw "exe exited before screenshot" }
Write-Output "Still running. Title='$($p.MainWindowTitle)'"
Save-Screenshot (Join-Path $OutDir "00-overview.png")

if ($Clicks -ne "") {
  $points = $Clicks -split ";"
  $names = $ShotNames -split ";"
  for ($i = 0; $i -lt $points.Count; $i++) {
    $xy = $points[$i] -split ","
    $x = [int]$xy[0]; $y = [int]$xy[1]
    $name = if ($i -lt $names.Count -and $names[$i] -ne "") { $names[$i] } else { "shot$($i+1)" }
    Write-Output "Clicking ($x,$y) for $name"
    [NativeMouse]::SetCursorPos($x, $y)
    Start-Sleep -Milliseconds 300
    [NativeMouse]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 150
    [NativeMouse]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Seconds $AfterClickSeconds
    $p = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if (-not $p -or $p.HasExited) { Write-Output "WARN: exe exited after click $name"; break }
    Save-Screenshot (Join-Path $OutDir "$name.png")
  }
}

Write-Output "Stopping exe PID $($proc.Id)"
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Get-ChildItem $OutDir | Select-Object Name, Length
