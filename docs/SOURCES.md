# Fontes, cobertura e metodologia

## Conectores ativos na versão 0.1

| Loja | País | Páginas observadas | Limite |
|---|---|---|---|
| Continente | PT | Arroz, massa, leites, azeite, ovos | Primeira página, até 36 referências por categoria |
| Auchan | PT | Arroz, azeite | Primeira página, até 36 referências por categoria |

As URLs exatas estão em `catalog.py:CATEGORY_SOURCES`. Cada recolha volta a consultar `robots.txt` no máximo a cada seis horas, verifica a permissão para a página e faz um pedido por categoria com uma pausa de dois segundos. Há identificação do robot, timeouts e limites; falhas não apagam a última observação. Não há paginação massiva, navegação autenticada, cookies de contas das lojas, proxies rotativos ou resolução de CAPTCHA.

O resultado é uma observação do catálogo público online **sem localização específica confirmada**. Não comprova stock nem preço numa loja física. Não implica uma parceria, API oficial ou autorização para redistribuição irrestrita de conteúdos. O repositório distribui o software, não uma base de dados comercial das lojas. Os termos de utilização e condições de acesso podem mudar: cada instalação deve verificar a adequação das fontes ao seu uso.

No teste inicial, o Intermarché devolveu 403. A API da Mercadona e a pesquisa interna do Continente restringem robots e não são utilizadas pela aplicação. A resposta inicial de diagnóstico não é usada como um feed. Não existe conector automático espanhol ativo.

## O que é guardado

- ID composto pela loja e referência, nome e marca publicados.
- Preço exibido em cêntimos de euro, privilegiando o preço visível sobre metadados analíticos.
- Quantidade e unidade quando o formato é explícito; formatos ambíguos ficam sem normalização e fora do planeador.
- URL da fonte, loja, país, canal, momento da observação e localização por confirmar.
- Condições reconhecidas ou indicação de que precisam de confirmação. Deteção de condições é conservadora, mas não substitui a consulta da fonte.

Não são copiadas fotografias, descrições longas, dados de login ou números de cartões. Referências indisponíveis ou mudanças no catálogo não podem ser confirmadas em tempo real: cada recomendação deve ser verificada na loja.

## Correspondência e custo

Regras conservadoras excluem algumas substituições de famílias de produto, como ovos de codorniz para uma pesquisa genérica de ovos ou farinha para uma pesquisa de arroz. Uma pesquisa explícita pode incluir essas variantes. Estas regras não garantem equivalência. As palavras da pesquisa têm de existir no nome da oferta após normalização de acentos e maiúsculas. Não há correspondência semântica por IA nem certificação de equivalência. Pode fixar uma referência específica a partir do catálogo. Para quantidades em kg/l/un, o custo é `ceil(quantidade necessária / conteúdo da embalagem) × preço da embalagem`, sem dividir embalagens nem assumir que uma embalagem de menor preço unitário é a compra mais barata.

Só entram lojas ativas e países selecionados no perfil, requisitos de acesso satisfeitos, preços com IVA, observações até 72 horas e validade compatível. Para datas futuras é exigida validade explícita. Preços apenas públicos não se tornam automaticamente preços válidos de uma promoção futura. Condições desconhecidas são excluídas. O saldo futuro não reduz o pagamento atual.

Os planos são ordenados primeiro pela cobertura, depois pelo custo observado e número de paragens. Um total com distância desconhecida é apenas um subtotal de produtos. Não compare como custo final dois planos em que só um inclui deslocações. A interface deve mostrar essa limitação; nenhum preço ausente é zero.

Preços manuais pertencem à conta que os criou. O utilizador indica local, IVA, validade e condições. Não há auditoria independente dos talões nem integração automática com cupões privados. Compras mínimas, promoções “leve/pague”, escalões e combinações de cupões ficam fora do motor inicial.

## Localizações e percursos

Geocodificação: [Nominatim](https://operations.osmfoundation.org/policies/nominatim/), só quando o utilizador carrega em Localizar, sem autocomplete. Identificação do cliente, cache e limite global de uma consulta por segundo por processo. A instância é pequena e pessoal; instalações públicas com utilização elevada devem contratar ou alojar um serviço apropriado.

Distâncias: [OSRM Table API](https://project-osrm.org/docs/v5.24.0/api/#table-service), com uma matriz para as localizações necessárias, até oito lojas com coordenadas. A escolha de até três paragens considera a assimetria dos trajetos. O desvio é a distância do percurso com compras menos o percurso base (casa→casa ou trabalho→casa). As coordenadas são enviadas ao serviço externo; resultados ficam em cache durante seis horas. Não há trânsito em tempo real. Se o serviço falhar, a app pode usar os desvios manuais, explicitamente identificados.

Dados geográficos: [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright). Não existem garantias de disponibilidade dos endpoints públicos.
