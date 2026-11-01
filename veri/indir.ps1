# ICAERUS (Zenodo) veri setlerini indirir — kaldığı yerden devam eder (curl -C -), bitince açar.
# Kullanım (PowerShell, repo kökünde):
#   powershell -ExecutionPolicy Bypass -File veri\indir.ps1            # 3. tur için gerekenler
#   powershell -ExecutionPolicy Bypass -File veri\indir.ps1 -Hepsi     # + 29 GB ikinci set (disk yeterse)
# Disk: 14967219 → 22 GB zip (açılınca ~22 GB daha; zip açıldıktan sonra silinir).
param([switch]$Hepsi)
$ErrorActionPreference = "Stop"
$Kok = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Hedef = Join-Path $Kok "veri\icaerus"
New-Item -ItemType Directory -Force -Path $Hedef | Out-Null

$Setler = @(
  @{ id = 12094356; ad = "set2";        not = "4 gerçek-sayılı video + izleme etiketleri (olc.py sınavı, 160 MB)" },
  @{ id = 14929694; ad = "set-keci";    not = "etiketli keçi görüntüleri (180 MB)" },
  @{ id = 14967219; ad = "set-cesitli"; not = "çeşitli koşullarda koyun video+foto, etiketsiz (22 GB)" }
)
if ($Hepsi) { $Setler += @{ id = 18889354; ad = "set-cesitli2"; not = "çeşitli koşullar II, etiketsiz (29 GB)" } }

foreach ($s in $Setler) {
  $klasor = Join-Path $Hedef $s.ad
  New-Item -ItemType Directory -Force -Path $klasor | Out-Null
  Write-Host "== $($s.ad): $($s.not)"
  $kayit = Invoke-RestMethod -Uri "https://zenodo.org/api/records/$($s.id)"
  foreach ($f in $kayit.files) {
    $dosya = Join-Path $klasor $f.key
    $bitti = Join-Path $klasor ("." + $f.key + ".ok")
    if (Test-Path $bitti) { Write-Host "   $($f.key) zaten indi"; continue }
    Write-Host ("   {0}  {1:N1} GB" -f $f.key, ($f.size / 1GB))
    # curl.exe Windows 10/11'de hazır; -C - kaldığı yerden sürer, --retry ağ koptuğunda yeniden dener
    & curl.exe -L -C - --retry 20 --retry-delay 10 --retry-all-errors -o "$dosya" $f.links.self
    if ($LASTEXITCODE -ne 0) { throw "indirme başarısız: $($f.key)" }
    if ((Get-Item $dosya).Length -ne $f.size) { throw "boyut tutmadı: $($f.key)" }
    if ($f.key -like "*.zip") {
      Write-Host "   açılıyor..."
      $icerik = Join-Path $klasor "icerik"
      Expand-Archive -LiteralPath $dosya -DestinationPath $icerik -Force
      Remove-Item $dosya   # yer aç
    }
    New-Item -ItemType File -Force -Path $bitti | Out-Null
  }
}
Write-Host "HEPSI_INDI"
