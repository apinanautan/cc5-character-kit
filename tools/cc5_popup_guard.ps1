param([switch]$Once,[switch]$DryRun,[int]$IntervalMs=700,[switch]$NoLog,[switch]$InvokeOnly)
# CC5 popup guard: closes KNOWN harmless popups so no AI/human has to screenshot + click them.
# Ported from iClone Story Pipeline\scripts\ic8_startup_popup_guard.ps1 (2026-11-19).
#   tools\cc5_popup_guard.ps1 -Once -DryRun   look once, log what it WOULD press (safe test)
#   tools\cc5_popup_guard.ps1 -Once           close known popups once
#   tools\cc5_popup_guard.ps1                 keep running (a background worker: only when the user authorizes it, AGENTS.md)
# Log: %LOCALAPPDATA%\CC5PopupGuard\guard.log
# To add a popup: add a row to $RULES. NEVER add Save / Don't Save / Delete / Overwrite / Replace buttons.
$ErrorActionPreference='Continue'
$logDir=Join-Path $env:LOCALAPPDATA 'CC5PopupGuard'; if(-not $NoLog){ New-Item -ItemType Directory -Force -Path $logDir|Out-Null }
$log=Join-Path $logDir 'guard.log'
function Log([string]$s){ $l=(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' '+$s; if(-not $NoLog){ Add-Content -Path $log -Encoding UTF8 -Value $l }; if($Once){Write-Output $l} }

Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes
Add-Type -Namespace CPG -Name U -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
[DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
[DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p);
[DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
public struct POINT{public int X,Y;}
public delegate bool EnumProc(IntPtr h,IntPtr l);
[DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc e,IntPtr l);
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr w,out uint p);
[DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr w);
'@
[CPG.U]::SetProcessDPIAware()|Out-Null
$A=[Windows.Automation.AutomationElement]; $TS=[Windows.Automation.TreeScope]

# text = regex that must appear in the popup; button = regex of the button to press; mouse = real click instead of UIA Invoke
$RULES=@(
 @{name='offline';      text='Failed to establish a connection|proper internet connection'; button='^OK$'},
 @{name='signup';       text='SIGN UP|Sign up|sign up|Sign me up|Why Register'; button='^(No, thank you\.?|No Thanks|Not Now)$'},
 @{name='plugin_compat';text='not compatible with this version'; button='^(OK|Yes)$'},
 @{name='fbx_import';   text='Import Settings|FBX Import Settings|Convert All'; button='^Convert All$'; mouse=$true}
)

function TextOf($el){ $p=New-Object System.Collections.Generic.List[string]; $p.Add($el.Current.Name)
 try{ $el.FindAll($TS::Descendants,[Windows.Automation.Condition]::TrueCondition)|%{ if($_.Current.Name){$p.Add($_.Current.Name)} } }catch{}; ($p -join "`n") }
function Press($el,$btn,$mouse){
 if(-not $mouse){ try{ $btn.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke(); return 'invoke' }catch{} }
 if($InvokeOnly){return 'invoke-unavailable'}
 $r=$btn.Current.BoundingRectangle; if($r.Width -le 0){return 'no-rect'}
 $p=New-Object CPG.U+POINT; [CPG.U]::GetCursorPos([ref]$p)|Out-Null
 try{[CPG.U]::SetForegroundWindow([IntPtr]$el.Current.NativeWindowHandle)|Out-Null}catch{}; Start-Sleep -Milliseconds 150
 [CPG.U]::SetCursorPos([int]($r.X+$r.Width/2),[int]($r.Y+$r.Height/2))|Out-Null; Start-Sleep -Milliseconds 80
 [CPG.U]::mouse_event(2,0,0,0,0); [CPG.U]::mouse_event(4,0,0,0,0); Start-Sleep -Milliseconds 80
 [CPG.U]::SetCursorPos($p.X,$p.Y)|Out-Null; 'click' }   # put the user's mouse back

$seen=@{}; Log "START once=$Once dryrun=$DryRun"
do{
 try{
  $ids=@(Get-Process -Name CharacterCreator -ErrorAction SilentlyContinue|%{$_.Id})
  if($ids.Count -eq 0 -and $Once){ Log 'CC5 not running' }
  if($ids.Count -gt 0){
   $script:hw=New-Object 'System.Collections.Generic.List[System.IntPtr]'
   $cb=[CPG.U+EnumProc]{ param([IntPtr]$h,[IntPtr]$l); [uint32]$p=0; [void][CPG.U]::GetWindowThreadProcessId($h,[ref]$p)
     if(($ids -contains [int]$p) -and [CPG.U]::IsWindowVisible($h)){ $script:hw.Add($h) }; return $true }
   [void][CPG.U]::EnumWindows($cb,[IntPtr]::Zero)
   foreach($h in $script:hw){
    try{ $d=$A::FromHandle($h) }catch{ continue }
    $rc=$d.Current.BoundingRectangle; if($rc.Width -le 0 -or $rc.Width -gt 1300 -or $rc.Height -gt 1000){continue}   # popups are small
    $txt=TextOf $d
    foreach($rule in $RULES){
     if($txt -notmatch $rule.text){continue}
     $btn=$d.FindAll($TS::Descendants,(New-Object Windows.Automation.PropertyCondition($A::ControlTypeProperty,[Windows.Automation.ControlType]::Button)))|?{ $_.Current.Name.Trim() -match $rule.button }|select -First 1
     if(-not $btn){continue}
     $key="$h-$($rule.name)-"+[int]((Get-Date).TimeOfDay.TotalSeconds/3); if($seen.ContainsKey($key)){continue}; $seen[$key]=1
     if($DryRun){ Log "DRYRUN $($rule.name) -> '$($btn.Current.Name)'"; continue }
     $method=Press $d $btn $rule.mouse
     if($method -eq 'invoke-unavailable'){ Log "BLOCKED $($rule.name) UIA Invoke unavailable"; continue }
     Log "CLOSED $($rule.name) -> '$($btn.Current.Name)' ($method)"; break
    }
   }
  }
 }catch{ Log ('ERROR '+$_.Exception.Message) }
 if($seen.Count -gt 500){$seen=@{}}
 if(-not $Once){ Start-Sleep -Milliseconds ([Math]::Max(300,$IntervalMs)) }
}while(-not $Once)
Log 'END'
