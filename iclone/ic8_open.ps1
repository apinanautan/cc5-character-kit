# Fill iClone's open/save file dialog and confirm it, Win32 only (fast, no mouse, no screenshot).
#   ic8_open.ps1 "<full path>"      (dialog must already be open: Ctrl+O, Script > Load Python, ...)
param([string]$path, [int]$waitSec = 15)
Add-Type -Namespace W -Name D -MemberDefinition @'
[DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr FindWindowEx(IntPtr p,IntPtr a,string c,string t);
[DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h,int m,IntPtr w,string l);
[DllImport("user32.dll")] public static extern IntPtr PostMessage(IntPtr h,int m,IntPtr w,IntPtr l);
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
'@ -ErrorAction SilentlyContinue
$ic = (Get-Process iClone).Id
$dlg = [IntPtr]::Zero
for ($i = 0; $i -lt $waitSec * 4 -and $dlg -eq [IntPtr]::Zero; $i++) {
    $h = [IntPtr]::Zero
    while (($h = [W.D]::FindWindowEx([IntPtr]::Zero, $h, "#32770", $null)) -ne [IntPtr]::Zero) {
        [uint32]$p = 0; [W.D]::GetWindowThreadProcessId($h, [ref]$p) | Out-Null
        if ($ic -contains $p) { $dlg = $h; break }
    }
    if ($dlg -eq [IntPtr]::Zero) { Start-Sleep -Milliseconds 250 }
}
if ($dlg -eq [IntPtr]::Zero) { "no dialog"; exit 1 }
$cbx = [W.D]::FindWindowEx($dlg, [IntPtr]::Zero, "ComboBoxEx32", $null)
$edit = if ($cbx -ne [IntPtr]::Zero) { [W.D]::FindWindowEx([W.D]::FindWindowEx($cbx, [IntPtr]::Zero, "ComboBox", $null), [IntPtr]::Zero, "Edit", $null) } else { [W.D]::FindWindowEx($dlg, [IntPtr]::Zero, "Edit", $null) }
[W.D]::SendMessage($edit, 0x000C, [IntPtr]::Zero, $path) | Out-Null       # WM_SETTEXT
[W.D]::PostMessage($dlg, 0x0111, [IntPtr]1, [IntPtr]::Zero) | Out-Null     # WM_COMMAND IDOK
"sent: $path"
