# Template: Skill

> Copie este arquivo para `.claude/skills/[nome-skill]/SKILL.md`

---

```markdown
---
name: [nome-da-skill]
description: >
  [Descrição do que a skill faz E quando usá-la - max 1024 caracteres.
  Inclua palavras-chave que Claude usará para detectar quando ativar.
  Exemplo: "Extrai texto de PDFs e preenche formulários. Use quando
  o usuário mencionar PDF, formulário, extração de documento."]

# === CAMPOS DE ISOLAMENTO (v2.7 - para contexto isolado) ===
context: fork
agent: general-purpose
allowed-tools: Bash Read Write

# === CAMPOS OPCIONAIS (remova se não usar) ===
license: [nome-da-licença ou "Ver LICENSE.txt"]
compatibility: >
  [Requisitos de ambiente. Ex: "Requer Python 3.10+, poppler-utils.
  Projetado para Claude Code."]
metadata:
  author: [nome-ou-organizacao]
  version: "[1.0.0]"
---

<!--
  ESTRUTURA DO CORPO (alinhada com spec oficial):

  A spec recomenda: "Step-by-step instructions, examples, edge cases"
  Nosso mapeamento em XML:

  | Spec Oficial              | Tag XML Super Jurista      |
  |---------------------------|----------------------------|
  | (identidade/contexto)     | <identidade>               |
  | (propósito/objetivo)      | <proposito>                |
  | When to use               | <quando_usar>              |
  | Step-by-step instructions | <instrucoes>               |
  | (conhecimento/domínio)    | <conhecimento>             |
  | (scripts executáveis)     | <scripts>                  |
  | Examples                  | <exemplos>                 |
  | Edge cases                | <casos_de_borda>           |
  | (referências adicionais)  | <referencias>              |
-->

<identidade>
  <papel>[Definição do papel - que expertise esta skill representa]</papel>
  <dominio>[Área de conhecimento ou atuação]</dominio>
</identidade>

<proposito>
  <objetivo>[O que a skill permite fazer]</objetivo>
  <razao>[Por que usar esta skill]</razao>
</proposito>

<quando_usar>
  <!-- IMPORTANTE: Liste palavras-chave que disparam a ativação -->
  <ativar_quando>
    - Usuário pede para "[verbo-gatilho-1]" um documento
    - Usuário menciona "[termo-chave-1]" ou "[termo-chave-2]"
    - Usuário quer "[ação-específica]"
  </ativar_quando>

  <nao_usar_quando>
    - [Situação em que NÃO deve usar]
    - [Outra situação inadequada]
  </nao_usar_quando>
</quando_usar>

<instrucoes>
  <!--
    STEP-BY-STEP INSTRUCTIONS (recomendação oficial da spec)
    Descreva o fluxo de uso da skill passo a passo.
  -->

  <passo numero="1" nome="[Nome do Passo]">
    [Descrição do que fazer neste passo]
  </passo>

  <passo numero="2" nome="[Nome do Passo]">
    [Descrição do que fazer neste passo]
  </passo>

  <passo numero="3" nome="[Nome do Passo]">
    [Descrição do que fazer neste passo]
  </passo>
</instrucoes>

<conhecimento>
  <!--
    ECONOMIA DE TOKENS (Progressive Disclosure):
    - Mantenha esta seção concisa (<500 linhas total no SKILL.md)
    - Mova conteúdo detalhado para references/
    - Claude carrega references/ sob demanda
  -->

  <topico nome="[Tópico 1]">
    [Explicação concisa do conhecimento relevante]
  </topico>

  <topico nome="[Tópico 2]">
    [Explicação concisa]
    <!-- Para detalhes: Ver references/[topico-2].md -->
  </topico>
</conhecimento>

<scripts>
  <!-- Opcional: Se a skill incluir scripts executáveis -->

  <script nome="[Nome do Script]">
    <comando>python .claude/skills/[nome-skill]/scripts/[script].py [ARGUMENTOS]</comando>

    <parametros>
      | Parâmetro | Tipo | Obrigatório | Descrição |
      |-----------|------|-------------|-----------|
      | `[arg1]` | string | Sim | [Descrição] |
      | `[arg2]` | string | Não | [Descrição] |
    </parametros>

    <saida>[arquivo ou diretório de saída]</saida>
  </script>
</scripts>

<exemplos>
  <!--
    EXAMPLES (recomendação oficial da spec)
    Mostre inputs e outputs concretos.
  -->

  <exemplo cenario="[Cenário típico de uso]">
    <entrada>[Input do usuário ou comando]</entrada>
    <saida>[Output esperado]</saida>
  </exemplo>

  <exemplo cenario="[Outro cenário]">
    <entrada>[Input do usuário ou comando]</entrada>
    <saida>[Output esperado]</saida>
  </exemplo>
</exemplos>

<casos_de_borda>
  <!--
    EDGE CASES (recomendação oficial da spec)
    Documente situações especiais e como lidar.
  -->

  <caso nome="[Situação especial]">
    <problema>[Descrição do problema]</problema>
    <solucao>[Como a skill deve lidar]</solucao>
  </caso>
</casos_de_borda>

<referencias>
  <!--
    Use caminhos RELATIVOS a partir da raiz da skill.
    Mantenha referências em um nível de profundidade.
  -->
  - [references/REFERENCE.md](references/REFERENCE.md) - Documentação técnica detalhada
  - [references/[topico].md](references/[topico].md) - [Descrição]
</referencias>

<pre_requisitos>
  <!-- Opcional: Dependências necessárias -->
  - [Dependência 1] - `comando de instalação`
  - [Dependência 2] - `comando de instalação`
</pre_requisitos>
```

---

## Estrutura de Diretórios (Padrão Anthropic)

```
.claude/skills/[nome-skill]/
├── SKILL.md              # Obrigatório: instruções principais (<500 linhas)
├── references/           # Opcional: documentação detalhada (carregada sob demanda)
│   ├── REFERENCE.md      # Referência técnica principal
│   ├── [topico-1].md
│   └── [topico-2].md
├── scripts/              # Opcional: scripts executáveis
│   ├── [script-1].py
│   └── [script-2].sh
└── assets/               # Opcional: recursos estáticos
    ├── templates/        # Templates de documento/configuração
    ├── images/           # Diagramas, exemplos visuais
    └── data/             # Lookup tables, schemas
```

---

## Guia de Preenchimento

### YAML Frontmatter

| Campo | Obrigatório | Constraints | Descrição |
|-------|-------------|-------------|-----------|
| `name` | **Sim** | Max 64 chars, lowercase+hyphens, deve coincidir com nome da pasta | Identificador único |
| `description` | **Sim** | Max 1024 chars | O que faz + quando usar + palavras-chave |
| `license` | Não | - | Nome da licença ou referência a arquivo |
| `compatibility` | Não | Max 500 chars | Requisitos de ambiente |
| `metadata` | Não | key-value strings | author, version, etc. |
| `allowed-tools` | Não | Space-delimited | Tools pré-aprovadas (experimental) |

### Campos de Isolamento (v2.7)

| Campo | Obrigatorio | Quando Usar | Descricao |
|-------|-------------|-------------|-----------|
| `context` | Nao | Skills com output verboso | `fork` = executa em sub-agente isolado |
| `agent` | Condicional | Junto com `context: fork` | Tipo: `general-purpose`, `Explore`, `Plan` |

**Quando usar `context: fork`:**
- Skill executa scripts que geram muito output
- Voce quer isolamento de contexto (output nao polui conversa)
- Skill e auto-contida (entrada → processamento → saida resumida)

**Exemplo com fork:**
```yaml
---
name: processar-documento
description: Processa documento com output isolado
context: fork
agent: general-purpose
allowed-tools: Bash Read Write
---

REGRA: Execute os scripts. NAO crie codigo novo.

Retorne APENAS: status, caminhos, estatisticas.
```

**Beneficios:**
1. Output verboso fica contido no sub-agente
2. Conversa principal recebe apenas resumo
3. Modelo segue instrucoes (contexto limpo)
4. Economia de tokens

### Regras para o Campo `name`

**Válidos:**
```yaml
name: pdf-processing
name: data-analysis
name: pesquisa-juridica
```

**Inválidos:**
```yaml
name: PDF-Processing      # maiúsculas não permitidas
name: -pdf                # não pode começar com hífen
name: pdf--processing     # hífens consecutivos não permitidos
name: pdf_processing      # underscore não permitido
```

### Regras para o Campo `description`

**Bom** (descreve O QUE + QUANDO + palavras-chave):
```yaml
description: >
  Extrai texto e tabelas de arquivos PDF, preenche formulários PDF e
  mescla múltiplos PDFs. Use quando trabalhar com documentos PDF ou
  quando o usuário mencionar PDFs, formulários ou extração de documentos.
```

**Ruim** (muito vago):
```yaml
description: Ajuda com PDFs.
```

### Tags XML (Mapeamento com Spec Oficial)

| Tag | Obrigatória | Spec Oficial | Descrição |
|-----|-------------|--------------|-----------|
| `<identidade>` | Sim | (contexto) | Papel e domínio da skill |
| `<proposito>` | Sim | (objetivo) | Objetivo e razão de uso |
| `<quando_usar>` | Sim | "When to use" | Gatilhos de ativação e situações inadequadas |
| `<instrucoes>` | **Sim** | **"Step-by-step instructions"** | Fluxo de uso passo a passo |
| `<conhecimento>` | Condicional* | (domínio) | Se skill é de conhecimento |
| `<scripts>` | Condicional* | (executáveis) | Se skill tem scripts |
| `<exemplos>` | **Recomendado** | **"Examples"** | Inputs/outputs concretos |
| `<casos_de_borda>` | **Recomendado** | **"Edge cases"** | Situações especiais |
| `<referencias>` | Opcional | (adicional) | Links para docs detalhadas |
| `<pre_requisitos>` | Condicional | (dependências) | Se houver dependências |

*Uma skill deve ter pelo menos `<conhecimento>` OU `<scripts>`.

**Negrito** = Recomendação explícita da spec oficial.

### Progressive Disclosure (Economia de Tokens)

```
┌─────────────────────────────────────────────────────────────────┐
│  CARREGAMENTO EM CAMADAS                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Nível 1: METADATA (~100 tokens)                                │
│  └─ Carregado no STARTUP                                        │
│  └─ Campos: name, description                                   │
│                                                                 │
│  Nível 2: SKILL.md (<5000 tokens recomendado)                   │
│  └─ Carregado quando ATIVADO                                    │
│  └─ Instruções principais, exemplos essenciais                  │
│                                                                 │
│  Nível 3: references/ (sob demanda)                             │
│  └─ Carregado quando NECESSÁRIO                                 │
│  └─ Documentação técnica detalhada                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Tipos de Skill

| Tipo | Conteúdo | Exemplo |
|------|----------|---------|
| **Conhecimento** | SKILL.md + references/ | pesquisa-precedentes |
| **Scripts** | SKILL.md + scripts/ | pje-integration |
| **Híbrida** | Conhecimento + Scripts | conversao-pdf |
| **Recursos** | SKILL.md + assets/ | brand-guidelines |

### Checklist de Validação

```
YAML Frontmatter:
[ ] name em lowercase com hífens, coincide com nome da pasta?
[ ] description descreve O QUE faz + QUANDO usar + palavras-chave?
[ ] description tem menos de 1024 caracteres?
[ ] allowed-tools sem colchetes (formato: "Read Write Bash")?

Estrutura:
[ ] SKILL.md tem menos de 500 linhas?
[ ] Diretório references/ (não reference/)?
[ ] Caminhos relativos nas referências?

Conteúdo XML (alinhado com spec oficial):
[ ] <identidade> define papel e domínio?
[ ] <proposito> explica objetivo e razão?
[ ] <quando_usar> tem gatilhos claros e situações inadequadas?
[ ] <instrucoes> tem passos numerados? (SPEC: "Step-by-step instructions")
[ ] <conhecimento> OU <scripts> documentados?
[ ] <exemplos> com inputs e outputs? (SPEC: "Examples")
[ ] <casos_de_borda> para situações especiais? (SPEC: "Edge cases")

Progressive Disclosure:
[ ] Conteúdo detalhado movido para references/?
[ ] SKILL.md focado em instruções essenciais?
```

---

## Validação via CLI (Opcional)

Se disponível, use a ferramenta de referência:

```bash
skills-ref validate ./minha-skill
```

Valida:
- Frontmatter válido
- Convenções de nomenclatura
- Campos obrigatórios presentes

---

## Exemplo Completo

Skill de processamento de PDF seguindo todas as recomendações da spec oficial:

```markdown
---
name: pdf-processing
description: >
  Extrai texto e tabelas de arquivos PDF, preenche formulários PDF e
  mescla múltiplos PDFs. Use quando trabalhar com documentos PDF ou
  quando o usuário mencionar PDFs, formulários ou extração de documentos.
license: Apache-2.0
compatibility: >
  Requer Python 3.8+ e biblioteca pdfplumber.
  Projetado para Claude Code.
metadata:
  author: super-jurista
  version: "1.0.0"
  category: document-processing
allowed-tools: Read Write Bash
---

<!--
  Mapeamento com spec oficial:
  - Step-by-step instructions → <instrucoes>
  - Examples → <exemplos>
  - Edge cases → <casos_de_borda>
-->

<identidade>
  <papel>Especialista em processamento de documentos PDF</papel>
  <dominio>Extração de dados, manipulação e conversão de PDFs</dominio>
</identidade>

<proposito>
  <objetivo>Permitir extração, preenchimento e mesclagem de PDFs</objetivo>
  <razao>Automatizar tarefas repetitivas com documentos PDF</razao>
</proposito>

<quando_usar>
  <ativar_quando>
    - Usuário pede para "extrair texto" de um PDF
    - Usuário menciona "PDF", "formulário" ou "documento"
    - Usuário quer "mesclar" ou "combinar" arquivos PDF
    - Usuário precisa "preencher" um formulário PDF
  </ativar_quando>

  <nao_usar_quando>
    - Documento não é PDF (use conversão primeiro)
    - PDF é apenas imagem escaneada sem OCR
    - Usuário quer editar layout/design do PDF
  </nao_usar_quando>
</quando_usar>

<instrucoes>
  <passo numero="1" nome="Verificar arquivo">
    Confirme que o arquivo existe e é um PDF válido.
    Use: file [caminho] ou python -c "import PyPDF2; ..."
  </passo>

  <passo numero="2" nome="Escolher operação">
    Identifique a operação desejada:
    - Extração de texto → usar extract_text.py
    - Extração de tabelas → usar extract_tables.py
    - Preenchimento de formulário → usar fill_form.py
    - Mesclagem → usar merge_pdfs.py
  </passo>

  <passo numero="3" nome="Executar script">
    Execute o script apropriado com os parâmetros corretos.
    Verifique o output e reporte ao usuário.
  </passo>

  <passo numero="4" nome="Validar resultado">
    Confirme que o arquivo de saída foi gerado corretamente.
    Informe o caminho e tamanho do arquivo resultante.
  </passo>
</instrucoes>

<conhecimento>
  <topico nome="Formatos suportados">
    - PDF 1.0 a 2.0
    - PDFs com texto selecionável
    - Formulários AcroForm e XFA
    <!-- Para detalhes técnicos: Ver references/formatos.md -->
  </topico>

  <topico nome="Limitações">
    - PDFs escaneados requerem OCR prévio
    - Formulários XFA têm suporte limitado
    - Arquivos protegidos por senha requerem desbloqueio
  </topico>
</conhecimento>

<scripts>
  <script nome="Extrair Texto">
    <comando>python .claude/skills/pdf-processing/scripts/extract_text.py INPUT OUTPUT</comando>
    <parametros>
      | Parâmetro | Tipo | Obrigatório | Descrição |
      |-----------|------|-------------|-----------|
      | `INPUT` | string | Sim | Caminho do PDF de entrada |
      | `OUTPUT` | string | Sim | Caminho do TXT de saída |
    </parametros>
    <saida>Arquivo .txt com texto extraído</saida>
  </script>

  <script nome="Mesclar PDFs">
    <comando>python .claude/skills/pdf-processing/scripts/merge_pdfs.py OUTPUT INPUT1 INPUT2 ...</comando>
    <parametros>
      | Parâmetro | Tipo | Obrigatório | Descrição |
      |-----------|------|-------------|-----------|
      | `OUTPUT` | string | Sim | Caminho do PDF mesclado |
      | `INPUT*` | string | Sim | Caminhos dos PDFs a mesclar |
    </parametros>
    <saida>Arquivo PDF único com todos os documentos</saida>
  </script>
</scripts>

<exemplos>
  <exemplo cenario="Extrair texto de um contrato">
    <entrada>Extraia o texto do arquivo contrato.pdf</entrada>
    <saida>
      Executando: python scripts/extract_text.py contrato.pdf contrato.txt
      Texto extraído com sucesso: contrato.txt (15.2 KB, 3 páginas)
    </saida>
  </exemplo>

  <exemplo cenario="Mesclar relatórios mensais">
    <entrada>Junte os PDFs janeiro.pdf, fevereiro.pdf e marco.pdf em um único arquivo</entrada>
    <saida>
      Executando: python scripts/merge_pdfs.py trimestre-q1.pdf janeiro.pdf fevereiro.pdf marco.pdf
      PDFs mesclados com sucesso: trimestre-q1.pdf (45 páginas)
    </saida>
  </exemplo>
</exemplos>

<casos_de_borda>
  <caso nome="PDF escaneado (imagem)">
    <problema>PDF contém apenas imagens, sem texto selecionável</problema>
    <solucao>Informar usuário que OCR é necessário. Sugerir ferramenta como Tesseract ou Adobe Acrobat.</solucao>
  </caso>

  <caso nome="PDF protegido por senha">
    <problema>Arquivo requer senha para abrir ou editar</problema>
    <solucao>Solicitar senha ao usuário. Se não tiver, informar impossibilidade de processamento.</solucao>
  </caso>

  <caso nome="PDF corrompido">
    <problema>Arquivo não pode ser lido (estrutura inválida)</problema>
    <solucao>Tentar reparo com qpdf --check. Se falhar, informar que arquivo está corrompido.</solucao>
  </caso>
</casos_de_borda>

<referencias>
  - [references/REFERENCE.md](references/REFERENCE.md) - Documentação técnica completa
  - [references/formatos.md](references/formatos.md) - Detalhes sobre formatos PDF suportados
  - [pdfplumber docs](https://github.com/jsvine/pdfplumber) - Biblioteca principal
</referencias>

<pre_requisitos>
  - Python 3.8+ - `python --version`
  - pdfplumber - `pip install pdfplumber`
  - PyPDF2 - `pip install PyPDF2`
</pre_requisitos>
```
