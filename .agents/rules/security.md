# Diretrizes de Segurança

## Políticas Obrigatórias
1. **Gestão de Segredos e Credenciais**:
   - **NUNCA** commitar senhas, chaves de API, certificados ou tokens no repositório.
   - Utilize arquivos de ambiente (`.env`) e mantenha-os explicitamente no `.gitignore`.
   - Utilize `.env.example` para documentar as variáveis necessárias sem valores reais.

2. **Validação e Sanitização de Entradas**:
   - Tratar todas as entradas de usuários ou sistemas externos como não confiáveis.
   - Utilizar validações de esquema rigorosas.
   - Proteger contra injeções (SQL Injection, XSS, Command Injection).

3. **Gerenciamento de Dependências**:
   - Bloquear versões no gerenciador de pacotes (lockfiles).
   - Executar varreduras periódicas de vulnerabilidades em dependências.
   - Não adicionar dependências não verificadas ou de fontes desconhecidas.
