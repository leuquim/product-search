#!/bin/bash

# Start Lenovo Part Search in background
# Useful for keeping terminal free

cd "$(dirname "$0")"

echo "🚀 Starting Lenovo Part Search in background..."

# Start the server in background
nohup ./quick_start.sh > server.log 2>&1 &

# Get the process ID
SERVER_PID=$!

echo "✅ Server started with PID: $SERVER_PID"
echo "📍 Local access: http://localhost:8080"
echo "📁 File management: http://localhost:8080/files"
echo ""
echo "📋 To stop the server later:"
echo "   kill $SERVER_PID"
echo ""
echo "📖 To view logs:"
echo "   tail -f server.log"

# Try to open browser after short delay
(sleep 3 && command -v xdg-open >/dev/null && xdg-open http://localhost:8080) &

echo ""
echo "🎉 Server is running in the background!"