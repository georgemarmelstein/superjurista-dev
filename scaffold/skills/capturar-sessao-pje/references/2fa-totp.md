# 2FA (Google Authenticator) no login do PJE — referência operacional

Desde a versão 2.11 do PJe TRF5 (05/07/2026), o login exige um código de 6 dígitos do
Google Authenticator. Este documento explica como o sistema gera esse código sozinho e
como operar/consertar. Registro histórico da mudança:
`docs/plans/2026-07-10-2fa-totp-pje.md`.

## Ideia central

O código do Google Authenticator é um **TOTP** (RFC 6238): deriva de um **seed**
(segredo base32 fixo) + relógio, em janelas de 30s. Com o mesmo seed, qualquer software
produz o mesmo código do celular. Guardamos o seed no `.env` e geramos o código por
software — o celular vira backup.

## Configuração (uma vez)

1. Obtenha o **seed** (ver "Como obter o seed" abaixo).
2. No `.env` da raiz do projeto (gitignored), preencha:
   ```
   PJE_TOTP_SEED=cole-a-chave-base32-aqui
   ```
   Pode colar com ou sem espaços; o gerador normaliza. Sem aspas.
3. Dependência: `pip install pyotp`.

## Uso

```bash
# Imprime SO os 6 digitos (para o passo de login consumir)
python .claude/skills/capturar-sessao-pje/scripts/gerar_totp.py

# Verboso: mostra os segundos restantes na janela atual
python .claude/skills/capturar-sessao-pje/scripts/gerar_totp.py -v

# Seed explicito (util para testar comparando com o celular)
python .claude/skills/capturar-sessao-pje/scripts/gerar_totp.py --seed "JBSW Y3DP ..."
```

No fluxo da skill, isso acontece na **Etapa 4.5** do `SKILL.md`: após o ENTRAR, se a
tela do autenticador aparecer, o gerador roda e o código é digitado automaticamente.
Gere o código **imediatamente antes** de digitar — ele vale ~30s.

## Como obter o seed

O Keycloak **nunca reexibe** o seed de um autenticador já cadastrado; ele só aparece ao
cadastrar um novo. Dois caminhos:

**A) Re-cadastrar (revela a chave em texto):**
1. Acesse `https://sso.cloud.pje.jus.br/auth/realms/pje/account/totp`
   (a entrada "Segundo fator" fica oculta no menu do tema antigo — use a URL direta).
2. Remova o autenticador atual (ícone de lixeira).
3. A tela mostra um QR + "não consegue escanear? use esta chave" — **essa chave é o
   seed**. Copie para o `.env`.
4. Reescaneie o novo QR no Google Authenticator do celular (backup) e conclua o
   cadastro com um código de confirmação (pode ser gerado pelo `gerar_totp.py`).
   Faça de uma vez só: entre remover e recadastrar, a conta fica sem 2FA.

**B) Exportar (não mexe no cadastro):** no app Google Authenticator,
*Transferir contas → Exportar*, gere o QR de migração (`otpauth-migration://offline?data=...`)
e decodifique para extrair o seed.

## Solução de problemas

| Sintoma | Causa provável | Remédio |
|---------|----------------|---------|
| Código não bate com o celular | Relógio do Windows desregulado | Sincronizar hora (tolerância ~30s) |
| Código não bate com o celular | Seed copiado errado | Reconferir `PJE_TOTP_SEED` (sem espaço/char a mais) |
| `[ERRO] Seed nao encontrado` | `PJE_TOTP_SEED` vazio no `.env` | Preencher o seed |
| `[ERRO] Seed invalido` | Não é base32 válido | Recopiar a chave (só A-Z e 2-7) |
| Login falha mesmo com 2FA OK | Cookies/cache antigos (PJe 2.11) | Limpar cookies/cache do PJe |
| PJe não pede o código (entra direto) | Sessão SSO ainda ativa | Normal — não há 2FA a preencher |

## Segurança

O seed é **credencial forte** — equivale a poder gerar o segundo fator. Regras:
- Fica só no `.env` (gitignored). Nunca versionar, nunca logar, nunca imprimir.
- O `gerar_totp.py` devolve apenas os 6 dígitos, jamais o seed.
- Guardar o seed junto da senha aproxima o 2FA de um fator só naquela máquina — trade-off
  aceito para automação pessoal, desde que o seed fique protegido.
