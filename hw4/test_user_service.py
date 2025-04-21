import pytest
from lecture_4.demo_service.core.users import (
    UserService,
    UserInfo,
    UserRole,
    password_is_longer_than_8,
)
from pydantic import SecretStr
from datetime import datetime


@pytest.fixture
def user_service():

    return UserService(
        password_validators=[
            password_is_longer_than_8,
            lambda pwd: any(char.isdigit() for char in pwd),
        ]
    )


def test_register_user(user_service):

    user_info = UserInfo(
        username="testuser",
        name="Test User",
        birthdate=datetime(1990, 1, 1),
        role=UserRole.USER,
        password=SecretStr("ValidPassword123"),
    )
    user = user_service.register(user_info)
    assert user.uid == 1
    assert user.info.username == "testuser"


@pytest.mark.parametrize(
    "password,expected_exception",
    [
        ("short", ValueError),  
        ("no_digit_password", ValueError),  
    ],
)
def test_register_user_with_invalid_password(
    user_service, password, expected_exception
):

    user_info = UserInfo(
        username="shortpassuser",
        name="Short Password User",
        birthdate=datetime(1990, 1, 1),
        role=UserRole.USER,
        password=SecretStr(password),
    )
    with pytest.raises(expected_exception):
        user_service.register(user_info)


def test_get_user_by_username(user_service):

    user_info = UserInfo(
        username="testuser",
        name="Test User",
        birthdate=datetime(1990, 1, 1),
        role=UserRole.USER,
        password=SecretStr("ValidPassword123"),
    )
    user_service.register(user_info)


    user = user_service.get_by_username("testuser")
    assert user is not None
    assert user.info.username == "testuser"


    user_not_found = user_service.get_by_username("nagibator2008")
    assert user_not_found is None


def test_get_user_by_id(user_service):

    # Создаем пользователя
    user_info = UserInfo(
        username="testuser",
        name="Test User",
        birthdate=datetime(1990, 1, 1),
        role=UserRole.USER,
        password=SecretStr("ValidPassword123"),
    )
    user = user_service.register(user_info)


    found_user = user_service.get_by_id(user.uid)
    assert found_user is not None
    assert found_user.uid == user.uid


    user_not_found = user_service.get_by_id(999)
    assert user_not_found is None


def test_grant_admin(user_service):

    user_info = UserInfo(
        username="regularuser",
        name="Regular User",
        birthdate=datetime(1990, 1, 1),
        role=UserRole.USER,
        password=SecretStr("ValidPassword123"),
    )
    user = user_service.register(user_info)

    user_service.grant_admin(user.uid)

    assert user_service.get_by_id(user.uid).info.role == UserRole.ADMIN

    with pytest.raises(ValueError, match="user not found"):
        user_service.grant_admin(999)


def test_register_existing_user(user_service):

    user_info = UserInfo(
        username="testuser",
        name="Test User",
        birthdate=datetime(1990, 1, 1),
        role=UserRole.USER,
        password=SecretStr("ValidPassword123"),
    )
    user_service.register(user_info)


    with pytest.raises(ValueError, match="username is already taken"):
        user_service.register(user_info)


@pytest.mark.parametrize(
    "password,expected_exception",
    [
        ("ValidPassword123", None),  
        ("NoDigitsHere", ValueError),  
    ],
)
def test_password_requires_digit(user_service, password, expected_exception):

    user_info = UserInfo(
        username="testuser",
        name="Test User",
        birthdate=datetime(1990, 1, 1),
        role=UserRole.USER,
        password=SecretStr(password),
    )

    if expected_exception:
        with pytest.raises(expected_exception):
            user_service.register(user_info)
    else:
        user_service.register(user_info) 
