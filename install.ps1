# Install the claude-motion-film skill on Windows.
param([string]$Dest = "$env:USERPROFILE\.dsh\skills")
$src = Join-Path $PSScriptRoot "skills\claude-motion-film"
$target = Join-Path $Dest "claude-motion-film"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
if (Test-Path $target) { Remove-Item -Recurse -Force $target }
Copy-Item -Recurse $src $target
Write-Output "installed -> $target"
Write-Output "start a new session, then ask your agent to use the skill."
