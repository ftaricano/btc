import smtplib
import json
import os
import glob
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from typing import Dict, Optional

class EmailSender:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.load_config()

    def load_config(self):
        """Carrega configurações do email"""
        self.email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.email_port = int(os.getenv('EMAIL_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.email_from = os.getenv('EMAIL_FROM', self.email_user)
        
        # Suporte para múltiplos destinatários separados por vírgula
        email_to_raw = os.getenv('EMAIL_TO', '')
        self.email_to_list = [email.strip() for email in email_to_raw.split(',') if email.strip()]
        self.email_to = ', '.join(self.email_to_list)  # Para compatibilidade
        
        self.subject_prefix = os.getenv('EMAIL_SUBJECT_PREFIX', '[BTC Market Data]')
        self.email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'

    def create_market_summary_html(self, market_data: Dict) -> str:
        """Cria um resumo HTML dos dados de mercado"""
        def format_number(num):
            if num >= 1e9:
                return f"{num/1e9:.2f}B"
            elif num >= 1e6:
                return f"{num/1e6:.2f}M"
            elif num >= 1e3:
                return f"{num/1e3:.2f}K"
            return f"{num:.2f}"

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 25px; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px; }}
                .section h3 {{ color: #495057; margin-top: 0; }}
                .metric {{ margin: 8px 0; }}
                .metric strong {{ color: #343a40; }}
                .positive {{ color: #28a745; }}
                .negative {{ color: #dc3545; }}
                .neutral {{ color: #6c757d; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📊 Relatório de Mercado - Bitcoin (BTC/USDT)</h2>
                <p><strong>Timestamp:</strong> {market_data['timestamp']}</p>
                <p><strong>Preço Atual:</strong> ${market_data['current_price']:,.2f} USDT</p>
            </div>

            <div class="section">
                <h3>📚 Order Book</h3>
                <div style="display: flex; gap: 20px;">
                    <div style="flex: 1;">
                        <h4>Top 5 Bids (Compra)</h4>
                        <table>
                            <tr><th>Preço</th><th>Quantidade</th></tr>
        """

        # Top Bids
        for price, qty in market_data['order_book']['top']['bids'][:5]:
            html += f"<tr><td>${price:,.2f}</td><td>{qty:.4f} BTC</td></tr>"
        
        html += """
                        </table>
                    </div>
                    <div style="flex: 1;">
                        <h4>Top 5 Asks (Venda)</h4>
                        <table>
                            <tr><th>Preço</th><th>Quantidade</th></tr>
        """

        # Top Asks
        for price, qty in market_data['order_book']['top']['asks'][:5]:
            html += f"<tr><td>${price:,.2f}</td><td>{qty:.4f} BTC</td></tr>"

        # Imbalance
        imbalance = market_data['order_book']['imbalance_pct']
        imbalance_class = 'positive' if imbalance > 0 else 'negative' if imbalance < 0 else 'neutral'
        imbalance_text = 'pressão compradora' if imbalance > 0 else 'pressão vendedora' if imbalance < 0 else 'equilibrado'

        html += f"""
                        </table>
                    </div>
                </div>
                <div class="metric">
                    <strong>Imbalance:</strong> <span class="{imbalance_class}">{imbalance:+.1f}% ({imbalance_text})</span>
                </div>
            </div>

            <div class="section">
                <h3>📈 Derivativos</h3>
                <div class="metric"><strong>Open Interest (USD):</strong> {format_number(market_data['derivatives']['open_interest_usd'])} USDT</div>
                <div class="metric"><strong>Open Interest (BTC):</strong> {format_number(market_data['derivatives']['open_interest_coin'])} BTC</div>
                <div class="metric"><strong>Variação OI 4h:</strong> {market_data['derivatives']['oi_change_4h_pct']:.2f}%</div>
                <div class="metric"><strong>Taxa de Funding:</strong> {market_data['derivatives']['funding_rate']*100:.4f}%</div>
                <div class="metric"><strong>Próximo Funding:</strong> {market_data['derivatives']['funding_next']}</div>
            </div>

            <div class="section">
                <h3>📊 Volume 24h</h3>
                <div class="metric"><strong>Volume Total:</strong> {format_number(market_data['stats']['volume_24h'])} USDT</div>
                <div class="metric"><strong>Volume Compra:</strong> {format_number(market_data['stats']['taker_buy_vol_24h'])} USDT</div>
                <div class="metric"><strong>Volume Venda:</strong> {format_number(market_data['stats']['taker_sell_vol_24h'])} USDT</div>
            </div>

            <div class="section">
                <h3>⚡ Liquidações 24h</h3>
        """

        if 'liquidations' in market_data:
            liq = market_data['liquidations']
            html += f"""
                <div class="metric"><strong>Liquidações Long:</strong> ${liq['long_liqs_24h']:,.2f} USDT</div>
                <div class="metric"><strong>Liquidações Short:</strong> ${liq['short_liqs_24h']:,.2f} USDT</div>
                <div class="metric"><strong>Total Liquidações:</strong> ${liq['total_liqs_24h']:,.2f} USDT</div>
            """
        else:
            html += "<div class='metric'>Liquidações: Não disponível</div>"

        html += """
            </div>

            <div class="section">
                <h3>📈 Indicadores Técnicos (15m)</h3>
        """

        indicators = market_data['timeframes']['15m']['indicators']
        
        # RSI
        if 'rsi_14' in indicators.get('rsi', {}):
            rsi_val = indicators['rsi']['rsi_14']
            if rsi_val is not None:
                rsi_class = 'positive' if rsi_val > 70 else 'negative' if rsi_val < 30 else 'neutral'
                html += f"<div class='metric'><strong>RSI 14:</strong> <span class='{rsi_class}'>{rsi_val:.2f}</span></div>"

        # MACD
        if 'macd' in indicators.get('macd', {}):
            macd_val = indicators['macd'].get('macd')
            if macd_val is not None:
                signal_val = indicators['macd'].get('macd_signal')
                hist_val = indicators['macd'].get('macd_hist')
                html += f"""
                <div class="metric"><strong>MACD:</strong> {macd_val:.2f}</div>
                <div class="metric"><strong>Signal:</strong> {signal_val:.2f}</div>
                <div class="metric"><strong>Histograma:</strong> {hist_val:.2f}</div>
                """

        html += """
            </div>

            <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; text-align: center; color: #6c757d;">
                <small>Este relatório foi gerado automaticamente pelo sistema de coleta de dados BTC</small>
            </div>
        </body>
        </html>
        """

        return html

    def send_market_data(self, market_data: Dict, attach_json: bool = True, json_folder: str = None, consolidated_file: str = None) -> bool:
        """Envia email com dados de mercado"""
        if not self.email_enabled:
            self.logger.info("Email desabilitado via configuração")
            return False

        if not self.email_user or not self.email_password or not self.email_to:
            self.logger.error("Configurações de email incompletas")
            return False

        try:
            # Cria a mensagem
            msg = MIMEMultipart('alternative')
            
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            price = market_data['current_price']
            
            msg['Subject'] = f"{self.subject_prefix} BTC: ${price:,.2f} - {timestamp}"
            msg['From'] = self.email_from
            msg['To'] = self.email_to

            # Texto simples
            text_content = f"""
Relatório de Mercado - Bitcoin (BTC/USDT)
Timestamp: {market_data['timestamp']}
Preço Atual: ${market_data['current_price']:,.2f} USDT

Para ver o relatório completo, visualize este email em HTML ou consulte o arquivo JSON anexo.
            """

            # HTML formatado
            html_content = self.create_market_summary_html(market_data)

            # Anexa as partes
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)

            # Anexa JSONs individuais se solicitado
            if attach_json and json_folder and os.path.exists(json_folder):
                # Anexa todos os JSONs da pasta
                json_files = glob.glob(os.path.join(json_folder, "market_data_2*.json"))  # Só individuais
                json_files.sort(key=os.path.getmtime, reverse=True)  # Mais recentes primeiro
                
                attached_count = 0
                for json_file in json_files:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            json_content = f.read()
                        
                        attachment = MIMEBase('application', 'json')
                        attachment.set_payload(json_content.encode('utf-8'))
                        encoders.encode_base64(attachment)
                        
                        filename = os.path.basename(json_file)
                        attachment.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{filename}"'
                        )
                        msg.attach(attachment)
                        attached_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Erro ao anexar {json_file}: {str(e)}")
                
                self.logger.info(f"[ATTACH] {attached_count} arquivo(s) JSON individuais anexado(s)")
            
            # Anexa o arquivo consolidado se existir (SEMPRE, independente do attach_json)
            if consolidated_file and os.path.exists(consolidated_file):
                try:
                    with open(consolidated_file, 'r', encoding='utf-8') as f:
                        consolidated_content = f.read()
                    
                    consolidated_attachment = MIMEBase('application', 'json')
                    consolidated_attachment.set_payload(consolidated_content.encode('utf-8'))
                    encoders.encode_base64(consolidated_attachment)
                    
                    consolidated_attachment.add_header(
                        'Content-Disposition',
                        f'attachment; filename="market_data_consolidated_for_ai.json"'
                    )
                    msg.attach(consolidated_attachment)
                    self.logger.info("[AI-FILE] Arquivo consolidado anexado")
                    
                except Exception as e:
                    self.logger.error(f"[ERROR] Erro ao anexar arquivo consolidado: {str(e)}")
            
            # Anexa JSON atual se não há pasta nem consolidado
            if attach_json and not json_folder and not consolidated_file:
                # Comportamento padrão - apenas o JSON atual
                json_data = json.dumps(market_data, indent=2, ensure_ascii=False)
                
                attachment = MIMEBase('application', 'json')
                attachment.set_payload(json_data.encode('utf-8'))
                encoders.encode_base64(attachment)
                
                timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
                attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename="market_data_{timestamp_file}.json"'
                )
                msg.attach(attachment)
                self.logger.info("[ATTACH] 1 arquivo JSON atual anexado")

            # Envia o email
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            
            server.send_message(msg)
            server.quit()

            self.logger.info(f"Email enviado com sucesso para {self.email_to}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """Testa a conexão com o servidor de email"""
        if not self.email_user or not self.email_password:
            self.logger.error("Credenciais de email não configuradas")
            return False

        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.quit()
            
            self.logger.info("Conexão com servidor de email testada com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao testar conexão de email: {str(e)}")
            return False 