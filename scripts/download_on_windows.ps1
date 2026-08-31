# Windows PowerShell 에서 실행: yt-dlp 로 나머지 영상 6개 다운로드
# 이전 실패 원인: cookies 미사용 + JS runtime 없음
# 이번 수정:
#   - --cookies-from-browser 로 브라우저 세션 직접 사용 (JS runtime 없이도 서명 우회 가능)
#   - 브라우저는 chrome/edge/firefox 중 자동 감지 시도
#
# 사전 준비:
#   1. yt-dlp.exe, ffmpeg.exe 를 이 스크립트와 같은 폴더에 둔다
#   2. Chrome 또는 Edge 에서 youtube.com 에 로그인된 상태여야 함 (일반적인 상태)
#   3. Chrome 실행 중이면 종료 (yt-dlp 가 cookie DB 열 때 락 충돌 방지)
#
# 실행:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
#   .\download_on_windows.ps1
#
# 브라우저 선택 (필요 시 아래 $browser 값 변경):
#   "chrome", "edge", "firefox", "brave", "vivaldi", "opera"

$browser = "chrome"   # ← 사용하는 브라우저로 변경 가능

$ErrorActionPreference = "Continue"

$videos = @(
    @{prefix="v2_j1jW"; url="https://www.youtube.com/watch?v=j1jWp9WxGLM"; dir="."},
    @{prefix="v3_zbBx"; url="https://www.youtube.com/watch?v=zbBxJLGaoys"; dir="."},
    @{prefix="v4_hmhH"; url="https://www.youtube.com/watch?v=hmhHPvDErhM"; dir="."},
    @{prefix="v5_UHZg"; url="https://www.youtube.com/watch?v=UHZg5-uk1-k"; dir="."},
    @{prefix="s2_SNiT"; url="https://www.youtube.com/shorts/SNiTgaNbWcc"; dir="shorts"},
    @{prefix="s7_Ecik"; url="https://www.youtube.com/shorts/EcikXB0Lq38"; dir="shorts"}
)

New-Item -ItemType Directory -Path "shorts" -Force | Out-Null

# 낮은 화질부터 시도 (JS runtime 없이도 되는 포맷 우선)
# 22: 720p mp4 (older combined), 18: 360p mp4, 137+140: 1080p+audio, 136+140: 720p+audio
$fmt = "22/18/best[ext=mp4]/best"

foreach ($v in $videos) {
    $out = Join-Path $v.dir "$($v.prefix).%(ext)s"
    Write-Host ""
    Write-Host ">>> $($v.prefix) : $($v.url)" -ForegroundColor Cyan

    # 이미 있으면 skip
    $existing = Get-ChildItem -Path $v.dir -Filter "$($v.prefix).mp4" -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "  이미 있음, skip" -ForegroundColor Yellow
        continue
    }

    & .\yt-dlp.exe `
        --cookies-from-browser $browser `
        -f $fmt `
        --merge-output-format mp4 `
        --write-info-json `
        --no-progress `
        -o $out `
        $v.url

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ⚠ 실패 — cobalt.tools 로 수동 다운로드 시도 필요" -ForegroundColor Yellow
    } else {
        Write-Host "  ✔ OK" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "==== 결과 ===="
Get-ChildItem -Path . -Filter "v?_*" -File |
    Select-Object Name, @{Name="MB";Expression={[math]::Round($_.Length/1MB,2)}} |
    Format-Table -AutoSize
Get-ChildItem -Path "shorts" -Filter "s?_*" -File |
    Select-Object Name, @{Name="MB";Expression={[math]::Round($_.Length/1MB,2)}} |
    Format-Table -AutoSize

Write-Host ""
Write-Host "실패한 것은 아래 방법으로 수동 다운로드:"
Write-Host "  1. https://cobalt.tools 접속"
Write-Host "  2. YouTube URL 붙여넣기 → 'Download' 클릭 → mp4 저장"
Write-Host "  3. 파일명을 v2_j1jW.mp4 / v3_zbBx.mp4 등으로 리네임"
