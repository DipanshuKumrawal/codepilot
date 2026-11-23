import jwt


SECRET_KEY = "secret"


def generate_token(user_id):

    payload = {
        "user_id": user_id
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm="HS256"
    )


def validate_token(token):

    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

    except jwt.InvalidTokenError:
        return None