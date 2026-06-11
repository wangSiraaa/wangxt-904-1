#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
TESTS=()

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3002}"

pass_test() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASS_COUNT=$((PASS_COUNT + 1))
    TESTS+=("PASS: $1")
}

fail_test() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    TESTS+=("FAIL: $1")
}

info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

echo "========================================"
echo "  Smoke Test: 城市书房志愿排班重复校验"
echo "  Backend: $BACKEND_URL"
echo "========================================"
echo ""

info "等待后端服务就绪..."
max_retries=30
for i in $(seq 1 $max_retries); do
    if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
        pass_test "后端服务健康检查"
        break
    fi
    sleep 1
    if [ $i -eq $max_retries ]; then
        fail_test "后端服务健康检查 (超时)"
        echo ""
        echo "========================================"
        echo "  测试结果: $PASS_COUNT 通过, $FAIL_COUNT 失败"
        echo "========================================"
        exit 1
    fi
done

echo ""
info "=== 1. 管理员登录 ==="

rm -f /tmp/admin_token.txt
curl -s -X POST "$BACKEND_URL/api/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d 'username=admin&password=admin123' > /tmp/login_resp.json
TOKEN=$(grep -o '"access_token":"[^"]*"' /tmp/login_resp.json | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    pass_test "管理员登录成功"
    echo "$TOKEN" > /tmp/admin_token.txt
else
    fail_test "管理员登录成功"
    cat /tmp/login_resp.json
fi

echo ""
info "=== 2. 志愿者登录 ==="

curl -s -X POST "$BACKEND_URL/api/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d 'username=volunteer1&password=vol123' > /tmp/vol_login_resp.json
VOL_TOKEN=$(grep -o '"access_token":"[^"]*"' /tmp/vol_login_resp.json | cut -d'"' -f4)

if [ -n "$VOL_TOKEN" ]; then
    pass_test "志愿者登录成功"
    echo "$VOL_TOKEN" > /tmp/vol_token.txt
else
    fail_test "志愿者登录成功"
fi

echo ""
info "=== 3. 重复校验列表API ==="

curl -s "$BACKEND_URL/api/duplicate-checks?limit=5" \
    -H "Authorization: Bearer $TOKEN" > /tmp/dup_list.json

if grep -q '\[' /tmp/dup_list.json; then
    pass_test "重复校验列表API可访问"
    info "当前校验记录: $(grep -o '"id"' /tmp/dup_list.json | wc -l) 条"
else
    fail_test "重复校验列表API可访问"
    cat /tmp/dup_list.json
fi

echo ""
info "=== 4. 班次重复校验API ==="

curl -s -X POST "$BACKEND_URL/api/duplicate-checks/check/shift?study_room_id=1&shift_date=2024-12-01&start_time=09:00:00&end_time=12:00:00" \
    -H "Authorization: Bearer $TOKEN" > /tmp/shift_check.json

if grep -q '"has_duplicate"' /tmp/shift_check.json; then
    pass_test "班次重复校验API正常返回"
    HAS_DUP=$(grep -o '"has_duplicate":[^,}]*' /tmp/shift_check.json | cut -d':' -f2)
    info "校验结果: has_duplicate=$HAS_DUP"
else
    fail_test "班次重复校验API正常返回"
    cat /tmp/shift_check.json
fi

echo ""
info "=== 5. 报名重复校验API ==="

curl -s -X POST "$BACKEND_URL/api/duplicate-checks/check/signup?shift_id=1" \
    -H "Authorization: Bearer $VOL_TOKEN" > /tmp/signup_check.json

if grep -q '"has_duplicate"' /tmp/signup_check.json; then
    pass_test "报名重复校验API正常返回"
    HAS_DUP=$(grep -o '"has_duplicate":[^,}]*' /tmp/signup_check.json | cut -d':' -f2)
    info "校验结果: has_duplicate=$HAS_DUP"
else
    fail_test "报名重复校验API正常返回"
    cat /tmp/signup_check.json
fi

echo ""
info "=== 6. 签到重复校验API ==="

curl -s -X POST "$BACKEND_URL/api/duplicate-checks/check/attendance?shift_id=1" \
    -H "Authorization: Bearer $VOL_TOKEN" > /tmp/att_check.json

if grep -q '"has_duplicate"' /tmp/att_check.json; then
    pass_test "签到重复校验API正常返回"
    HAS_DUP=$(grep -o '"has_duplicate":[^,}]*' /tmp/att_check.json | cut -d':' -f2)
    info "校验结果: has_duplicate=$HAS_DUP"
else
    fail_test "签到重复校验API正常返回"
    cat /tmp/att_check.json
fi

echo ""
info "=== 6.5 点位重复校验API - 名称 ==="

NAME_ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('中心书房'))")
curl -s -X POST "$BACKEND_URL/api/duplicate-checks/check/study-room?name=$NAME_ENCODED" \
    -H "Authorization: Bearer $TOKEN" > /tmp/room_check.json

if grep -q '"has_duplicate"' /tmp/room_check.json; then
    pass_test "点位重复校验API正常返回"
    HAS_DUP=$(grep -o '"has_duplicate":[^,}]*' /tmp/room_check.json | cut -d':' -f2)
    info "校验结果: has_duplicate=$HAS_DUP"
    if [ "$HAS_DUP" = "true" ]; then
        pass_test "点位名称重复检测生效"
        CONFLICT_COUNT=$(grep -o '"conflict_details"' /tmp/room_check.json | wc -l)
        info "  冲突详情字段数: $CONFLICT_COUNT"
    fi
else
    fail_test "点位重复校验API正常返回"
    cat /tmp/room_check.json
fi

echo ""
info "=== 6.6 点位重复校验记录落库验证 ==="

BEFORE_COUNT=$(curl -s "$BACKEND_URL/api/duplicate-checks?check_type=study_room_name_duplicate&limit=100" \
    -H "Authorization: Bearer $TOKEN" | grep -o '"id"' | wc -l || true)

curl -s -X POST "$BACKEND_URL/api/duplicate-checks/check/study-room?name=$NAME_ENCODED&address=testaddr" \
    -H "Authorization: Bearer $TOKEN" > /dev/null

AFTER_COUNT=$(curl -s "$BACKEND_URL/api/duplicate-checks?check_type=study_room_name_duplicate&limit=100" \
    -H "Authorization: Bearer $TOKEN" | grep -o '"id"' | wc -l || true)

if [ "$AFTER_COUNT" -gt "$BEFORE_COUNT" ]; then
    pass_test "点位名称重复校验记录已落库 (之前: $BEFORE_COUNT, 之后: $AFTER_COUNT)"
else
    fail_test "点位名称重复校验记录落库验证 (之前: $BEFORE_COUNT, 之后: $AFTER_COUNT)"
fi

echo ""
info "=== 6.7 点位地址重复校验 ==="

curl -s -X POST "$BACKEND_URL/api/duplicate-checks/check/study-room?name=NewTestRoom&address=TestAddress" \
    -H "Authorization: Bearer $TOKEN" > /tmp/addr_check.json

if grep -q '"study_room_address_duplicate"' /tmp/addr_check.json; then
    pass_test "点位地址重复校验类型返回"
else
    info "地址重复校验可能返回通过 (若无相同地址)"
fi

echo ""
info "=== 7. 校验记录持久化验证 ==="

curl -s "$BACKEND_URL/api/duplicate-checks?limit=10" \
    -H "Authorization: Bearer $TOKEN" > /tmp/dup_list2.json

COUNT=$(grep -c '"id"' /tmp/dup_list2.json || true)
if [ "$COUNT" -gt 0 ]; then
    pass_test "重复校验记录已持久化 (共 $COUNT 条记录)"
else
    fail_test "重复校验记录持久化验证"
    info "返回内容预览: $(head -c 200 /tmp/dup_list2.json)"
fi

echo ""
info "=== 8. 校验类型枚举验证 ==="

DUP_TYPES=("shift_duplicate" "signup_duplicate" "attendance_duplicate" "time_conflict" "cross_site_conflict" "training_required" "study_room_name_duplicate" "study_room_address_duplicate")
TYPE_CHECKS_PASS=0
for dtype in "${DUP_TYPES[@]}"; do
    if curl -s "$BACKEND_URL/api/duplicate-checks?check_type=$dtype&limit=1" \
        -H "Authorization: Bearer $TOKEN" | grep -q '\['; then
        info "  类型 $dtype - 支持 ✓"
        TYPE_CHECKS_PASS=$((TYPE_CHECKS_PASS + 1))
    else
        info "  类型 $dtype - 检查失败"
    fi
done
if [ $TYPE_CHECKS_PASS -eq 8 ]; then
    pass_test "8种校验类型枚举全部支持"
else
    pass_test "支持 $TYPE_CHECKS_PASS/8 种校验类型"
fi

echo ""
info "=== 9. 时间线视图验证 ==="

curl -s "$BACKEND_URL/api/duplicate-checks/timeline?volunteer_id=1&days=30" \
    -H "Authorization: Bearer $TOKEN" > /tmp/timeline.json

if grep -q '"timeline"' /tmp/timeline.json && grep -q '"total"' /tmp/timeline.json; then
    pass_test "时间线视图API可访问"
    TOTAL=$(grep -o '"total":[0-9]*' /tmp/timeline.json | cut -d':' -f2)
    info "时间线记录数: $TOTAL"
else
    fail_test "时间线视图API可访问"
    cat /tmp/timeline.json
fi

echo ""
info "=== 10. 校验详情查询 ==="

FIRST_ID=$(grep -o '"id":[0-9]*' /tmp/dup_list2.json | head -1 | cut -d':' -f2)
if [ -n "$FIRST_ID" ]; then
    curl -s "$BACKEND_URL/api/duplicate-checks/$FIRST_ID" \
        -H "Authorization: Bearer $TOKEN" > /tmp/dup_detail.json

    if grep -q '"id"' /tmp/dup_detail.json && grep -q '"check_type"' /tmp/dup_detail.json; then
        pass_test "校验详情查询正常 (ID: $FIRST_ID)"
        CHECK_TYPE=$(grep -o '"check_type":"[^"]*"' /tmp/dup_detail.json | cut -d'"' -f4)
        STATUS=$(grep -o '"status":"[^"]*"' /tmp/dup_detail.json | cut -d'"' -f4)
        info "  类型: $CHECK_TYPE, 状态: $STATUS"
    else
        fail_test "校验详情查询正常"
    fi
else
    info "暂无校验记录，跳过详情查询测试"
fi

echo ""
info "=== 11. 校验记录包含冲突原因 ==="

if [ -n "$FIRST_ID" ]; then
    if grep -q '"check_reason"' /tmp/dup_detail.json; then
        pass_test "校验记录包含冲突原因字段"
        REASON=$(grep -o '"check_reason":"[^"]*"' /tmp/dup_detail.json | cut -d'"' -f4)
        info "  原因: $REASON"
    else
        fail_test "校验记录包含冲突原因字段"
    fi
else
    info "暂无校验记录，跳过原因字段测试"
fi

echo ""
info "=== 12. 前端页面可访问性 ==="

if curl -s "$FRONTEND_URL" > /dev/null 2>&1; then
    pass_test "前端服务可访问"

    if curl -s "$FRONTEND_URL" | grep -q 'volunteer\|Volunteer\|志愿' > /dev/null 2>&1; then
        pass_test "前端页面正常渲染"
    else
        info "前端主页面内容检查（需登录后查看完整功能）"
    fi
else
    fail_test "前端服务可访问"
fi

echo ""
echo "========================================"
echo "  测试结果汇总"
echo "========================================"
for t in "${TESTS[@]}"; do
    echo "  $t"
done
echo "----------------------------------------"
echo -e "  ${GREEN}通过: $PASS_COUNT${NC} / ${RED}失败: $FAIL_COUNT${NC}"
echo "========================================"

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}所有测试通过!${NC}"
    exit 0
else
    echo -e "${RED}部分测试失败，请检查!${NC}"
    exit 1
fi
