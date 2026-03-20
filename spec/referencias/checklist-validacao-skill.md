# Checklist de Validação: Skill v1.0

> **Propósito:** Métrica de conformidade para validar se uma skill segue o spec de skills.
>
> **Como usar:** Aplique este checklist a cada skill criada. Score mínimo recomendado: 80%.
>
> **Versão:** 1.0

---

## Pontuação

| Categoria | Peso | Descrição |
|-----------|------|-----------|
| CRÍTICO | 10 pts | Falha impede funcionamento correto |
| ALTO | 5 pts | Falha compromete reutilização/manutenção |
| MÉDIO | 3 pts | Falha afeta qualidade mas não funcionalidade |
| MENOR | 1 pt | Melhoria recomendada |

**Score máximo:** 120 pontos
**Score mínimo recomendado:** 96 pontos (80%)

---

## 1. YAML Frontmatter (25 pontos)

### 1.1 Estrutura (CRÍTICO - 10 pts)

```
[ ] Bloco YAML presente no início do arquivo?
    Formato: --- no início e fim do bloco
```

### 1.2 Campo `name` (CRÍTICO - 10 pts)

```
[ ] Campo `name` presente?
[ ] Formato kebab-case? (minúsculas + hífens)
[ ] Nome corresponde ao nome da PASTA?
[ ] Sem underscores, espaços ou maiúsculas?

Exemplos válidos:
  ✅ name: pje-download (pasta: .claude/skills/pje-download/)
  ✅ name: converter-pdf (pasta: .claude/skills/converter-pdf/)
  ❌ name: pje_download (underscore)
  ❌ name: PjeDownload (PascalCase)
```

### 1.3 Campo `description` (ALTO - 5 pts)

```
[ ] Campo `description` presente?
[ ] Estrutura: O QUE faz + QUANDO usar?
[ ] Contém palavras-chave que disparam a skill?
[ ] Tamanho < 1024 caracteres?

Formato esperado:
  description: |
    [O que faz]. [Quando usar/disparadores].

Exemplos válidos:
  ✅ "Baixa processos do PJE via automação. Use quando precisar capturar
      sessão, listar processos ou baixar PDFs do PJE."
  ❌ "Skill para PJE" (muito vago, sem O QUE nem QUANDO)
```

---

## 2. Estrutura de Diretório (20 pontos)

### 2.1 Localização do SKILL.md (CRÍTICO - 10 pts)

```
[ ] Arquivo está em `.claude/skills/[name]/SKILL.md`?
[ ] Nome da pasta corresponde ao campo `name` do YAML?

Estrutura correta:
  .claude/skills/
  └── pje-download/           ← pasta = name do YAML
      ├── SKILL.md            ← arquivo principal
      ├── references/         ← documentação detalhada (opcional)
      └── scripts/            ← scripts executáveis (se houver)

Erros comuns:
  ❌ .claude/skills/pje-download.md (arquivo solto, não diretório)
  ❌ .claude/skills/pje_download/SKILL.md (underscore no nome)
```

### 2.2 Tamanho do SKILL.md (ALTO - 5 pts)

```
[ ] SKILL.md tem menos de 500 linhas?

Regra de Progressive Disclosure:
  - SKILL.md: instruções essenciais (< 500 linhas)
  - references/: documentação detalhada, exemplos extensos
  - scripts/: código executável

Se ultrapassar 500 linhas:
  - Mover conhecimento de domínio para references/
  - Mover exemplos extensos para references/exemplos.md
  - Manter apenas o essencial para execução
```

### 2.3 Diretório references/ (ALTO - 5 pts)

```
[ ] Se há conhecimento extenso, existe references/?
[ ] Arquivos em references/ são referenciados no SKILL.md?

Conteúdo típico de references/:
  references/
  ├── api-pje.md              # Documentação da API
  ├── exemplos-avancados.md   # Casos de uso complexos
  └── troubleshooting.md      # Resolução de problemas

Referência no SKILL.md:
  > Para detalhes da API, veja references/api-pje.md
```

---

## 3. Tags XML Obrigatórias (35 pontos)

### 3.1 Tag `<identidade>` (ALTO - 5 pts)

```
[ ] Tag <identidade> presente?
[ ] Subtag <papel> presente e preenchida?
[ ] Subtag <estilo> presente e preenchida?

Formato correto:
  <identidade>
    <papel>Especialista em automação de download do PJE</papel>
    <estilo>Técnico, passo-a-passo, orientado a scripts</estilo>
  </identidade>
```

### 3.2 Tag `<proposito>` (CRÍTICO - 10 pts)

```
[ ] Tag <proposito> presente?
[ ] Define claramente O QUE a skill faz?
[ ] Define VALOR que entrega ao usuário?
[ ] NÃO menciona pipelines ou contextos específicos?

Formato correto:
  <proposito>
    Automatizar a captura de sessão do PJE e download de PDFs de processos,
    eliminando a necessidade de navegação manual e cliques repetitivos.
  </proposito>
```

### 3.3 Tag `<quando_usar>` (CRÍTICO - 10 pts)

```
[ ] Tag <quando_usar> presente?
[ ] Lista CENÁRIOS de uso claros?
[ ] Identifica PALAVRAS-CHAVE de disparo?
[ ] Tem seção de "quando NÃO usar"?

Formato correto:
  <quando_usar>
    USAR quando:
    - Usuário pede para "baixar processo do PJE"
    - Usuário menciona "capturar sessão"
    - Usuário quer "converter PDF para texto"

    NÃO usar quando:
    - Processo já está baixado localmente
    - Usuário quer apenas consultar andamento (usar MCP direto)
  </quando_usar>
```

### 3.4 Tag `<instrucoes>` (ALTO - 5 pts)

```
[ ] Tag <instrucoes> presente?
[ ] Usa subtags <passo numero="N" nome="...">?
[ ] Passos em ordem lógica?
[ ] Referencia scripts/tools disponíveis?

Formato correto:
  <instrucoes>
    <passo numero="1" nome="Verificar sessão">
      Verificar se pje_session.json existe e está válido.
      Se não, instruir usuário a executar captura de sessão.
    </passo>
    <passo numero="2" nome="Listar processos">
      Executar script: python scripts/listar_processos.py
    </passo>
  </instrucoes>
```

### 3.5 Tag `<conhecimento>` OU `<scripts>` (ALTO - 5 pts)

```
[ ] Tag <conhecimento> presente? (para skills baseadas em conhecimento)
OU
[ ] Tag <scripts> presente? (para skills baseadas em execução)
[ ] Pelo menos UMA das duas tags deve existir!

Skill baseada em conhecimento:
  <conhecimento>
    - Formato de sessão PJE: JSON com cookies e headers
    - Endpoints da API: /consulta, /processo, /documento
    - Limitações: máximo 50 processos por requisição
  </conhecimento>

Skill baseada em scripts:
  <scripts>
    | Script | Localização | Função |
    |--------|-------------|--------|
    | listar_processos.py | scripts/ | Lista processos disponíveis |
    | baixar_pdfs.py | scripts/ | Baixa PDFs de um processo |
  </scripts>
```

---

## 4. Tags XML Recomendadas (15 pontos)

### 4.1 Tag `<exemplos>` (MÉDIO - 5 pts)

```
[ ] Tag <exemplos> presente?
[ ] Exemplo de uso típico?
[ ] Exemplo de saída esperada?

Formato:
  <exemplos>
    ### Uso típico
    Usuário: "Baixe os processos de sentença do PJE"

    Claude: Executa listar_processos.py → baixar_pdfs.py → retorna lista

    ### Saída esperada
    Processos baixados:
    - 0807674-42.2015.4.05.8100 → data/sentenca/0807674-42.../
  </exemplos>
```

### 4.2 Tag `<casos_de_borda>` (MÉDIO - 5 pts)

```
[ ] Tag <casos_de_borda> presente?
[ ] Cobre erros comuns?
[ ] Define comportamento para edge cases?

Formato:
  <casos_de_borda>
    - Sessão expirada: Instruir usuário a recapturar sessão
    - Processo não encontrado: Verificar número e tentar novamente
    - Timeout na requisição: Aumentar timeout ou dividir em lotes
  </casos_de_borda>
```

### 4.3 Tag `<restricoes>` (ALTO - 5 pts)

```
[ ] Tag <restricoes> presente?
[ ] Usa prefixos NUNCA/NÃO/SEMPRE?
[ ] Define limites operacionais?

Formato:
  <restricoes>
    - NUNCA armazenar credenciais em código
    - NÃO baixar mais de 10 processos por vez sem confirmação
    - SEMPRE verificar validade da sessão antes de requisições
    - SEMPRE usar português com acentos corretos
  </restricoes>
```

---

## 5. Ausência de Anti-Patterns (15 pontos)

### 5.1 Sem Caminhos Absolutos Hardcoded (CRÍTICO - 10 pts)

```
[ ] NENHUM caminho absoluto específico do usuário?

Buscar por padrões proibidos:
  ❌ C:\Users\fulano\
  ❌ /home/usuario/
  ❌ ~/projetos/cliente/

Caminhos relativos permitidos:
  ✅ scripts/listar_processos.py
  ✅ references/api-pje.md
  ✅ data/sentenca/ (relativo ao workspace)
```

### 5.2 Sem Credenciais ou Secrets (CRÍTICO - 5 pts)

```
[ ] NENHUMA credencial, token ou senha no arquivo?
[ ] NENHUM exemplo com dados reais sensíveis?

Buscar por padrões proibidos:
  ❌ password: "minhasenha123"
  ❌ token: "eyJhbGciOiJIUzI1NiIs..."
  ❌ cookie: "JSESSIONID=ABC123..."

Se precisar de exemplo:
  ✅ password: "<SUA_SENHA>"
  ✅ token: "<TOKEN_DO_PJE>"
```

---

## 6. Scripts e Dependências (10 pontos)

### 6.1 Documentação de Scripts (ALTO - 5 pts)

```
[ ] Se há scripts, estão documentados no SKILL.md?
[ ] Parâmetros de entrada claros?
[ ] Formato de saída documentado?

Formato esperado:
  ### listar_processos.py

  **Parâmetros:**
  - --cookies: Caminho para pje_session.json
  - --modo: "sentenca" ou "decisao"
  - --limite: Número máximo de processos

  **Saída:** processos.json com lista de processos
```

### 6.2 Dependências Listadas (ALTO - 5 pts)

```
[ ] Dependências de sistema listadas?
[ ] Dependências Python/Node listadas?
[ ] Comandos de instalação documentados?

Formato:
  ## Dependências

  **Python:**
  ```bash
  pip install requests beautifulsoup4 pdfplumber
  ```

  **Sistema:**
  - Tesseract OCR (para OCR de PDFs)
  - Poppler (para conversão de PDF)
```

---

## Cálculo do Score

```
YAML Frontmatter:            ___ / 25
Estrutura de Diretório:      ___ / 20
Tags Obrigatórias:           ___ / 35
Tags Recomendadas:           ___ / 15
Ausência Anti-Patterns:      ___ / 15
Scripts e Dependências:      ___ / 10
─────────────────────────────────────
TOTAL:                       ___ / 120
```

### Interpretação

| Score | % | Classificação | Ação |
|-------|---|---------------|------|
| 108-120 | 90%+ | Excelente | Aprovado |
| 96-107 | 80-89% | Bom | Aprovado com observações |
| 84-95 | 70-79% | Regular | Correções recomendadas |
| 72-83 | 60-69% | Insuficiente | Correções necessárias |
| < 72 | < 60% | Reprovado | Refazer seguindo spec |

---

## Checklist Rápido (Versão Resumida)

Para uso diário, versão simplificada:

```
CRÍTICO (deve ter todos):
[ ] YAML frontmatter com name e description
[ ] Localização correta (.claude/skills/[name]/SKILL.md)
[ ] Nome da pasta = campo name do YAML
[ ] Tag <proposito> definindo O QUE e POR QUE
[ ] Tag <quando_usar> com cenários e palavras-chave
[ ] ZERO caminhos absolutos hardcoded
[ ] ZERO credenciais ou secrets no arquivo

ALTO (deve ter maioria):
[ ] SKILL.md < 500 linhas
[ ] Tag <identidade> com <papel> e <estilo>
[ ] Tag <instrucoes> com passos numerados
[ ] Tag <conhecimento> OU <scripts> (ao menos uma)
[ ] Tag <restricoes> com limites operacionais
[ ] Scripts documentados (se houver)
[ ] Dependências listadas (se houver)

RECOMENDADO (nice to have):
[ ] Diretório references/ para docs extensos
[ ] Tag <exemplos> com uso típico
[ ] Tag <casos_de_borda> com edge cases
[ ] Referências cruzadas entre SKILL.md e references/
```

---

## Diferenças entre Agent e Skill

| Aspecto | Agent | Skill |
|---------|-------|-------|
| Localização | `.claude/agents/[name].md` | `.claude/skills/[name]/SKILL.md` |
| Estrutura | Arquivo único | Diretório com SKILL.md + references/ + scripts/ |
| Foco | Capacidade de processamento | Conhecimento + Ferramentas |
| Tag principal | `<capacidade>` | `<proposito>` + `<quando_usar>` |
| Execução | Via Task tool com prompt | Via Skill tool com nome |
| Tamanho | Sem limite rígido | SKILL.md < 500 linhas |

---

**Versão:** 1.0
**Data:** 2026-01-18
**Baseado em:** Template de Skill + Checklist de Agent v1.2
