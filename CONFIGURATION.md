# Configuration Guide

Este documento descreve todas as variáveis de ambiente e configurações do sistema DEKIDS.

## Arquivos de Configuração

O sistema usa arquivos `.env` para configuração por ambiente:

- `.env.development` - Desenvolvimento local
- `.env.staging` - Ambiente de homologação
- `.env.production` - Ambiente de produção
- `.env` - Arquivo local (não versionado, copie de um dos templates acima)

## Variáveis de Ambiente

### Application

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `APP_NAME` | Nome da aplicação | DEKIDS | Não |
| `APP_VERSION` | Versão da aplicação | 2.0.0 | Não |
| `ENVIRONMENT` | Ambiente (development/staging/production) | development | Não |
| `DEBUG` | Modo debug (true/false) | false | Não |

### Database

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `DATABASE_URL` | URL de conexão PostgreSQL | - | **Sim** |
| `DB_POOL_MIN` | Tamanho mínimo do pool | 10 | Não |
| `DB_POOL_MAX` | Tamanho máximo do pool | 20 | Não |
| `DB_TIMEOUT` | Timeout de comandos (segundos) | 60.0 | Não |

**Formato DATABASE_URL:**
```
postgresql://user:password@host:port/database
```

**Exemplo Supabase:**
```
postgresql://postgres:your-password@db.xxxxx.supabase.co:5432/postgres
```

### Security

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `SECRET_KEY` | Chave secreta (min 32 chars) | - | **Sim** |
| `ENCRYPTION_KEY` | Chave de criptografia (min 32 chars) | - | **Sim** |
| `SESSION_DURATION_HOURS` | Duração da sessão em horas | 8 | Não |
| `PASSWORD_MIN_LENGTH` | Tamanho mínimo de senha | 12 | Não |
| `MAX_LOGIN_ATTEMPTS` | Tentativas de login antes de bloquear | 5 | Não |
| `LOCKOUT_DURATION_MINUTES` | Duração do bloqueio em minutos | 30 | Não |

**Gerando chaves seguras:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Cache

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `CACHE_BACKEND` | Backend de cache (memory/redis) | memory | Não |
| `REDIS_HOST` | Host do Redis | localhost | Não |
| `REDIS_PORT` | Porta do Redis | 6379 | Não |
| `CACHE_DEFAULT_TTL` | TTL padrão em segundos | 300 | Não |

**Recomendação:** Use `memory` para desenvolvimento e `redis` para produção.

### Logging

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `LOG_LEVEL` | Nível de log (DEBUG/INFO/WARNING/ERROR) | INFO | Não |
| `LOG_FILE` | Caminho do arquivo de log | logs/dekids.log | Não |
| `LOG_ROTATION` | Rotação de logs (daily/weekly) | daily | Não |
| `LOG_RETENTION_DAYS` | Dias de retenção de logs | 90 | Não |

### Performance

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `QUERY_SLOW_THRESHOLD_MS` | Threshold para query lenta (ms) | 1000 | Não |
| `ASYNC_THRESHOLD_MS` | Threshold para operação async (ms) | 100 | Não |
| `MAX_CONCURRENT_OPS` | Máximo de operações concorrentes | 5 | Não |

### File Upload

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `MAX_UPLOAD_SIZE_MB` | Tamanho máximo de upload (MB) | 10 | Não |
| `ALLOWED_FILE_EXTENSIONS` | Extensões permitidas (separadas por vírgula) | csv,pdf,jpg,png | Não |

## Setup Inicial

### 1. Copiar arquivo de configuração

```bash
# Para desenvolvimento
cp .env.development .env

# Para produção
cp .env.production .env
```

### 2. Editar variáveis obrigatórias

Edite o arquivo `.env` e configure:

1. `DATABASE_URL` - URL do seu banco Supabase
2. `SECRET_KEY` - Gere uma chave aleatória
3. `ENCRYPTION_KEY` - Gere uma chave aleatória

### 3. Validar configuração

```bash
python -c "from src.infrastructure.config import validate_required_settings; validate_required_settings()"
```

## Configuração por Ambiente

### Development

- `DEBUG=true` - Habilita logs detalhados
- `LOG_LEVEL=DEBUG` - Mostra todos os logs
- `CACHE_BACKEND=memory` - Cache em memória
- `DB_POOL_MIN=5` - Pool menor para economia de recursos

### Staging

- `DEBUG=false` - Desabilita debug
- `LOG_LEVEL=INFO` - Logs informativos
- `CACHE_BACKEND=memory` - Cache em memória (pode usar Redis)
- Configurações similares à produção para testes

### Production

- `DEBUG=false` - **NUNCA** habilite debug em produção
- `LOG_LEVEL=INFO` ou `WARNING` - Apenas logs importantes
- `CACHE_BACKEND=redis` - Cache distribuído
- `DB_POOL_MAX=20` - Pool maior para alta carga
- `QUERY_SLOW_THRESHOLD_MS=500` - Threshold mais rigoroso

## Segurança

### ⚠️ IMPORTANTE

1. **NUNCA** commite o arquivo `.env` com credenciais reais
2. **SEMPRE** use chaves diferentes para cada ambiente
3. **SEMPRE** use HTTPS em produção
4. **SEMPRE** faça backup das chaves de criptografia

### Rotação de Chaves

Para rotacionar chaves de segurança:

1. Gere novas chaves
2. Atualize `SECRET_KEY` e `ENCRYPTION_KEY`
3. Reinicie a aplicação
4. **Importante:** Usuários precisarão fazer login novamente

## Troubleshooting

### Erro: "DATABASE_URL must be a PostgreSQL connection string"

Verifique se a URL começa com `postgresql://` ou `postgres://`

### Erro: "Security keys must be at least 32 characters"

Gere chaves com pelo menos 32 caracteres:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Erro: "Configuration validation failed"

Execute a validação para ver detalhes:
```bash
python -c "from src.infrastructure.config import validate_required_settings; validate_required_settings()"
```

## Monitoramento

Use o MonitoringService para verificar a saúde do sistema:

```python
from src.services.monitoring_service import MonitoringService

# Verificar saúde
health = await monitoring_service.get_system_health()
print(health)

# Verificar métricas
metrics = await monitoring_service.get_performance_metrics()
print(metrics)
```

## Suporte

Para mais informações, consulte:
- `README_NEW.md` - Guia de início rápido
- `DOCUMENTACAO_TECNICA.md` - Documentação técnica completa
- `migrations/QUICK_START.md` - Guia de migrações
