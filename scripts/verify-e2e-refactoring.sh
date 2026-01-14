#!/bin/bash

# E2E 测试重构验证脚本
# 用于验证重构是否成功完成

set -e

echo "======================================"
echo "🔍 E2E 测试重构验证"
echo "======================================"
echo

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. 检查前端 E2E 目录
echo "1. 检查前端 E2E 目录..."
if [ -d "frontend/e2e" ]; then
    check_pass "frontend/e2e/ 目录存在"
else
    check_fail "frontend/e2e/ 目录不存在"
fi

# 2. 检查前端 E2E 测试文件
echo "2. 检查前端 E2E 测试文件..."
if [ -f "frontend/e2e/ui-full-flow.spec.ts" ]; then
    check_pass "ui-full-flow.spec.ts 已移动到 frontend/e2e/"
else
    check_fail "ui-full-flow.spec.ts 不在 frontend/e2e/"
fi

if [ -f "frontend/e2e/visual-regression.spec.ts" ]; then
    check_pass "visual-regression.spec.ts 已移动到 frontend/e2e/"
else
    check_fail "visual-regression.spec.ts 不在 frontend/e2e/"
fi

# 3. 检查 Playwright 配置
echo "3. 检查 Playwright 配置..."
if [ -f "frontend/playwright.config.ts" ]; then
    check_pass "playwright.config.ts 已移动到 frontend/"
else
    check_fail "playwright.config.ts 不在 frontend/"
fi

# 4. 检查前端 package.json
echo "4. 检查前端 package.json..."
if grep -q "@playwright/test" frontend/package.json; then
    check_pass "frontend/package.json 包含 Playwright 依赖"
else
    check_fail "frontend/package.json 缺少 Playwright 依赖"
fi

if grep -q "test:e2e" frontend/package.json; then
    check_pass "frontend/package.json 包含 E2E 测试脚本"
else
    check_fail "frontend/package.json 缺少 E2E 测试脚本"
fi

# 5. 检查后端集成测试
echo "5. 检查后端集成测试..."
if [ -f "backend/tests/integration/test_api_full_flow.py" ]; then
    check_pass "test_api_full_flow.py 已创建在 backend/tests/integration/"
else
    check_fail "test_api_full_flow.py 不在 backend/tests/integration/"
fi

# 6. 检查根目录清理
echo "6. 检查根目录清理..."
if [ ! -d "e2e" ]; then
    check_pass "根目录 e2e/ 已删除"
else
    check_warn "根目录 e2e/ 仍然存在（应该已删除）"
fi

if [ ! -f "playwright.config.ts" ]; then
    check_pass "根目录 playwright.config.ts 已删除"
else
    check_warn "根目录 playwright.config.ts 仍然存在（应该已删除）"
fi

if [ ! -f "tsconfig.json" ]; then
    check_pass "根目录 tsconfig.json 已删除"
else
    check_warn "根目录 tsconfig.json 仍然存在（应该已删除）"
fi

if [ ! -d "node_modules" ]; then
    check_pass "根目录 node_modules/ 已删除"
else
    check_warn "根目录 node_modules/ 仍然存在（应该已删除）"
fi

# 7. 检查 CI 配置
echo "7. 检查 CI 配置..."
if grep -q "cd frontend" .github/workflows/ci-test.yml; then
    check_pass "CI 配置已更新（包含 'cd frontend'）"
else
    check_warn "CI 配置可能未更新"
fi

if grep -q "test_api_full_flow.py" .github/workflows/ci-test.yml; then
    check_pass "CI 配置包含后端 API 测试"
else
    check_warn "CI 配置可能缺少后端 API 测试"
fi

# 8. 检查 .gitignore
echo "8. 检查 .gitignore..."
if grep -q "test-results/" frontend/.gitignore; then
    check_pass "frontend/.gitignore 已更新"
else
    check_warn "frontend/.gitignore 可能需要更新"
fi

echo
echo "======================================"
echo "✅ E2E 测试重构验证完成！"
echo "======================================"
echo
echo "下一步："
echo "1. cd frontend && npm install  # 安装前端依赖（包括 Playwright）"
echo "2. cd frontend && npm run test:e2e  # 运行前端 E2E 测试"
echo "3. cd backend && pixi run pytest tests/integration/ -v  # 运行后端集成测试"
echo

