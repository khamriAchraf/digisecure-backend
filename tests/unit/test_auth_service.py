from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.services import auth_service


@pytest.mark.unit
class TestTokenCreation:
    """Unit tests for JWT token creation functions."""

    @patch("app.services.auth_service.datetime")
    @patch("app.services.auth_service.jwt")
    def test_create_access_token_success(self, mock_jwt, mock_datetime):
        """Test successful access token creation."""
        # Mock datetime.utcnow() to return a fixed time
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        mock_jwt.encode.return_value = "mock_access_token"

        data = {"sub": "123", "email": "test@example.com"}
        result = auth_service.create_access_token(data)

        expected_expire = mock_now + timedelta(
            minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        expected_payload = {
            "sub": "123",
            "email": "test@example.com",
            "exp": expected_expire,
            "iat": mock_now,
            "type": "access",
        }
        mock_jwt.encode.assert_called_once_with(
            expected_payload, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM
        )
        assert result == "mock_access_token"

    @patch("app.services.auth_service.datetime")
    @patch("app.services.auth_service.jwt")
    def test_create_access_token_with_custom_expiry(self, mock_jwt, mock_datetime):
        """Test access token creation with custom expiration."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        mock_jwt.encode.return_value = "mock_access_token"

        data = {"sub": "123"}
        custom_expiry = timedelta(hours=2)
        result = auth_service.create_access_token(data, expires_delta=custom_expiry)

        expected_expire = mock_now + custom_expiry
        expected_payload = {
            "sub": "123",
            "exp": expected_expire,
            "iat": mock_now,
            "type": "access",
        }
        mock_jwt.encode.assert_called_once_with(
            expected_payload, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM
        )
        assert result == "mock_access_token"

    @patch("app.services.auth_service.datetime")
    @patch("app.services.auth_service.jwt")
    def test_create_refresh_token_success(self, mock_jwt, mock_datetime):
        """Test successful refresh token creation."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        mock_jwt.encode.return_value = "mock_refresh_token"

        data = {"sub": "123", "email": "test@example.com"}

        mock_db = Mock(spec=Session)
        with patch("app.services.auth_service.refresh_token_crud.create_refresh_token"):
            with patch(
                "app.services.auth_service.secrets.token_urlsafe",
                return_value="fixed_jti",
            ):
                result = auth_service.create_refresh_token(data, db=mock_db)

        expected_expire = mock_now + timedelta(
            days=auth_service.REFRESH_TOKEN_EXPIRE_DAYS
        )
        expected_payload = {
            "sub": "123",
            "email": "test@example.com",
            "exp": expected_expire,
            "iat": mock_now,
            "jti": "fixed_jti",
            "type": "refresh",
        }
        mock_jwt.encode.assert_called_once_with(
            expected_payload, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM
        )
        assert result == "mock_refresh_token"

    @patch("app.services.auth_service.datetime")
    @patch("app.services.auth_service.jwt")
    def test_create_refresh_token_with_custom_expiry(self, mock_jwt, mock_datetime):
        """Test refresh token creation with custom expiration."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        mock_jwt.encode.return_value = "mock_refresh_token"

        data = {"sub": "123"}
        custom_expiry = timedelta(days=30)
        mock_db = Mock(spec=Session)
        with patch("app.services.auth_service.refresh_token_crud.create_refresh_token"):
            with patch(
                "app.services.auth_service.secrets.token_urlsafe",
                return_value="fixed_jti",
            ):
                result = auth_service.create_refresh_token(
                    data, db=mock_db, expires_delta=custom_expiry
                )

        expected_expire = mock_now + custom_expiry
        expected_payload = {
            "sub": "123",
            "exp": expected_expire,
            "iat": mock_now,
            "jti": "fixed_jti",
            "type": "refresh",
        }
        mock_jwt.encode.assert_called_once_with(
            expected_payload, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM
        )
        assert result == "mock_refresh_token"


@pytest.mark.unit
class TestTokenDecoding:
    """Unit tests for JWT token decoding functions."""

    @patch("app.services.auth_service.jwt")
    def test_decode_access_token_success(self, mock_jwt):
        """Test successful access token decoding."""
        mock_payload = {"sub": "123", "email": "test@example.com", "type": "access"}
        mock_jwt.decode.return_value = mock_payload

        result = auth_service.decode_access_token("valid_token")

        mock_jwt.decode.assert_called_once_with(
            "valid_token", auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM]
        )
        assert result == "123"

    @patch("app.services.auth_service.jwt")
    def test_decode_access_token_missing_sub(self, mock_jwt):
        """Test access token decoding with missing sub field."""
        mock_payload = {"email": "test@example.com"}  # Missing 'sub'
        mock_jwt.decode.return_value = mock_payload

        result = auth_service.decode_access_token("invalid_token")

        assert result is None

    @patch("app.services.auth_service.jwt")
    def test_decode_access_token_none_sub(self, mock_jwt):
        """Test access token decoding with None sub field."""
        mock_payload = {"sub": None, "email": "test@example.com"}
        mock_jwt.decode.return_value = mock_payload

        result = auth_service.decode_access_token("invalid_token")

        assert result is None

    @patch("app.services.auth_service.jwt")
    def test_decode_access_token_jwt_error(self, mock_jwt):
        """Test access token decoding with JWT error."""
        mock_jwt.decode.side_effect = JWTError("Invalid token")

        result = auth_service.decode_access_token("invalid_token")

        assert result is None

    @patch("app.services.auth_service.jwt")
    def test_decode_refresh_token_success(self, mock_jwt):
        """Test successful refresh token decoding."""
        mock_payload = {"sub": "123", "type": "refresh", "jti": "test_jti"}
        mock_jwt.decode.return_value = mock_payload

        mock_db = Mock(spec=Session)
        with patch(
            "app.services.auth_service.refresh_token_crud.get_valid_refresh_token",
            return_value=True,
        ):
            result = auth_service.decode_refresh_token("valid_refresh_token", mock_db)

        mock_jwt.decode.assert_called_once_with(
            "valid_refresh_token",
            auth_service.SECRET_KEY,
            algorithms=[auth_service.ALGORITHM],
        )
        assert result == ("123", "test_jti")

    @patch("app.services.auth_service.jwt")
    def test_decode_refresh_token_wrong_type(self, mock_jwt):
        """Test refresh token decoding with wrong token type."""
        mock_payload = {"sub": "123", "type": "access"}  # Wrong type
        mock_jwt.decode.return_value = mock_payload

        mock_db = Mock(spec=Session)
        result = auth_service.decode_refresh_token("wrong_type_token", mock_db)

        assert result is None

    @patch("app.services.auth_service.jwt")
    def test_decode_refresh_token_missing_type(self, mock_jwt):
        """Test refresh token decoding with missing type field."""
        mock_payload = {"sub": "123"}  # Missing 'type'
        mock_jwt.decode.return_value = mock_payload

        mock_db = Mock(spec=Session)
        result = auth_service.decode_refresh_token("missing_type_token", mock_db)

        assert result is None

    @patch("app.services.auth_service.jwt")
    def test_decode_refresh_token_missing_sub(self, mock_jwt):
        """Test refresh token decoding with missing sub field."""
        mock_payload = {"type": "refresh"}  # Missing 'sub'
        mock_jwt.decode.return_value = mock_payload

        mock_db = Mock(spec=Session)
        result = auth_service.decode_refresh_token("missing_sub_token", mock_db)

        assert result is None

    @patch("app.services.auth_service.jwt")
    def test_decode_refresh_token_jwt_error(self, mock_jwt):
        """Test refresh token decoding with JWT error."""
        mock_jwt.decode.side_effect = JWTError("Invalid refresh token")

        mock_db = Mock(spec=Session)
        result = auth_service.decode_refresh_token("invalid_refresh_token", mock_db)

        assert result is None


@pytest.mark.unit
class TestUserAuthentication:
    """Unit tests for user authentication functions."""

    @patch("app.services.auth_service.verify_password")
    def test_authenticate_user_success(self, mock_verify_password):
        """Test successful user authentication."""
        # Create mock user
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        mock_user.hashed_password = "hashed_password"

        # Create mock database session
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock password verification
        mock_verify_password.return_value = True

        result = auth_service.authenticate_user(
            mock_db, "test@example.com", "password123"
        )

        # Verify database query was called correctly
        mock_db.query.assert_called_once_with(User)
        mock_db.query.return_value.filter.assert_called_once()
        mock_verify_password.assert_called_once_with("password123", "hashed_password")
        assert result == mock_user

    @patch("app.services.auth_service.verify_password")
    def test_authenticate_user_not_found(self, mock_verify_password):
        """Test authentication with non-existent user."""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = auth_service.authenticate_user(
            mock_db,
            "nonexistent@example.com",
            "password123",
        )

        mock_verify_password.assert_not_called()
        assert result is None

    @patch("app.services.auth_service.verify_password")
    def test_authenticate_user_wrong_password(self, mock_verify_password):
        """Test authentication with wrong password."""
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        mock_user.hashed_password = "hashed_password"

        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        mock_verify_password.return_value = False

        result = auth_service.authenticate_user(
            mock_db, "test@example.com", "wrongpassword"
        )

        mock_verify_password.assert_called_once_with("wrongpassword", "hashed_password")
        assert result is None

    def test_get_user_by_id_success(self):
        """Test successful user retrieval by ID."""
        mock_user = Mock(spec=User)
        mock_user.id = 123
        mock_user.email = "test@example.com"

        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.get_user_by_id(mock_db, 123)

        mock_db.query.assert_called_once_with(User)
        mock_db.query.return_value.filter.assert_called_once()
        assert result == mock_user

    def test_get_user_by_id_not_found(self):
        """Test user retrieval by ID when user doesn't exist."""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = auth_service.get_user_by_id(mock_db, 999)

        assert result is None


@pytest.mark.unit
class TestGetCurrentUser:
    """Unit tests for get_current_user dependency function."""

    @patch("app.api.dependencies.decode_access_token")
    @patch("app.api.dependencies.get_user_by_id")
    def test_get_current_user_success(self, mock_get_user_by_id, mock_decode_token):
        """Test successful current user retrieval."""
        # Mock token decoding
        mock_decode_token.return_value = "123"

        # Mock user retrieval
        mock_user = Mock(spec=User)
        mock_user.id = 123
        mock_user.email = "test@example.com"
        mock_get_user_by_id.return_value = mock_user

        # Mock dependencies
        mock_token = "valid_token"
        mock_db = Mock(spec=Session)

        result = get_current_user(mock_token, mock_db)

        mock_decode_token.assert_called_once_with(mock_token)
        mock_get_user_by_id.assert_called_once_with(mock_db, 123)
        assert result == mock_user

    @patch("app.api.dependencies.decode_access_token")
    def test_get_current_user_invalid_token(self, mock_decode_token):
        """Test current user retrieval with invalid token."""
        mock_decode_token.return_value = None

        mock_token = "invalid_token"
        mock_db = Mock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_token, mock_db)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"
        mock_decode_token.assert_called_once_with(mock_token)

    @patch("app.api.dependencies.decode_access_token")
    @patch("app.api.dependencies.get_user_by_id")
    def test_get_current_user_user_not_found(
        self, mock_get_user_by_id, mock_decode_token
    ):
        """Test current user retrieval when user doesn't exist."""
        mock_decode_token.return_value = "123"
        mock_get_user_by_id.return_value = None

        mock_token = "valid_token"
        mock_db = Mock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_token, mock_db)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"
        mock_decode_token.assert_called_once_with(mock_token)
        mock_get_user_by_id.assert_called_once_with(mock_db, 123)


@pytest.mark.unit
class TestTokenExpiration:
    """Unit tests for token expiration scenarios."""

    @patch("app.services.auth_service.datetime")
    @patch("app.services.auth_service.jwt")
    def test_access_token_expiration_time(self, mock_jwt, mock_datetime):
        """Test that access tokens use correct expiration time."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        mock_jwt.encode.return_value = "mock_token"

        data = {"sub": "123"}
        auth_service.create_access_token(data)

        # Verify expiration time is set correctly
        expected_expire = mock_now + timedelta(
            minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        call_args = mock_jwt.encode.call_args[0][0]  # First argument (payload)
        assert call_args["exp"] == expected_expire

    @patch("app.services.auth_service.datetime")
    @patch("app.services.auth_service.jwt")
    def test_refresh_token_expiration_time(self, mock_jwt, mock_datetime):
        """Test that refresh tokens use correct expiration time."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        mock_jwt.encode.return_value = "mock_token"

        data = {"sub": "123"}
        mock_db = Mock(spec=Session)
        with patch("app.services.auth_service.refresh_token_crud.create_refresh_token"):
            with patch(
                "app.services.auth_service.secrets.token_urlsafe",
                return_value="fixed_jti",
            ):
                auth_service.create_refresh_token(data, db=mock_db)

        # Verify expiration time is set correctly
        expected_expire = mock_now + timedelta(
            days=auth_service.REFRESH_TOKEN_EXPIRE_DAYS
        )
        call_args = mock_jwt.encode.call_args[0][0]  # First argument (payload)
        assert call_args["exp"] == expected_expire


@pytest.mark.unit
class TestEdgeCases:
    """Unit tests for edge cases and error conditions."""

    @patch("app.services.auth_service.jwt")
    def test_decode_token_with_empty_payload(self, mock_jwt):
        """Test token decoding with empty payload."""
        mock_jwt.decode.return_value = {}

        result = auth_service.decode_access_token("empty_payload_token")
        assert result is None

    @patch("app.services.auth_service.jwt")
    def test_decode_refresh_token_with_empty_payload(self, mock_jwt):
        """Test refresh token decoding with empty payload."""
        mock_jwt.decode.return_value = {}

        mock_db = Mock(spec=Session)
        result = auth_service.decode_refresh_token(
            "empty_payload_refresh_token", mock_db
        )
        assert result is None

    @patch("app.services.auth_service.verify_password")
    def test_authenticate_user_with_empty_password(self, mock_verify_password):
        """Test authentication with empty password."""
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        mock_user.hashed_password = "hashed_password"

        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        mock_verify_password.return_value = False

        result = auth_service.authenticate_user(mock_db, "test@example.com", "")

        mock_verify_password.assert_called_once_with("", "hashed_password")
        assert result is None

    @patch("app.services.auth_service.verify_password")
    def test_authenticate_user_with_empty_email(self, mock_verify_password):
        """Test authentication with empty email."""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = auth_service.authenticate_user(mock_db, "", "password123")

        mock_verify_password.assert_not_called()
        assert result is None
