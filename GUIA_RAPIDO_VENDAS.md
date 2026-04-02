# 🚀 Guia Rápido - Sistema de Vendas DEKIDS

## ⚡ Referência Rápida para Operações Diárias

---

## 🛒 Realizar uma Venda em 5 Passos

### 1️⃣ Adicionar Produtos
```
Menu > Vendas (PDV)
↓
Buscar produto (código/referência/descrição)
↓
Clicar em "Adicionar" para cada produto
```

### 2️⃣ Aplicar Desconto (Opcional)
```
Desconto % → Digite percentual → "Aplicar Desconto %"
OU
Desconto R$ → Digite valor → "Aplicar Desconto R$"
```

### 3️⃣ Vincular Cliente (Opcional)
```
"Buscar Cliente" → Digite CPF/nome/telefone → Selecionar
OU
Deixar vazio para venda avulsa
```

### 4️⃣ Adicionar Pagamentos
```
Selecionar forma de pagamento
↓
Digite valor
↓
"Adicionar Pagamento"
↓
Repetir até Valor Restante = R$ 0,00
```

### 5️⃣ Finalizar
```
"Finalizar Venda" → Comprovante gerado ✅
```

---

## 👥 Cadastrar Cliente Rápido

```
Menu > Clientes
↓
"Novo Cliente"
↓
Preencher:
  • Nome Completo *
  • CPF (11 dígitos) *
  • Telefone *
  • Email
  • Endereço (opcional)
↓
"Salvar Cliente" ✅
```

**Campos obrigatórios:** Nome, CPF, Telefone

---

## ❌ Cancelar Venda

```
Menu > Cancelar Venda
↓
Buscar por número OU período
↓
"Cancelar Venda"
↓
Digite motivo do cancelamento
↓
"Confirmar Cancelamento" ✅
```

**Resultado:** Estoque restaurado automaticamente

---

## 📊 Gerar Relatórios

### Vendas por Período
```
Menu > Relatórios de Vendas > Aba "Vendas por Período"
↓
Selecionar Data Inicial e Final
↓
Aplicar filtros (opcional): Vendedor, Forma de Pagamento
↓
"Gerar Relatório"
```

### Produtos Mais Vendidos
```
Menu > Relatórios de Vendas > Aba "Produtos Mais Vendidos"
↓
Selecionar período
↓
Filtros (opcional): Gênero, Marca, Faixa de Preço, Top N
↓
"Gerar Relatório"
```

### Vendas por Vendedor
```
Menu > Relatórios de Vendas > Aba "Vendas por Vendedor"
↓
Selecionar período
↓
"Gerar Relatório"
```

---

## 💡 Atalhos e Dicas

### No PDV
| Ação | Como Fazer |
|------|------------|
| Buscar produto | Digite e pressione Enter |
| Adicionar mesmo produto | Clique "Adicionar" novamente (incrementa quantidade) |
| Remover desconto | Botão "Remover Desconto" |
| Limpar carrinho | Finalize a venda ou recarregue a página |

### Formas de Pagamento
| Forma | Campos Necessários |
|-------|-------------------|
| 💵 Dinheiro | Valor + Valor Recebido (calcula troco) |
| 💳 Cartão Débito | Valor |
| 💳 Cartão Crédito | Valor + Parcelas (1-12) |
| 📱 PIX | Valor |

### Validações Automáticas
- ✅ Estoque disponível ao adicionar produto
- ✅ Desconto não excede total
- ✅ CPF único (não duplicado)
- ✅ Email formato válido
- ✅ Soma de pagamentos = total da venda

---

## ⚠️ Erros Comuns e Soluções

| Erro | Solução Rápida |
|------|----------------|
| "Estoque insuficiente" | Reduza quantidade ou escolha outro produto |
| "CPF já cadastrado" | Busque e use o cadastro existente |
| "Valor não corresponde" | Ajuste pagamentos para somar exatamente o total |
| "Botão Finalizar desabilitado" | Verifique: produtos no carrinho + valor restante = R$ 0,00 |
| "Sessão expirada" | Faça login novamente |

---

## 📋 Checklist Diário

### Abertura do Caixa
- [ ] Fazer login no sistema
- [ ] Verificar conexão com internet
- [ ] Conferir estoque de produtos principais

### Durante o Expediente
- [ ] Vincular clientes sempre que possível
- [ ] Conferir valores antes de finalizar vendas
- [ ] Imprimir/enviar comprovantes aos clientes
- [ ] Manter cadastros de clientes atualizados

### Fechamento do Caixa
- [ ] Gerar relatório de vendas do dia
- [ ] Conferir total de vendas por forma de pagamento
- [ ] Verificar se há vendas pendentes
- [ ] Fazer backup (se aplicável)

---

## 🔢 Fórmulas Úteis

### Cálculos do Sistema
```
Subtotal = Soma de (Quantidade × Preço Unitário) de todos os itens

Desconto Percentual = Subtotal × (Percentual ÷ 100)

Desconto Valor = Valor fixo informado

Total = Subtotal - Desconto

Troco = Valor Recebido - Total

Ticket Médio = Faturamento Total ÷ Número de Vendas

Parcela = Valor Total ÷ Número de Parcelas
```

---

## 📞 Contatos Rápidos

| Situação | Ação |
|----------|------|
| Dúvida sobre operação | Consultar Manual Completo: `MANUAL_USUARIO_VENDAS.md` |
| Erro técnico | Consultar Documentação Técnica: `DOCUMENTACAO_TECNICA_VENDAS.md` |
| Problema de conexão | Verificar internet e aguardar reconexão automática |
| Suporte urgente | Contatar administrador do sistema |

---

## 🎯 Metas de Atendimento

### Tempo Médio por Operação
- ⏱️ Venda simples (1-3 produtos): **2-3 minutos**
- ⏱️ Venda complexa (múltiplos produtos/pagamentos): **5-7 minutos**
- ⏱️ Cadastro de cliente: **3-5 minutos**
- ⏱️ Cancelamento de venda: **2-3 minutos**

### Boas Práticas
- ✅ Sempre confirme dados com o cliente
- ✅ Ofereça o comprovante
- ✅ Seja cordial e eficiente
- ✅ Mantenha o sistema organizado

---

## 📱 Atalhos de Teclado (Quando Disponível)

| Tecla | Ação |
|-------|------|
| Enter | Confirmar busca |
| Esc | Fechar modal |
| Tab | Navegar entre campos |

---

## 🔐 Segurança

### Lembre-se:
- 🔒 Nunca compartilhe sua senha
- 🔒 Faça logout ao sair
- 🔒 Não deixe o sistema aberto sem supervisão
- 🔒 Verifique sempre a identidade do cliente em vendas de alto valor

---

## 📊 Indicadores de Desempenho

### Acompanhe Diariamente:
- 💰 **Faturamento do Dia**: Meta vs Realizado
- 🛒 **Número de Vendas**: Quantidade de transações
- 💵 **Ticket Médio**: Valor médio por venda
- 👥 **Novos Clientes**: Cadastros realizados

### Acompanhe Semanalmente:
- 📈 **Produtos Mais Vendidos**: Top 10 da semana
- 💳 **Formas de Pagamento**: Distribuição percentual
- 🏆 **Desempenho de Vendedores**: Ranking da equipe

---

## 🆘 Situações de Emergência

### Sistema Lento ou Travado
1. Aguarde 30 segundos
2. Recarregue a página (F5)
3. Faça login novamente se necessário
4. Contate suporte se persistir

### Erro ao Finalizar Venda
1. Anote os dados da venda
2. Verifique conexão com internet
3. Tente novamente
4. Se falhar, registre manualmente e informe suporte

### Comprovante Não Imprimiu
1. Acesse Menu > Relatórios
2. Busque a venda pelo número
3. Reimprima o comprovante
4. Ou exporte como PDF

---

## ✅ Versão Rápida

**Última atualização:** Janeiro 2025  
**Versão:** 1.0  
**Para manual completo:** Consulte `MANUAL_USUARIO_VENDAS.md`

---

**💡 Dica Final:** Mantenha este guia sempre à mão para consultas rápidas durante o atendimento!
