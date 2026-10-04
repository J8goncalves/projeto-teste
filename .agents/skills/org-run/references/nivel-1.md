# Fluxo Nível 1

- INTAKE.
- PLANNING reduzido (o `developer` e o `qa` leem o pedido; `product-manager` entra apenas se os critérios estiverem ambíguos).
- BUILD (fatia pequena, branch isolada, prática de TDD, checks locais).
- VERIFY (`qa` automatizado; `security-reviewer` atua apenas se houver flag de sensibilidade de segurança; scanners rodam no CI).
- Gate 3 (decisão/aprovação pelo humano).
- Gate 4 (caso haja release para o usuário final).
- LEARN rápido (no máximo 1 memória destilada e registrada).

Sem Discovery, sem memo de decisão e sem participação do CEO.
