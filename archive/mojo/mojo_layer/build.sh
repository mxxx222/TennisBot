#!/bin/bash
#
# Build script for Mojo Performance Layer
# Compiles all Mojo modules for production use
#

set -e

echo "🔧 Building Mojo Performance Layer..."

# Check if Mojo is installed
if ! command -v mojo &> /dev/null; then
    echo "⚠️  Mojo SDK not found. Mojo modules will not be compiled."
    echo "   Install Mojo SDK from: https://www.modular.com/max/mojo"
    exit 0
fi

MOJO_LAYER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${MOJO_LAYER_DIR}/build"

# Create build directory
mkdir -p "${BUILD_DIR}"

# Build core modules
echo "📦 Building core modules..."
if [ -f "${MOJO_LAYER_DIR}/core/tensor_ops.mojo" ]; then
    mojo build "${MOJO_LAYER_DIR}/core/tensor_ops.mojo" -o "${BUILD_DIR}/tensor_ops.mojopkg" || echo "⚠️  Failed to build tensor_ops"
fi

if [ -f "${MOJO_LAYER_DIR}/core/math_utils.mojo" ]; then
    mojo build "${MOJO_LAYER_DIR}/core/math_utils.mojo" -o "${BUILD_DIR}/math_utils.mojopkg" || echo "⚠️  Failed to build math_utils"
fi

# Build ML modules
echo "🤖 Building ML modules..."
if [ -f "${MOJO_LAYER_DIR}/ml/inference.mojo" ]; then
    mojo build "${MOJO_LAYER_DIR}/ml/inference.mojo" -o "${BUILD_DIR}/inference.mojopkg" || echo "⚠️  Failed to build inference"
fi

if [ -f "${MOJO_LAYER_DIR}/ml/ensemble.mojo" ]; then
    mojo build "${MOJO_LAYER_DIR}/ml/ensemble.mojo" -o "${BUILD_DIR}/ensemble.mojopkg" || echo "⚠️  Failed to build ensemble"
fi

# Build feature engineering modules
echo "🔬 Building feature engineering modules..."
if [ -f "${MOJO_LAYER_DIR}/features/engineering.mojo" ]; then
    mojo build "${MOJO_LAYER_DIR}/features/engineering.mojo" -o "${BUILD_DIR}/engineering.mojopkg" || echo "⚠️  Failed to build engineering"
fi

if [ -f "${MOJO_LAYER_DIR}/features/transforms.mojo" ]; then
    mojo build "${MOJO_LAYER_DIR}/features/transforms.mojo" -o "${BUILD_DIR}/transforms.mojopkg" || echo "⚠️  Failed to build transforms"
fi

# Build batch processing modules
echo "⚡ Building batch processing modules..."
if [ -f "${MOJO_LAYER_DIR}/batch/processor.mojo" ]; then
    mojo build "${MOJO_LAYER_DIR}/batch/processor.mojo" -o "${BUILD_DIR}/processor.mojopkg" || echo "⚠️  Failed to build processor"
fi

# Build ROI calculation modules
echo "💰 Building ROI calculation modules..."
if [ -f "${MOJO_LAYER_DIR}/roi/calculations.mojo" ]; then
    mojo build "${MOJO_LAYER_DIR}/roi/calculations.mojo" -o "${BUILD_DIR}/roi_calculations.mojopkg" || echo "⚠️  Failed to build ROI calculations"
fi

echo "✅ Mojo build complete! Built packages in ${BUILD_DIR}/"
echo ""
echo "📝 Note: If Mojo SDK is not installed, Python fallback will be used automatically."

