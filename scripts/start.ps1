# SkillScope AI — Windows 11 PowerShell Başlatma ve Doğrulama Scripti
# Kullanım: .\scripts\start.ps1

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  SKILLSCOPE AI — KURULUM VE BAŞLATMA YARDIMCISI" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[+] .env dosyası .env.example üzerinden oluşturuldu." -ForegroundColor Green
}

Write-Host "[*] Docker servis durumu kontrol ediliyor..." -ForegroundColor Yellow
docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Docker Desktop çalışmıyor. Lütfen Docker Desktop uygulamasını başlatıp tekrar deneyin." -ForegroundColor Red
    exit 1
}

Write-Host "[+] Docker aktif. Konteynerler derleniyor ve başlatılıyor..." -ForegroundColor Green
docker compose up --build -d

Write-Host "[+] Servisler başlatıldı:" -ForegroundColor Green
Write-Host "    - Web Arayüzü (Frontend): http://localhost:5173" -ForegroundColor Cyan
Write-Host "    - Backend REST API:       http://localhost:8000/api/v1/health" -ForegroundColor Cyan
Write-Host "    - Swagger API Dokümanı:   http://localhost:8000/docs" -ForegroundColor Cyan
