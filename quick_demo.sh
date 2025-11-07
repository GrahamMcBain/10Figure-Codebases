#!/bin/bash
set -e

echo "🚀 Setting up Legacy Codebase Benchmark Demo..."

# Check if we're in the right directory
if [[ ! -f "README.md" ]] || [[ ! -d "scripts" ]]; then
    echo "❌ Please run this from the 10Figure-Codebases directory"
    echo "   git clone https://github.com/GrahamMcBain/10Figure-Codebases.git"
    echo "   cd 10Figure-Codebases"
    echo "   ./quick_demo.sh"
    exit 1
fi

echo "✅ Installing Python dependencies..."
make install

echo "✅ Building corpus (small version for demo)..."
make build-corpus-small

echo "✅ Generating benchmark tasks..."
make generate-tasks

echo ""
echo "🎯 BENCHMARK READY!"
echo ""
echo "Next steps for AI agent evaluation:"
echo "1. Give your AI agent the prompt from AGENT_DEMO.md"
echo "2. Let it explore the codebase and complete tasks"
echo "3. Run: python3 scripts/validate_patch.py [agent_solution].diff"
echo ""
echo "Quick test with dummy patch:"
echo "   python3 scripts/validate_patch.py test_patch.diff"
echo ""
echo "📖 Full instructions: cat AGENT_DEMO.md"
