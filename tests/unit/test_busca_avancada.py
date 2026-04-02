"""
Testes unitários para busca avançada de produtos

Feature: sistema-estoque-melhorado
Requisitos: 9.1, 9.2
"""

import pytest
from unittest.mock import Mock, patch
import os

# Configurar variáveis de ambiente antes de importar database
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_KEY'] = 'test-key'

# Mock do supabase antes de importar database
with patch('database.create_client'):
    import database


class TestBuscarProdutosAvancado:
    """Testes para a função buscar_produtos_avancado"""
    
    @patch('database.supabase')
    def test_busca_multi_campo_descricao(self, mock_supabase):
        """Testa busca por termo na descrição (case-insensitive)"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Conjunto Moletom Infantil",
                "marca": "Brandili",
                "referencia": "MOL123",
                "genero": "Masculino",
                "preco": 89.90,
                "quantidade": 10
            },
            {
                "id": 2,
                "descricao": "Camiseta Básica",
                "marca": "Malwee",
                "referencia": "CAM456",
                "genero": "Feminino",
                "preco": 29.90,
                "quantidade": 15
            }
        ]
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({"termo": "moletom"})
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["id"] == 1
        assert "moletom" in resultado[0]["descricao"].lower()
    
    @patch('database.supabase')
    def test_busca_multi_campo_marca(self, mock_supabase):
        """Testa busca por termo na marca (case-insensitive)"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Conjunto Moletom",
                "marca": "Brandili",
                "referencia": "MOL123",
                "genero": "Masculino",
                "preco": 89.90,
                "quantidade": 10
            },
            {
                "id": 2,
                "descricao": "Camiseta Básica",
                "marca": "Malwee",
                "referencia": "CAM456",
                "genero": "Feminino",
                "preco": 29.90,
                "quantidade": 15
            }
        ]
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({"termo": "BRANDILI"})
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["id"] == 1
        assert "brandili" in resultado[0]["marca"].lower()
    
    @patch('database.supabase')
    def test_busca_multi_campo_referencia(self, mock_supabase):
        """Testa busca por termo na referência (case-insensitive)"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Conjunto Moletom",
                "marca": "Brandili",
                "referencia": "MOL123",
                "genero": "Masculino",
                "preco": 89.90,
                "quantidade": 10
            },
            {
                "id": 2,
                "descricao": "Camiseta Básica",
                "marca": "Malwee",
                "referencia": "CAM456",
                "genero": "Feminino",
                "preco": 29.90,
                "quantidade": 15
            }
        ]
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({"termo": "cam456"})
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["id"] == 2
        assert "cam456" in resultado[0]["referencia"].lower()
    
    @patch('database.supabase')
    def test_filtro_por_genero(self, mock_supabase):
        """Testa filtro por gênero"""
        # Arrange
        mock_query = Mock()
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Conjunto Moletom",
                "marca": "Brandili",
                "referencia": "MOL123",
                "genero": "Masculino",
                "preco": 89.90,
                "quantidade": 10
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({"genero": "Masculino"})
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["genero"] == "Masculino"
    
    @patch('database.supabase')
    def test_filtro_por_marca(self, mock_supabase):
        """Testa filtro por marca"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 2,
                "descricao": "Camiseta Básica",
                "marca": "Malwee",
                "referencia": "CAM456",
                "genero": "Feminino",
                "preco": 29.90,
                "quantidade": 15
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({"marca": "Malwee"})
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["marca"] == "Malwee"
    
    @patch('database.supabase')
    def test_filtro_por_faixa_preco(self, mock_supabase):
        """Testa filtro por faixa de preço"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Conjunto Moletom",
                "marca": "Brandili",
                "referencia": "MOL123",
                "genero": "Masculino",
                "preco": 89.90,
                "quantidade": 10
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({
            "preco_min": 50.0,
            "preco_max": 100.0
        })
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["preco"] >= 50.0
        assert resultado[0]["preco"] <= 100.0
    
    @patch('database.supabase')
    def test_filtros_combinados(self, mock_supabase):
        """Testa combinação de múltiplos filtros (AND)"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Conjunto Moletom Infantil",
                "marca": "Brandili",
                "referencia": "MOL123",
                "genero": "Masculino",
                "preco": 89.90,
                "quantidade": 10
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({
            "termo": "moletom",
            "genero": "Masculino",
            "marca": "Brandili",
            "preco_min": 50.0,
            "preco_max": 100.0
        })
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["genero"] == "Masculino"
        assert resultado[0]["marca"] == "Brandili"
        assert resultado[0]["preco"] >= 50.0
        assert resultado[0]["preco"] <= 100.0
        assert "moletom" in resultado[0]["descricao"].lower()
    
    @patch('database.supabase')
    def test_busca_sem_resultados(self, mock_supabase):
        """Testa busca que não retorna resultados"""
        # Arrange
        mock_response = Mock()
        mock_response.data = []
        
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({"termo": "produto_inexistente"})
        
        # Assert
        assert len(resultado) == 0
    
    @patch('database.supabase')
    def test_busca_sem_filtros(self, mock_supabase):
        """Testa busca sem filtros (retorna todos os produtos)"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Produto 1",
                "marca": "Marca A",
                "referencia": "REF1",
                "genero": "Masculino",
                "preco": 50.0,
                "quantidade": 10
            },
            {
                "id": 2,
                "descricao": "Produto 2",
                "marca": "Marca B",
                "referencia": "REF2",
                "genero": "Feminino",
                "preco": 60.0,
                "quantidade": 15
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({})
        
        # Assert
        assert len(resultado) == 2
    
    @patch('database.supabase')
    @patch('database.reconectar_supabase')
    def test_reconexao_em_caso_de_erro(self, mock_reconectar, mock_supabase):
        """Testa reconexão automática em caso de erro de conexão"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Produto 1",
                "marca": "Marca A",
                "referencia": "REF1",
                "genero": "Masculino",
                "preco": 50.0,
                "quantidade": 10
            }
        ]
        
        # Primeira chamada falha, segunda sucede
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.side_effect = [
            Exception("Connection timeout"),
            mock_response
        ]
        mock_reconectar.return_value = True
        
        # Act
        resultado = database.buscar_produtos_avancado({})
        
        # Assert
        assert len(resultado) == 1
        mock_reconectar.assert_called_once()

    @patch('database.supabase')
    def test_ordenacao_por_nome_ascendente(self, mock_supabase):
        """Testa ordenação por nome (descrição) em ordem ascendente"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 3,
                "descricao": "Zebra Conjunto",
                "marca": "Marca C",
                "referencia": "REF3",
                "preco": 70.0,
                "quantidade": 5
            },
            {
                "id": 1,
                "descricao": "Abacaxi Camiseta",
                "marca": "Marca A",
                "referencia": "REF1",
                "preco": 50.0,
                "quantidade": 10
            },
            {
                "id": 2,
                "descricao": "Banana Shorts",
                "marca": "Marca B",
                "referencia": "REF2",
                "preco": 60.0,
                "quantidade": 15
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({
            "order_by": "nome",
            "order_direction": "asc"
        })
        
        # Assert
        assert len(resultado) == 3
        assert resultado[0]["descricao"] == "Abacaxi Camiseta"
        assert resultado[1]["descricao"] == "Banana Shorts"
        assert resultado[2]["descricao"] == "Zebra Conjunto"
    
    @patch('database.supabase')
    def test_ordenacao_por_nome_descendente(self, mock_supabase):
        """Testa ordenação por nome (descrição) em ordem descendente"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Abacaxi Camiseta",
                "marca": "Marca A",
                "referencia": "REF1",
                "preco": 50.0,
                "quantidade": 10
            },
            {
                "id": 2,
                "descricao": "Banana Shorts",
                "marca": "Marca B",
                "referencia": "REF2",
                "preco": 60.0,
                "quantidade": 15
            },
            {
                "id": 3,
                "descricao": "Zebra Conjunto",
                "marca": "Marca C",
                "referencia": "REF3",
                "preco": 70.0,
                "quantidade": 5
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({
            "order_by": "nome",
            "order_direction": "desc"
        })
        
        # Assert
        assert len(resultado) == 3
        assert resultado[0]["descricao"] == "Zebra Conjunto"
        assert resultado[1]["descricao"] == "Banana Shorts"
        assert resultado[2]["descricao"] == "Abacaxi Camiseta"
    
    @patch('database.supabase')
    def test_ordenacao_por_preco_ascendente(self, mock_supabase):
        """Testa ordenação por preço em ordem ascendente"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 3,
                "descricao": "Produto C",
                "marca": "Marca C",
                "referencia": "REF3",
                "preco": 90.0,
                "quantidade": 5
            },
            {
                "id": 1,
                "descricao": "Produto A",
                "marca": "Marca A",
                "referencia": "REF1",
                "preco": 30.0,
                "quantidade": 10
            },
            {
                "id": 2,
                "descricao": "Produto B",
                "marca": "Marca B",
                "referencia": "REF2",
                "preco": 60.0,
                "quantidade": 15
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({
            "order_by": "preco",
            "order_direction": "asc"
        })
        
        # Assert
        assert len(resultado) == 3
        assert resultado[0]["preco"] == 30.0
        assert resultado[1]["preco"] == 60.0
        assert resultado[2]["preco"] == 90.0
    
    @patch('database.supabase')
    def test_ordenacao_por_preco_descendente(self, mock_supabase):
        """Testa ordenação por preço em ordem descendente"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Produto A",
                "marca": "Marca A",
                "referencia": "REF1",
                "preco": 30.0,
                "quantidade": 10
            },
            {
                "id": 2,
                "descricao": "Produto B",
                "marca": "Marca B",
                "referencia": "REF2",
                "preco": 60.0,
                "quantidade": 15
            },
            {
                "id": 3,
                "descricao": "Produto C",
                "marca": "Marca C",
                "referencia": "REF3",
                "preco": 90.0,
                "quantidade": 5
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({
            "order_by": "preco",
            "order_direction": "desc"
        })
        
        # Assert
        assert len(resultado) == 3
        assert resultado[0]["preco"] == 90.0
        assert resultado[1]["preco"] == 60.0
        assert resultado[2]["preco"] == 30.0
    
    @patch('database.supabase')
    def test_ordenacao_por_quantidade_ascendente(self, mock_supabase):
        """Testa ordenação por quantidade em ordem ascendente"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 2,
                "descricao": "Produto B",
                "marca": "Marca B",
                "referencia": "REF2",
                "preco": 60.0,
                "quantidade": 20
            },
            {
                "id": 1,
                "descricao": "Produto A",
                "marca": "Marca A",
                "referencia": "REF1",
                "preco": 30.0,
                "quantidade": 5
            },
            {
                "id": 3,
                "descricao": "Produto C",
                "marca": "Marca C",
                "referencia": "REF3",
                "preco": 90.0,
                "quantidade": 15
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({
            "order_by": "quantidade",
            "order_direction": "asc"
        })
        
        # Assert
        assert len(resultado) == 3
        assert resultado[0]["quantidade"] == 5
        assert resultado[1]["quantidade"] == 15
        assert resultado[2]["quantidade"] == 20
    
    @patch('database.supabase')
    def test_ordenacao_por_quantidade_descendente(self, mock_supabase):
        """Testa ordenação por quantidade em ordem descendente"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Produto A",
                "marca": "Marca A",
                "referencia": "REF1",
                "preco": 30.0,
                "quantidade": 5
            },
            {
                "id": 3,
                "descricao": "Produto C",
                "marca": "Marca C",
                "referencia": "REF3",
                "preco": 90.0,
                "quantidade": 15
            },
            {
                "id": 2,
                "descricao": "Produto B",
                "marca": "Marca B",
                "referencia": "REF2",
                "preco": 60.0,
                "quantidade": 20
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({
            "order_by": "quantidade",
            "order_direction": "desc"
        })
        
        # Assert
        assert len(resultado) == 3
        assert resultado[0]["quantidade"] == 20
        assert resultado[1]["quantidade"] == 15
        assert resultado[2]["quantidade"] == 5
    
    @patch('database.supabase')
    def test_ordenacao_com_filtros_combinados(self, mock_supabase):
        """Testa ordenação combinada com filtros"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Conjunto Moletom A",
                "marca": "Brandili",
                "referencia": "MOL1",
                "genero": "Masculino",
                "preco": 89.90,
                "quantidade": 10
            },
            {
                "id": 2,
                "descricao": "Conjunto Moletom B",
                "marca": "Brandili",
                "referencia": "MOL2",
                "genero": "Masculino",
                "preco": 79.90,
                "quantidade": 15
            },
            {
                "id": 3,
                "descricao": "Conjunto Moletom C",
                "marca": "Brandili",
                "referencia": "MOL3",
                "genero": "Masculino",
                "preco": 99.90,
                "quantidade": 5
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_response
        
        # Act
        resultado = database.buscar_produtos_avancado({
            "termo": "moletom",
            "genero": "Masculino",
            "marca": "Brandili",
            "order_by": "preco",
            "order_direction": "asc"
        })
        
        # Assert
        assert len(resultado) == 3
        assert resultado[0]["preco"] == 79.90
        assert resultado[1]["preco"] == 89.90
        assert resultado[2]["preco"] == 99.90
    
    @patch('database.supabase')
    def test_ordenacao_padrao_ascendente(self, mock_supabase):
        """Testa que a ordenação padrão é ascendente quando não especificada"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 2,
                "descricao": "Produto B",
                "marca": "Marca B",
                "referencia": "REF2",
                "preco": 60.0,
                "quantidade": 15
            },
            {
                "id": 1,
                "descricao": "Produto A",
                "marca": "Marca A",
                "referencia": "REF1",
                "preco": 30.0,
                "quantidade": 10
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        # Act - não especificar order_direction
        resultado = database.buscar_produtos_avancado({
            "order_by": "preco"
        })
        
        # Assert
        assert len(resultado) == 2
        assert resultado[0]["preco"] == 30.0
        assert resultado[1]["preco"] == 60.0



class TestCalcularDistanciaLevenshtein:
    """Testes para a função calcular_distancia_levenshtein"""
    
    def test_strings_identicas(self):
        """Testa distância entre strings idênticas (deve ser 0)"""
        # Act
        distancia = database.calcular_distancia_levenshtein("moletom", "moletom")
        
        # Assert
        assert distancia == 0
    
    def test_strings_identicas_case_insensitive(self):
        """Testa que a comparação é case-insensitive"""
        # Act
        distancia = database.calcular_distancia_levenshtein("Moletom", "MOLETOM")
        
        # Assert
        assert distancia == 0
    
    def test_uma_string_vazia(self):
        """Testa distância quando uma string é vazia"""
        # Act
        distancia1 = database.calcular_distancia_levenshtein("", "moletom")
        distancia2 = database.calcular_distancia_levenshtein("moletom", "")
        
        # Assert
        assert distancia1 == 7  # tamanho de "moletom"
        assert distancia2 == 7
    
    def test_uma_substituicao(self):
        """Testa distância com uma substituição"""
        # Act
        distancia = database.calcular_distancia_levenshtein("moletom", "moleton")
        
        # Assert
        assert distancia == 1  # substituir 'm' por 'n'
    
    def test_uma_insercao(self):
        """Testa distância com uma inserção"""
        # Act
        distancia = database.calcular_distancia_levenshtein("moletom", "moletoms")
        
        # Assert
        assert distancia == 1  # inserir 's' no final
    
    def test_uma_delecao(self):
        """Testa distância com uma deleção"""
        # Act
        distancia = database.calcular_distancia_levenshtein("moletom", "moleto")
        
        # Assert
        assert distancia == 1  # deletar 'm' do final
    
    def test_multiplas_operacoes(self):
        """Testa distância com múltiplas operações"""
        # Act
        distancia = database.calcular_distancia_levenshtein("kitten", "sitting")
        
        # Assert
        assert distancia == 3  # k->s, e->i, inserir g
    
    def test_strings_completamente_diferentes(self):
        """Testa distância entre strings completamente diferentes"""
        # Act
        distancia = database.calcular_distancia_levenshtein("abc", "xyz")
        
        # Assert
        assert distancia == 3  # 3 substituições


class TestGerarSugestoes:
    """Testes para a função gerar_sugestoes"""
    
    @patch('database.supabase')
    def test_gerar_sugestoes_basico(self, mock_supabase):
        """Testa geração de sugestões básicas"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "descricao": "Conjunto Moletom Infantil",
                "marca": "Brandili",
                "referencia": "MOL123"
            },
            {
                "descricao": "Camiseta Básica",
                "marca": "Malwee",
                "referencia": "CAM456"
            },
            {
                "descricao": "Shorts Jeans",
                "marca": "Hering",
                "referencia": "SHO789"
            }
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        sugestoes = database.gerar_sugestoes("moleton")
        
        # Assert
        assert len(sugestoes) > 0
        # "moletom" deve estar entre as sugestões (distância 1 de "moleton")
        assert any("moletom" in s.lower() for s in sugestoes)
    
    @patch('database.supabase')
    def test_gerar_sugestoes_retorna_top_5(self, mock_supabase):
        """Testa que retorna no máximo 5 sugestões"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {"descricao": f"Produto {i}", "marca": f"Marca {i}", "referencia": f"REF{i}"}
            for i in range(20)
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        sugestoes = database.gerar_sugestoes("produto")
        
        # Assert
        assert len(sugestoes) <= 5
    
    @patch('database.supabase')
    def test_gerar_sugestoes_ordenadas_por_similaridade(self, mock_supabase):
        """Testa que sugestões são ordenadas por similaridade (menor distância primeiro)"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "descricao": "Moletom",  # distância 1 de "moleton"
                "marca": "Brandili",
                "referencia": "MOL1"
            },
            {
                "descricao": "Camiseta",  # distância maior de "moleton"
                "marca": "Malwee",
                "referencia": "CAM1"
            },
            {
                "descricao": "Moleto",  # distância 1 de "moleton"
                "marca": "Hering",
                "referencia": "MOL2"
            }
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        sugestoes = database.gerar_sugestoes("moleton")
        
        # Assert
        assert len(sugestoes) > 0
        # Primeiras sugestões devem ser mais similares
        # "moletom" e "moleto" têm distância 1, "camiseta" tem distância maior
        primeiras_duas = sugestoes[:2]
        assert any("moletom" in s.lower() or "moleto" in s.lower() for s in primeiras_duas)
    
    @patch('database.supabase')
    def test_gerar_sugestoes_sem_produtos(self, mock_supabase):
        """Testa geração de sugestões quando não há produtos"""
        # Arrange
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        sugestoes = database.gerar_sugestoes("moleton")
        
        # Assert
        assert len(sugestoes) == 0
    
    @patch('database.supabase')
    def test_gerar_sugestoes_exclui_termo_busca(self, mock_supabase):
        """Testa que o próprio termo de busca não é incluído nas sugestões"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "descricao": "Moletom",
                "marca": "Brandili",
                "referencia": "MOL123"
            }
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        sugestoes = database.gerar_sugestoes("moletom")
        
        # Assert
        # "moletom" exato não deve estar nas sugestões (case-insensitive)
        assert "moletom" not in [s.lower() for s in sugestoes]
    
    @patch('database.supabase')
    def test_gerar_sugestoes_inclui_palavras_individuais(self, mock_supabase):
        """Testa que palavras individuais da descrição são incluídas"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "descricao": "Conjunto Moletom Infantil Premium",
                "marca": "Brandili",
                "referencia": "MOL123"
            }
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        sugestoes = database.gerar_sugestoes("conjuto")  # erro de digitação
        
        # Assert
        assert len(sugestoes) > 0
        # "conjunto" deve estar nas sugestões (distância 1 de "conjuto")
        assert any("conjunto" in s.lower() for s in sugestoes)
    
    @patch('database.supabase')
    def test_gerar_sugestoes_ignora_palavras_curtas(self, mock_supabase):
        """Testa que palavras com menos de 3 caracteres são ignoradas"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "descricao": "Conjunto de Moletom",  # "de" tem 2 caracteres
                "marca": "Brandili",
                "referencia": "MOL123"
            }
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        sugestoes = database.gerar_sugestoes("moleton")
        
        # Assert
        # "de" não deve estar nas sugestões
        assert "de" not in sugestoes
    
    @patch('database.supabase')
    def test_gerar_sugestoes_inclui_marcas(self, mock_supabase):
        """Testa que marcas são incluídas nas sugestões"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "descricao": "Conjunto Moletom",
                "marca": "Brandili",
                "referencia": "MOL123"
            }
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        sugestoes = database.gerar_sugestoes("brandilli")  # erro de digitação
        
        # Assert
        assert len(sugestoes) > 0
        # "Brandili" deve estar nas sugestões
        assert any("brandili" in s.lower() for s in sugestoes)
    
    @patch('database.supabase')
    def test_gerar_sugestoes_inclui_referencias(self, mock_supabase):
        """Testa que referências são incluídas nas sugestões"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "descricao": "Conjunto Moletom",
                "marca": "Brandili",
                "referencia": "MOL123"
            }
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        sugestoes = database.gerar_sugestoes("MOL124")  # referência similar
        
        # Assert
        assert len(sugestoes) > 0
        # "MOL123" deve estar nas sugestões
        assert any("mol123" in s.lower() for s in sugestoes)
    
    @patch('database.supabase')
    def test_gerar_sugestoes_max_sugestoes_customizado(self, mock_supabase):
        """Testa parâmetro max_sugestoes customizado"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {"descricao": f"Produto {i}", "marca": f"Marca {i}", "referencia": f"REF{i}"}
            for i in range(20)
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        sugestoes = database.gerar_sugestoes("produto", max_sugestoes=3)
        
        # Assert
        assert len(sugestoes) <= 3
    
    @patch('database.supabase')
    @patch('database.reconectar_supabase')
    def test_gerar_sugestoes_reconexao_em_erro(self, mock_reconectar, mock_supabase):
        """Testa reconexão automática em caso de erro de conexão"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "descricao": "Conjunto Moletom",
                "marca": "Brandili",
                "referencia": "MOL123"
            }
        ]
        
        # Primeira chamada falha, segunda sucede
        mock_supabase.table.return_value.select.return_value.execute.side_effect = [
            Exception("Connection timeout"),
            mock_response
        ]
        mock_reconectar.return_value = True
        
        # Act
        sugestoes = database.gerar_sugestoes("moleton")
        
        # Assert
        assert len(sugestoes) > 0
        mock_reconectar.assert_called_once()
    
    @patch('database.supabase')
    def test_gerar_sugestoes_erro_retorna_lista_vazia(self, mock_supabase):
        """Testa que erro retorna lista vazia"""
        # Arrange
        mock_supabase.table.return_value.select.return_value.execute.side_effect = Exception("Database error")
        
        # Act
        sugestoes = database.gerar_sugestoes("moleton")
        
        # Assert
        assert sugestoes == []
