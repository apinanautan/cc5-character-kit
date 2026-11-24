# ocr.ps1 <image> : text in the image with the OCR built into Windows 10/11 (no download). Run with Windows PowerShell 5.1.
# Prints "NO_OCR_LANGUAGE" when this PC has no OCR language (ailog.py then uses rapidocr instead).
param([string]$Img)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(20000) | Out-Null; $task.Result }
[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
[void][Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
[void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $eng) { $l = [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages | Select-Object -First 1; if ($l) { $eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($l) } }
if (-not $eng) { 'NO_OCR_LANGUAGE'; exit 0 }
$f = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path $Img).Path)) ([Windows.Storage.StorageFile])
$s = Await ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$d = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
$b = Await ($d.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$r = Await ($eng.RecognizeAsync($b)) ([Windows.Media.Ocr.OcrResult])
$s.Dispose()
($r.Lines | % { $_.Text }) -join "`n"
