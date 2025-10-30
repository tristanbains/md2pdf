.PHONY: restart build clean install-deps dev stop git-quick

# Development: restart server and open browser
restart:
	@echo "🛑 Killing existing server..."
	@lsof -ti:8000 | xargs kill -TERM 2>/dev/null || true
	@sleep 1
	@echo "🚀 Starting server (press CTRL+C to stop)..."
	@(for i in 1 2 3 4 5 6 7 8 9 10; do curl -s http://127.0.0.1:8000 > /dev/null 2>&1 && break || sleep 0.5; done; open http://127.0.0.1:8000) &
	@uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Start dev server (alias of restart)
dev: restart

# Stop server
stop:
	@echo "🛑 Stopping server..."
	@lsof -ti:8000 | xargs kill -TERM 2>/dev/null && echo "✅ Server stopped" || echo "ℹ️  No server running on port 8000"

# Install build dependencies
install-deps:
	uv add py2app

# Build macOS .app bundle
build:
	@echo "📦 Building MD2PDF.app..."
	uv run python setup.py py2app
	@echo "✅ Build complete! App located at: dist/MD2PDF.app"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build dist
	@echo "✅ Clean complete!"

# Quick git: add, commit, and push
git-quick:
	@if [ -z "$(m)" ]; then \
		echo "❌ Error: Commit message required. Usage: make git-quick m=\"your message\""; \
		exit 1; \
	fi
	@echo "📝 Adding all files..."
	@git add .
	@echo "💾 Committing with message: $(m)"
	@git commit -m "$(m)"
	@echo "🚀 Pushing to remote..."
	@git push
	@echo "✅ Done!"
