#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# LLM Serving Framework Benchmark - 자동 환경 세팅 스크립트
#
# 사용법:
#   curl -fsSL https://raw.githubusercontent.com/.../setup.sh | bash
#
# 서버 재시작 후 이 스크립트를 실행하면 전체 환경이 자동으로 구성됩니다.
# =============================================================================

WORK_DIR="/home/work"
PROJECT_REPO="https://github.com/KihongK/llm-serving-framework-benchmark-test.git"
PROJECT_DIR="${WORK_DIR}/llm-serving-framework-benchmark-test"

# PyTorch CUDA 12.1 wheel index — vLLM에서 사용
TORCH_INDEX="https://download.pytorch.org/whl/cu121"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

step=0
total_steps=7

print_step() {
    step=$((step + 1))
    echo -e "\n${GREEN}[${step}/${total_steps}]${NC} $1"
    echo "─────────────────────────────────────────────"
}

print_warn() {
    echo -e "${YELLOW}⚠  $1${NC}"
}

print_done() {
    echo -e "${GREEN}✓  $1${NC}"
}

print_error() {
    echo -e "${RED}✗  $1${NC}"
}

# ─────────────────────────────────────────────
# 1. 시스템 패키지 설치 (apt)
# ─────────────────────────────────────────────
print_step "시스템 패키지 설치 (apt-get)"

export DEBIAN_FRONTEND=noninteractive
export TZ=Asia/Seoul

# read-only 파일시스템에서 tzdata 설정 실패 방지
# debconf pre-seed로 tzdata 인터랙티브 프롬프트 방지
echo 'tzdata tzdata/Areas select Asia' | sudo debconf-set-selections 2>/dev/null || true
echo 'tzdata tzdata/Zones/Asia select Seoul' | sudo debconf-set-selections 2>/dev/null || true
sudo ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime 2>/dev/null || true

# /etc/timezone 이 read-only면 tzdata dpkg 스크립트를 패치하여 /tmp/timezone 으로 우회
if ! echo "Asia/Seoul" | sudo tee /etc/timezone >/dev/null 2>&1; then
    echo "Asia/Seoul" > /tmp/timezone
    for f in /var/lib/dpkg/info/tzdata.config /var/lib/dpkg/info/tzdata.postinst; do
        [ -f "$f" ] && sudo sed -i 's|/etc/timezone|/tmp/timezone|g' "$f"
    done
    sudo dpkg --configure tzdata 2>/dev/null || true
fi

sudo apt-get update -qq

# 기본 빌드/개발 도구
APT_PACKAGES=(
    build-essential
    git
    curl
    wget
    unzip
    jq
    htop
    tmux
    net-tools
    lsb-release
    ca-certificates
    gnupg
    software-properties-common
    # Python 빌드 의존성
    python3-dev
    python3-pip
    python3-venv
    libssl-dev
    libffi-dev
    zlib1g-dev
    libbz2-dev
    libreadline-dev
    libsqlite3-dev
    liblzma-dev
    libncurses5-dev
    libncursesw5-dev
    tk-dev
    # 네트워크/모니터링
    openssh-client
    rsync
    sysstat
    iotop
)

if sudo apt-get install -y -qq "${APT_PACKAGES[@]}"; then
    print_done "시스템 패키지 설치 완료"
else
    print_warn "일부 패키지 설치 실패 — dpkg 복구 시도"
    # tzdata dpkg 스크립트 패치 재시도
    echo "Asia/Seoul" > /tmp/timezone 2>/dev/null || true
    for f in /var/lib/dpkg/info/tzdata.config /var/lib/dpkg/info/tzdata.postinst; do
        [ -f "$f" ] && sudo sed -i 's|/etc/timezone|/tmp/timezone|g' "$f"
    done
    sudo dpkg --configure -a --force-confdef --force-confold 2>/dev/null || true
    sudo apt-get install -y -qq --fix-broken 2>/dev/null || true
    # 그래도 실패하면 tzdata를 hold 처리 후 나머지 패키지만 설치
    if ! dpkg -l tzdata 2>/dev/null | grep -q '^ii'; then
        echo "tzdata hold" | sudo dpkg --set-selections 2>/dev/null || true
        sudo apt-get install -y -qq "${APT_PACKAGES[@]}" 2>/dev/null || true
    fi
    print_done "시스템 패키지 설치 완료 (일부 경고 있음)"
fi

# ─────────────────────────────────────────────
# GitHub CLI (gh) 설치
# ─────────────────────────────────────────────
if command -v gh &>/dev/null; then
    print_done "GitHub CLI 이미 설치됨 ($(gh --version | head -1))"
else
    sudo mkdir -p -m 755 /etc/apt/keyrings
    wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
    sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli-stable.list >/dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq gh
    print_done "GitHub CLI 설치 완료"
fi

# ─────────────────────────────────────────────
# Git 사용자 설정
# ─────────────────────────────────────────────
git config --global user.name "Roy"
git config --global user.email "kkhong@alphacode.ai"
print_done "Git 사용자 설정 완료 (Roy <kkhong@alphacode.ai>)"

# ─────────────────────────────────────────────
# 2. uv 설치
# ─────────────────────────────────────────────
print_step "uv 설치"
if command -v uv &>/dev/null; then
    print_done "uv 이미 설치됨 ($(uv --version))"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # uv 설치 후 PATH에 추가
    export PATH="$HOME/.local/bin:$PATH"
    print_done "uv 설치 완료 ($(uv --version))"
fi

# ─────────────────────────────────────────────
# 3. Claude Code 설치
# ─────────────────────────────────────────────
print_step "Claude Code 설치"
if command -v claude &>/dev/null; then
    print_done "Claude Code 이미 설치됨"
else
    curl -fsSL https://claude.ai/install.sh | bash
    # PATH 갱신
    export PATH="$HOME/.local/bin:$PATH"
    if command -v claude &>/dev/null; then
        print_done "Claude Code 설치 완료"
    else
        print_warn "Claude Code 설치 후 PATH를 확인하세요"
    fi
fi

# ─────────────────────────────────────────────
# 4. 프로젝트 클론
# ─────────────────────────────────────────────
print_step "프로젝트 저장소 클론"
if [ -d "${PROJECT_DIR}/.git" ]; then
    print_done "프로젝트 이미 존재 — git pull 실행"
    git -C "${PROJECT_DIR}" pull --ff-only || true
else
    git clone "${PROJECT_REPO}" "${PROJECT_DIR}"
    print_done "프로젝트 클론 완료"
fi

# ─────────────────────────────────────────────
# 5. SGLang 가상환경 세팅
# ─────────────────────────────────────────────
print_step "SGLang 가상환경 생성 및 패키지 설치"
SGLANG_ENV="${PROJECT_DIR}/sglang/sglang_env"
if [ -d "${SGLANG_ENV}" ] && [ -f "${SGLANG_ENV}/bin/python" ]; then
    print_done "SGLang 가상환경 이미 존재"
else
    mkdir -p "${PROJECT_DIR}/sglang"
    uv venv "${SGLANG_ENV}" --python 3.12
    (
        source "${SGLANG_ENV}/bin/activate"
        pip install --upgrade pip
        pip install uv
        uv pip install sglang
    )
    print_done "SGLang 설치 완료"
fi

# ─────────────────────────────────────────────
# 6. vLLM 가상환경 세팅
# ─────────────────────────────────────────────
print_step "vLLM 가상환경 생성 및 패키지 설치"
VLLM_ENV="${PROJECT_DIR}/vllm/vllm_env"
if [ -d "${VLLM_ENV}" ] && [ -f "${VLLM_ENV}/bin/python" ]; then
    print_done "vLLM 가상환경 이미 존재"
else
    mkdir -p "${PROJECT_DIR}/vllm"
    uv venv "${VLLM_ENV}" --python 3.12
    (
        source "${VLLM_ENV}/bin/activate"
        # PyTorch CUDA wheel만 설치 (torchvision/torchaudio 제거 — 벤치마크에 불필요)
        uv pip install torch --index-url "${TORCH_INDEX}"
        uv pip install vllm --extra-index-url "${TORCH_INDEX}"
    )
    print_done "vLLM 설치 완료"
fi

# ─────────────────────────────────────────────
# 7. Ollama 바이너리 설치
# ─────────────────────────────────────────────
print_step "Ollama 바이너리 설치"
if command -v ollama &>/dev/null; then
    print_done "Ollama 이미 설치됨 ($(ollama --version 2>/dev/null || echo 'version unknown'))"
else
    curl -fsSL https://ollama.com/install.sh | sh
    print_done "Ollama 설치 완료"
fi

# ─────────────────────────────────────────────
# 완료 요약
# ─────────────────────────────────────────────
echo ""
echo "=========================================="
echo -e "${GREEN} 환경 세팅 완료${NC}"
echo "=========================================="
echo ""
echo "프로젝트 경로: ${PROJECT_DIR}"
echo ""
echo "다음 단계:"
echo "  1. GitHub CLI 로그인:"
echo "       gh auth login"
echo ""
echo "  2. Claude Code 로그인:"
echo "       claude login"
echo ""
echo "  3. 프로젝트 디렉토리로 이동:"
echo "       cd ${PROJECT_DIR}"
echo ""
echo "  4. Claude Code 실행:"
echo "       claude"
echo ""
echo "  5. 프레임워크 서버 실행 (필요 시):"
echo "       # SGLang"
echo "       source sglang/sglang_env/bin/activate"
echo "       python3 -m sglang.launch_server --model-path openai/gpt-oss-20b --tp 1"
echo ""
echo "       # vLLM"
echo "       source vllm/vllm_env/bin/activate"
echo "       vllm serve openai/gpt-oss-20b --host 0.0.0.0 --port 8000"
echo ""
echo "       # Ollama"
echo "       ollama serve"
echo "=========================================="
