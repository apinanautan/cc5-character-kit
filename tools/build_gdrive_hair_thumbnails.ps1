param(
 [Parameter(Mandatory=$true)][string]$Manifest,
 [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference='Stop'
if($env:COMPUTERNAME -ne 'DESKTOP-F1PJT4S'){throw 'Wrong host'}
if(-not(Test-Path -LiteralPath $Manifest)){throw 'Manifest missing'}
[IO.Directory]::CreateDirectory((Join-Path $Output 'thumbs'))|Out-Null
[IO.Directory]::CreateDirectory((Join-Path $Output 'crops'))|Out-Null
$cs=@'
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public static class CC5HairPreview {
 [StructLayout(LayoutKind.Sequential)]
 public struct SIZE { public int cx,cy; public SIZE(int a,int b){cx=a;cy=b;} }
 [ComImport,InterfaceType(ComInterfaceType.InterfaceIsIUnknown),Guid("bcc18b79-ba16-442f-80c4-8a59c30c463b")]
 public interface IFactory {void GetImage(SIZE size,uint flags,out IntPtr phbm);}
 [DllImport("shell32.dll",CharSet=CharSet.Unicode,PreserveSig=false)]
 public static extern void SHCreateItemFromParsingName(string path,IntPtr bind,ref Guid riid,[MarshalAs(UnmanagedType.Interface)]out IFactory factory);
 [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr h);
 public static string Extract(string src,string dest,string cropped){
   IntPtr hb=IntPtr.Zero;
   try {
     Guid iid=typeof(IFactory).GUID;IFactory factory;
     SHCreateItemFromParsingName(src,IntPtr.Zero,ref iid,out factory);
     factory.GetImage(new SIZE(720,720),8,out hb);
     if(hb==IntPtr.Zero)return "NO_THUMBNAIL";
     using(Bitmap original=Image.FromHbitmap(hb)) {
       int w=original.Width,h=original.Height;
       if(w<90 || h<90) return "TOO_SMALL:"+w+"x"+h;
       using(Bitmap big=new Bitmap(480,480))
       using(Graphics g=Graphics.FromImage(big)) {
         g.Clear(Color.FromArgb(242,243,245));
         g.InterpolationMode=InterpolationMode.HighQualityBicubic;
         g.SmoothingMode=SmoothingMode.HighQuality;
         g.PixelOffsetMode=PixelOffsetMode.HighQuality;
         float scale=Math.Min(480f/w,480f/h);
         float dw=w*scale,dh=h*scale;
         g.DrawImage(original,new RectangleF((480-dw)/2,(480-dh)/2,dw,dh),new RectangleF(0,0,w,h),GraphicsUnit.Pixel);
         big.Save(dest,ImageFormat.Jpeg);
       }
       using(Bitmap detail=new Bitmap(600,360))
       using(Graphics g=Graphics.FromImage(detail)) {
         g.Clear(Color.FromArgb(242,243,245));
         g.InterpolationMode=InterpolationMode.HighQualityBicubic;
         g.SmoothingMode=SmoothingMode.HighQuality;
         g.PixelOffsetMode=PixelOffsetMode.HighQuality;
         // Crop crown/fringe and sides, retaining original asset appearance.
         g.DrawImage(original,new RectangleF(0,0,600,360),
            new RectangleF(w*0.06f,0,w*0.88f,h*0.66f),GraphicsUnit.Pixel);
         detail.Save(cropped,ImageFormat.Jpeg);
       }
       return "OK:"+w+"x"+h;
     }
   } catch(Exception e){
     string msg=e.Message.Replace("\r"," ").Replace("\n"," ");
     return "ERROR:"+e.GetType().Name+":"+msg.Substring(0,Math.Min(150,msg.Length));
   } finally{if(hb!=IntPtr.Zero)DeleteObject(hb);}
 }
}
'@
Add-Type -TypeDefinition $cs -ReferencedAssemblies System.Drawing
$items=@((Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8|ConvertFrom-Json).items)
$log=Join-Path $Output 'thumbnail_extract.ndjson'
$enc=New-Object System.Text.UTF8Encoding($false)
$wr=New-Object IO.StreamWriter($log,$true,$enc)
$ok=0;$skip=0;$failed=0
try{
 foreach($asset in $items){
  $id=$asset.id
  # These packs explicitly require rights review, and one caused the native
  # preview provider to terminate. Preserve their metadata without requesting
  # a risky preview or treating them as usable hairstyles.
  if([string]$asset.source_path -match '(?i)CRACKED|CRKD'){
    $state='SKIPPED_REQUIRES_RIGHTS_REVIEW'
    $rec=[ordered]@{id=$id;status=$state;source_path=$asset.source_path;utc=(Get-Date).ToUniversalTime().ToString('s')}
    $wr.WriteLine(($rec|ConvertTo-Json -Compress -Depth 4));$wr.Flush()
    $failed++
    continue
  }
  $full=Join-Path $Output ('thumbs\'+$id+'.jpg')
  $crop=Join-Path $Output ('crops\'+$id+'.jpg')
  if((Test-Path $full) -and (Test-Path $crop) -and (Get-Item $full).Length -gt 800 -and (Get-Item $crop).Length -gt 800){
    $skip++;continue
  }
  $status=[CC5HairPreview]::Extract([string]$asset.source_path,$full,$crop)
  $rec=[ordered]@{id=$id;status=$status;source_path=$asset.source_path;utc=(Get-Date).ToUniversalTime().ToString('s')}
  $wr.WriteLine(($rec|ConvertTo-Json -Compress -Depth 4))
  $wr.Flush()
  if($status.StartsWith('OK:')){$ok++}else{$failed++}
  $count=$ok+$skip+$failed
  if(($count%15) -eq 0){Write-Output ("PROGRESS {0}/{1} valid={2} failed={3} skipped={4}" -f $count,$items.Count,$ok,$failed,$skip)}
 }
} finally{$wr.Close()}
Write-Output ("DONE total={0} valid_new={1} failed={2} skipped={3}" -f $items.Count,$ok,$failed,$skip)
