import sys
import os
from datetime import date, time, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import (
    User, StudyRoom, VolunteerProfile, Shift, Signup,
    RoleEnum, TrainingStatusEnum, ShiftTypeEnum, ShiftStatusEnum,
    SignupStatusEnum
)
from app.auth import get_password_hash


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(User).count() > 0:
            print("数据库已有数据，跳过初始化")
            return

        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            name="系统管理员",
            role=RoleEnum.ADMIN,
            phone="13800000000",
            email="admin@example.com"
        )
        db.add(admin)

        operations = User(
            username="operations",
            password_hash=get_password_hash("ops123"),
            name="运营人员",
            role=RoleEnum.OPERATIONS,
            phone="13800000001",
            email="ops@example.com"
        )
        db.add(operations)

        training = User(
            username="training",
            password_hash=get_password_hash("train123"),
            name="培训负责人",
            role=RoleEnum.TRAINING,
            phone="13800000002",
            email="training@example.com"
        )
        db.add(training)

        volunteer1 = User(
            username="volunteer1",
            password_hash=get_password_hash("vol123"),
            name="张志愿",
            role=RoleEnum.VOLUNTEER,
            phone="13900000001",
            email="zhang@example.com"
        )
        db.add(volunteer1)

        volunteer2 = User(
            username="volunteer2",
            password_hash=get_password_hash("vol123"),
            name="李服务",
            role=RoleEnum.VOLUNTEER,
            phone="13900000002",
            email="li@example.com"
        )
        db.add(volunteer2)

        volunteer3 = User(
            username="volunteer3",
            password_hash=get_password_hash("vol123"),
            name="王奉献",
            role=RoleEnum.VOLUNTEER,
            phone="13900000003",
            email="wang@example.com"
        )
        db.add(volunteer3)

        volunteer4 = User(
            username="volunteer4",
            password_hash=get_password_hash("vol123"),
            name="赵爱心",
            role=RoleEnum.VOLUNTEER,
            phone="13900000004",
            email="zhao@example.com"
        )
        db.add(volunteer4)

        db.flush()

        profile1 = VolunteerProfile(
            user_id=volunteer1.id,
            real_name="张志愿",
            id_card="110101199001011234",
            phone="13900000001",
            training_status=TrainingStatusEnum.COMPLETED,
            training_date=date.today() - timedelta(days=30),
            training_teacher="培训负责人",
            skills="图书整理,读者服务"
        )
        db.add(profile1)

        profile2 = VolunteerProfile(
            user_id=volunteer2.id,
            real_name="李服务",
            id_card="110101199002021234",
            phone="13900000002",
            training_status=TrainingStatusEnum.COMPLETED,
            training_date=date.today() - timedelta(days=20),
            training_teacher="培训负责人",
            skills="活动组织,咨询服务"
        )
        db.add(profile2)

        profile3 = VolunteerProfile(
            user_id=volunteer3.id,
            real_name="王奉献",
            id_card="110101199003031234",
            phone="13900000003",
            training_status=TrainingStatusEnum.NONE,
            skills="技术支持"
        )
        db.add(profile3)

        profile4 = VolunteerProfile(
            user_id=volunteer4.id,
            real_name="赵爱心",
            id_card="110101199004041234",
            phone="13900000004",
            training_status=TrainingStatusEnum.PENDING,
            skills="儿童阅读指导"
        )
        db.add(profile4)

        room1 = StudyRoom(
            name="中心书房",
            address="市中心广场东侧",
            description="城市中心书房，藏书丰富",
            capacity=50,
            status="active"
        )
        db.add(room1)

        room2 = StudyRoom(
            name="社区书房",
            address="阳光社区服务中心",
            description="社区级书房，服务周边居民",
            capacity=30,
            status="active"
        )
        db.add(room2)

        room3 = StudyRoom(
            name="科技书房",
            address="科技园A座一层",
            description="科技主题书房",
            capacity=40,
            status="active"
        )
        db.add(room3)

        db.flush()

        today = date.today()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)

        shifts_data = [
            (room1.id, today, time(9, 0), time(12, 0), ShiftTypeEnum.MORNING, 3, ShiftStatusEnum.PUBLISHED),
            (room1.id, today, time(14, 0), time(17, 0), ShiftTypeEnum.AFTERNOON, 3, ShiftStatusEnum.PUBLISHED),
            (room1.id, today, time(18, 0), time(21, 0), ShiftTypeEnum.NIGHT, 2, ShiftStatusEnum.PUBLISHED),
            (room2.id, today, time(9, 0), time(12, 0), ShiftTypeEnum.MORNING, 2, ShiftStatusEnum.PUBLISHED),
            (room2.id, tomorrow, time(14, 0), time(17, 0), ShiftTypeEnum.AFTERNOON, 2, ShiftStatusEnum.PUBLISHED),
            (room3.id, tomorrow, time(9, 0), time(12, 0), ShiftTypeEnum.MORNING, 3, ShiftStatusEnum.PUBLISHED),
            (room3.id, next_week, time(18, 0), time(21, 0), ShiftTypeEnum.NIGHT, 2, ShiftStatusEnum.DRAFT),
        ]

        shifts = []
        for room_id, shift_date, start_time, end_time, shift_type, max_vol, status in shifts_data:
            shift = Shift(
                study_room_id=room_id,
                shift_date=shift_date,
                start_time=start_time,
                end_time=end_time,
                shift_type=shift_type,
                max_volunteers=max_vol,
                current_volunteers=0,
                status=status,
                created_by=admin.id,
                notes=f"{shift_type.value} 班次"
            )
            db.add(shift)
            shifts.append(shift)

        db.flush()

        signup1 = Signup(
            shift_id=shifts[0].id,
            volunteer_id=volunteer1.id,
            status=SignupStatusEnum.APPROVED,
            signup_time=__import__('datetime').datetime.utcnow() - timedelta(hours=2),
            review_time=__import__('datetime').datetime.utcnow() - timedelta(hours=1),
            reviewed_by=admin.id
        )
        db.add(signup1)

        signup2 = Signup(
            shift_id=shifts[0].id,
            volunteer_id=volunteer2.id,
            status=SignupStatusEnum.APPROVED,
            signup_time=__import__('datetime').datetime.utcnow() - timedelta(hours=3),
            review_time=__import__('datetime').datetime.utcnow() - timedelta(hours=2),
            reviewed_by=admin.id
        )
        db.add(signup2)

        signup3 = Signup(
            shift_id=shifts[2].id,
            volunteer_id=volunteer1.id,
            status=SignupStatusEnum.PENDING,
            signup_time=__import__('datetime').datetime.utcnow() - timedelta(minutes=30)
        )
        db.add(signup3)

        shifts[0].current_volunteers = 2

        db.commit()
        print("数据库初始化完成！")
        print("")
        print("默认账号：")
        print("  管理员: admin / admin123")
        print("  运营人员: operations / ops123")
        print("  培训负责人: training / train123")
        print("  志愿者1(已培训): volunteer1 / vol123")
        print("  志愿者2(已培训): volunteer2 / vol123")
        print("  志愿者3(未培训): volunteer3 / vol123")
        print("  志愿者4(培训中): volunteer4 / vol123")
        print("")
        print("书房点位: 中心书房、社区书房、科技书房")
        print("班次: 已创建 7 个班次（草稿+发布状态")

    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
