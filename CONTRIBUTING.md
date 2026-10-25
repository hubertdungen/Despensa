# Contribuir para a Despensa

Aceitamos issues e pull requests em português ou espanhol. Antes de propor um conector, descreva a fonte, cobertura por loja/região, condições de acesso, permissões e limitações. Não acrescente preços fictícios ao catálogo real.

1. Crie um fork e uma branch.
2. Instale `requirements-dev.txt` num ambiente virtual Python 3.12+.
3. Execute `python -m pytest -q` e `node --check static/app.js`.
4. Para alterações visuais, verifique computador e telemóvel, teclado, contraste, estados vazios e falhas de rede.
5. Inclua evidência da origem e um teste de parsing pequeno e sintético. Não copie páginas inteiras nem dados pessoais para os testes.

## Princípios

- Nunca mostrar uma fonte antiga como preço em tempo real.
- Nunca apresentar um cabaz incompleto como se estivesse completo.
- Distinguir desconto imediato, acesso condicionado e saldo futuro.
- Não adivinhar IVA, conteúdo da embalagem, validade ou equivalência.
- Respeitar bloqueios e regras de acesso; não introduzir evasão de autenticação ou CAPTCHA.
- Manter as traduções PT-PT e es-ES em conjunto.
- Sem telemetria ou serviços pagos obrigatórios.

O projeto usa AGPL-3.0-or-later. As contribuições devem ser compatíveis com essa licença. Fotografias, marcas e bases de dados de terceiros conservam as respetivas condições.
