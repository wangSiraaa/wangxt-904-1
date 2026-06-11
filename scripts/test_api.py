import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"

def login(username, password):
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": username, "password": password}
    )
    assert r.status_code == 200, f"登录失败 ({username}): {r.text}"
    return r.json()["access_token"]

def test_1_health():
    print("[测试1] 健康检查...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    print("  ✓ 通过\n")

def test_2_night_shift_rule():
    print("[测试2] 未培训志愿者不能排晚班...")
    admin_token = login("admin", "admin123")
    vol3_token = login("volunteer3", "vol123")

    rooms = requests.get(
        f"{BASE_URL}/api/study-rooms",
        headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    room_id = rooms[0]["id"]

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    shift_data = {
        "study_room_id": room_id,
        "shift_date": tomorrow,
        "start_time": "18:00:00",
        "end_time": "21:00:00",
        "shift_type": "night",
        "max_volunteers": 3
    }
    r = requests.post(
        f"{BASE_URL}/api/shifts",
        json=shift_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 200, f"创建班次失败: {r.text}"
    shift = r.json()
    shift_id = shift["id"]
    print(f"  创建晚班成功 (ID: {shift_id})")

    r = requests.post(
        f"{BASE_URL}/api/shifts/{shift_id}/publish",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 200, f"发布班次失败: {r.text}"
    print("  发布班次成功")

    signup_data = {"shift_id": shift_id}
    r = requests.post(
        f"{BASE_URL}/api/signups",
        json=signup_data,
        headers={"Authorization": f"Bearer {vol3_token}"}
    )
    print(f"  未培训志愿者报名状态码: {r.status_code}")
    print(f"  响应: {r.json()}")

    assert r.status_code == 400, f"应该返回400但返回了{r.status_code}"
    detail = r.json()["detail"]
    assert "培训" in detail or "晚班" in detail, f"错误信息不对: {detail}"
    print("  ✓ 通过 - 未培训志愿者不能排晚班\n")
    return shift_id

def test_3_cross_room_conflict():
    print("[测试3] 同日跨点位排班冲突检测...")
    admin_token = login("admin", "admin123")
    vol1_token = login("volunteer1", "vol123")

    rooms = requests.get(
        f"{BASE_URL}/api/study-rooms",
        headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    assert len(rooms) >= 2, "需要至少2个书房点位"
    room1_id = rooms[0]["id"]
    room2_id = rooms[1]["id"]
    print(f"  点位1: {rooms[0]['name']}, 点位2: {rooms[1]['name']}")

    tomorrow = (date.today() + timedelta(days=2)).isoformat()

    shift1_data = {
        "study_room_id": room1_id,
        "shift_date": tomorrow,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "shift_type": "morning",
        "max_volunteers": 3
    }
    r = requests.post(
        f"{BASE_URL}/api/shifts",
        json=shift1_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    shift1 = r.json()
    r = requests.post(
        f"{BASE_URL}/api/shifts/{shift1['id']}/publish",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print(f"  点位1班次创建并发布 (ID: {shift1['id']})")

    shift2_data = {
        "study_room_id": room2_id,
        "shift_date": tomorrow,
        "start_time": "14:00:00",
        "end_time": "17:00:00",
        "shift_type": "afternoon",
        "max_volunteers": 3
    }
    r = requests.post(
        f"{BASE_URL}/api/shifts",
        json=shift2_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    shift2 = r.json()
    r = requests.post(
        f"{BASE_URL}/api/shifts/{shift2['id']}/publish",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print(f"  点位2班次创建并发布 (ID: {shift2['id']})")

    r = requests.post(
        f"{BASE_URL}/api/signups",
        json={"shift_id": shift1["id"]},
        headers={"Authorization": f"Bearer {vol1_token}"}
    )
    assert r.status_code == 200, f"报名班次1失败: {r.text}"
    signup1 = r.json()

    r = requests.put(
        f"{BASE_URL}/api/signups/{signup1['id']}/approve",
        json={"review_notes": "审核通过"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 200, f"审核班次1失败: {r.text}"
    print("  志愿者报名并审核通过班次1")

    r = requests.post(
        f"{BASE_URL}/api/signups",
        json={"shift_id": shift2["id"]},
        headers={"Authorization": f"Bearer {vol1_token}"}
    )
    print(f"  同日跨点位报名状态码: {r.status_code}")
    print(f"  响应: {r.json()}")

    assert r.status_code == 400, f"应该返回400但返回了{r.status_code}"
    detail = r.json()["detail"]
    assert "冲突" in detail or "同一" in detail, f"错误信息不对: {detail}"
    print("  ✓ 通过 - 同日跨点位排班冲突被检测\n")

def test_4_full_shift_capacity():
    print("[测试4] 满员班次重复报名不会超员...")
    admin_token = login("admin", "admin123")
    vol1_token = login("volunteer1", "vol123")
    vol2_token = login("volunteer2", "vol123")

    rooms = requests.get(
        f"{BASE_URL}/api/study-rooms",
        headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    room_id = rooms[0]["id"]

    day_after = (date.today() + timedelta(days=3)).isoformat()
    shift_data = {
        "study_room_id": room_id,
        "shift_date": day_after,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "shift_type": "morning",
        "max_volunteers": 1
    }
    r = requests.post(
        f"{BASE_URL}/api/shifts",
        json=shift_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    shift = r.json()
    shift_id = shift["id"]
    r = requests.post(
        f"{BASE_URL}/api/shifts/{shift_id}/publish",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print(f"  创建容量为1的班次 (ID: {shift_id})")

    r = requests.post(
        f"{BASE_URL}/api/signups",
        json={"shift_id": shift_id},
        headers={"Authorization": f"Bearer {vol1_token}"}
    )
    signup1 = r.json()
    r = requests.put(
        f"{BASE_URL}/api/signups/{signup1['id']}/approve",
        json={"review_notes": "审核通过"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print("  志愿者1报名并审核通过")

    r = requests.get(
        f"{BASE_URL}/api/shifts/{shift_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    current_shift = r.json()
    print(f"  当前班次人数: {current_shift['current_volunteers']}/{current_shift['max_volunteers']}")
    assert current_shift["current_volunteers"] == 1

    r = requests.post(
        f"{BASE_URL}/api/signups",
        json={"shift_id": shift_id},
        headers={"Authorization": f"Bearer {vol2_token}"}
    )
    print(f"  志愿者2报名状态码: {r.status_code}")
    if r.status_code != 200:
        print(f"  响应: {r.json()}")

    if r.status_code == 200:
        signup2 = r.json()
        r = requests.put(
            f"{BASE_URL}/api/signups/{signup2['id']}/approve",
            json={"review_notes": "审核通过"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"  审核状态码: {r.status_code}")
        if r.status_code != 200:
            print(f"  审核响应: {r.json()}")

    r = requests.get(
        f"{BASE_URL}/api/shifts/{shift_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    final_shift = r.json()
    final_count = final_shift["current_volunteers"]
    print(f"  最终班次人数: {final_count}/{final_shift['max_volunteers']}")

    assert final_count <= 1, f"班次人数超过限制: {final_count}"
    print("  ✓ 通过 - 满员班次不会超员\n")

if __name__ == "__main__":
    passed = 0
    failed = 0
    tests = [test_1_health, test_2_night_shift_rule, test_3_cross_room_conflict, test_4_full_shift_capacity]

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ 失败: {e}\n")
            failed += 1

    print("=" * 50)
    print(f"  测试结果: {passed} 通过, {failed} 失败")
    print("=" * 50)
