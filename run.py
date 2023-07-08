from app import create_app, db
from app.models import Users
from app.functions import load_users

app = create_app()
with app.app_context():
    db.create_all()

    check = Users.query.all()
    if not check:
        print("No users found, loading users...")
        load_users()
    else:
        print("Users already populated")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
