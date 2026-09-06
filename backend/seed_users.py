from app.core.security import password_hash
from app.database import SessionLocal
from app.models.user import User, UserRole


DEMO_USERS = [
    {
        "email": "admin@example.com",
        "password": "Admin@12345",
        "role": UserRole.ADMIN,
    },
    {
        "email": "editor@example.com",
        "password": "Editor@12345",
        "role": UserRole.EDITOR,
    },
    {
        "email": "viewer@example.com",
        "password": "Viewer@12345",
        "role": UserRole.VIEWER,
    },
]


def seed_users() -> None:
    db = SessionLocal()

    try:
        for user_data in DEMO_USERS:
            existing_user = (
                db.query(User)
                .filter(User.email == user_data["email"])
                .first()
            )

            if existing_user:
                print(f"Already exists: {user_data['email']}")
                continue

            user = User(
                email=user_data["email"],
                password_hash=password_hash.hash(user_data["password"]),
                role=user_data["role"],
                is_active=True,
            )

            db.add(user)
            print(f"Created: {user_data['email']}")

        db.commit()
        print("Demo users seeded successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_users()