# Authelia e Rumo

Estas integrações são opcionais. Uma instalação normal funciona com contas locais e orçamento próprio. O repositório não contém segredos, bases de dados ou configuração privada do NAS.

## Entrada direta pelo Authelia

O reverse proxy autentica o utilizador no Authelia e transmite `Remote-User`. A Despensa exige também um segredo partilhado com pelo menos 32 caracteres, lido de um ficheiro montado, em `X-Despensa-Proxy-Token`. Só o proxy deve conhecer esse valor. Cabeçalhos enviados pelo navegador têm de ser eliminados **antes** de executar a autenticação do proxy.

Variáveis da aplicação:

```yaml
environment:
  DESPENSA_AUTH_MODE: proxy
  DESPENSA_PROXY_SECRET_FILE: /run/secrets/proxy-secret
  DESPENSA_LOGIN_URL: https://compras.example.org
  DESPENSA_LOGOUT_URL: https://auth.example.org/logout
  DESPENSA_REGISTRATION: "false"
volumes:
  - ./secrets/proxy-secret:/run/secrets/proxy-secret:ro
```

Gere um valor aleatório para o ficheiro, limite as permissões de leitura e forneça o mesmo valor ao proxy através do seu sistema de segredos. Nunca o coloque num commit. Isole a porta interna da aplicação quando a disponibilizar publicamente.

Exemplo de Caddy (o segredo vem do ambiente do Caddy):

```caddyfile
compras.example.org {
    route {
        request_header -Remote-User
        request_header -Remote-Name
        request_header -Remote-Email
        request_header -Remote-Groups
        request_header -X-Despensa-Proxy-Token
        forward_auth authelia:9091 {
            uri /api/authz/forward-auth
            copy_headers Remote-User
        }
        reverse_proxy despensa:8108 {
            header_up X-Despensa-Proxy-Token {$DESPENSA_PROXY_SECRET}
        }
    }
}
```

Para instalar a PWA, pode servir `/static/*`, `/manifest.webmanifest`, `/logo.svg`, `/icon-192.png`, `/icon-512.png` e `/sw.js` sem autenticação, eliminando sempre os cabeçalhos de identidade nessa rota. São apenas recursos públicos. Os endpoints `/api/*` com dados continuam protegidos. A política CSP do portal Authelia não deve ser aplicada aos recursos da Despensa.

No modo `proxy`, a aplicação não aceita palavras-passe locais. Cada identidade Authelia recebe uma conta separada. Não existe fusão automática por nome: para preservar uma conta local existente, faça um backup consistente e estabeleça explicitamente a associação na tabela `identities(provider,subject,user_id)`, com `provider='authelia'`. Nunca associe contas apenas por coincidência de nomes recebidos de um cliente não autenticado.

### Bitwarden e chaves FIDO2

A Despensa delega estes métodos no Authelia. São credenciais WebAuthn: o navegador oferece Bitwarden, passkeys do dispositivo ou chave física. Não é necessário guardar uma chave API ou a palavra-passe do Bitwarden na Despensa.

O Authelia 4.39 suporta `webauthn.enable_passkey_login: true`. A preferência de ligação vazia permite escolher o tipo de autenticador. `selection_criteria.discoverability: preferred` permite também credenciais FIDO2 sem armazenamento residente; estas podem servir como segundo fator, mas não como passkeys descobertas no login sem nome de utilizador. Para passkeys sincronizadas, `filtering.prohibit_backup_eligibility` deve ser `false`. Consulte a [configuração oficial](https://www.authelia.com/configuration/second-factor/webauthn/) antes de alterar políticas de autenticação.

O registo é pessoal: entre no portal Authelia, abra as definições de segurança e adicione uma credencial WebAuthn. Confirme a identidade quando for solicitado. Guarde uma no Bitwarden e registe outra usando a chave física. O navegador/gestor pode pedir PIN, biometria ou toque na chave. O servidor não consegue efetuar este registo pelo utilizador. [Instruções do Bitwarden](https://bitwarden.com/help/storing-passkeys/).

## Orçamento mensal do Rumo

O exportador suporta a estrutura de base de dados Rumo com `months(year,month)` e `month_expenses(month_id,name,category,planned,actual)`. Não executa migrações ou escritas no Rumo. Filtra nomes exatos após normalização de acentos e maiúsculas, por defeito **Supermercado**. Não inclui “Compras Online” nem categorias vagamente relacionadas.

```sh
python integrations/export_rumo_budget.py \
  --database /rumo/rumo.db \
  --output /export/budget.json \
  --watch 60
```

Pode repetir `--name` para incluir outras linhas expressamente escolhidas. A exportação é atómica, tem permissões restritas e preserva o último ficheiro em caso de falha.

Execute o exportador num processo/serviço separado, com o diretório do Rumo montado em só de leitura (incluindo os ficheiros WAL necessários). Apenas o exportador deve conseguir ler o Rumo inteiro. Monte **só a pasta da exportação**, em só de leitura, na Despensa e configure:

```yaml
environment:
  DESPENSA_RUMO_SNAPSHOT: /run/rumo/budget.json
  DESPENSA_RUMO_USER_IDS: UUID-DA-CONTA-AUTORIZADA
  DESPENSA_RUMO_URL: https://rumo.example.org
volumes:
  - ./budget-export:/run/rumo:ro
```

`DESPENSA_RUMO_USER_IDS` aceita IDs de conta Despensa separados por vírgulas; não nomes de utilizador. Só essas contas veem a ligação. O orçamento segue o mês selecionado; um mês ausente ou exportação com mais de cinco minutos é assinalado, sem reutilizar valores de outro mês. O perfil pode escolher orçamento próprio. A integração é apenas de leitura: confirmar uma compra na Despensa não altera automaticamente a contabilidade do Rumo.

## Trânsito opcional e transportes

O planeamento de carro funciona sem chaves, com tempos rodoviários OSRM identificados como estimativas sem trânsito ao vivo. Para ativar TomTom, monte uma chave da Routing API no servidor. Exemplo de `compose.override.yaml` (junte às integrações existentes):

```yaml
services:
  despensa:
    environment:
      DESPENSA_TOMTOM_KEY_FILE: /run/secrets/tomtom-key
    volumes:
      - ./secrets/tomtom-key:/run/secrets/tomtom-key:ro
```

Crie o ficheiro com a chave e leitura permitida apenas aos utilizadores necessários, incluindo o UID 1000 do contentor. Não publique o ficheiro nem o Compose privado. A alternativa é `DESPENSA_TOMTOM_KEY` no ambiente do servidor. Consulte limites e condições da sua conta TomTom. A app limita o refinamento a um candidato por número de lojas e guarda respostas em memória durante cinco minutos; uma falha preserva a estimativa estática com identificação explícita.

O modo transportes usa o serviço público Transitous para aplicações livres não comerciais compatíveis com a [política de utilização](https://transitous.org/api/). Está limitado a 200 consultas por instalação/dia, com cache e [atribuição das fontes](https://transitous.org/sources/). Para MOTIS próprio ou outro uso, configure `DESPENSA_TRANSIT_URL` com o URL base do servidor (sem `/api/v6/plan`), além das condições/licenças dos dados necessários. Preço por embarque e cobertura do passe são declarados no perfil; não são tarifas consultadas automaticamente.
