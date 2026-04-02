# DEKIDS - Sistema de Gestão (Refatorado)

Sistema de gestão de estoque e vendas com arquitetura de 3 camadas, segurança aprimorada e testes abrangentes.

## 🏗️ Arquitetura

```
┌─────────────────────────────────────┐
│         UI Layer (Flet)             │
│  Apresentação e Interação           │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│       Service Layer                 │
│  Lógica de Negócio                  │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│     Database Layer (Repository)     │
│  Acesso a Dados                     │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│    PostgreSQL (Supabase)            │
└─────────────────────────────────────┘
```

## 📁 Estrutura do Projeto

```
dekids/
├── src/
│   ├── domain/          # Modelos de domínio (Pydantic)
│   ├── repositories/    # Camada de dados (Repository Pattern)
│   ├── services/        # Lógica de negócio
│   ├── ui/              # Interface do usuário (Flet)
│   ├── infrastructure/  # Serviços transversais
│   └── utils/           # Utilitários
├── tests/
│   ├── unit/            # Testes unitários
│   ├── integration/     # Testes de integração
│   └── property/        # Testes baseados em propriedades
├── migrations/          # Migrações do banco de dados (Alembic)
└── logs/                # Arquivos de log
```

## 🚀 Instalação

### Requisitos
- Python 3.10+
- PostgreSQL (via Supabase)
- Redis (opcional, para cache)

### Configuração

1. Clone o repositório
```bash
git clone <repository-url>
cd dekids
```

2. Crie um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite .env com suas configurações
```

5. Execute as migrações do banco de dados
```bash
alembic upgrade head
```

6. Inicie a aplicação
```bash
python app.py
```

## 🧪 Testes

### Executar todos os testes
```bash
pytest
```

### Executar testes com cobertura
```bash
pytest --cov=src --cov-report=html
```

### Executar apenas testes unitários
```bash
pytest tests/unit/
```

### Executar testes de propriedades
```bash
pytest tests/property/
```

## 🔒 Segurança

- **Autenticação**: Senha com 12+ caracteres, complexidade obrigatória
- **Rate Limiting**: 5 tentativas de login em 15 minutos
- **Criptografia**: AES-256 para tokens de sessão
- **Auditoria**: Trilha completa de todas as operações
- **Validação**: Sanitização de todas as entradas

## 📊 Qualidade de Código

### Verificar tipos com mypy
```bash
mypy src/
```

### Verificar qualidade com pylint
```bash
pylint src/
```

### Formatar código com black
```bash
black src/ tests/
```

## 🔧 Desenvolvimento

### Criar nova migração
```bash
alembic revision -m "description"
```

### Reverter migração
```bash
alembic downgrade -1
```

### Gerar chave de criptografia
```python
from src.infrastructure.encryption import EncryptionService
print(EncryptionService.generate_master_key())
```

## 📈 Monitoramento

### Health Check
```
GET /health
```

### Métricas
- Tempo de resposta de queries
- Taxa de acerto do cache
- Contagem de erros
- Usuários ativos

## 🚢 Deploy no Render

1. Crie Web Service no Render
2. Conecte o repositório GitHub
3. Configure variáveis de ambiente (ver .env.example)
4. Deploy automático!

## 📝 Licença

Propriedade de DEKIDS Moda Infantil

## 👥 Contribuindo

1. Crie uma branch para sua feature
2. Escreva testes para suas mudanças
3. Garanta que todos os testes passam
4. Garanta que mypy e pylint não reportam erros
5. Submeta um Pull Request

## 📞 Suporte

Para suporte, entre em contato com a equipe de desenvolvimento.
