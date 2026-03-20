---
description: Baixa processos do PJE (apenas PDF)
argument-hint: [quantidade] [modo: sentenca|decisao]
allowed-tools: Bash, Read, Write, mcp__claude-in-chrome__*
---

# /baixar-pje

Baixa processos do PJE. NAO converte para TXT.

## Argumentos

```
$1 = quantidade (padrao: 1)
$2 = modo (padrao: sentenca)
```

---

## EXECUCAO OBRIGATORIA

### Etapa 0: Verificar sessao existente

```bash
python -c "
import json
from pathlib import Path
import sys
if not Path('pje_session.json').exists():
    print('SESSAO_INEXISTENTE')
    sys.exit(1)
d = json.load(open('pje_session.json'))
has_xpje = 'X-pje-cookies' in d.get('headers_api', {})
if has_xpje:
    print('SESSAO_COMPLETA')
else:
    print('SESSAO_INCOMPLETA')
    sys.exit(1)
"
```

- Se `SESSAO_COMPLETA` → Pular para Etapa 2 (Listar processos)
- Se `SESSAO_INEXISTENTE` ou `SESSAO_INCOMPLETA` → Ir para Etapa 1

---

### Etapa 1: Capturar sessao (Chrome MCP + HAR)

#### Passo 1.1: Verificar se usuario ja esta logado

```
mcp__claude-in-chrome__tabs_context_mcp
```

Verificar se existe aba com URL contendo `pje1g.trf5.jus.br`.

#### Passo 1.2: Se NAO logado, fazer login via Chrome MCP

1. Pedir credenciais ao usuario (se nao tiver):
   - CPF
   - Senha

2. Navegar para login:
```
mcp__claude-in-chrome__navigate -> https://pje1g.trf5.jus.br/pje/login.seam
```

3. Preencher formulario:
```
mcp__claude-in-chrome__read_page (filter: interactive)
mcp__claude-in-chrome__form_input (campo CPF)
mcp__claude-in-chrome__form_input (campo Senha)
mcp__claude-in-chrome__computer (click no botao Entrar)
```

4. Aguardar login:
```
mcp__claude-in-chrome__computer (wait 3s)
```

5. Verificar se logou (URL deve conter `QuadroAviso` ou `painel-usuario`)

#### Passo 1.3: Pedir HAR ao usuario

Exibir mensagem:
```
Login realizado! Agora preciso capturar os cookies de sessao.

Por favor:
1. Na aba do PJE, pressione F12 (DevTools)
2. Clique na aba "Network" (Rede)
3. Clique em alguma tarefa no painel (para gerar requisicoes)
4. Clique direito na lista de requisicoes → "Save all as HAR with content"
5. Me informe o caminho do arquivo salvo

Exemplo: C:\Users\georg\Downloads\pje1g.trf5.jus.br.har
```

#### Passo 1.4: Extrair cookies do HAR

Apos usuario informar caminho:
```bash
python .claude/skills/pje-download/scripts/extrair_cookies_har.py --har "CAMINHO_DO_HAR" --output pje_session.json
```

**Checkpoint:** Script retornou `[OK]`?

---

### Etapa 2: Listar processos

Executar EXATAMENTE:
```bash
python .claude/skills/pje-download/scripts/listar_processos.py --cookies pje_session.json --modo $2 --limite $1 --output processos.json
```

**Checkpoint:** Arquivo `processos.json` existe e contem processos?

- Se erro "Nenhum processo encontrado" → Sessao expirou, voltar a Etapa 1
- Se erro "Expecting value" → Sessao expirou, voltar a Etapa 1

---

### Etapa 3: Baixar PDFs

Executar EXATAMENTE:
```bash
python .claude/skills/pje-download/scripts/baixar_pdfs.py --cookies pje_session.json --processos processos.json --output data/$2 --delay 2
```

**Checkpoint:** PDFs baixados em `data/$2/`?

- Se erro "cookies_expirados" → Sessao expirou, voltar a Etapa 1

---

### Etapa 4: Relatorio

Informar:
- Quantidade de processos baixados
- Tamanho total
- Caminhos dos arquivos
- Proximo passo: `/baixar-converter` para converter para TXT

---

## Saida Esperada

```
data/[modo]/
├── processos.json
├── _download_log.json
└── [numero-processo]/
    └── [numero].pdf
```

---

## Notas Tecnicas

- O PJE usa header `X-pje-cookies` para autenticacao de download
- Este header so e capturado via HAR (nao via JavaScript)
- Chrome MCP automatiza o login, mas HAR ainda e necessario
- Sessao expira em ~30 minutos de inatividade
