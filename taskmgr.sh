#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$DIR/.flask.pid"
LOG_FILE="$DIR/flask.log"
HOST="127.0.0.1"
PORT=5000
VENV_PYTHON="$DIR/.venv/bin/python"

start() {
    if status >/dev/null 2>&1; then
        echo "服务已在运行 (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    nohup "$VENV_PYTHON" "$DIR/run.py" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    # 等待最多 5 秒确认启动成功
    for i in $(seq 1 10); do
        if curl --noproxy '*' -s -o /dev/null -w '' "http://$HOST:$PORT/" 2>/dev/null; then
            echo "服务已启动 (PID: $(cat "$PID_FILE"), http://$HOST:$PORT)"
            return 0
        fi
        sleep 0.5
    done

    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "进程已启动但尚未响应 (PID: $(cat "$PID_FILE"))，日志: $LOG_FILE"
        return 0
    else
        echo "启动失败，请查看日志: $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "服务未运行"
        return 1
    fi

    local pid
    pid=$(cat "$PID_FILE")

    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        # 等待最多 3 秒
        for i in $(seq 1 6); do
            if ! kill -0 "$pid" 2>/dev/null; then
                rm -f "$PID_FILE"
                echo "服务已停止"
                return 0
            fi
            sleep 0.5
        done
        # 强制杀死
        kill -9 "$pid" 2>/dev/null || true
        rm -f "$PID_FILE"
        echo "服务已强制停止"
    else
        rm -f "$PID_FILE"
        echo "PID 文件过期，已清理"
    fi
}

status() {
    if [ ! -f "$PID_FILE" ]; then
        echo "服务未运行"
        return 1
    fi

    local pid
    pid=$(cat "$PID_FILE")

    if kill -0 "$pid" 2>/dev/null; then
        echo "服务运行中 (PID: $pid, http://$HOST:$PORT)"
        return 0
    else
        echo "服务未运行 (PID 文件过期)"
        rm -f "$PID_FILE"
        return 1
    fi
}

case "${1:-}" in
    start)  start  ;;
    stop)   stop   ;;
    status) status ;;
    restart) stop 2>/dev/null; sleep 1; start ;;
    log)    less +G "$LOG_FILE" ;;
    *)
        echo "用法: $0 {start|stop|restart|status|log}"
        exit 1
        ;;
esac
