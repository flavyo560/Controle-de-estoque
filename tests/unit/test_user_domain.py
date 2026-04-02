"""
Testes unitários para o módulo de domínio User.

Este módulo testa todas as classes e validadores do domínio User,
incluindo validação de username, email, role e regras de segurança.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.domain.user import (
    User,
    UserCreate,
    UserUpdate,
    UserRole
)


class TestUserRole:
    """Testes para o enum UserRole."""
    
    def test_user_role_admin(self):
        """Testa role admin."""
        assert UserRole.ADMIN == "admin"
    
    def test_use