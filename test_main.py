from fastapi.testclient import TestClient


from main import app

client = TestClient(app)





def test_register_user_with_existing_username():
    # Создаем первого пользователя
    client.post("/register/", json={
        "username": "existing_user",
        "email": "existing_user@example.com",
        "full_name": "Existing User",
        "password": "password123"
    })

    # Пробуем зарегистрировать второго с таким же username
    response = client.post("/register/", json={
        "username": "existing_user",
        "email": "new_email@example.com",
        "full_name": "Another User",
        "password": "password123"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered!"


def test_register_user_with_existing_email():
    # Создаем первого пользователя
    client.post("/register/", json={
        "username": "new_username",
        "email": "existing_email@example.com",
        "full_name": "New User",
        "password": "password123"
    })

    # Пробуем зарегистрировать второго с таким же email
    response = client.post("/register/", json={
        "username": "another_username",
        "email": "existing_email@example.com",
        "full_name": "Another User",
        "password": "password123"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered!"




def test_login_for_access_token():
    # Сначала зарегистрируем пользователя для теста
    client.post("/register/", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "password123"
    })

    # Попытка получить токен
    response = client.post("/token", data={
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None

def test_login_with_invalid_credentials():
    response = client.post("/token", data={
        "username": "wronguser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_login_with_expired_token():
    # Зарегистрируем и аутентифицируем пользователя для получения токена
    response = client.post("/token", data={
        "username": "testuser",
        "password": "password123"
    })
    token = response.json()["access_token"]

    # Создаем запрос с неправильным (неистекшим) токеном
    expired_token = token[:-1]  # Подделаем токен
    response = client.get("/users/", headers={
        "Authorization": f"Bearer {expired_token}"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_users():
    # Получаем список пользователей с токеном
    response = client.post("/token", data={
        "username": "user1",
        "password": "password123"
    })
    token = response.json()["access_token"]

    response = client.get("/users/", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    users = response.json()
    assert len(users) > 0
    assert users[0]["username"] == "Username123"


def test_get_current_user():
    # Зарегистрируем пользователя и получим токен
    client.post("/register/", json={
        "username": "currentuser",
        "email": "currentuser@example.com",
        "full_name": "Current User",
        "password": "password123"
    })

    response = client.post("/token", data={
        "username": "currentuser",
        "password": "password123"
    })
    token = response.json()["access_token"]

    # Получаем информацию о текущем пользователе
    response = client.get("/users/me", headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == 200
    assert response.json()["username"] == "currentuser"
    assert response.json()["email"] == "currentuser@example.com"





def test_delete_user():
    # Зарегистрируем пользователя
    response = client.post("/register/", json={
        "username": "deleteuser",
        "email": "deleteuser@example.com",
        "full_name": "DeleteUser",
        "password": "password123"
    })

    # Получаем токен
    response = client.post("/token", data={
        "username": "deleteuser",
        "password": "password123"
    })
    token = response.json()["access_token"]

    # Получаем данные пользователя для получения его ID
    response = client.get("/users/", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    users = response.json()

    # Предположим, что пользователя "deleteuser" есть в списке пользователей
    user_id = None
    for user in users:
        if user["username"] == "deleteuser":
            user_id = user["id"]
            break

    # Убедимся, что нашли нужного пользователя
    assert user_id is not None, "User 'deleteuser' not found"

    # Удаляем пользователя
    response = client.delete(f"/users/{user_id}", headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == 200
    assert response.json()["username"] == "deleteuser"

    # Проверяем, что пользователь удален
    response = client.get("/users/", headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == 401 # Убедимся, что пользователь больше не существует


def test_cors():
    # Попытка отправить запрос с неподдерживаемого домена
    response = client.get("/users/", headers={
        "Origin": "http://untrusted.com"
    })

    assert response.status_code == 401  # Проблемы с CORS