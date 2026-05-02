from app.db import Base, engine
import app.models  # noqa

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")
