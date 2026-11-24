# iClone UI helper without screenshots (UI Automation).
#   ic8_ui.ps1 list                 -> list iClone windows + buttons
#   ic8_ui.ps1 click "OK","No, thank you"  -> press the first button whose name matches, in any iClone window
param([string]$cmd = "list", [string[]]$names)
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$A = [Windows.Automation.AutomationElement]
$pids = (Get-Process iClone -ErrorAction SilentlyContinue).Id
$cond = New-Object Windows.Automation.PropertyCondition($A::ControlTypeProperty, [Windows.Automation.ControlType]::Button)
$wins = $A::RootElement.FindAll([Windows.Automation.TreeScope]::Children, [Windows.Automation.Condition]::TrueCondition) |
    ? { $pids -contains $_.Current.ProcessId }
$done = @()
foreach ($w in $wins) {
    $btns = $w.FindAll([Windows.Automation.TreeScope]::Descendants, $cond)
    if ($cmd -eq "list") { "[win] " + $w.Current.Name; $btns | % { "   btn: " + $_.Current.Name } ; continue }
    foreach ($n in $names) {
        $b = $btns | ? { $_.Current.Name -eq $n } | select -First 1
        if ($b) {
            try { $b.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke(); $done += "$n ($($w.Current.Name))" } catch { "fail $n : $_" }
        }
    }
}
#   ic8_ui.ps1 open "<file path>"  -> fill the open-file dialog's File name box and press Open (dialog must be up)
if ($cmd -eq "open") {
    $ec = New-Object Windows.Automation.PropertyCondition($A::ControlTypeProperty, [Windows.Automation.ControlType]::Edit)
    foreach ($w in $wins) {
        $dlg = $w.FindAll([Windows.Automation.TreeScope]::Subtree, (New-Object Windows.Automation.PropertyCondition($A::ClassNameProperty, "#32770"))) | select -First 1
        if (-not $dlg) { if ($w.Current.ClassName -eq "#32770") { $dlg = $w } else { continue } }
        # Win32 file dialog (Thai Windows): the name box is the Edit inside the ComboBox; buttons show as Pane
        $all = $dlg.FindAll([Windows.Automation.TreeScope]::Descendants, [Windows.Automation.Condition]::TrueCondition)
        $e = $all | ? { $_.Current.ClassName -eq "Edit" } | select -First 1
        # UIA patterns are unsupported here -> plain Win32 messages (WM_SETTEXT, BM_CLICK)
        Add-Type -Namespace W -Name U -MemberDefinition '[DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h,int m,IntPtr w,string l); [DllImport("user32.dll")] public static extern IntPtr PostMessage(IntPtr h,int m,IntPtr w,IntPtr l);' -ErrorAction SilentlyContinue
        [W.U]::SendMessage([IntPtr]$e.Current.NativeWindowHandle, 0x000C, [IntPtr]::Zero, $names[0]) | Out-Null
        $ob = $all | ? { $_.Current.ClassName -eq "Button" -and $_.Current.Name -match "^(&?Open|&?Save|เปิด|บันทึก)" } | select -First 1
        [W.U]::PostMessage([IntPtr]$ob.Current.NativeWindowHandle, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null; "opened: " + $names[0]; break
    }
}
if ($cmd -eq "click") { "clicked: " + ($done -join ", ") }
