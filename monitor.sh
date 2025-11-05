#!/bin/bash

# Betfury System Monitor
# ======================
# Monitors the Docker container and restarts if needed
# Runs every 15 minutes via cron

LOG_FILE="/var/log/betfury-monitor.log"
CONTAINER_NAME="betfury-ultimate"
TELEGRAM_BOT_TOKEN="8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM"
TELEGRAM_CHAT_ID="-4956738581"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to send Telegram alert
send_telegram() {
    local message="$1"
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "text=$message" \
        -d "parse_mode=Markdown" > /dev/null
}

log "🔍 Starting system health check..."

# Check if container is running
if ! docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    log "⚠️ Container not running! Restarting..."
    send_telegram "🚨 Betfury system was down and has been restarted"
    
    # Try to start the container
    if docker-compose up -d; then
        log "✅ Container restarted successfully"
        send_telegram "✅ Betfury system restarted successfully"
    else
        log "❌ Failed to restart container"
        send_telegram "❌ Failed to restart Betfury system"
        exit 1
    fi
else
    log "✅ Container is running"
fi

# Check container health
CONTAINER_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
if [ "$CONTAINER_HEALTH" = "unhealthy" ]; then
    log "⚠️ Container health check failed! Restarting..."
    send_telegram "⚠️ Betfury system health check failed, restarting..."
    
    docker-compose restart
    sleep 10
    
    if docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        log "✅ Container restarted after health check failure"
        send_telegram "✅ Betfury system restarted successfully after health check failure"
    else
        log "❌ Container failed to restart"
        send_telegram "❌ Betfury system failed to restart"
        exit 1
    fi
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    log "⚠️ Disk usage high: ${DISK_USAGE}%"
    
    # Clean old logs
    find ./logs/ -name "*.log" -mtime +7 -delete 2>/dev/null
    docker system prune -f > /dev/null 2>&1
    
    log "🧹 Cleaned old logs and Docker resources"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$MEMORY_USAGE" -gt 90 ]; then
    log "⚠️ Memory usage high: ${MEMORY_USAGE}%. Restarting container..."
    send_telegram "⚠️ High memory usage detected (${MEMORY_USAGE}%), restarting..."
    
    docker-compose restart
    sleep 10
    
    if docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        log "✅ Container restarted due to high memory usage"
        send_telegram "✅ Betfury system restarted due to high memory usage"
    fi
fi

# Check recent logs for errors
ERROR_COUNT=$(docker-compose logs --since="1h" | grep -i "error\|exception\|failed" | wc -l)
if [ "$ERROR_COUNT" -gt 10 ]; then
    log "⚠️ High error count in logs: $ERROR_COUNT errors in last hour"
    send_telegram "⚠️ High error count detected ($ERROR_COUNT errors in last hour)"
fi

# Check network connectivity
if ! ping -c 1 google.com > /dev/null 2>&1; then
    log "⚠️ Network connectivity issue detected"
    send_telegram "⚠️ Network connectivity issue detected"
fi

# Show system status
log "📊 System Status:"
log "   Docker containers: $(docker ps --format '{{.Names}}' | tr '\n' ' ')"
log "   Disk usage: ${DISK_USAGE}%"
log "   Memory usage: ${MEMORY_USAGE}%"
log "   Recent errors: $ERROR_COUNT"

log "✅ System health check completed"

# Create log rotation
if [ ! -f "/var/log/betfury-monitor.logrotate" ]; then
    cat > /var/log/betfury-monitor.logrotate << 'EOF'
/var/log/betfury-monitor.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
}
EOF
fi

exit 0