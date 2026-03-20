# Referência: Contrato de Dados (Avançado)

> **Quando usar:** Apenas para pipelines complexos (10+ etapas) que precisam de documentação formal separada, integração com sistemas externos, ou requisitos de auditoria/compliance.
>
> **Para pipelines simples:** Use a seção `<contratos_dados>` dentro do próprio orquestrador.

---

```markdown
<contrato etapa="[Nome da Etapa]">

  <metadados>
    | Campo | Valor |
    |-------|-------|
    | **Pipeline** | [nome-do-pipeline] |
    | **Etapa** | [número] - [nome] |
    | **Agent** | `.claude/agents/[agent].md` |
    | **Versão** | 1.0 |
  </metadados>

  <entrada>
    <campos>
      | Campo | Tipo | Obrigatório | Descrição |
      |-------|------|-------------|-----------|
      | `[campo_1]` | string | Sim | [Descrição] |
      | `[campo_2]` | string | Não | [Descrição] |
      | `[campo_3]` | array | Sim | [Descrição] |
    </campos>

    <arquivo>
      Caminho: $WORKSPACE/[arquivo-entrada]
      Formato: [TXT|MD|JSON]
      Encoding: UTF-8
    </arquivo>

    <exemplo>
      [Exemplo do conteúdo esperado na entrada]
    </exemplo>
  </entrada>

  <saida>
    <campos>
      | Campo | Tipo | Obrigatório | Descrição |
      |-------|------|-------------|-----------|
      | `[campo_1]` | string | Sim | [Descrição] |
      | `[campo_2]` | string | Sim | [Descrição] |
      | `[campo_3]` | array | Não | [Descrição] |
    </campos>

    <arquivo>
      Caminho: $WORKSPACE/[arquivo-saida]
      Formato: [TXT|MD|JSON]
      Encoding: UTF-8
    </arquivo>

    <estrutura>
      [SINALIZADOR_INICIO]

      [Seção 1]
      [conteúdo]

      [Seção 2]
      [conteúdo]

      [SINALIZADOR_FIM]
    </estrutura>

    <exemplo>
      [Exemplo do conteúdo esperado na saída]
    </exemplo>
  </saida>

  <validacao>
    <sinalizadores>
      | Posição | Texto Obrigatório | Regex |
      |---------|-------------------|-------|
      | Início | `[TEXTO_INICIO]` | `^[TEXTO_INICIO]` |
      | Fim | `[TEXTO_FIM]` | `[TEXTO_FIM]$` |
    </sinalizadores>

    <regras>
      | # | Regra | Tipo | Ação se Falhar |
      |---|-------|------|----------------|
      | 1 | Arquivo existe | CRÍTICO | ERRO |
      | 2 | Tamanho > 0 bytes | CRÍTICO | ERRO |
      | 3 | Sinalizador início presente | FORMATO | REGENERAR |
      | 4 | Sinalizador fim presente | FORMATO | REGENERAR |
      | 5 | Contém acentos (é, á, ã, ç) | FORMATO | REGENERAR |
      | 6 | Sem markdown (*, #) | FORMATO | REGENERAR |
    </regras>

    <sufixo_correcao>
      [FALHA DE FORMATO. Releia o prompt em .claude/agents/[agent].md.
      DEVE começar com "[SINALIZADOR_INICIO]".
      DEVE terminar com "[SINALIZADOR_FIM]".
      Use acentos do português: é, á, ã, ç, ô, ê, í, ú.]
    </sufixo_correcao>
  </validacao>

  <dependencias>
    <anteriores>
      | Etapa | Arquivo Gerado | Usado Como |
      |-------|----------------|------------|
      | [N-1] | [arquivo] | Entrada principal |
      | [N-2] | [arquivo] | Contexto adicional |
    </anteriores>

    <posteriores>
      | Etapa | Usa Este Arquivo Como |
      |-------|----------------------|
      | [N+1] | Entrada principal |
      | [N+2] | Contexto adicional |
    </posteriores>
  </dependencias>

  <erros>
    | Cenário | Causa Provável | Ação |
    |---------|----------------|------|
    | Arquivo não criado | Path incorreto | Verificar variáveis |
    | Arquivo vazio | Agent não executou | Regenerar |
    | Sinalizador ausente | Prompt não seguido | Regenerar + Sufixo |
    | Sem acentos | Normalização indevida | Regenerar + Sufixo |
    | Conteúdo truncado | Timeout ou limite | Aumentar timeout |
  </erros>

  <historico>
    | Versão | Data | Alteração |
    |--------|------|-----------|
    | 1.0 | [data] | Versão inicial |
  </historico>

</contrato>
```

---

## Quando Usar Este Template

| Cenário | Usar Contrato Separado? |
|---------|------------------------|
| Pipeline simples (3-5 etapas) | NÃO - use `<contratos_dados>` no orquestrador |
| Pipeline complexo (10+ etapas) | SIM - documentação separada facilita manutenção |
| Integração com sistema externo | SIM - spec formal necessária |
| Auditoria/Compliance | SIM - documentação rastreável |
| Prototipagem rápida | NÃO - overhead desnecessário |

## Tags XML

| Tag | Obrigatória | Descrição |
|-----|-------------|-----------|
| `<contrato>` | Sim | Raiz com atributo `etapa` |
| `<metadados>` | Sim | Identificação do contrato |
| `<entrada>` | Sim | Especificação do input |
| `<saida>` | Sim | Especificação do output |
| `<validacao>` | Sim | Sinalizadores e regras |
| `<dependencias>` | Sim | Relações com outras etapas |
| `<erros>` | Recomendado | Casos de erro conhecidos |
| `<historico>` | Opcional | Versionamento |

## Checklist de Validação

```
[ ] Atributo etapa preenchido no <contrato>?
[ ] <metadados> com pipeline, etapa, agent e versão?
[ ] <entrada> com campos, arquivo e exemplo?
[ ] <saida> com campos, arquivo, estrutura e exemplo?
[ ] <validacao> com sinalizadores e regras?
[ ] <sufixo_correcao> pronto para retry?
[ ] <dependencias> mapeiam etapas anteriores e posteriores?
```
