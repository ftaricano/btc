# 📧 Configuração de Email - BTC Collector

Este documento explica como configurar o envio automático de emails com os dados de mercado do Bitcoin.

## 🚀 Configuração Rápida

### 1. Arquivo `.env`
Crie ou edite o arquivo `.env` na raiz do projeto:

```env
# Configurações de Email
EMAIL_ENABLED=true
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app_aqui
EMAIL_TO=destinatario1@gmail.com,destinatario2@gmail.com
```

### 2. Exemplo Real
```env
EMAIL_ENABLED=true
EMAIL_USER=btcsepcional@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
EMAIL_TO=btcsepcional@gmail.com,ryan.richard1324@gmail.com
```

## 🔐 Como Obter Senha de App do Gmail

### Passo 1: Ativar Verificação em 2 Etapas
1. Acesse: https://myaccount.google.com/signinoptions/two-step-verification
2. Siga as instruções para ativar
3. **OBRIGATÓRIO** para criar senhas de app

### Passo 2: Criar Senha de App
1. Acesse: https://security.google.com/settings/security/apppasswords
2. Selecione **"Outro (nome personalizado)"**
3. Digite: `BTC Collector`
4. Clique em **"GERAR"**
5. **Copie a senha de 16 caracteres** (ex: `abcd efgh ijkl mnop`)

## 📋 Configurações Detalhadas

### Variáveis de Ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `EMAIL_ENABLED` | Ativar/desativar emails | `true` ou `false` |
| `EMAIL_USER` | Seu email Gmail | `seuemail@gmail.com` |
| `EMAIL_PASSWORD` | Senha de app (16 chars) | `abcd efgh ijkl mnop` |
| `EMAIL_TO` | Destinatários (separados por vírgula) | `email1@gmail.com,email2@gmail.com` |

### Configurações Opcionais (já configuradas internamente)

```python
# Estas configurações já estão no código:
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USE_TLS = True
```

## 📨 O que é Enviado por Email

### Conteúdo do Email
- **Assunto:** "🚀 Relatório BTC/USDT - [Data/Hora]"
- **Dados principais:**
  - Preço atual do BTC
  - VWAP (1h, 4h, diário)
  - Volume de compra/venda
  - Open Interest
  - Taxa de Funding
  - Indicadores técnicos (RSI, MACD, EMAs)
  - Delta Volume e análise de fluxo
  - Imbalance Score
  - Flags de absorção

### Anexos
- **JSON consolidado** otimizado para análise de IA
- Últimos 15 snapshots de dados históricos

## 🚀 Executar com Email

### Coleta Única
```bash
python run_collector.py
```

### Coleta Automatizada (a cada 2 minutos)
```bash
python run_collector_with_email.py
```

## ⚡ Teste de Configuração

### Verificar se email está funcionando:
```bash
# O sistema vai testar a conexão automaticamente
python run_collector_with_email.py
```

### Logs importantes:
```
[OK] Configuração de email OK
[INFO] Email enviado com sucesso!
```

## 🛠️ Solução de Problemas

### Erro: "Configuração de email inválida"
- ✅ Verifique se a senha de app está correta
- ✅ Confirme que verificação em 2 etapas está ativa
- ✅ Use apenas Gmail (outros provedores precisam configuração adicional)

### Erro: "Authentication failed"
- ✅ Regenere uma nova senha de app
- ✅ Certifique-se de copiar a senha COM os espaços
- ✅ Verifique se o email está correto

### Erro de encoding no `.env`
```bash
# Se houver erro de encoding, recrie o arquivo:
Remove-Item -Path ".env" -Force
echo "EMAIL_ENABLED=true" | Out-File -FilePath '.env' -Encoding UTF8
```

## 📊 Exemplo de Email Recebido

```
🚀 Relatório BTC/USDT - 18/06/2025 20:16

=== ANÁLISE DE MERCADO ===
💰 Preço Atual: $104,858.67
📈 VWAP 1h: $105,530.38
📊 VWAP 4h: $105,586.80
📅 VWAP Diário: $94,650.91

=== FLUXO DE MERCADO ===
🔄 Delta Volume: -$430,000.00
⚖️ Imbalance Score: 1.0 (próximo ao ASK)
💹 Funding Rate: 0.0007%

=== INDICADORES TÉCNICOS ===
📊 RSI 14: 55.52
📈 MACD: 143.40
🎯 EMA 9: $104,772.54
🎯 EMA 21: $104,605.05

Arquivo JSON consolidado em anexo para análise detalhada.
```

## 🎯 Configuração Recomendada

### Para Trading Pessoal:
```env
EMAIL_ENABLED=true
EMAIL_USER=seuemail@gmail.com
EMAIL_PASSWORD=sua_senha_de_app
EMAIL_TO=seuemail@gmail.com
```

### Para Equipe/Grupo:
```env
EMAIL_ENABLED=true
EMAIL_USER=bottrading@gmail.com
EMAIL_PASSWORD=senha_de_app_bot
EMAIL_TO=trader1@gmail.com,trader2@gmail.com,analista@gmail.com
```

## 📝 Notas Importantes

- ⚡ **Frequência:** Emails enviados a cada 2 minutos
- 🗂️ **Armazenamento:** Mantém apenas os 15 arquivos mais recentes
- 🤖 **IA:** JSON consolidado otimizado para análise automática
- 🔒 **Segurança:** Use sempre senhas de app, nunca sua senha principal

---

**🚀 Pronto! Com esta configuração você receberá relatórios automáticos profissionais do mercado BTC/USDT!** 