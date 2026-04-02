# 📘 Manual do Usuário - Sistema de Vendas DEKIDS

## 🎯 Visão Geral

Bem-vindo ao Sistema de Vendas DEKIDS! Este manual irá guiá-lo através de todas as funcionalidades do sistema, desde a realização de vendas até a geração de relatórios gerenciais.

### O que você pode fazer com este sistema:

- ✅ Realizar vendas com controle automático de estoque
- 👥 Gerenciar cadastro de clientes
- 💰 Processar múltiplas formas de pagamento
- 📊 Gerar relatórios de vendas e desempenho
- ❌ Cancelar vendas com estorno automático de estoque

---

## 📋 Índice

1. [Acessando o Sistema](#1-acessando-o-sistema)
2. [Realizando uma Venda (PDV)](#2-realizando-uma-venda-pdv)
3. [Gestão de Clientes](#3-gestão-de-clientes)
4. [Geração de Relatórios](#4-geração-de-relatórios)
5. [Cancelamento de Vendas](#5-cancelamento-de-vendas)
6. [Dicas e Boas Práticas](#6-dicas-e-boas-práticas)
7. [Solução de Problemas](#7-solução-de-problemas)

---

## 1. Acessando o Sistema

### 1.1 Login

1. Execute o sistema através do arquivo `main.py`
2. Na tela de login, insira seu **usuário** e **senha**
3. Clique em **"Entrar"**
4. Após o login bem-sucedido, você verá o menu principal

### 1.2 Menu Principal

O menu lateral contém as seguintes opções:

- **🏠 Início**: Tela inicial do sistema
- **📦 Estoque**: Gerenciamento de produtos (sistema existente)
- **🛒 Vendas (PDV)**: Ponto de venda para realizar vendas
- **👥 Clientes**: Cadastro e gestão de clientes
- **📊 Relatórios de Vendas**: Análises e relatórios gerenciais
- **❌ Cancelar Venda**: Cancelamento de vendas realizadas

---

## 2. Realizando uma Venda (PDV)

### 2.1 Acessando o PDV

1. No menu lateral, clique em **"Vendas (PDV)"**
2. Você verá a tela dividida em três seções principais:
   - **Busca de Produtos** (esquerda)
   - **Carrinho de Compras** (centro)
   - **Pagamento** (direita)

### 2.2 Adicionando Produtos ao Carrinho

#### Buscar Produto

1. Na seção **"Busca de Produtos"**, digite no campo de busca:
   - Código de barras do produto
   - Referência do produto
   - Parte da descrição do produto

2. Clique em **"Buscar"** ou pressione Enter

3. Os produtos encontrados aparecerão na tabela abaixo

#### Adicionar ao Carrinho

1. Localize o produto desejado na lista
2. Clique no botão **"Adicionar"** ao lado do produto
3. O produto será adicionado ao carrinho com quantidade inicial de 1 unidade

> **💡 Dica:** Se você adicionar o mesmo produto novamente, a quantidade será incrementada automaticamente.

### 2.3 Gerenciando o Carrinho

#### Alterar Quantidade

1. No carrinho, localize o produto
2. Clique no botão **"+"** para aumentar a quantidade
3. Clique no botão **"-"** para diminuir a quantidade
4. O sistema valida automaticamente se há estoque disponível

#### Remover Produto

1. Localize o produto no carrinho
2. Clique no botão **"🗑️ Remover"**
3. O produto será removido e o total recalculado

#### Visualizar Totais

O carrinho exibe em tempo real:
- **Subtotal**: Soma de todos os produtos
- **Desconto**: Valor do desconto aplicado (se houver)
- **Total**: Valor final a pagar

### 2.4 Aplicando Descontos

#### Desconto Percentual

1. Na seção do carrinho, localize o campo **"Desconto %"**
2. Digite o percentual de desconto (0 a 100)
3. Clique em **"Aplicar Desconto %"**
4. O desconto será calculado sobre o subtotal

#### Desconto em Valor Fixo

1. Localize o campo **"Desconto R$"**
2. Digite o valor fixo do desconto
3. Clique em **"Aplicar Desconto R$"**
4. O valor será subtraído do subtotal

#### Remover Desconto

1. Clique no botão **"Remover Desconto"**
2. O total voltará ao valor original

> **⚠️ Atenção:** 
> - Descontos percentuais devem estar entre 0% e 100%
> - Descontos em valor não podem exceder o total do carrinho

### 2.5 Vinculando Cliente à Venda

#### Venda com Cliente Cadastrado

1. Na seção **"Cliente"**, clique no botão **"Buscar Cliente"**
2. Digite CPF, nome ou telefone do cliente
3. Selecione o cliente na lista
4. O nome do cliente aparecerá vinculado à venda

#### Venda Avulsa (Sem Cliente)

1. Deixe o campo de cliente vazio
2. A venda será registrada como "Venda Avulsa"
3. Não haverá histórico de compras para esta venda

#### Cadastrar Novo Cliente

1. Clique em **"Novo Cliente"**
2. Preencha os dados do cliente (veja seção [3. Gestão de Clientes](#3-gestão-de-clientes))
3. Salve o cadastro
4. O cliente estará disponível para vinculação

### 2.6 Processando Pagamento

#### Pagamento Único

**Dinheiro:**
1. Selecione **"Dinheiro"** no dropdown de forma de pagamento
2. Digite o valor total da venda no campo **"Valor"**
3. Digite o valor recebido do cliente em **"Valor Recebido"**
4. O sistema calculará automaticamente o **troco**
5. Clique em **"Adicionar Pagamento"**

**Cartão de Débito:**
1. Selecione **"Cartão de Débito"**
2. Digite o valor total da venda
3. Clique em **"Adicionar Pagamento"**

**PIX:**
1. Selecione **"PIX"**
2. Digite o valor total da venda
3. Clique em **"Adicionar Pagamento"**

**Cartão de Crédito:**
1. Selecione **"Cartão de Crédito"**
2. Digite o valor total da venda
3. Selecione o número de parcelas (1 a 12)
4. O sistema mostrará o valor de cada parcela
5. Clique em **"Adicionar Pagamento"**

#### Pagamento Misto (Múltiplas Formas)

1. Adicione a primeira forma de pagamento com seu valor
2. O sistema mostrará o **"Valor Restante"**
3. Adicione outra forma de pagamento com o valor restante
4. Repita até que o valor restante seja **R$ 0,00**

**Exemplo:**
- Total da venda: R$ 150,00
- Pagamento 1: R$ 100,00 em Dinheiro
- Pagamento 2: R$ 50,00 em PIX
- Valor Restante: R$ 0,00 ✅

> **⚠️ Atenção:** O botão "Finalizar Venda" só será habilitado quando o valor restante for exatamente R$ 0,00

### 2.7 Finalizando a Venda

1. Certifique-se de que:
   - ✅ O carrinho contém produtos
   - ✅ Os pagamentos somam o valor total
   - ✅ O valor restante é R$ 0,00

2. Clique no botão **"Finalizar Venda"**

3. O sistema irá:
   - Validar disponibilidade de estoque
   - Registrar a venda no banco de dados
   - Dar baixa automática no estoque
   - Gerar o comprovante da venda

4. Uma janela com o **comprovante** será exibida

### 2.8 Comprovante de Venda

O comprovante contém:
- **Número da Venda**: Identificador único
- **Data e Hora**: Momento da venda
- **Cliente**: Nome e CPF (se não for venda avulsa)
- **Produtos**: Lista com descrição, quantidade, preço unitário e subtotal
- **Totais**: Subtotal, desconto e valor final
- **Pagamentos**: Formas de pagamento utilizadas
- **Vendedor**: Nome do usuário que realizou a venda

#### Opções do Comprovante

- **📄 Visualizar**: Ver o comprovante na tela
- **🖨️ Imprimir**: Enviar para impressora
- **📥 Exportar PDF**: Salvar como arquivo PDF
- **✅ Fechar**: Fechar o comprovante e iniciar nova venda

---

## 3. Gestão de Clientes

### 3.1 Acessando a Tela de Clientes

1. No menu lateral, clique em **"Clientes"**
2. Você verá a tela dividida em:
   - **Busca e Lista de Clientes** (esquerda)
   - **Formulário de Cadastro/Edição** (direita)

### 3.2 Buscando Clientes

1. Digite no campo de busca:
   - CPF do cliente (com ou sem pontuação)
   - Nome completo ou parte do nome
   - Telefone

2. Clique em **"Buscar"** ou pressione Enter

3. Os clientes encontrados aparecerão na tabela

4. Clique em **"Visualizar"** para ver detalhes do cliente

### 3.3 Cadastrando Novo Cliente

#### Dados Obrigatórios

1. Clique em **"Novo Cliente"** para limpar o formulário

2. Preencha os campos obrigatórios:
   - **Nome Completo**: Nome do cliente
   - **CPF**: 11 dígitos (apenas números)
   - **Telefone**: Telefone de contato

#### Dados Opcionais

3. Preencha os campos opcionais:
   - **Email**: Email do cliente
   - **Endereço Completo**:
     - Logradouro (rua, avenida)
     - Número
     - Complemento (apto, bloco)
     - Bairro
     - Cidade
     - Estado (UF)
     - CEP

4. Clique em **"Salvar Cliente"**

5. Uma mensagem de sucesso será exibida

> **⚠️ Validações:**
> - CPF deve ter exatamente 11 dígitos
> - CPF não pode estar duplicado no sistema
> - Email deve ter formato válido (exemplo@dominio.com)

### 3.4 Editando Cliente Existente

1. Busque o cliente desejado
2. Clique em **"Editar"** na lista
3. Os dados do cliente serão carregados no formulário
4. Altere os campos desejados
5. Clique em **"Salvar Cliente"**
6. As alterações serão salvas

### 3.5 Visualizando Histórico de Compras

1. Busque o cliente desejado
2. Clique em **"Histórico"** na lista
3. Uma janela será aberta com:

#### Métricas do Cliente
- **Total Gasto**: Soma de todas as compras
- **Número de Compras**: Quantidade de vendas realizadas
- **Última Compra**: Data da compra mais recente
- **Ticket Médio**: Valor médio por compra

#### Lista de Vendas
- Número da venda
- Data da compra
- Valor total
- Status (Finalizada/Cancelada)

#### Produtos Mais Comprados
- Lista dos produtos que o cliente mais adquiriu
- Quantidade total de cada produto

4. Clique em uma venda para ver detalhes completos

---

## 4. Geração de Relatórios

### 4.1 Acessando Relatórios

1. No menu lateral, clique em **"Relatórios de Vendas"**
2. Você verá três abas:
   - **Vendas por Período**
   - **Produtos Mais Vendidos**
   - **Vendas por Vendedor**

### 4.2 Relatório de Vendas por Período

Este relatório mostra o desempenho de vendas em um período específico.

#### Gerando o Relatório

1. Clique na aba **"Vendas por Período"**

2. Selecione o período:
   - **Data Inicial**: Data de início do período
   - **Data Final**: Data de término do período

3. Aplique filtros opcionais:
   - **Vendedor**: Filtrar por vendedor específico
   - **Forma de Pagamento**: Filtrar por método de pagamento

4. Clique em **"Gerar Relatório"**

#### Informações Exibidas

**Métricas Gerais:**
- **Faturamento Total**: Soma de todas as vendas do período
- **Número de Vendas**: Quantidade de vendas realizadas
- **Ticket Médio**: Valor médio por venda

**Distribuição por Forma de Pagamento:**
- Valor total por cada forma de pagamento
- Percentual de participação de cada forma
- Gráfico visual da distribuição

**Lista Detalhada de Vendas:**
- Número da venda
- Data e hora
- Cliente (se houver)
- Valor total
- Vendedor

#### Opções do Relatório

- **📊 Ordenar**: Clique nos cabeçalhos da tabela para ordenar
- **📥 Exportar CSV**: Salvar relatório em formato Excel
- **🔄 Atualizar**: Gerar novamente com novos filtros

### 4.3 Relatório de Produtos Mais Vendidos

Este relatório identifica os produtos com maior demanda.

#### Gerando o Relatório

1. Clique na aba **"Produtos Mais Vendidos"**

2. Selecione o período:
   - **Data Inicial**
   - **Data Final**

3. Aplique filtros opcionais:
   - **Gênero**: Masculino, Feminino, Unissex
   - **Marca**: Filtrar por marca específica
   - **Faixa de Preço**: Mínimo e máximo

4. Defina limite (opcional):
   - **Top N Produtos**: Mostrar apenas os N produtos mais vendidos
   - Exemplo: Top 10, Top 20

5. Clique em **"Gerar Relatório"**

#### Informações Exibidas

Para cada produto:
- **Descrição**: Nome completo do produto
- **Marca**: Fabricante
- **Referência**: Código de referência
- **Tamanho**: Tamanho do produto
- **Quantidade Vendida**: Total de unidades vendidas
- **Faturamento Gerado**: Valor total de vendas do produto
- **Participação %**: Percentual no faturamento total

**Gráfico Visual:**
- Gráfico de barras mostrando os produtos mais vendidos
- Facilita identificação rápida dos top performers

#### Opções do Relatório

- **📥 Exportar CSV**: Salvar para análise externa
- **🔍 Filtrar**: Refinar resultados por categoria

### 4.4 Relatório de Vendas por Vendedor

Este relatório avalia o desempenho individual de cada vendedor.

#### Gerando o Relatório

1. Clique na aba **"Vendas por Vendedor"**

2. Selecione o período:
   - **Data Inicial**
   - **Data Final**

3. Clique em **"Gerar Relatório"**

#### Informações Exibidas

Para cada vendedor:
- **Nome do Vendedor**: Usuário do sistema
- **Número de Vendas**: Quantidade de vendas realizadas
- **Faturamento Total**: Soma de todas as vendas
- **Ticket Médio**: Valor médio por venda
- **Participação %**: Percentual no faturamento total

**Ordenação:**
- Vendedores são ordenados por faturamento (maior para menor)

**Gráfico Comparativo:**
- Gráfico de barras comparando desempenho entre vendedores
- Facilita identificação de top performers

#### Detalhamento

1. Clique em **"Ver Detalhes"** ao lado de um vendedor
2. Visualize todas as vendas individuais do vendedor
3. Analise padrões e comportamentos

#### Opções do Relatório

- **📥 Exportar CSV**: Salvar para análise de RH
- **📊 Comparar**: Visualizar gráficos comparativos

---

## 5. Cancelamento de Vendas

### 5.1 Quando Cancelar uma Venda

Cancele uma venda nos seguintes casos:
- ❌ Erro no registro da venda
- 🔄 Devolução de produtos pelo cliente
- 💳 Problema com pagamento
- 📝 Correção de dados incorretos

> **⚠️ Importante:** O cancelamento é irreversível e restaura automaticamente o estoque.

### 5.2 Acessando o Cancelamento

1. No menu lateral, clique em **"Cancelar Venda"**
2. Você verá a tela de busca de vendas

### 5.3 Buscando a Venda

#### Busca por Número da Venda

1. Digite o número da venda no campo **"Número da Venda"**
2. Clique em **"Buscar"**
3. A venda será exibida na lista

#### Busca por Data

1. Selecione a **Data Inicial** e **Data Final**
2. Clique em **"Buscar por Período"**
3. Todas as vendas do período serão listadas

### 5.4 Visualizando Detalhes da Venda

1. Localize a venda na lista
2. Clique em **"Ver Detalhes"**
3. Uma janela mostrará:
   - Número da venda
   - Data e hora
   - Cliente (se houver)
   - Lista de produtos
   - Valores e pagamentos
   - Status atual

### 5.5 Cancelando a Venda

1. Localize a venda desejada
2. Clique no botão **"❌ Cancelar Venda"**
3. Uma janela de confirmação será exibida com:
   - Todos os detalhes da venda
   - Campo para **motivo do cancelamento**

4. Digite o motivo do cancelamento (obrigatório)
   - Exemplo: "Devolução de produto com defeito"
   - Exemplo: "Erro no registro da venda"

5. Clique em **"Confirmar Cancelamento"**

6. O sistema irá:
   - ✅ Marcar a venda como cancelada
   - ✅ Restaurar o estoque de todos os produtos
   - ✅ Registrar data e hora do cancelamento
   - ✅ Registrar o usuário que cancelou
   - ✅ Salvar o motivo do cancelamento

7. Uma mensagem de sucesso será exibida

### 5.6 Verificando Vendas Canceladas

1. Vendas canceladas aparecem com status **"Cancelada"** na lista
2. Elas são excluídas automaticamente dos relatórios de faturamento
3. O registro permanece no sistema para auditoria
4. O estoque é restaurado automaticamente

> **💡 Dica:** Sempre documente bem o motivo do cancelamento para facilitar auditorias futuras.

---

## 6. Dicas e Boas Práticas

### 6.1 Realizando Vendas

✅ **Sempre verifique o estoque** antes de prometer produtos ao cliente
- O sistema valida automaticamente, mas é bom confirmar visualmente

✅ **Vincule clientes sempre que possível**
- Permite histórico de compras
- Facilita atendimento personalizado
- Melhora análises de vendas

✅ **Confira os valores antes de finalizar**
- Verifique subtotal, desconto e total
- Confirme as formas de pagamento
- Valide o troco em pagamentos em dinheiro

✅ **Imprima ou envie o comprovante**
- Sempre ofereça o comprovante ao cliente
- Guarde uma cópia para controle interno

### 6.2 Gestão de Clientes

✅ **Mantenha cadastros atualizados**
- Peça para o cliente confirmar dados a cada compra
- Atualize telefone e email quando mudarem

✅ **Cadastre endereço completo**
- Facilita entregas futuras
- Melhora análise geográfica de vendas

✅ **Use o histórico de compras**
- Ofereça produtos relacionados ao histórico
- Identifique clientes VIP (alto valor gasto)

### 6.3 Relatórios

✅ **Gere relatórios regularmente**
- Diário: Acompanhe vendas do dia
- Semanal: Identifique tendências
- Mensal: Avalie metas e desempenho

✅ **Analise produtos mais vendidos**
- Mantenha estoque adequado dos top produtos
- Identifique produtos com baixa saída

✅ **Acompanhe desempenho de vendedores**
- Reconheça e incentive top performers
- Identifique necessidades de treinamento

### 6.4 Cancelamentos

✅ **Documente bem o motivo**
- Facilita auditorias
- Ajuda a identificar problemas recorrentes

✅ **Cancele apenas quando necessário**
- Cancelamentos afetam relatórios
- Impactam análise de desempenho

✅ **Verifique o estoque após cancelamento**
- Confirme que produtos voltaram ao estoque
- Valide quantidades no sistema de estoque

---

## 7. Solução de Problemas

### 7.1 Problemas Comuns no PDV

#### "Produto não encontrado"
**Causa:** Produto não cadastrado ou sem estoque
**Solução:** 
1. Verifique o cadastro no módulo de Estoque
2. Confirme que o produto tem quantidade disponível
3. Verifique se digitou corretamente o código/referência

#### "Estoque insuficiente"
**Causa:** Quantidade solicitada maior que disponível
**Solução:**
1. Verifique a quantidade disponível no estoque
2. Ajuste a quantidade no carrinho
3. Ofereça produto alternativo ao cliente

#### "Valor dos pagamentos não corresponde ao total"
**Causa:** Soma dos pagamentos diferente do valor final
**Solução:**
1. Verifique o valor total da venda
2. Some os valores dos pagamentos adicionados
3. Ajuste os valores para que a soma seja exata

#### "Botão Finalizar Venda desabilitado"
**Causa:** Alguma validação não foi atendida
**Solução:**
1. Verifique se há produtos no carrinho
2. Confirme que valor restante é R$ 0,00
3. Valide que todos os pagamentos foram adicionados

### 7.2 Problemas com Clientes

#### "CPF já cadastrado"
**Causa:** Cliente já existe no sistema
**Solução:**
1. Busque o cliente pelo CPF
2. Edite o cadastro existente se necessário
3. Use o cadastro existente para a venda

#### "CPF inválido"
**Causa:** CPF não tem 11 dígitos ou formato incorreto
**Solução:**
1. Digite apenas números (sem pontos ou traços)
2. Confirme que são exatamente 11 dígitos
3. Valide o CPF com o cliente

#### "Email inválido"
**Causa:** Formato de email incorreto
**Solução:**
1. Verifique se tem @ e domínio
2. Exemplo correto: cliente@email.com
3. Confirme o email com o cliente

### 7.3 Problemas com Relatórios

#### "Nenhuma venda encontrada"
**Causa:** Período selecionado sem vendas ou filtros muito restritivos
**Solução:**
1. Amplie o período de busca
2. Remova filtros aplicados
3. Verifique se há vendas no sistema

#### "Relatório vazio"
**Causa:** Filtros não retornaram resultados
**Solução:**
1. Revise os filtros aplicados
2. Tente sem filtros primeiro
3. Verifique se os dados existem no período

### 7.4 Problemas com Cancelamento

#### "Venda não encontrada"
**Causa:** Número incorreto ou venda não existe
**Solução:**
1. Confirme o número da venda no comprovante
2. Busque por data se não souber o número
3. Verifique se a venda foi realmente finalizada

#### "Venda já cancelada"
**Causa:** Tentativa de cancelar venda já cancelada
**Solução:**
1. Verifique o status da venda
2. Vendas canceladas não podem ser canceladas novamente
3. Consulte o histórico de cancelamentos

#### "Erro ao restaurar estoque"
**Causa:** Problema na integração com sistema de estoque
**Solução:**
1. Tente novamente
2. Verifique conexão com banco de dados
3. Contate o suporte técnico se persistir

### 7.5 Problemas de Conexão

#### "Erro de conexão com banco de dados"
**Causa:** Perda de conexão com Supabase
**Solução:**
1. Verifique sua conexão com internet
2. Aguarde alguns segundos e tente novamente
3. O sistema tentará reconectar automaticamente
4. Contate o administrador se persistir

#### "Sessão expirada"
**Causa:** Tempo de inatividade excedido
**Solução:**
1. Faça login novamente
2. Suas vendas em andamento podem ter sido perdidas
3. Recomece o processo de venda

---

## 📞 Suporte e Contato

### Precisa de Ajuda?

Se você encontrou um problema não listado neste manual ou precisa de assistência adicional:

1. **Consulte a documentação técnica**: `DOCUMENTACAO_TECNICA_VENDAS.md`
2. **Verifique os logs do sistema**: Pasta `logs/`
3. **Entre em contato com o administrador do sistema**

### Feedback

Sua opinião é importante! Se você tem sugestões de melhorias para o sistema ou para este manual, por favor compartilhe com a equipe de desenvolvimento.

---

## 📝 Notas da Versão

**Versão do Manual:** 1.0  
**Data:** Janeiro 2025  
**Sistema:** DEKIDS Moda Infantil - Módulo de Vendas  
**Compatível com:** Sistema de Estoque DEKIDS v2.0+

---

**© 2025 DEKIDS Moda Infantil - Todos os direitos reservados**
