#!/bin/bash
set -e

run_migrations() {
    echo "==> Running Django database migrations..."
    python manage.py migrate --noinput
}

case "$1" in
    backend)
        run_migrations
        APP_PORT="${PORT:-8000}"
        echo "==> Starting Django API server on 0.0.0.0:$APP_PORT..."
        if command -v gunicorn >/dev/null 2>&1; then
            exec gunicorn cropdoctor.wsgi:application --bind "0.0.0.0:$APP_PORT" --workers 2 --timeout 120
        else
            exec python manage.py runserver "0.0.0.0:$APP_PORT"
        fi
        ;;
    frontend)
        APP_PORT="${PORT:-8501}"
        echo "==> Starting Streamlit UI on 0.0.0.0:$APP_PORT..."
        exec streamlit run streamlit_app.py \
            --server.port="$APP_PORT" \
            --server.address=0.0.0.0 \
            --server.headless=true \
            --server.enableCORS=false \
            --server.enableXsrfProtection=false \
            --browser.gatherUsageStats=false \
            --server.fileWatcherType=none
        ;;
    all|"")
        echo "==> Starting in single-container mode (Django API + Streamlit UI)..."
        run_migrations

        # In single container mode, ensure Streamlit points to internal Django
        if [ -z "$API_URL" ] || [[ "$API_URL" == *"backend:8000"* ]]; then
            export API_URL="http://127.0.0.1:8000/api/analyze/"
        fi
        echo "==> Streamlit will communicate with Django API at: $API_URL"

        echo "==> Starting Django API server on 127.0.0.1:8000 in background..."
        if command -v gunicorn >/dev/null 2>&1; then
            gunicorn cropdoctor.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 120 &
        else
            python manage.py runserver 127.0.0.1:8000 &
        fi
        BACKEND_PID=$!

        APP_PORT="${PORT:-8501}"
        echo "==> Starting Streamlit UI on 0.0.0.0:$APP_PORT..."
        streamlit run streamlit_app.py \
            --server.port="$APP_PORT" \
            --server.address=0.0.0.0 \
            --server.headless=true \
            --server.enableCORS=false \
            --server.enableXsrfProtection=false \
            --browser.gatherUsageStats=false \
            --server.fileWatcherType=none &
        FRONTEND_PID=$!

        # Wait for any process to stop, then clean up
        wait -n $BACKEND_PID $FRONTEND_PID
        EXIT_CODE=$?
        kill -TERM $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
        exit $EXIT_CODE
        ;;
    *)
        exec "$@"
        ;;
esac
