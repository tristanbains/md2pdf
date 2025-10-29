.PHONY: restart build clean install-deps dev git-quick

# Development: restart server and open browser
restart:
	@echo "🛑 Killing existing server..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@sleep 1
	@echo "🚀 Starting server..."
	@uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000 &
	@sleep 2
	@echo "🌐 Opening browser..."
	@open http://127.0.0.1:8000
	@echo "✅ Server started!"

# Start dev server (foreground with logs)
dev:
	uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000

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
