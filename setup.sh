#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# LLM Serving Framework Benchmark - 자동 환경 세팅 스크립트
#
# 사용법:
#   bash setup.sh
#
# 서버 재시작 후 이 스크립트를 실행하면 전체 환경이 자동으로 구성됩니다.
# =============================================================================

WORK_DIR="/home/work"
PROJECT_REPO="https://github.com/KihongK/llm-serving-framework-benchmark-test.git"
PROJECT_DIR="${WORK_DIR}/llm-serving-framework-benchmark-test"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

step=0
total_steps=8

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

apt-get update -qq

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

apt-get install -y -qq "${APT_PACKAGES[@]}"
print_done "시스템 패키지 설치 완료"

# ─────────────────────────────────────────────
# GitHub CLI (gh) 설치
# ─────────────────────────────────────────────
if command -v gh &>/dev/null; then
    print_done "GitHub CLI 이미 설치됨 ($(gh --version | head -1))"
else
    mkdir -p -m 755 /etc/apt/keyrings
    wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
    chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli-stable.list >/dev/null
    apt-get update -qq
    apt-get install -y -qq gh
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
# 5. 프레임워크 소스 클론
# ─────────────────────────────────────────────
print_step "프레임워크 소스 클론 (sglang, vllm, ollama)"

clone_framework() {
    local name=$1 url=$2 tag=$3
    local dir="${PROJECT_DIR}/${name}"
    if [ -d "${dir}/.git" ]; then
        print_done "${name} 이미 클론됨"
    else
        git clone "${url}" "${dir}"
        git -C "${dir}" checkout "${tag}"
        print_done "${name} 클론 완료 (${tag})"
    fi
}

clone_framework "sglang" "https://github.com/sgl-project/sglang.git" "v0.5.6.post2"
clone_framework "vllm"   "https://github.com/vllm-project/vllm.git"  "v0.16.0rc1"
clone_framework "ollama"  "https://github.com/ollama/ollama.git"      "v0.15.6"

# ─────────────────────────────────────────────
# 6. SGLang 가상환경 세팅
# ─────────────────────────────────────────────
print_step "SGLang 가상환경 생성 및 패키지 설치"
SGLANG_ENV="${PROJECT_DIR}/sglang/sglang_env"
if [ -d "${SGLANG_ENV}" ] && [ -f "${SGLANG_ENV}/bin/python" ]; then
    print_done "SGLang 가상환경 이미 존재"
else
    uv venv "${SGLANG_ENV}" --python 3.12
    # subshell로 가상환경 활성화 후 설치
    (
        source "${SGLANG_ENV}/bin/activate"
        uv pip install "sglang[all]==0.5.6.post2"
    )
    print_done "SGLang 설치 완료"
fi

# ─────────────────────────────────────────────
# 7. vLLM 가상환경 세팅
# ─────────────────────────────────────────────
print_step "vLLM 가상환경 생성 및 패키지 설치"
VLLM_ENV="${PROJECT_DIR}/vllm/vllm_env"
if [ -d "${VLLM_ENV}" ] && [ -f "${VLLM_ENV}/bin/python" ]; then
    print_done "vLLM 가상환경 이미 존재"
else
    uv venv "${VLLM_ENV}" --python 3.12
    (
        source "${VLLM_ENV}/bin/activate"
        uv pip install vllm
    )
    print_done "vLLM 설치 완료"
fi

# ─────────────────────────────────────────────
# 8. Ollama 바이너리 설치
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
echo "  4. 프레임워크 서버 실행 (필요 시):"
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
