<#
cc5_gui.ps1 - one command per CC5 GUI chore, so no AI has to screenshot + click step by step.
Ported from iClone Story Pipeline\scripts\ic8_gui.ps1 (2026-11-19). Every command prints OK/FAIL.
  powershell -NoProfile -ExecutionPolicy Bypass -File tools\cc5_gui.ps1 <command> [args]

  shot                      DPI-correct screenshot of the screen CC5 is on -> cc5_jobs\gui_shot.png
  front                     bring CC5 to the front and PROVE it (keys are never sent to another app)
  keys <combo>              send a hotkey to CC5 by virtual-key code (Thai keyboard safe), e.g. "ctrl+s" "ctrl+shift+s" "f" "delete"
  list                      list CC5 windows/popups and their buttons (UI Automation, no screenshot)
  press <regex>             press the first button matching regex in a small CC5 popup (e.g. "^(OK|Yes)$")
  dialog <full path>        fill an already-open Win32 file dialog (Open/Save/Import/Export) and press Open/Save
  save                      Ctrl+S, wait until the title loses '*', verify the file changed on disk (backup first)
  saveas <full .ccProject>  Ctrl+Shift+S, fill the dialog, verify on disk (backup if it exists)
  open <full .ccProject>    Ctrl+O, fill the dialog, wait for the title to show the file
  job <script.py> [k=v ..]  run a script inside CC5 through the CC5Bridge (= python tools\cc5.py run ...)
Rules (AGENTS.md): no restart / forced close of unsaved CC5; ask the user before driving CC5 for real work.
#>
param([Parameter(Position=0)][string]$Cmd='shot',[Parameter(Position=1)][string]$A1,
      [Parameter(ValueFromRemainingArguments=$true)][string[]]$Rest)
$ErrorActionPreference='Stop'
$ROOT = Split-Path $PSScriptRoot -Parent
$J    = Join-Path $env:LOCALAPPDATA 'Tidmunz Studio\snapgen_data\cc5_jobs'
$BAK  = Join-Path $J 'gui_backup'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)

Add-Type -AssemblyName System.Windows.Forms,System.Drawing,UIAutomationClient,UIAutomationTypes
Add-Type -Namespace CG -Name U -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT r);
[DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
[DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e);
[DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h,int m,IntPtr w,string l);
[DllImport("user32.dll")] public static extern IntPtr PostMessage(IntPtr h,int m,IntPtr w,IntPtr l);
[DllImport("user32.dll")] public static extern void keybd_event(byte vk,byte sc,int f,int e);
[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr w,out uint p);
[DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr w);
[DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h,System.Text.StringBuilder text,int max);
public delegate bool EnumProc(IntPtr h,IntPtr l);
[DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc e,IntPtr l);
public struct RECT{public int L,T,R,B;}
'@
[CG.U]::SetProcessDPIAware()|Out-Null
$A=[Windows.Automation.AutomationElement]; $TS=[Windows.Automation.TreeScope]

function Say($s){ Write-Output $s }
function Fail($s){ Write-Output "FAIL: $s"; exit 1 }
function Proc { $p=Get-Process CharacterCreator -ErrorAction SilentlyContinue|?{$_.MainWindowHandle -ne 0}|select -First 1; if(-not $p){Fail 'CC5 (CharacterCreator.exe) is not running'}; $p }
function Title { (Proc).MainWindowTitle }
function MainH { if(-not $script:MH){ $script:MH=(Proc).MainWindowHandle }; $script:MH }
function WinRect { $r=New-Object CG.U+RECT; [CG.U]::GetWindowRect((MainH),[ref]$r)|Out-Null; $r }
function FgIsCC5 { [uint32]$p=0; [void][CG.U]::GetWindowThreadProcessId([CG.U]::GetForegroundWindow(),[ref]$p); $p -eq [uint32](Proc).Id }
function Click([int]$x,[int]$y){ [CG.U]::SetCursorPos($x,$y)|Out-Null; Start-Sleep -Milliseconds 120; [CG.U]::mouse_event(2,0,0,0,0); [CG.U]::mouse_event(4,0,0,0,0); Start-Sleep -Milliseconds 300 }
# Windows may refuse SetForegroundWindow from a background script -> fall back to clicking CC5's own title bar
function Front { $h=MainH
  for($i=0;$i -lt 3;$i++){ [CG.U]::SetForegroundWindow($h)|Out-Null; Start-Sleep -Milliseconds 300; if(FgIsCC5){ return }
    $r=WinRect; Click ([int](($r.L+$r.R)/2)) ($r.T+12); Start-Sleep -Milliseconds 300; if(FgIsCC5){ return } }
  Fail 'could not bring CC5 to the front; no keys were sent' }
$VK=@{ctrl=0x11;shift=0x10;alt=0x12;enter=0x0D;esc=0x1B;tab=0x09;delete=0x2E;del=0x2E;space=0x20;home=0x24;end=0x23}
function Keys([string]$combo){
  $parts=$combo.ToLower().Split('+'); $mods=@(); for($i=0;$i -lt $parts.Count-1;$i++){ $mods+=[byte]$VK[$parts[$i]] }
  $k=$parts[-1]; if($VK.ContainsKey($k)){$vk=[byte]$VK[$k]} elseif($k -match '^f(\d+)$'){$vk=[byte](0x6F+[int]$Matches[1])} elseif($k.Length -eq 1){$vk=[byte][char]$k.ToUpper()} else {Fail "unknown key '$k'"}
  Front; if(-not (FgIsCC5)){Fail 'CC5 lost focus; key not sent'}
  foreach($m in $mods){[CG.U]::keybd_event($m,0,0,0)}; [CG.U]::keybd_event($vk,0,0,0); [CG.U]::keybd_event($vk,0,2,0)
  [array]::Reverse($mods); foreach($m in $mods){[CG.U]::keybd_event($m,0,2,0)}; Start-Sleep -Milliseconds 300 }
# every visible top-level window of CC5 (Qt popups are only reachable this way + UIA FromHandle)
function Handles($processId,[switch]$IncludeHidden) {
  $script:cpid=[uint32]$processId; $script:includeHidden=[bool]$IncludeHidden
  $script:hw=New-Object 'System.Collections.Generic.List[System.IntPtr]'
  $cb=[CG.U+EnumProc]{ param($h,$l); [uint32]$p=0; [void][CG.U]::GetWindowThreadProcessId($h,[ref]$p); if($p -eq $script:cpid -and ($script:includeHidden -or [CG.U]::IsWindowVisible($h))){$script:hw.Add($h)}; $true }
  [void][CG.U]::EnumWindows($cb,[IntPtr]::Zero); $script:hw
}
function Windows($processId) {
  if(-not $processId){$processId=(Proc).Id}
  foreach($h in (Handles $processId)){ try{ $A::FromHandle($h) }catch{} }
}
function Buttons($w){ $w.FindAll($TS::Descendants,(New-Object Windows.Automation.PropertyCondition($A::ControlTypeProperty,[Windows.Automation.ControlType]::Button))) }
function PressButton([string]$rx){
  foreach($w in (Windows)){ $r=$w.Current.BoundingRectangle; if($r.Width -gt 1300 -or $r.Height -gt 1000){continue}
    $b=Buttons $w|?{$_.Current.Name.Trim() -match $rx}|select -First 1
    if($b){ try{$b.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke()}catch{ $q=$b.Current.BoundingRectangle; Click ($q.X+$q.Width/2) ($q.Y+$q.Height/2) }; return $b.Current.Name } }
  $null }
function FillDialog([string]$path){
  for($i=0;$i -lt 120;$i++){ $dlg=Windows|?{ $_.Current.ClassName -eq '#32770' -and $_.FindFirst($TS::Descendants,(New-Object Windows.Automation.PropertyCondition($A::ClassNameProperty,'Edit'))) }|select -First 1; if($dlg){break}; Start-Sleep -Milliseconds 500 }
  if(-not $dlg){ Fail 'file dialog did not appear' }
  $all=$dlg.FindAll($TS::Descendants,[Windows.Automation.Condition]::TrueCondition)
  $e=$all|?{$_.Current.ClassName -eq 'Edit'}|select -First 1
  [CG.U]::SendMessage([IntPtr]$e.Current.NativeWindowHandle,0x000C,[IntPtr]::Zero,$path)|Out-Null
  $b=$all|?{$_.Current.ClassName -eq 'Button' -and $_.Current.Name -match '^(&?Open|&?Save|เปิด|บันทึก)'}|select -First 1
  if(-not $b){ Fail 'no Open/Save button in the dialog' }
  [CG.U]::PostMessage([IntPtr]$b.Current.NativeWindowHandle,0x00F5,[IntPtr]::Zero,[IntPtr]::Zero)|Out-Null; Start-Sleep 1
  foreach($d in @(Windows|?{$_.Current.ClassName -eq '#32770'})){ $y=$d.FindAll($TS::Descendants,[Windows.Automation.Condition]::TrueCondition)|?{$_.Current.ClassName -eq 'Button' -and $_.Current.Name -match '^(&?Yes|ใช่)'}|select -First 1
    if($y){ [CG.U]::PostMessage([IntPtr]$y.Current.NativeWindowHandle,0x00F5,[IntPtr]::Zero,[IntPtr]::Zero)|Out-Null; Say 'confirmed overwrite' } }
  Say "OK dialog <- $path" }
function Backup($f){ if($f -and (Test-Path $f)){ New-Item -ItemType Directory -Force $BAK|Out-Null; Copy-Item $f $BAK -Force; Say "backup: $BAK\$(Split-Path $f -Leaf)" } }
function WaitSaved($file,$before){
  for($i=0;$i -lt 400;$i++){ Start-Sleep 1; if((Title) -notmatch '\*\s*$'){break} }
  if((Title) -match '\*\s*$'){ Fail "title still has * after 400 s: $(Title)" }
  if($file){ $last=-1; for($i=0;$i -lt 120;$i++){ Start-Sleep 2; $f=Get-Item $file -ErrorAction SilentlyContinue; if($f -and $f.Length -eq $last -and (-not $before -or $f.LastWriteTime -gt $before)){break}; if($f){$last=$f.Length} }
    $f=Get-Item $file -ErrorAction SilentlyContinue; if(-not $f -or ($before -and $f.LastWriteTime -le $before)){ Fail "file on disk did not change: $file" }
    Say ("OK saved {0}  {1:N0} bytes  {2:HH:mm:ss}" -f $f.FullName,$f.Length,$f.LastWriteTime) } else { Say "OK saved (title: $(Title))" } }

switch($Cmd){
 'shot'   { $s=[Windows.Forms.Screen]::PrimaryScreen
            if(Get-Process CharacterCreator -ErrorAction SilentlyContinue|?{$_.MainWindowHandle -ne 0}){
              $w=WinRect; $monitor=[Windows.Forms.Screen]::AllScreens|?{$_.Bounds.Contains(($w.L+50),($w.T+50))}|select -First 1
              if($monitor){$s=$monitor} }
            $r=$s.Bounds; $bmp=New-Object Drawing.Bitmap $r.Width,$r.Height; [Drawing.Graphics]::FromImage($bmp).CopyFromScreen($r.Location,[Drawing.Point]::Empty,$r.Size)
            if($A1){ $out=$A1 } else { New-Item -ItemType Directory -Force $J | Out-Null; $out=Join-Path $J 'gui_shot.png' }
            $bmp.Save($out); $bmp.Dispose(); Say "shot: $out" }
 'inspect' { $processes=@(Get-Process CharacterCreator -ErrorAction SilentlyContinue)
             if($processes.Count -ne 1){Fail 'Expected exactly one CC5 process'}
             $p=$processes[0]; $main=$p.MainWindowHandle; $title=$p.MainWindowTitle
             if($main -eq [IntPtr]::Zero){
               $candidates=@(foreach($h in (Handles $p.Id -IncludeHidden)){
                 $buffer=New-Object Text.StringBuilder 512
                 [void][CG.U]::GetWindowText($h,$buffer,$buffer.Capacity)
                 $name=$buffer.ToString()
                 if($name -match '^Character Creator\s+5\s+-\s+'){ @{handle=$h;title=$name} }
               })
               if($candidates.Count -ne 1){Fail 'Could not verify the CC5 project window'}
               $main=$candidates[0].handle; $title=$candidates[0].title
             }
             $windows=@(foreach($w in (Windows $p.Id)){
              if($w.Current.NativeWindowHandle -eq $main.ToInt64()){continue}
              if(-not $w.Current.Name -and $w.Current.ClassName -ne '#32770'){continue}
              $names=@($w.FindAll($TS::Descendants,[Windows.Automation.Condition]::TrueCondition)|%{$_.Current.Name}|?{$_}|Select-Object -First 60)
              @{title=$w.Current.Name; class=$w.Current.ClassName; text=$names} })
             @{title=$title; dialogs=$windows}|ConvertTo-Json -Depth 5 -Compress }
 'front'  { Front; Say "OK front: $(Title)" }
 'keys'   { Keys $A1; Say "OK sent $A1" }
 'list'   { foreach($w in (Windows)){ $r=$w.Current.BoundingRectangle; Say ("[win] '{0}' {1} {2}x{3}" -f $w.Current.Name,$w.Current.ClassName,[int]$r.Width,[int]$r.Height); Buttons $w|%{ if($_.Current.Name){ Say "   btn: $($_.Current.Name)" } } } }
 'press'  { $n=PressButton $A1; if($n){Say "OK pressed '$n'"} else {Fail "no popup button matches $A1"} }
 'dialog' { FillDialog $A1 }
 'save'   { $t=Title; Say "title: $t"; Keys 'ctrl+s'; WaitSaved $null $null }
 'saveas' { $before=$null; if(Test-Path $A1){ Backup $A1; $before=(Get-Item $A1).LastWriteTime }; Keys 'ctrl+shift+s'; FillDialog $A1; WaitSaved $A1 $before }
 'open'   { if(-not (Test-Path $A1)){Fail "no file: $A1"}; if((Title) -match '\*\s*$'){Fail "current project has unsaved changes ($(Title)); save first"}
            Keys 'ctrl+o'; FillDialog $A1; $n=[IO.Path]::GetFileNameWithoutExtension($A1)
            for($i=0;$i -lt 600;$i++){ if((Title) -match [regex]::Escape($n)){break}; Start-Sleep 1 }; if((Title) -notmatch [regex]::Escape($n)){Fail "did not load: $(Title)"}; Say "OK loaded: $(Title)" }
 'job'    { & python (Join-Path $PSScriptRoot 'cc5.py') run $A1 @Rest }
 default  { Get-Content $PSCommandPath -TotalCount 18 }
}
