# Fontes, cobertura e metodologia

## Radar automático ibérico (0.3)

A investigação é automática para os produtos da lista e as palavras pesquisadas. A pesquisa considera nomes, marcas, formatos, plurais, prefixos e grafias próximas quando não há correspondência exata. Portugal/Espanha são selecionáveis na pesquisa. Os grupos completos são calculados antes de paginar, sem limitar a comparação aos primeiros 300 preços.

As pesquisas interativas têm uma fila persistente própria, processada por dois workers independentes da recolha geral, até seis páginas relevantes por loja. Uma pesquisa nova pode consultar páginas de produto ainda não visitadas mesmo durante a espera normal da recolha geral. Respeita os bloqueios e intervalos de espera de fontes que falharam. Os pedidos das três tarefas partilham o limite de dois segundos por domínio. O navegador consulta o progresso a cada três segundos, apenas enquanto há pesquisa pendente e a vista está aberta. `research.py` contém o registo de fontes, os métodos alternativos e a fila persistente; `catalog.py` mantém os formatos e conectores específicos. Há fontes configuradas para as principais cadeias portuguesas e espanholas, incluindo lojas profissionais. O estado de cada fonte aparece no radar: programada, a investigar, com preços, a descobrir páginas, parcialmente disponível ou com nova tentativa prevista.

Uma passagem não equivale a recolher uma loja inteira. O orçamento inicial é de 12 páginas por cadeia por passagem, no máximo duas de mapas do site. As páginas ainda não visitadas ficam na base de dados. A prioridade reconhece palavras portuguesas/espanholas e reparte as consultas pelos produtos pedidos; não favorece para sempre um único termo. A descoberta continua entre atualizações de preços. O limite de segurança da fila é de 200 mil URLs por cadeia.

### Métodos complementares

1. Leitura do preço apresentado nas páginas de categoria, quando existe um formato identificado (Continente, Auchan e Pingo Doce).
2. JSON-LD `Product/Offer` publicado pela própria loja em páginas de produto.
3. Dados de catálogo embebidos na página, incluindo o catálogo ALDI em Next.js: preço, formato, datas e disponibilidade.
4. Microdados de produto quando o JSON-LD falta ou não pode ser interpretado.
5. Mapas oficiais do site e ligações públicas para descobrir outras páginas de produto/categoria. Este método descobre URLs; não transforma uma URL num preço.
6. No Pingo Doce, JSON-LD para identificar o produto e o preço visível dentro do bloco desse produto. O valor do minicarrinho não é usado.

Os métodos de leitura são independentes. Um JSON inválido não impede os outros leitores; uma página de categoria alterada pode ser substituída por uma página de produto descoberta no mapa. Uma fonte totalmente inacessível não é apresentada como coberta.

O robot identifica-se, aplica pausas de pelo menos dois segundos por domínio, limites de tamanho, timeouts e cache. Consulta `robots.txt` antes da recolha e não contorna autenticação, CAPTCHAs ou restrições de acesso. Os redirecionamentos de investigação estão limitados ao mesmo retalhista. Falhas preservam observações anteriores e têm espera progressiva: 15 min, 30 min, 1 h, até 24 h. A fila e o estado sobrevivem a reinícios.

### Validação real e limites

Na validação da versão 0.2 foram extraídos preços reais de **Continente, Auchan, Pingo Doce, Lidl PT, ALDI PT/ES, DIA e Lidl ES**, através de métodos diferentes. A resposta de uma fonte pode mudar entre tentativas. Algumas fontes devolveram HTTP 403, verificação de acesso, mapas sem preço ou páginas sem preço legível; essas tentativas ficam identificadas e são repetidas com espera. Mercadona PT/ES, Intermarché, Makro, Recheio, Carrefour, Alcampo e Eroski têm mecanismos de descoberta/investigação configurados, mas isso não constitui garantia de preços disponíveis.

Não se promete o preço mais baixo de todo o mercado nem o catálogo integral de todas as lojas. Também não se transforma uma falha automática na obrigação de introduzir preços manualmente: o radar continua a investigar. O registo manual é uma opção adicional para preços observados fisicamente.

## Observações e imagens

Guardamos referência, nome/marca, preço em cêntimos, formato/unidade quando explícitos, fonte, país, canal, condição, validade e momento da observação. As fotografias publicadas pelas lojas podem aparecer através de um proxy com uma lista fixa de domínios/caminhos, limite de 2 MB por imagem, tipos de imagem permitidos e cache em memória de até 16 MB. O navegador não recebe cookies das lojas nem lhes envia os seus próprios cookies. O endpoint não aceita URLs arbitrárias. Os direitos das fotografias e marcas pertencem aos titulares; o código não concede direitos sobre esses conteúdos.

O repositório distribui software, não uma base de dados comercial das lojas. Preços publicados podem variar por região, disponibilidade e localização. Uma observação não confirma stock numa loja concreta. A aplicação não recolhe credenciais de supermercados ou números de cartões.

## Correspondência e custo

As sugestões reconhecem famílias conservadoras. Leite magro, meio gordo, sem lactose, fresco e biológico são separados quando a informação está presente. Palavras frequentes são normalizadas entre português e espanhol. Famílias não reconhecidas podem ser agrupadas por EAN/GTIN com dígito de controlo válido, unidade e conteúdo da embalagem iguais. Sem essa informação ficam como referências individuais. Não há certificação de equivalência nutricional ou de qualidade entre marcas.

Uma referência específica pode ser fixada. Uma lista genérica procura alternativas pelas palavras/família escolhidas. Para kg/l/un, o custo é `ceil(quantidade / conteúdo da embalagem) × preço da embalagem`: uma unidade mais barata não implica necessariamente um cabaz mais barato. O histórico guarda preços observados, sem inventar preços anteriores.

Só entram no plano lojas/países ativos, acesso profissional satisfeito, IVA incluído, observações com até 72 h e validade compatível com a data. Para datas futuras é exigida validade explícita. Condições desconhecidas ficam fora da otimização. Cartão não equivale a cupão. EntregaZero é uma subscrição de entregas e não desbloqueia automaticamente descontos em produtos. Saldo futuro não reduz o pagamento de hoje. Promoções por combinações ou valor mínimo não são presumidas elegíveis.

## Lojas próximas e percursos

A descoberta consulta separadamente as zonas de **casa e trabalho**. Localizadores oficiais de [Continente](https://feed.continente.pt/lojas) e [Auchan](https://www.auchan.pt/pt/lojas) dão coordenadas verificáveis; [Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API) alarga a pesquisa às outras cadeias em Portugal e Espanha. A ausência de resposta do serviço de mapas não elimina as lojas dos localizadores oficiais. A cobertura parcial é assinalada.

A zona inicial tem raio de 6 km por origem. Preservam-se até 12 candidatos de cada zona (24 no conjunto), calculando distâncias rodoviárias e o desvio trabalho→loja→casa. Cada cadeia pode fornecer até três filiais candidatas ao planeador, que considera até três paragens e a assimetria das estradas.

Geocodificação: [Nominatim](https://operations.osmfoundation.org/policies/nominatim/), ao guardar zonas ou carregar em Localizar, sem autocomplete, com cache e máximo uma consulta por segundo. Se houver ambiguidade, o utilizador escolhe o resultado. Distâncias: [OSRM](https://project-osrm.org/docs/v5.24.0/api/#table-service), cache de seis horas. Descoberta: cache de 24 h; falhas sem resultados têm espera de cinco minutos. Operadores podem configurar os próprios serviços. Dados: [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright).

Os quilómetros são calculados automaticamente. O desvio é o percurso com compras menos o percurso base (casa→casa ou trabalho→casa). Sem resposta rodoviária não há quilómetros inventados: na descoberta pode mostrar linha reta claramente identificada; no plano a deslocação fica por confirmar e o total é apenas de produtos. Não há trânsito em tempo real nem tempo de permanência nas lojas.

## Poupança mensal

A poupança registada é `referência confirmada − valor efetivamente pago`, por compra. A referência é guardada na data da compra, usando uma oferta elegível da loja habitual e embalagens inteiras ou um total expressamente confirmado. Compras offline/passadas não recebem retroativamente preços automáticos atuais. Sem referência, a compra conta para gastos mas não para poupança. O resultado pode ser negativo.

Custos adicionais de deslocação só entram depois de registados e ficam identificados quando estimados. A aplicação mostra dados em falta e não apresenta a diferença para a oferta mais cara do catálogo como dinheiro já poupado. As compras e referências pertencem à conta, têm identificadores idempotentes e são exportáveis. Não há verificação independente de talões.
