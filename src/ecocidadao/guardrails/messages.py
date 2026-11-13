from __future__ import annotations

SCOPE_REFUSAL = (
    "Posso ajudar apenas com descarte de resíduos, reciclagem, "
    "sustentabilidade municipal e Ecopontos de EcoCidade. Para outros "
    "assuntos, procure o canal municipal adequado."
)

PROMPT_INJECTION_REFUSAL = (
    "Não posso seguir instruções que tentem alterar meu funcionamento, "
    "ignorar as regras de segurança, revelar configurações internas ou "
    "modificar o contexto documental. Posso ajudar com dúvidas sobre "
    "descarte e Ecopontos de EcoCidade."
)

LGPD_REFUSAL = (
    "Não posso fornecer, solicitar ou confirmar dados pessoais de "
    "terceiros. Para tratar de dados pessoais, procure o canal oficial "
    "da Prefeitura de EcoCidade."
)

INSUFFICIENT_CONTEXT_ANSWER = (
    "Não encontrei informações suficientes na base documental para "
    "responder com segurança. Para orientações adicionais, procure a "
    "Secretaria Municipal de Meio Ambiente de EcoCidade ou o Ecoponto "
    "mais próximo."
)

OUTPUT_FALLBACK_ANSWER = INSUFFICIENT_CONTEXT_ANSWER

PERSONAL_DATA_REDACTION = "[dado pessoal removido]"
REMOVED_INSTRUCTION = (
    "[conteúdo instrucional não confiável removido por segurança]"
)

__all__ = [
    "INSUFFICIENT_CONTEXT_ANSWER",
    "LGPD_REFUSAL",
    "OUTPUT_FALLBACK_ANSWER",
    "PERSONAL_DATA_REDACTION",
    "PROMPT_INJECTION_REFUSAL",
    "REMOVED_INSTRUCTION",
    "SCOPE_REFUSAL",
]
