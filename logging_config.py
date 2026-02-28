"""
Módulo de configuração de logging estruturado para o Sistema de Estoque DEKIDS.

Este módulo fornece funcionalidades de logging com formato JSON estruturado,
incluindo timestamp, nível, módulo, função, mensagem, detalhes e user_id.
Implementa rotação automática de arquivos de log.
"""

import logging
import json
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """
    Formatter customizado que gera logs em formato JSON estruturado.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o registro de log em JSON estruturado.
        
        Args:
            record: Registro de log a ser formatado
            
        Returns:
            String JSON com os dados estruturados do log
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        
        # Adicionar detalhes extras se fornecidos
        if hasattr(record, 'details'):
            log_data["details"] = record.details
        
        # Adicionar user_id se fornecido
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        
        # Adicionar informações de exceção se houver
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def configurar_logging(
    log_dir: str = "logs",
    log_file: str = "estoque.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configura o sistema de logging com rotação de arquivos.
    
    Args:
        log_dir: Diretório onde os logs serão armazenados
        log_file: Nome do arquivo de log
        max_bytes: Tamanho máximo do arquivo antes de rotacionar (padrão: 10MB)
        backup_count: Número de arquivos de backup a manter (padrão: 5)
        level: Nível mínimo de log (padrão: INFO)
        
    Returns:
        Logger configurado
    """
    # Criar diretório de logs se não existir
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Criar logger
    logger = logging.getLogger("estoque")
    logger.setLevel(level)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Configurar handler com rotação de arquivos
    file_handler = RotatingFileHandler(
        filename=log_path / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(StructuredFormatter())
    
    # Adicionar handler ao logger
    logger.addHandler(file_handler)
    
    # Adicionar handler para console (opcional, para desenvolvimento)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Apenas warnings e erros no console
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)
    
    return logger


def registrar_erro(
    mensagem: str,
    modulo: str,
    funcao: str,
    detalhes: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    exc_info: bool = False
) -> None:
    """
    Registra um erro no sistema de logging.
    
    Args:
        mensagem: Mensagem descritiva do erro
        modulo: Nome do módulo onde o erro ocorreu
        funcao: Nome da função onde o erro ocorreu
        detalhes: Dicionário com informações adicionais sobre o erro
        user_id: ID do usuário relacionado ao erro (se aplicável)
        exc_info: Se True, inclui informações de exceção do contexto atual
    """
    logger = logging.getLogger("estoque")
    
    # Criar um LogRecord customizado
    extra = {}
    if detalhes:
        extra['details'] = detalhes
    if user_id:
        extra['user_id'] = user_id
    
    logger.error(mensagem, extra=extra, exc_info=exc_info)


def registrar_aviso(
    mensagem: str,
    modulo: str,
    funcao: str,
    detalhes: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None
) -> None:
    """
    Registra um aviso no sistema de logging.
    
    Args:
        mensagem: Mensagem descritiva do aviso
        modulo: Nome do módulo onde o aviso foi gerado
        funcao: Nome da função onde o aviso foi gerado
        detalhes: Dicionário com informações adicionais
        user_id: ID do usuário relacionado ao aviso (se aplicável)
    """
    logger = logging.getLogger("estoque")
    
    extra = {}
    if detalhes:
        extra['details'] = detalhes
    if user_id:
        extra['user_id'] = user_id
    
    logger.warning(mensagem, extra=extra)


def registrar_info(
    mensagem: str,
    modulo: str,
    funcao: str,
    detalhes: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None
) -> None:
    """
    Registra uma informação no sistema de logging.
    
    Args:
        mensagem: Mensagem informativa
        modulo: Nome do módulo
        funcao: Nome da função
        detalhes: Dicionário com informações adicionais
        user_id: ID do usuário relacionado (se aplicável)
    """
    logger = logging.getLogger("estoque")
    
    extra = {}
    if detalhes:
        extra['details'] = detalhes
    if user_id:
        extra['user_id'] = user_id
    
    logger.info(mensagem, extra=extra)


# Inicializar logger ao importar o módulo
_logger = configurar_logging()
