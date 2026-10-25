<p align="center"><img src="static/logo.svg" width="88" alt="Despensa"></p>
<h1 align="center">Despensa</h1>
<p align="center"><strong>Compras com sentido. Compras con sentido.</strong><br>A sua lista, os preços à vista e um plano para comprar melhor em Portugal e Espanha.</p>
<p align="center"><a href="#começar">Instalar</a> · <a href="docs/README.es.md">Español</a> · <a href="docs/SOURCES.md">Fontes e metodologia</a> · <a href="CONTRIBUTING.md">Contribuir</a></p>

![Interface de computador](docs/screenshots/desktop.png)

Despensa é uma aplicação de compras pessoais que pode alojar no seu computador ou NAS. Organiza listas mensais, guarda as suas preferências e compara os produtos para os quais existem preços observados. A interface funciona em português europeu e espanhol, no computador e no telemóvel.

**Versão 0.1: funcional, com cobertura de preços deliberadamente parcial.** Não promete o preço mais baixo de todas as lojas. As alternativas são propostas por palavras, não por uma equivalência certificada de produtos.

## O que já pode fazer

- Criar contas separadas, com listas e perfis privados.
- Organizar produtos por mês e categoria, com quantidades, notas e data de compra; repetir o mês anterior.
- Usar um modo de compras com controlos maiores e lista offline. Alterações feitas offline ficam numa fila local e sincronizam quando regressa a ligação e a sessão continua válida.
- Pesquisar o catálogo guardado e consultar a fonte, data e histórico de cada observação.
- Recolher diariamente algumas categorias públicas do Continente e Auchan em Portugal. Intervalo configurável entre 6 e 168 horas; recolha manual com um intervalo mínimo de 15 minutos. O servidor trabalha mesmo com a app fechada.
- Registar preços de lojas físicas de Portugal e Espanha, incluindo Makro e Recheio, formato, IVA, localização, validade, cartão, subscrição ou cupão específico.
- Definir as lojas acessíveis e os cartões, subscrições e códigos de cupão que possui. Ter cartão não equivale a ter um cupão.
- Comparar até três lojas por ida, comprando embalagens inteiras. Os cabazes incompletos são identificados e nunca vencem um completo por omitir produtos.
- Separar o valor pago hoje do saldo futuro em cartão.
- Localizar casa, trabalho e lojas; estimar o desvio rodoviário com OSRM, incluindo o regresso do trabalho nos dias configurados. Sem coordenadas, pode indicar quilómetros adicionais estimados.
- Exportar os seus dados em JSON.
- Instalar como PWA em navegadores compatíveis, através de HTTPS.

<p align="center"><img src="docs/screenshots/mobile.png" width="330" alt="Lista no telemóvel"></p>

## Começar

Precisa de Docker e Docker Compose. Não precisa de chaves de IA ou de serviços pagos.

```sh
git clone https://github.com/hubertdungen/Despensa.git
cd Despensa
docker compose up -d --build
```

Abra `http://IP-DO-SERVIDOR:8108` e crie a sua conta. O volume Docker `despensa-data` guarda a base de dados. A primeira conta ativa a recolha diária por defeito; também pode carregar em **Atualizar preços**. Uma recolha percorre sete páginas com pausas entre pedidos; se uma fonte falhar, preserva as observações anteriores e identifica a falha.

Para instalar no telemóvel e ter a lista offline, publique a instalação através de um reverse proxy com **HTTPS válido**. Em Android/PC, use a opção de instalação do navegador; no iPhone, **Partilhar → Adicionar ao ecrã principal**. A forma de instalação varia por navegador. `localhost` é uma exceção de desenvolvimento; um endereço HTTP do NAS não permite todas as funções PWA.

O registo está ativo por defeito. Depois de criar as contas pretendidas, pode alterar `DESPENSA_REGISTRATION` para `"false"` no Compose e executar novamente `docker compose up -d`. Quando desativado, só permite criar a primeira conta numa base de dados vazia. Use uma palavra-passe com pelo menos 10 caracteres. O cookie de sessão dura 30 dias; um gateway de autenticação externo pode ter uma duração diferente.

Exemplo de Caddy:

```caddyfile
compras.example.org {
    reverse_proxy 127.0.0.1:8108
}
```

A API verifica a origem dos pedidos de escrita. Configure o proxy para preservar o cabeçalho `Host`. O valor `X-Forwarded-Proto: https` ativa cookies seguros. O endpoint `/api/health` serve para monitorização; os dados exigem sessão. Manifesto, ícones e recursos estáticos não contêm dados pessoais e podem ser públicos se usar um gateway de autenticação.

## Preços e comparações honestas

O catálogo automático inicial cobre **arroz, massa, leite, azeite e ovos no Continente; arroz e azeite no Auchan**, apenas a primeira página de cada categoria, até 36 referências por página. Não cobre toda a loja nem garante stock, preço físico ou preço de uma localização específica.

Espanha está disponível na interface, nos perfis e nos preços manuais. **Ainda não há recolha automática espanhola.** A API da Mercadona e a pesquisa dinâmica do Continente restringem robots; não são utilizadas. O Intermarché bloqueou o teste inicial. Não contornamos bloqueios, autenticação ou CAPTCHAs.

Observações com mais de 72 horas ficam fora dos planos. Para datas futuras, apenas entram preços com validade explícita que inclua essa data. Quando as condições de uma oferta automática são ambíguas, a oferta fica fora da otimização. Preços manuais de uma loja concreta continuam a necessitar de confirmação da disponibilidade e condições; o utilizador é responsável por indicar o preço final com IVA. Consulte [as fontes e limitações](docs/SOURCES.md).

Uma lista genérica, por exemplo “arroz carolino”, pode encontrar várias marcas que contenham essas palavras. Adicionar uma referência através de **Explorar preços** fixa esse produto específico. Regras conservadoras excluem algumas substituições erradas, como ovos de codorniz numa pesquisa genérica de ovos, ou farinha numa pesquisa de arroz. A comparação não reconhece automaticamente EAN nem garante equivalência nutricional ou de qualidade. O total considera a quantidade pedida e o número inteiro de embalagens necessário.

O planeador mostra o custo de deslocação separadamente. Quando faltam distâncias, o total inclui apenas produtos. Desvios indicados manualmente são somados e identificados como estimativas. Com coordenadas, é calculada a ordem mais curta entre as lojas do cabaz, até três paragens; os tempos não incluem trânsito em tempo real nem permanência nas lojas. Lojas profissionais exigem acesso confirmado no perfil. Descontos dependentes de valor mínimo de compra, escalões, combinações ou cupões personalizados não são interpretados automaticamente: registe apenas ofertas cujas condições consegue cumprir.

## Privacidade e serviços externos

Listas, contas, preferências e preços manuais ficam na base de dados da instalação. As observações públicas automáticas são partilhadas entre contas dessa instalação para reduzir pedidos às lojas. As palavras-passe são guardadas com scrypt e os tokens de sessão com hash. A app não inclui analytics, publicidade, fontes externas ou imagens de produtos de terceiros.

No dispositivo, a lista e uma fila de alterações ficam guardadas para uso offline, associadas à conta. Terminar sessão elimina essa cópia local. Não termine sessão com alterações ainda por sincronizar. A sessão precisa de estar válida para sincronizar; se expirar, volte a entrar na mesma conta.

Use uma zona ou um local público próximo para casa e trabalho, sem dados pessoais. Ao carregar em **Localizar**, envia esse texto ao serviço público Nominatim, sujeito à [política de utilização](https://operations.osmfoundation.org/policies/nominatim/): consultas iniciadas pelo utilizador, sem autocomplete, com cache e no máximo uma por segundo. Ao abrir o plano com coordenadas guardadas, envia coordenadas ao serviço público OSRM. Os operadores podem configurar serviços próprios através de `DESPENSA_GEOCODER_URL` e `DESPENSA_ROUTER_URL`, sem alterar o código. Ambos usam dados [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright); existem cache, limites e tolerância a falhas. Estes serviços públicos não garantem disponibilidade. Não são solicitados GPS, acesso ao calendário, credenciais de supermercados ou o número do cartão de cliente.

## Desenvolvimento e testes

Python 3.12+:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python app.py
```

Não existe compilação do frontend. HTML, CSS, JavaScript e ícones vetoriais são servidos localmente. O servidor usa Flask/Waitress, SQLite em WAL e um worker no mesmo processo. Execute uma única instância por base de dados; não use vários workers WSGI, réplicas ou um sistema de ficheiros de rede para o ficheiro SQLite. Para outra porta ou diretório: `DESPENSA_PORT`, `DESPENSA_HOST` e `DESPENSA_DATA`.

Para os testes de navegador: `npm ci`, `npx playwright install chromium` e `npm run test:e2e`. O teste inicia um servidor isolado com uma base temporária e sem worker de recolha. O CI executa os testes Python e de navegador, verifica a sintaxe JavaScript e constrói a imagem Docker. Os testes não contactam lojas nem serviços de mapas. As imagens do README mostram uma conta de demonstração isolada e observações reais; são ilustrativas, não preços garantidos para hoje.

Para backups consistentes, use a API de backup do SQLite ou pare a aplicação antes de copiar o volume completo. O JSON exporta dados de utilizador; ainda não existe importação/restauro desse JSON pela interface.

## Próximos passos

- Aumentar as categorias e criar conectores ibéricos com fontes e permissões adequadas.
- Validar equivalências por EAN, marcas, tipo e formato, com revisão humana.
- Interpretar promoções complexas, compras mínimas e regras de acumulação.
- Partilhar listas e sincronizar vários membros do mesmo agregado em simultâneo.
- Alertas de preços e evolução do orçamento.
- Instaladores Windows `.exe` e Android `.apk`, com builds e assinatura. **Ainda não estão disponíveis**; a versão instalável atual é a PWA. Instalar um cliente não fornece, por si só, um serviço central gratuito de preços.

## Licença

**AGPL-3.0-or-later.** Gratuito para utilização pessoal e também utilizável comercialmente nos termos da licença. Distribuições e versões modificadas disponibilizadas pela rede devem respeitar as obrigações da AGPL. A licença do código não concede direitos sobre conteúdos, marcas ou bases de dados das lojas. Não existe afiliação aos supermercados mencionados.
