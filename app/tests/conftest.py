import pytest
from auth.jwt_auth import generate_access_token
from core.database import Base, get_db
from faker import Faker
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker
from tasks.models import TaskModel
from users.models import UserModel

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="package")
def db_session():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def override_dependencies(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="session", autouse=True)
def tear_up_down_database():

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="package")
def anon_client():
    client = TestClient(app)
    yield client


@pytest.fixture(scope="package")
def auth_client(db_session):
    client = TestClient(app)
    user = db_session.query(UserModel).filter(UserModel.username == "testuser").first()
    access_token = generate_access_token(user.id)
    client._headers.update({"Authorization": f"Bearer {access_token}"})
    yield client


@pytest.fixture(scope="function")
def random_task(db_session):
    user = db_session.query(UserModel).filter(UserModel.username == "testuser").first()
    task = db_session.query(TaskModel).filter(TaskModel.user_id == user.id).first()
    return task


fake = Faker()


@pytest.fixture(scope="package", autouse=True)
def generate_mock_data(db_session):
    user = UserModel(username="testuser")
    user.set_password("Test123456")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    print(f"User created with username: {user.username} dn ID {user.id}")

    tasks_list = []
    for _ in range(10):
        tasks_list.append(
            TaskModel(
                user_id=user.id,
                title=fake.sentence(nb_words=6),
                description=fake.text(),
                is_completed=fake.boolean(),
            )
        )
    db_session.add_all(tasks_list)
    db_session.commit()
    print(f"Added {10} tasks for user id:{user.id}")
