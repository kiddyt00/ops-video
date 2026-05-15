"""Reset admin user password."""
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.db.user_crud import user_crud

db = SessionLocal()
user = user_crud.get_by_email(db, 'admin@test.com')
if user:
    user.hashed_password = get_password_hash('test123456')
    db.commit()
    print('Password reset to test123456')
else:
    print('Admin user not found')
db.close()
