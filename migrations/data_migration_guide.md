# Data Migration Guide

Este guia descreve como migrar dados existentes do sistema antigo para a nova arquitetura.

## ⚠️ IMPORTANTE - Leia Antes de Executar

1. **SEMPRE faça backup completo antes de migrar**
2. **Teste em ambiente de desenvolvimento primeiro**
3. **Execute as migrações em horário de baixo movimento**
4. **Tenha um plano de rollback preparado**

## Pré-requisitos

- Python 3.10+
- Acesso ao banco de dados Supabase
- Variáveis de ambiente configuradas (.env)
- Backup completo do banco de dados

## Ordem de Execução

Execute os scripts nesta ordem:

1. `backup_database.py` - Criar backup completo
2. `migrate_users.py` - Migrar usuários para novo schema
3. `migrate_products.py` - Migrar produtos com version=1
4. `migrate_sales.py` - Migrar vendas com version=1
5. `verify_migration.py` - Verificar integridade dos dados

## Scripts de Migração

### 1. Backup do Banco de Dados

```bash
python migrations/scripts/backup_database.py
```

Cria um backup completo em `migrations/backups/backup_YYYYMMDD_HHMMSS.sql`

### 2. Migração de Usuários

```bash
python migrations/scripts/migrate_users.py
```

**O que faz:**
- Adiciona campos de segurança (failed_login_attempts, locked_until, etc.)
- Define version=1 para todos os usuários
- **IMPORTANTE**: Força reset de senha no próximo login (password_changed_at = NULL)

**Ações necessárias após migração:**
- Todos os usuários precisarão redefinir suas senhas
- Envie comunicado aos usuários sobre o reset de senha

### 3. Migração de Produtos

```bash
python migrations/scripts/migrate_products.py
```

**O que faz:**
- Adiciona version=1 para controle de concorrência otimista
- Verifica e corrige constraints (quantity >= 0, price > 0)
- Adiciona low_stock_threshold se não existir

### 4. Migração de Vendas

```bash
python migrations/scripts/migrate_sales.py
```

**O que faz:**
- Adiciona version=1 para controle de concorrência otimista
- Cria registros de inventory_movements para vendas existentes
- Verifica integridade de sale_items e payments

### 5. Verificação de Integridade

```bash
python migrations/scripts/verify_migration.py
```

**O que verifica:**
- Todos os registros têm version >= 1
- Constraints estão sendo respeitados
- Relacionamentos estão íntegros
- Não há dados órfãos

## Rollback

Se algo der errado, execute:

```bash
python migrations/scripts/rollback.py --backup-file migrations/backups/backup_YYYYMMDD_HHMMSS.sql
```

## Monitoramento Pós-Migração

Após a migração, monitore:

1. **Logs de erro** - Verifique `logs/dekids.log`
2. **Performance** - Use MonitoringService.get_performance_metrics()
3. **Integridade** - Execute verify_migration.py periodicamente

## Troubleshooting

### Erro: "version column not found"

Execute as migrações do Alembic primeiro:

```bash
alembic upgrade head
```

### Erro: "constraint violation"

Verifique os dados antes de migrar:

```bash
python migrations/scripts/check_data_quality.py
```

### Erro: "connection timeout"

Aumente o timeout no .env:

```
DB_TIMEOUT=120.0
```

## Suporte

Em caso de problemas:

1. Verifique os logs em `logs/dekids.log`
2. Execute `verify_migration.py` para diagnóstico
3. Consulte a documentação técnica em `DOCUMENTACAO_TECNICA.md`
