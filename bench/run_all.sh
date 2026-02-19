#!/usr/bin/env bash
# =============================================================================
# LLM Serving Framework Benchmark - 전체 실행 스크립트
# =============================================================================
#
# 사용법:
#   bash bench/run_all.sh                              # 전체 실행 (SGLang -> vLLM -> Ollama)
#   bash bench/run_all.sh sglang                       # SGLang만 실행
#   bash bench/run_all.sh vllm concurrent              # vLLM의 concurrent 시나리오만 실행
#   bash bench/run_all.sh ollama single                # Ollama의 single 시나리오만 실행
#   bash bench/run_all.sh sglang all llama3.1-8b       # SGLang + Llama 3.1 8B 모델
#
# 주의: 각 프레임워크 서버를 별도로 시작해야 합니다.
#       이 스크립트는 이미 실행 중인 서버에 대해 벤치마크를 수행합니다.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 벤치마크 전용 가상환경
BENCH_ENV="$SCRIPT_DIR/bench_env"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ---- 벤치마크 환경 준비 ----
setup_bench_env() {
    if [ ! -d "$BENCH_ENV" ]; then
        log_info "Creating benchmark virtual environment..."
        uv venv "$BENCH_ENV" --python 3.12
        source "$BENCH_ENV/bin/activate"
        uv pip install aiohttp numpy tqdm matplotlib
        deactivate
        log_info "Benchmark environment created."
    else
        log_info "Benchmark environment already exists."
    fi
}

# ---- GPU 상태 확인 ----
check_gpu() {
    log_info "GPU Status:"
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu \
        --format=csv,noheader 2>/dev/null || log_warn "nvidia-smi not available"
    echo ""
}

# ---- 서버 health 체크 ----
wait_for_server() {
    local url=$1
    local name=$2
    local max_wait=120
    local waited=0

    log_info "Waiting for $name server at $url ..."
    while [ $waited -lt $max_wait ]; do
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            log_info "$name server is ready."
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done

    log_error "$name server did not respond within ${max_wait}s at $url"
    return 1
}

# ---- 프레임워크별 벤치마크 실행 ----
run_benchmark() {
    local framework=$1
    local scenario=${2:-all}
    local model=${3:-gpt-oss-20b}

    log_info "============================================"
    log_info "Running benchmark: $framework (model: $model, scenario: $scenario)"
    log_info "============================================"

    # 서버 health 체크
    case $framework in
        sglang)
            wait_for_server "http://localhost:30000/health" "SGLang" || return 1
            ;;
        vllm)
            wait_for_server "http://localhost:8000/health" "vLLM" || return 1
            ;;
        ollama)
            wait_for_server "http://localhost:11434/api/tags" "Ollama" || return 1
            ;;
    esac

    # 벤치마크 실행
    local trials=${BENCH_TRIALS:-1}
    source "$BENCH_ENV/bin/activate"
    python3 -m bench \
        --framework "$framework" \
        --model "$model" \
        --scenario "$scenario" \
        --trials "$trials" \
        --output-dir "$PROJECT_DIR/results/$framework"
    deactivate

    log_info "$framework benchmark complete."
    echo ""
}

# ---- 결과 요약 생성 ----
generate_summary() {
    log_info "Generating summary..."

    local summary_dir="$PROJECT_DIR/results/summary"
    local results_dir="$PROJECT_DIR/results"
    mkdir -p "$summary_dir"

    # 모든 결과 JSON을 하나의 요약으로 합치기
    source "$BENCH_ENV/bin/activate"
    python3 -c "
import json, glob, os

summary_dir = '$summary_dir'
results_dir = '$results_dir'
all_data = {}

for fw in ['sglang', 'vllm', 'ollama']:
    fw_dir = os.path.join(results_dir, fw)
    if not os.path.isdir(fw_dir):
        continue
    for fname in sorted(os.listdir(fw_dir)):
        if fname.endswith('_results.json'):
            fpath = os.path.join(fw_dir, fname)
            with open(fpath) as f:
                key = fname.replace('_results.json', '')
                all_data[key] = json.load(f)

if all_data:
    with open(os.path.join(summary_dir, 'all_results.json'), 'w') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f'Summary saved to {summary_dir}/all_results.json')

    # 간단한 비교 표 생성
    lines = ['# Benchmark Results Summary\n']
    lines.append(f'Generated: {__import__(\"time\").strftime(\"%Y-%m-%d %H:%M:%S\")}\n')

    for scenario in ['single_request', 'concurrent_load', 'long_context', 'prefix_cache']:
        lines.append(f'\n## {scenario}\n')
        lines.append('| Framework | Concurrency | Input | TTFT(avg) | Throughput | p99 Latency | Success |')
        lines.append('|-----------|-------------|-------|-----------|------------|-------------|---------|')
        for fw, data in all_data.items():
            for r in data.get('results', []):
                if r['scenario'] == scenario:
                    lines.append(
                        f\"| {fw} | {r['concurrency']} | {r['input_tokens']} | \"
                        f\"{r['avg_ttft_ms']}ms | {r['total_token_throughput']}tok/s | \"
                        f\"{r['p99_latency_ms']}ms | {r['success_rate']}% |\"
                    )

    with open(os.path.join(summary_dir, 'comparison.md'), 'w') as f:
        f.write('\n'.join(lines))
    print(f'Comparison saved to {summary_dir}/comparison.md')
else:
    print('No result files found.')
"
    deactivate
}

# ---- 분석 보고서 + 차트 생성 ----
run_analysis() {
    log_info "Generating analysis report and charts..."
    source "$BENCH_ENV/bin/activate"
    python3 -m bench.analyze --results-dir "$PROJECT_DIR/results"
    deactivate
    log_info "Analysis complete. See results/summary/"
}

# ---- 메인 ----
main() {
    local target_framework=${1:-all}
    local target_scenario=${2:-all}
    local target_model=${3:-gpt-oss-20b}

    echo "============================================"
    echo " LLM Serving Framework Benchmark"
    echo " Model: $target_model"
    echo " $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================"
    echo ""

    check_gpu
    setup_bench_env

    if [ "$target_framework" = "all" ]; then
        # 전체 실행: 각 프레임워크별로 서버가 실행 중이어야 함
        log_warn "Running all frameworks sequentially."
        log_warn "Make sure each framework server is started BEFORE its benchmark runs."
        log_warn "Recommended: run each framework separately:"
        log_warn "  bash bench/run_all.sh sglang all gpt-oss-20b"
        log_warn "  bash bench/run_all.sh vllm all gpt-oss-20b"
        log_warn "  bash bench/run_all.sh ollama all gpt-oss-20b"
        echo ""

        for fw in sglang vllm ollama; do
            run_benchmark "$fw" "$target_scenario" "$target_model" || log_error "$fw benchmark failed. Continuing..."
            echo ""
        done

        generate_summary
        run_analysis
    else
        run_benchmark "$target_framework" "$target_scenario" "$target_model"
    fi

    log_info "All done."
}

main "$@"
