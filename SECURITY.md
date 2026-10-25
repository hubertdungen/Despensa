# Segurança

Não publique palavras-passe, tokens, bases de dados ou moradas numa issue. Para comunicar uma vulnerabilidade, use a área **Security → Report a vulnerability** do GitHub, se disponível, ou contacte o mantenedor através do perfil público antes de partilhar detalhes exploráveis.

A versão 0.1 suporta uma única instância por base de dados. Use HTTPS fora de localhost, mantenha backups consistentes e feche novos registos quando não forem necessários. Não use `flask run` como servidor de produção: `python app.py` usa Waitress. Atualizações de dependências e o teste de isolamento entre contas fazem parte da manutenção.
