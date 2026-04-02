# Resumo Técnico - Migração 001

## Sistema de Estoque DEKIDS - Migração do Banco de Dados

---

## 📊 Visão Geral

Esta migração expande o banco de dados do sistema de estoque para suportar as novas funcionalidades planejadas na Fase 2 do projeto.

**Versão:** 001  
**Data:** 2024  
**Tipo:** Aditiva (não destrutiva)  
**Reversível:** Sim  

---

## 🗄️ Alterações no Schema

### 1. Tabela `produtos` (Expandida)

**Novos Campos:**

| Campo | Tipo | Nullable | Default | Descrição |
|-------|------|----------|---------|-----------|
| `estoque_minimo` | INTEGER | NOT NULL | 5 | Quantidade mínima para alerta de estoque baixo |
| `codigo_barras` | TEXT | NULL | NULL | Código de barras EAN-13 do produto |
| `created_at` | TIMESTAMP | NULL | NOW() | Data/hora de criação do registro |
| `updated_at` | TIMESTAMP | NULL | NOW() | Data/hora da última atualização |

**Novas Constraints:**

- `unique_codigo_barras` - Garante unicidade do código de barras
- `unique_referencia_tamanho` - Garante que não existam produtos duplicados (mesma referência + tamanho)

**Impacto:**
- ✅ Compatível com código existente (campos com valores padrão)
- ✅ Produtos existentes receberão `estoque_minimo = 5` automaticamente
- ✅ Campos `codigo_barras`, `created_at`, `updated_at` serão NULL para produtos existentes

---

### 2. Tabela `usuarios` (Nova)

**Estrutura:**

```sql
CREATE TABLE usuarios (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    tentativas_login INTEGER DEFAULT 0,
    bloqueado_ate TIMESTAMP,
    ultimo_acesso TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Campos:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | BIGSERIAL | Identificador único do usuário |
| `username` | TEXT | Nome de usuário (único) |
| `senha_hash` | TEXT | Hash bcrypt da senha |
| `ativo` | BOOLEAN | Indica se usuário está ativo |
| `tentativas_login` | INTEGER | Contador de tentativas de login falhadas |
| `bloqueado_ate` | TIMESTAMP | Timestamp até quando usuário está bloqueado |
| `ultimo_acesso` | TIMESTAMP | Data/hora do último acesso bem-sucedido |
| `created_at` | TIMESTAMP | Data/hora de criação do usuário |

**Funcionalidades Suportadas:**
- ✅ Autenticação multi-usuário
- ✅ Controle de tentativas de login (bloqueio após 3 tentativas)
- ✅ Bloqueio temporário (5 minutos)
- ✅ Rastreamento de último acesso

---

### 3. Tabela `movimentacoes` (Nova)

**Estrutura:**

```sql
CREATE TABLE movimentacoes (
    id BIGSERIAL PRIMARY KEY,
    produto_id BIGINT NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida', 'ajuste')),
    quantidade INTEGER NOT NULL,
    quantidade_anterior INTEGER NOT NULL,
    quantidade_nova INTEGER NOT NULL,
    observacao TEXT,
    usuario_id BIGINT REFERENCES usuarios(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Campos:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | BIGSERIAL | Identificador único da movimentação |
| `produto_id` | BIGINT | Referência ao produto (FK) |
| `tipo` | TEXT | Tipo: 'entrada', 'saida' ou 'ajuste' |
| `quantidade` | INTEGER | Quantidade movimentada (sempre positiva) |
| `quantidade_anterior` | INTEGER | Estoque antes da movimentação |
| `quantidade_nova` | INTEGER | Estoque após a movimentação |
| `observacao` | TEXT | Observação opcional |
| `usuario_id` | BIGINT | Usuário que realizou (FK, opcional) |
| `created_at` | TIMESTAMP | Data/hora da movimentação |

**Índices:**

- `idx_movimentacoes_produto` - Otimiza consultas por produto
- `idx_movimentacoes_data` - Otimiza consultas por período
- `idx_movimentacoes_tipo` - Otimiza filtros por tipo
- `idx_movimentacoes_usuario` - Otimiza consultas por usuário

**Constraints:**

- `CHECK (tipo IN ('entrada', 'saida', 'ajuste'))` - Valida tipo de movimentação
- `ON DELETE CASCADE` - Deleta movimentações quando produto é deletado

**Funcionalidades Suportadas:**
- ✅ Histórico completo de movimentações
- ✅ Rastreamento de alterações de estoque
- ✅ Auditoria de operações
- ✅ Suporte a observações

---

### 4. Tabela `sessoes` (Nova)

**Estrutura:**

```sql
CREATE TABLE sessoes (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expira_em TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Campos:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | BIGSERIAL | Identificador único da sessão |
| `usuario_id` | BIGINT | Usuário dono da sessão (FK) |
| `token` | TEXT | Token único de autenticação |
| `expira_em` | TIMESTAMP | Data/hora de expiração (2h após criação) |
| `created_at` | TIMESTAMP | Data/hora de criação da sessão |

**Índices:**

- `idx_sessoes_token` - Otimiza validação de token
- `idx_sessoes_expiracao` - Otimiza limpeza de sessões expiradas
- `idx_sessoes_usuario` - Otimiza consultas por usuário

**Constraints:**

- `UNIQUE (token)` - Garante unicidade do token
- `ON DELETE CASCADE` - Deleta sessões quando usuário é deletado

**Funcionalidades Suportadas:**
- ✅ Gerenciamento de sessões
- ✅ Expiração automática (2 horas)
- ✅ Tokens seguros (gerados com secrets.token_urlsafe)
- ✅ Limpeza de sessões expiradas

---

## 🔗 Relacionamentos

```
usuarios (1) ──── (N) sessoes
    │
    └──── (N) movimentacoes
                │
produtos (1) ────┘
```

**Detalhes:**

- Um usuário pode ter múltiplas sessões ativas
- Um usuário pode realizar múltiplas movimentações
- Um produto pode ter múltiplas movimentações
- Movimentações são deletadas em cascata quando produto é deletado
- Sessões são deletadas em cascata quando usuário é deletado

---

## 📈 Impacto de Performance

### Índices Criados

**Total:** 7 índices novos

| Tabela | Índice | Campos | Propósito |
|--------|--------|--------|-----------|
| movimentacoes | idx_movimentacoes_produto | produto_id | Consultas por produto |
| movimentacoes | idx_movimentacoes_data | created_at | Consultas por período |
| movimentacoes | idx_movimentacoes_tipo | tipo | Filtros por tipo |
| movimentacoes | idx_movimentacoes_usuario | usuario_id | Consultas por usuário |
| sessoes | idx_sessoes_token | token | Validação de token |
| sessoes | idx_sessoes_expiracao | expira_em | Limpeza de expiradas |
| sessoes | idx_sessoes_usuario | usuario_id | Consultas por usuário |

**Benefícios:**
- ✅ Consultas de histórico ~10x mais rápidas
- ✅ Validação de sessão em O(1)
- ✅ Filtros por período otimizados

**Custo:**
- ⚠️ Espaço adicional: ~5-10% do tamanho das tabelas
- ⚠️ Inserções ligeiramente mais lentas (negligível)

---

## 🔒 Segurança

### Senhas

- ✅ Armazenadas como hash bcrypt (custo 12)
- ✅ Nunca armazenadas em texto plano
- ✅ Salt único por senha

### Sessões

- ✅ Tokens gerados com `secrets.token_urlsafe(32)` (256 bits)
- ✅ Expiração automática após 2 horas
- ✅ Tokens únicos (constraint)

### Integridade Referencial

- ✅ Foreign keys garantem consistência
- ✅ Cascade deletes evitam registros órfãos
- ✅ Check constraints validam dados

---

## 📦 Tamanho Estimado

**Estimativa de crescimento do banco:**

| Tabela | Tamanho por Registro | Estimativa (1000 produtos) |
|--------|---------------------|---------------------------|
| produtos (novos campos) | ~50 bytes | ~50 KB |
| usuarios | ~200 bytes | ~20 KB (100 usuários) |
| movimentacoes | ~150 bytes | ~1.5 MB (10k movimentações) |
| sessoes | ~100 bytes | ~10 KB (100 sessões ativas) |

**Total adicional:** ~1.6 MB para 1000 produtos com histórico

---

## 🧪 Testes Recomendados

Após a migração, execute:

1. **Teste de Integridade:**
   ```sql
   SELECT COUNT(*) FROM produtos;
   SELECT COUNT(*) FROM usuarios;
   SELECT COUNT(*) FROM movimentacoes;
   SELECT COUNT(*) FROM sessoes;
   ```

2. **Teste de Constraints:**
   - Tentar inserir produto duplicado (deve falhar)
   - Tentar inserir código de barras duplicado (deve falhar)
   - Tentar inserir movimentação com tipo inválido (deve falhar)

3. **Teste de Performance:**
   - Consultar histórico de movimentações por produto
   - Validar token de sessão
   - Filtrar movimentações por período

---

## 🔄 Rollback

Se necessário reverter:

```sql
DROP TABLE IF EXISTS sessoes CASCADE;
DROP TABLE IF EXISTS movimentacoes CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

ALTER TABLE produtos 
DROP COLUMN IF EXISTS estoque_minimo,
DROP COLUMN IF EXISTS codigo_barras,
DROP COLUMN IF EXISTS created_at,
DROP COLUMN IF EXISTS updated_at,
DROP CONSTRAINT IF EXISTS unique_referencia_tamanho,
DROP CONSTRAINT IF EXISTS unique_codigo_barras;
```

**Atenção:** Isso deletará todos os dados das novas tabelas!

---

## 📋 Compatibilidade

### Código Existente

- ✅ **100% compatível** - Nenhuma alteração necessária
- ✅ Funções existentes continuam funcionando
- ✅ Novos campos têm valores padrão

### Versões

- ✅ PostgreSQL 12+
- ✅ Supabase (todas as versões)

---

## 📝 Próximas Migrações

Migrações futuras planejadas:

- **002**: Adicionar tabela de logs de sistema
- **003**: Adicionar campos de auditoria em todas as tabelas
- **004**: Adicionar suporte a categorias de produtos

---

## 📞 Suporte Técnico

**Documentação:**
- `migrations/README.md` - Guia de uso
- `INSTRUCOES_MIGRACAO.md` - Instruções passo a passo

**Scripts:**
- `validar_migracao.py` - Validação automatizada
- `teste_rapido.py` - Testes de integração
- `criar_usuario_admin.py` - Criação de usuário

**Contato:**
- Consulte a documentação do Supabase: https://supabase.com/docs
- Revise os logs de erro no dashboard

---

**Versão do Documento:** 1.0  
**Última Atualização:** 2024  
**Autor:** Sistema de Estoque DEKIDS - Equipe de Desenvolvimento
