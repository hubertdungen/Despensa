# Fontes, cobertura e metodologia

## Radar automático ibérico (0.5)

A investigação é automática para os produtos da lista e as palavras pesquisadas. A pesquisa considera nomes, marcas, formatos, plurais, prefixos e grafias próximas quando não há correspondência exata. Portugal/Espanha são selecionáveis na pesquisa. Os grupos completos são calculados antes de paginar, sem limitar a comparação aos primeiros 300 preços.

As pesquisas interativas têm uma fila persistente própria, processada por dois workers independentes da recolha geral, até seis páginas relevantes por loja. Uma pesquisa nova pode consultar páginas de produto ainda não visitadas mesmo durante a espera normal da recolha geral. Respeita os bloqueios e intervalos de espera de fontes que falharam. Os pedidos das três tarefas partilham o limite de dois segundos por domínio. O navegador consulta o progresso a cada três segundos, apenas enquanto há pesquisa pendente e a vista está aberta. `research.py` contém o registo de fontes, os métodos alternativos e a fila persistente; `catalog.py` mantém os formatos e conectores específicos. Há fontes configuradas para as principais cadeias portuguesas e espanholas, incluindo lojas profissionais. O estado de cada fonte aparece no radar: programada, a investigar, com preços, a descobrir páginas, parcialmente disponível ou com nova tentativa prevista.

Uma passagem não equivale a recolher uma loja inteira. O orçamento inicial é de 12 páginas por cadeia por passagem, no máximo duas de mapas do site. As páginas ainda não visitadas ficam na base de dados. A prioridade reconhece palavras portuguesas/espanholas e reparte as consultas pelos produtos pedidos; não favorece para sempre um único termo. A descoberta continua entre atualizações de preços. O limite de segurança da fila é de 200 mil URLs por cadeia.

### Métodos complementares

1. Leitura do preço apresentado nas páginas de categoria, quando existe um formato identificado (Continente, Auchan e Pingo Doce).
2. JSON-LD `Product/Offer` publicado pela própria loja em páginas de produto.
3. Dados de catálogo embebidos na página, incluindo ALDI em Next.js (produto e resultados de categoria) e Lidl em Nuxt: preço, formato, datas, disponibilidade e preços Lidl Plus separados. O leitor Nuxt interpreta apenas referências JSON; não executa scripts.
4. Microdados de produto quando o JSON-LD falta ou não pode ser interpretado.
5. Mapas oficiais do site e ligações públicas para descobrir outras páginas de produto/categoria. Este método descobre URLs; não transforma uma URL num preço.
6. Pesquisa pública direta do Auchan, sujeita a `robots.txt`. O Continente e o Pingo Doce restringem os respetivos endpoints de pesquisa; nesses casos usamos categorias e páginas de produto descobertas nos mapas. Marca e volume não precisam de estar no URL: o formato é verificado no produto, depois da leitura.
7. Catálogo público anónimo da [Makro ES](https://tienda.makro.es/shop), com `grossPrice` explícito, sem inferir IVA a partir de preços líquidos nem aplicar descontos por volume. O centro de referência atual é Barajas (00001): o preço e a localização são mostrados, mas estes registos ficam fora do plano até existir confirmação da loja.
8. Folheto digital oficial do [Recheio](https://folhetos.recheio.pt/recheio-cash-carry/recheio/folheto-digital-bons-negocios/): metadados públicos da publicação e referências estruturadas dos produtos, com data explícita. Os preços Cash são **sem IVA**, exigem condições profissionais e ficam excluídos do plano e da poupança pessoal. Não inferimos taxas de IVA nem imagens a partir de ícones genéricos.
9. No Pingo Doce, JSON-LD para identificar o produto e o preço visível dentro do bloco desse produto. O valor do minicarrinho não é usado.

Os métodos de leitura são independentes. Um JSON inválido não impede os outros leitores; uma página de categoria alterada pode ser substituída por uma página de produto descoberta no mapa. Uma fonte totalmente inacessível não é apresentada como coberta.

O robot identifica-se, aplica pausas de pelo menos dois segundos por domínio, limites de tamanho, timeouts e cache. Consulta `robots.txt` antes da recolha e não contorna autenticação, CAPTCHAs ou restrições de acesso. Os redirecionamentos de investigação estão limitados ao mesmo retalhista. Falhas preservam observações anteriores e têm espera progressiva: 15 min, 30 min, 1 h, até 24 h. A fila e o estado sobrevivem a reinícios.

### Validação real e limites

Na validação da versão 0.2 foram extraídos preços reais de **Continente, Auchan, Pingo Doce, Lidl PT, ALDI PT/ES, DIA e Lidl ES**, através de métodos diferentes. A resposta de uma fonte pode mudar entre tentativas. Algumas fontes devolveram HTTP 403, verificação de acesso, mapas sem preço ou páginas sem preço legível; essas tentativas ficam identificadas e são repetidas com espera. A validação 0.4 confirmou banana e frango no Continente, Água Luso 7L no Auchan, banana ALDI, banana Lidl com Lidl Plus e preços com IVA no catálogo público da Makro ES. Na validação 0.5, o folheto público do Recheio forneceu 677 preços Cash sem IVA, válidos de 27 de outubro a 2 de novembro de 2026. A [Makro PT](https://produtos.makro.pt/shop) tem um catálogo público alternativo com referências e formatos; os preços permanecem reservados a sessões autenticadas da própria loja. Authelia autentica a Despensa e não substitui essa conta.

Mercadona PT/ES, Intermarché, Makro PT, Recheio, Carrefour, Alcampo e Eroski têm mecanismos de descoberta/investigação configurados, mas isso não constitui garantia de preços disponíveis.

Não se promete o preço mais baixo de todo o mercado nem o catálogo integral de todas as lojas. Também não se transforma uma falha automática na obrigação de introduzir preços manualmente: o radar continua a investigar. O registo manual é uma opção adicional para preços observados fisicamente.

## Observações e imagens

Guardamos referência, nome/marca, preço em cêntimos, formato/unidade quando explícitos, fonte, país, canal, condição, validade e momento da observação. As fotografias publicadas pelas lojas podem aparecer através de um proxy com uma lista fixa de domínios/caminhos, limite de 2 MB por imagem, tipos de imagem permitidos e cache em memória de até 16 MB. O navegador não recebe cookies das lojas nem lhes envia os seus próprios cookies. O endpoint não aceita URLs arbitrárias. Os direitos das fotografias e marcas pertencem aos titulares; o código não concede direitos sobre esses conteúdos.

O repositório distribui software, não uma base de dados comercial das lojas. Preços publicados podem variar por região, disponibilidade e localização. Uma observação não confirma stock numa loja concreta. A aplicação não recolhe credenciais de supermercados ou números de cartões.

## Correspondência e custo

As sugestões reconhecem famílias conservadoras. Leite magro, meio gordo, sem lactose, fresco e biológico são separados quando a informação está presente. Palavras frequentes são normalizadas entre português e espanhol. Famílias não reconhecidas podem ser agrupadas por EAN/GTIN com dígito de controlo válido, unidade e conteúdo da embalagem iguais. Sem essa informação ficam como referências individuais. Não há certificação de equivalência nutricional ou de qualidade entre marcas.

Uma referência específica pode ser fixada. Uma lista genérica procura alternativas pelas palavras/família escolhidas. Nas embalagens fechadas de kg/l/un, o custo é `ceil(quantidade / conteúdo da embalagem) × preço da embalagem`: uma unidade mais barata não implica necessariamente um cabaz mais barato. Nas vendas a peso, €/kg é uma base de comparação e não o preço de uma embalagem. O custo estimado usa o peso pedido, respeitando o mínimo publicado e, quando a loja vende uma embalagem de peso aproximado, múltiplos desse peso nominal. O preço final depende da pesagem. O mesmo cálculo é usado no plano e na referência guardada com uma compra. O histórico guarda preços observados, sem inventar preços anteriores.

Só entram no plano lojas/países ativos, acesso profissional satisfeito, IVA incluído, observações com até 72 h e validade compatível com a data. Para datas futuras é exigida validade explícita. Condições desconhecidas ficam fora da otimização. Cartão não equivale a cupão. EntregaZero é uma subscrição de entregas e não desbloqueia automaticamente descontos em produtos. Saldo futuro não reduz o pagamento de hoje. Promoções por combinações ou valor mínimo não são presumidas elegíveis.

## Lojas próximas e percursos

A descoberta consulta separadamente as zonas de **casa e trabalho**. Localizadores oficiais de [Continente](https://feed.continente.pt/lojas) e [Auchan](https://www.auchan.pt/pt/lojas) dão coordenadas verificáveis; [Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API) alarga a pesquisa às outras cadeias em Portugal e Espanha. A ausência de resposta do serviço de mapas não elimina as lojas dos localizadores oficiais. A cobertura parcial é assinalada.

A zona inicial tem raio de 6 km por origem. Preservam-se até 12 candidatos de cada zona (24 no conjunto), calculando distâncias rodoviárias e o desvio trabalho→loja→casa. Cada cadeia pode fornecer até três filiais candidatas ao planeador, que considera até três paragens e a assimetria das estradas.

A escolha pelo botão **Localizar** guarda imediatamente a morada e as coordenadas na conta, sem depender do botão geral Guardar. Alterar uma morada sem novas coordenadas invalida as antigas. Se o geocodificador falhar, a morada escrita continua a ser guardada e a interface pede uma nova tentativa para confirmar coordenadas. Dados em falta são identificados no plano.

Geocodificação: [Nominatim](https://operations.osmfoundation.org/policies/nominatim/), ao guardar zonas ou carregar em Localizar, sem autocomplete, com cache e máximo uma consulta por segundo. Se houver ambiguidade, o utilizador escolhe o resultado. Distâncias: [OSRM](https://project-osrm.org/docs/v5.24.0/api/#table-service), cache de seis horas. Descoberta: cache de 24 h; falhas sem resultados têm espera de cinco minutos. Operadores podem configurar os próprios serviços. Dados: [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright).

Os quilómetros são calculados automaticamente. O desvio é o percurso com compras menos o percurso base (casa→casa ou trabalho→casa). Sem resposta rodoviária não há quilómetros inventados: na descoberta pode mostrar linha reta claramente identificada; no plano a deslocação fica por confirmar e o total é apenas de produtos. Não há trânsito em tempo real nem tempo de permanência nas lojas.

## Poupança mensal

A poupança registada é `referência confirmada − valor efetivamente pago`, por compra. A referência é guardada na data da compra, usando uma oferta elegível da loja habitual e embalagens inteiras ou um total expressamente confirmado. Compras offline/passadas não recebem retroativamente preços automáticos atuais. Sem referência, a compra conta para gastos mas não para poupança. O resultado pode ser negativo.

Custos adicionais de deslocação só entram depois de registados e ficam identificados quando estimados. A aplicação mostra dados em falta e não apresenta a diferença para a oferta mais cara do catálogo como dinheiro já poupado. As compras e referências pertencem à conta, têm identificadores idempotentes e são exportáveis. Não há verificação independente de talões.

## Sugestões e alternativas de pesquisa (0.5)

As sugestões incluem referências individuais, mesmo quando não existe uma família comparável. Categoria, unidade e quantidade vêm dos dados publicados; campos já alterados pelo utilizador são preservados. Café em grão, moído e cápsulas continuam a ser escolhas distintas. A marca é incluída na pesquisa quando não consta do nome publicado. Uma referência individual fica fixada à oferta escolhida; uma família pode comparar várias lojas.

“Linha e Fibra” é também uma categoria comercial dos [cereais Continente](https://www.continente.pt/mercearia/cereais-e-barras/cereais-linha-e-fibra/constant/fitness/) e [Auchan](https://www.auchan.pt/pt/alimentacao/mercearia/cereais-e-barras/linha-e-fibra/). A pesquisa pode usar essa categoria mantendo a marca Fitness. Quando a categoria não está publicada, os resultados mais amplos são assinalados como relacionados; restrições como “sem açúcar” continuam obrigatórias. Não tratamos todos os cereais Fitness como o mesmo produto.

As alternativas avaliadas são páginas de produto/categoria, pesquisa pública permitida, dados estruturados, catálogos anónimos e folhetos oficiais. Uma integração com contas de supermercado ainda não está implementada. Não recolhemos credenciais nem apresentamos índices de terceiros como preços confirmados da loja.

O leitor de robots aplica wildcards e precedência da regra mais específica. Para os assets públicos de folhetos no CDN iPaper, a inexistência do recurso robots (403/404) segue [RFC 9309, 2.3.1.3](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.3.1.3). Erros de rede/5xx e bloqueios dos próprios assets continuam a interromper a leitura. Os URLs admitidos pertencem apenas ao CDN e à publicação oficial.

### Correções 0.5.1

A pesquisa ignora artigos como “os/as” e acrescenta resultados de Fitness Original mesmo quando já encontrou variantes com “Linha/Fibra” no nome ou categoria. Marca, formato e restrições dietéticas mantêm-se obrigatórios. Os resultados adicionais sem categoria publicada são assinalados como relacionados.

Quando um item pede unidades e a loja publica uma embalagem fechada em kg/l, cada unidade representa uma embalagem, com o formato explícito no plano. Por exemplo, 1 un de cereais 625 g compra uma embalagem; 1 kg exige duas embalagens de 625 g. Não se aplica esta conversão a fruta/carne vendida a peso, nem se alteram as quantidades guardadas. O mesmo cálculo é usado na referência de poupança de uma compra.

Cada alternativa identifica os produtos em falta. Apenas um cabaz completo pode receber a etiqueta “Plano sugerido”. O percurso mostra quilómetros e minutos totais, trajeto habitual e desvio/custo adicionais. Um desvio de 0 km não significa uma viagem de 0 km. Respostas antigas da lista não podem substituir um cálculo rodoviário mais recente. A app avisa quando deteta uma versão nova no servidor, permitindo atualizar a interface.

A pesquisa genérica de cereais e o planeador excluem barras/barritas, salvo pedido explícito, para não substituir uma caixa de pequeno-almoço por um snack mais barato. A fila local de alterações confirma cada operação sobre a fila atual, preservando produtos adicionados enquanto outro pedido estava em curso. O plano aguarda essas gravações antes de consultar o cabaz no servidor.
