# 📊 Fluxogramas - Sistema de Vendas DEKIDS

## 🎯 Visão Geral

Este documento apresenta os fluxogramas visuais das principais operações do Sistema de Vendas DEKIDS.

---

## 📋 Índice

1. [Fluxo Completo de Venda](#1-fluxo-completo-de-venda)
2. [Fluxo de Gestão de Clientes](#2-fluxo-de-gestão-de-clientes)
3. [Fluxo de Geração de Relatórios](#3-fluxo-de-geração-de-relatórios)
4. [Fluxo de Cancelamento de Vendas](#4-fluxo-de-cancelamento-de-vendas)

---

## 1. Fluxo Completo de Venda

### 1.1 Visão Geral do Processo

```
┌─────────────────────────────────────────────────────────────┐
│                    INÍCIO DA VENDA                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 1: Acessar PDV                                       │
│  • Menu > Vendas (PDV)                                      │
│  • Sistema valida autenticação                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 2: Adicionar Produtos ao Carrinho                    │
│  • Buscar produto (código/referência/descrição)             │
│  • Validar estoque disponível                               │
│  • Adicionar ao carrinho                                    │
│  • Ajustar quantidades se necessário                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 3: Aplicar Desconto (Opcional)                      │
│  ┌─────────────────┐                                        │
│  │ Desconto %?     │ → SIM → Aplicar desconto percentual    │
│  └────────┬────────┘                                        │
│           │ NÃO                                             │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Desconto R$?    │ → SIM → Aplicar desconto em valor     │
│  └────────┬────────┘                                        │
│           │ NÃO                                             │
│           ▼                                                 │
│  Prosseguir sem desconto                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 4: Vincular Cliente (Opcional)                      │
│  ┌─────────────────┐                                        │
│  │ Cliente         │ → SIM → Buscar e selecionar cliente   │
│  │ cadastrado?     │                                        │
│  └────────┬────────┘                                        │
│           │ NÃO                                             │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Cadastrar       │ → SIM → Cadastrar novo cliente        │
│  │ novo?           │                                        │
│  └────────┬────────┘                                        │
│           │ NÃO                                             │
│           ▼                                                 │
│  Venda Avulsa (sem cliente)                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 5: Adicionar Formas de Pagamento                    │
│  • Selecionar forma de pagamento                            │
│  • Informar valor                                           │
│  • Adicionar parcelas (se cartão crédito)                   │
│  • Informar valor recebido (se dinheiro)                    │
│  • Repetir até Valor Restante = R$ 0,00                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 6: Validações Finais                                │
│  ┌─────────────────┐                                        │
│  │ Carrinho vazio? │ → SIM → ❌ Erro: Adicione produtos    │
│  └────────┬────────┘                                        │
│           │ NÃO                                             │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Valor Restante  │ → SIM → ❌ Erro: Ajuste pagamentos    │
│  │ ≠ R$ 0,00?      │                                        │
│  └────────┬────────┘                                        │
│           │ NÃO                                             │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Estoque         │ → NÃO → ❌ Erro: Estoque insuficiente │
│  │ disponível?     │                                        │
│  └────────┬────────┘                                        │
│           │ SIM                                             │
│           ▼                                                 │
│  ✅ Validações OK                                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 7: Finalizar Venda                                  │
│  • Clicar em "Finalizar Venda"                              │
│  • Sistema processa transação                               │
│  • Registra venda no banco de dados                         │
│  • Dá baixa automática no estoque                           │
│  • Gera comprovante                                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 8: Comprovante                                       │
│  • Visualizar comprovante na tela                           │
│  • Imprimir comprovante                                     │
│  • Exportar PDF (opcional)                                  │
│  • Entregar ao cliente                                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    ✅ VENDA CONCLUÍDA                       │
│  • Carrinho limpo automaticamente                           │
│  • Sistema pronto para nova venda                           │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Fluxo de Decisão: Formas de Pagamento

```
                    ┌──────────────────┐
                    │ Forma de         │
                    │ Pagamento?       │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┬────────────┐
            │                │                │            │
            ▼                ▼                ▼            ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐
    │   DINHEIRO   │ │   CARTÃO     │ │  CARTÃO  │ │   PIX    │
    │              │ │   DÉBITO     │ │  CRÉDITO │ │          │
    └──────┬───────┘ └──────┬───────┘ └────┬─────┘ └────┬─────┘
           │                │               │            │
           ▼                ▼               ▼            ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐
    │ Valor        │ │ Valor        │ │ Valor    │ │ Valor    │
    │ Recebido     │ │              │ │ Parcelas │ │          │
    │ Calcular     │ │              │ │ (1-12)   │ │          │
    │ Troco        │ │              │ │          │ │          │
    └──────┬───────┘ └──────┬───────┘ └────┬─────┘ └────┬─────┘
           │                │               │            │
           └────────────────┴───────────────┴────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Adicionar        │
                    │ Pagamento        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Valor Restante   │
                    │ = R$ 0,00?       │
                    └────────┬─────────┘
                             │
                    ┌────────┴────────┐
                    │ SIM             │ NÃO
                    ▼                 ▼
            ┌──────────────┐   ┌──────────────┐
            │ Habilitar    │   │ Adicionar    │
            │ Finalizar    │   │ mais         │
            │ Venda        │   │ pagamentos   │
            └──────────────┘   └──────┬───────┘
                                      │
                                      └──────┐
                                             │
                                             ▼
                                    (Repetir processo)
```

---

## 2. Fluxo de Gestão de Clientes

### 2.1 Cadastro de Novo Cliente

```
┌─────────────────────────────────────────────────────────────┐
│                 CADASTRO DE CLIENTE                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 1: Acessar Tela de Clientes                         │
│  • Menu > Clientes                                          │
│  • Clicar em "Novo Cliente"                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 2: Preencher Dados Obrigatórios                     │
│  • Nome Completo                                            │
│  • CPF (11 dígitos)                                         │
│  • Telefone                                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 3: Preencher Dados Opcionais                        │
│  • Email                                                    │
│  • Endereço completo                                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 4: Validações                                        │
│  ┌─────────────────┐                                        │
│  │ CPF válido?     │ → NÃO → ❌ Erro: CPF inválido         │
│  │ (11 dígitos)    │                                        │
│  └────────┬────────┘                                        │
│           │ SIM                                             │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ CPF duplicado?  │ → SIM → ❌ Erro: CPF já cadastrado    │
│  └────────┬────────┘                                        │
│           │ NÃO                                             │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Email válido?   │ → NÃO → ❌ Erro: Email inválido       │
│  └────────┬────────┘                                        │
│           │ SIM                                             │
│           ▼                                                 │
│  ✅ Validações OK                                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 5: Salvar Cliente                                   │
│  • Clicar em "Salvar Cliente"                               │
│  • Sistema registra no banco de dados                       │
│  • Exibe mensagem de sucesso                                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              ✅ CLIENTE CADASTRADO                          │
│  • Cliente disponível para vendas                           │
│  • Histórico de compras iniciado                            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Consulta de Histórico de Compras

```
┌─────────────────────────────────────────────────────────────┐
│            HISTÓRICO DE COMPRAS DO CLIENTE                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 1: Buscar Cliente                                   │
│  • Digitar CPF, nome ou telefone                            │
│  • Clicar em "Buscar"                                       │
│  • Selecionar cliente na lista                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 2: Visualizar Histórico                             │
│  • Clicar em "Histórico"                                    │
│  • Sistema carrega dados do cliente                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  INFORMAÇÕES EXIBIDAS:                                      │
│                                                             │
│  📊 MÉTRICAS DO CLIENTE                                     │
│  • Total Gasto: R$ X.XXX,XX                                 │
│  • Número de Compras: XX vendas                             │
│  • Última Compra: DD/MM/AAAA                                │
│  • Ticket Médio: R$ XXX,XX                                  │
│                                                             │
│  📋 LISTA DE VENDAS                                         │
│  • Venda #XXXX - DD/MM/AAAA - R$ XXX,XX - Status           │
│  • Venda #XXXX - DD/MM/AAAA - R$ XXX,XX - Status           │
│  • ...                                                      │
│                                                             │
│  🛍️ PRODUTOS MAIS COMPRADOS                                 │
│  • Produto A - XX unidades                                  │
│  • Produto B - XX unidades                                  │
│  • ...                                                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  AÇÕES DISPONÍVEIS:                                         │
│  • Ver detalhes de venda específica                         │
│  • Fechar histórico                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Fluxo de Geração de Relatórios

### 3.1 Relatório de Vendas por Período

```
┌─────────────────────────────────────────────────────────────┐
│           RELATÓRIO DE VENDAS POR PERÍODO                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 1: Acessar Relatórios                               │
│  • Menu > Relatórios de Vendas                              │
│  • Aba "Vendas por Período"                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 2: Definir Período                                  │
│  • Selecionar Data Inicial                                  │
│  • Selecionar Data Final                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 3: Aplicar Filtros (Opcional)                       │
│  ┌─────────────────┐                                        │
│  │ Filtrar por     │ → SIM → Selecionar vendedor           │
│  │ vendedor?       │                                        │
│  └────────┬────────┘                                        │
│           │ NÃO                                             │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Filtrar por     │ → SIM → Selecionar forma pagamento    │
│  │ pagamento?      │                                        │
│  └────────┬────────┘                                        │
│           │ NÃO                                             │
│           ▼                                                 │
│  Prosseguir sem filtros                                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 4: Gerar Relatório                                  │
│  • Clicar em "Gerar Relatório"                              │
│  • Sistema processa dados                                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  RESULTADOS EXIBIDOS:                                       │
│                                                             │
│  📊 MÉTRICAS GERAIS                                         │
│  • Faturamento Total: R$ XX.XXX,XX                          │
│  • Número de Vendas: XXX vendas                             │
│  • Ticket Médio: R$ XXX,XX                                  │
│                                                             │
│  💳 DISTRIBUIÇÃO POR FORMA DE PAGAMENTO                     │
│  • Dinheiro: R$ X.XXX,XX (XX%)                              │
│  • Cartão Crédito: R$ X.XXX,XX (XX%)                        │
│  • Cartão Débito: R$ X.XXX,XX (XX%)                         │
│  • PIX: R$ X.XXX,XX (XX%)                                   │
│  [Gráfico de Pizza]                                         │
│                                                             │
│  📋 LISTA DETALHADA DE VENDAS                               │
│  • Venda #XXXX - DD/MM - Cliente - R$ XXX - Vendedor       │
│  • ...                                                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  AÇÕES DISPONÍVEIS:                                         │
│  • Ordenar por data/valor/vendedor                          │
│  • Exportar para CSV                                        │
│  • Gerar novo relatório                                     │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Relatório de Produtos Mais Vendidos

```
┌─────────────────────────────────────────────────────────────┐
│         RELATÓRIO DE PRODUTOS MAIS VENDIDOS                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 1: Acessar Relatório                                │
│  • Menu > Relatórios de Vendas                              │
│  • Aba "Produtos Mais Vendidos"                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 2: Definir Período e Filtros                        │
│  • Selecionar Data Inicial e Final                          │
│  • Filtros opcionais:                                       │
│    - Gênero (Masculino/Feminino/Unissex)                   │
│    - Marca                                                  │
│    - Faixa de Preço (Min/Max)                               │
│    - Top N produtos (ex: Top 10)                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 3: Gerar Relatório                                  │
│  • Clicar em "Gerar Relatório"                              │
│  • Sistema agrega dados de vendas                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  RESULTADOS EXIBIDOS:                                       │
│                                                             │
│  📊 RANKING DE PRODUTOS                                     │
│  ┌────┬──────────┬──────┬────────┬────────────┬──────┐     │
│  │ # │ Produto  │ Qtd  │ Fatur. │ Particip.% │ ...  │     │
│  ├────┼──────────┼──────┼────────┼────────────┼──────┤     │
│  │ 1  │ Prod. A  │ 150  │ 4.500  │   25%      │ ...  │     │
│  │ 2  │ Prod. B  │ 120  │ 3.600  │   20%      │ ...  │     │
│  │ 3  │ Prod. C  │ 100  │ 3.000  │   17%      │ ...  │     │
│  │... │ ...      │ ...  │ ...    │   ...      │ ...  │     │
│  └────┴──────────┴──────┴────────┴────────────┴──────┘     │
│                                                             │
│  📊 GRÁFICO DE BARRAS                                       │
│  [Visualização dos top produtos]                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  AÇÕES DISPONÍVEIS:                                         │
│  • Exportar para CSV                                        │
│  • Ajustar filtros                                          │
│  • Visualizar detalhes de produto                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Relatório de Vendas por Vendedor

```
┌─────────────────────────────────────────────────────────────┐
│          RELATÓRIO DE VENDAS POR VENDEDOR                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 1: Acessar Relatório                                │
│  • Menu > Relatórios de Vendas                              │
│  • Aba "Vendas por Vendedor"                                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 2: Definir Período                                  │
│  • Selecionar Data Inicial                                  │
│  • Selecionar Data Final                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 3: Gerar Relatório                                  │
│  • Clicar em "Gerar Relatório"                              │
│  • Sistema agrega vendas por vendedor                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  RESULTADOS EXIBIDOS:                                       │
│                                                             │
│  🏆 RANKING DE VENDEDORES                                   │
│  ┌────┬──────────┬──────┬────────┬────────┬──────────┐     │
│  │ # │ Vendedor │ Qtd  │ Fatur. │ Ticket │ Partic.% │     │
│  ├────┼──────────┼──────┼────────┼────────┼──────────┤     │
│  │ 1  │ João     │ 85   │ 12.750 │  150   │   35%    │     │
│  │ 2  │ Maria    │ 70   │ 10.500 │  150   │   29%    │     │
│  │ 3  │ Pedro    │ 60   │  9.000 │  150   │   25%    │     │
│  │... │ ...      │ ...  │ ...    │  ...   │   ...    │     │
│  └────┴──────────┴──────┴────────┴────────┴──────────┘     │
│                                                             │
│  📊 GRÁFICO COMPARATIVO                                     │
│  [Barras comparando faturamento por vendedor]               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  AÇÕES DISPONÍVEIS:                                         │
│  • Ver detalhes de vendas do vendedor                       │
│  • Exportar para CSV                                        │
│  • Comparar períodos                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Fluxo de Cancelamento de Vendas

### 4.1 Processo Completo de Cancelamento

```
┌─────────────────────────────────────────────────────────────┐
│              CANCELAMENTO DE VENDA                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 1: Acessar Cancelamento                             │
│  • Menu > Cancelar Venda                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 2: Buscar Venda                                     │
│  ┌─────────────────┐                                        │
│  │ Buscar por      │ → Número → Digite número da venda     │
│  │ número ou data? │                                        │
│  └────────┬────────┘                                        │
│           │ Data                                            │
│           ▼                                                 │
│  Selecionar período (Data Inicial/Final)                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 3: Clicar em "Buscar"                               │
│  • Sistema lista vendas encontradas                         │
│  • Exibe: Número, Data, Cliente, Valor, Status             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 4: Verificar Status da Venda                        │
│  ┌─────────────────┐                                        │
│  │ Venda já        │ → SIM → ❌ Erro: Venda já cancelada   │
│  │ cancelada?      │                                        │
│  └────────┬────────┘                                        │
│           │ NÃO                                             │
│           ▼                                                 │
│  Venda disponível para cancelamento                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 5: Visualizar Detalhes                              │
│  • Clicar em "Ver Detalhes" (opcional)                      │
│  • Confirmar que é a venda correta                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 6: Iniciar Cancelamento                             │
│  • Clicar em "❌ Cancelar Venda"                            │
│  • Modal de confirmação é exibido                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 7: Confirmar Cancelamento                           │
│  • Revisar detalhes da venda no modal                       │
│  • Digitar motivo do cancelamento (obrigatório)             │
│    Exemplos:                                                │
│    - "Devolução de produto com defeito"                     │
│    - "Erro no registro da venda"                            │
│    - "Cliente desistiu da compra"                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 8: Validação do Motivo                              │
│  ┌─────────────────┐                                        │
│  │ Motivo          │ → NÃO → ❌ Erro: Motivo obrigatório   │
│  │ preenchido?     │                                        │
│  └────────┬────────┘                                        │
│           │ SIM                                             │
│           ▼                                                 │
│  Prosseguir com cancelamento                                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 9: Processar Cancelamento                           │
│  • Clicar em "Confirmar Cancelamento"                       │
│  • Sistema inicia transação                                 │
│                                                             │
│  Operações executadas:                                      │
│  1. Marcar venda como cancelada                             │
│  2. Registrar data/hora do cancelamento                     │
│  3. Registrar usuário que cancelou                          │
│  4. Salvar motivo do cancelamento                           │
│  5. Restaurar estoque de cada produto                       │
│     (registrar movimentação tipo 'entrada')                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PASSO 10: Verificar Resultado                             │
│  ┌─────────────────┐                                        │
│  │ Sucesso?        │ → NÃO → ❌ Erro: Rollback executado   │
│  │                 │         Venda não foi cancelada        │
│  └────────┬────────┘                                        │
│           │ SIM                                             │
│           ▼                                                 │
│  ✅ Cancelamento concluído com sucesso                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│           ✅ VENDA CANCELADA COM SUCESSO                    │
│                                                             │
│  Efeitos do cancelamento:                                   │
│  • Status da venda: "Cancelada"                             │
│  • Estoque restaurado automaticamente                       │
│  • Venda excluída de relatórios de faturamento              │
│  • Registro mantido para auditoria                          │
│  • Motivo documentado                                       │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Fluxo de Decisão: Estorno de Estoque

```
                    ┌──────────────────┐
                    │ Venda Cancelada  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Buscar Itens     │
                    │ da Venda         │
                    └────────┬─────────┘
                             │
                             ▼
            ┌────────────────┴────────────────┐
            │                                 │
            ▼                                 ▼
    ┌──────────────┐                 ┌──────────────┐
    │ Item 1       │                 │ Item N       │
    │ Produto A    │                 │ Produto Z    │
    │ Qtd: 2       │                 │ Qtd: 5       │
    └──────┬───────┘                 └──────┬───────┘
           │                                 │
           ▼                                 ▼
    ┌──────────────┐                 ┌──────────────┐
    │ Registrar    │                 │ Registrar    │
    │ Movimentação │                 │ Movimentação │
    │ Tipo: ENTRADA│                 │ Tipo: ENTRADA│
    │ Qtd: 2       │                 │ Qtd: 5       │
    └──────┬───────┘                 └──────┬───────┘
           │                                 │
           ▼                                 ▼
    ┌──────────────┐                 ┌──────────────┐
    │ Atualizar    │                 │ Atualizar    │
    │ Estoque      │                 │ Estoque      │
    │ Produto A    │                 │ Produto Z    │
    │ +2 unidades  │                 │ +5 unidades  │
    └──────┬───────┘                 └──────┬───────┘
           │                                 │
           └────────────────┬────────────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │ Todos os itens   │
                   │ processados?     │
                   └────────┬─────────┘
                            │
                   ┌────────┴────────┐
                   │ SIM             │ NÃO
                   ▼                 ▼
           ┌──────────────┐   ┌──────────────┐
           │ COMMIT       │   │ ROLLBACK     │
           │ Transação    │   │ Cancelamento │
           │ Concluída    │   │ Falhou       │
           └──────────────┘   └──────────────┘
```

---

## 📝 Legenda de Símbolos

```
┌─────────┐
│ Processo│  = Ação ou etapa do processo
└─────────┘

┌─────────┐
│ Decisão?│  = Ponto de decisão (SIM/NÃO)
└─────────┘

    │
    ▼         = Fluxo sequencial

    ├──────   = Ramificação de fluxo

✅           = Sucesso / Conclusão positiva

❌           = Erro / Validação falhou

💡           = Dica ou informação importante

⚠️           = Atenção / Cuidado

📊           = Dados / Métricas

🔄           = Processo repetitivo
```

---

## 🎯 Dicas de Uso dos Fluxogramas

1. **Treinamento**: Use os fluxogramas para treinar novos usuários
2. **Referência Rápida**: Consulte durante operações complexas
3. **Troubleshooting**: Identifique onde o processo pode ter falhado
4. **Otimização**: Analise os fluxos para identificar melhorias
5. **Documentação**: Mantenha atualizado conforme o sistema evolui

---

**Versão:** 1.0  
**Data:** Janeiro 2025  
**Sistema:** DEKIDS Moda Infantil - Módulo de Vendas
