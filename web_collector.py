#!/usr/bin/env python3
"""
Versão Web do Coletor de Dados BTC
Acesse pelo navegador do celular em: http://seu-ip:8080
"""

from flask import Flask, jsonify, render_template_string
import json
from datetime import datetime
from src.market_data_collector import MarketDataCollector

app = Flask(__name__)

# Template HTML simples
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BTC Market Data Collector</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #1a1a1a; 
            color: #fff; 
        }
        .container { max-width: 800px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .btn { 
            background: #f7931a; 
            color: white; 
            padding: 15px 30px; 
            border: none; 
            border-radius: 5px; 
            font-size: 16px; 
            cursor: pointer; 
            margin: 10px;
            width: 100%;
            max-width: 300px;
        }
        .btn:hover { background: #e8851f; }
        .json-output { 
            background: #2d2d2d; 
            padding: 20px; 
            border-radius: 5px; 
            white-space: pre-wrap; 
            font-family: monospace; 
            font-size: 12px;
            max-height: 500px;
            overflow-y: auto;
            margin-top: 20px;
        }
        .loading { 
            text-align: center; 
            color: #f7931a; 
            font-size: 18px;
            display: none;
        }
        .copy-btn {
            background: #28a745;
            margin-top: 10px;
            max-width: 200px;
        }
        .copy-btn:hover { background: #218838; }
        .status { 
            padding: 10px; 
            border-radius: 5px; 
            margin: 10px 0;
            text-align: center;
        }
        .success { background: #28a745; }
        .error { background: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 BTC Market Data Collector</h1>
            <p>Coleta dados em tempo real da Binance Futures</p>
        </div>
        
        <div style="text-align: center;">
            <button class="btn" onclick="collectData()">📊 Coletar Dados</button>
            <button class="btn" onclick="autoRefresh()">🔄 Auto Refresh (30s)</button>
        </div>
        
        <div id="loading" class="loading">
            <p>⏳ Coletando dados... Aguarde...</p>
        </div>
        
        <div id="status"></div>
        
        <div id="json-container" style="display: none;">
            <button class="btn copy-btn" onclick="copyToClipboard()">📋 Copiar JSON</button>
            <div id="json-output" class="json-output"></div>
        </div>
    </div>

    <script>
        let autoRefreshInterval = null;
        
        async function collectData() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('json-container').style.display = 'none';
            document.getElementById('status').innerHTML = '';
            
            try {
                const response = await fetch('/api/collect');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('json-output').textContent = JSON.stringify(data.data, null, 2);
                    document.getElementById('json-container').style.display = 'block';
                    showStatus('✅ Dados coletados com sucesso!', 'success');
                } else {
                    showStatus('❌ Erro: ' + data.error, 'error');
                }
            } catch (error) {
                showStatus('❌ Erro de conexão: ' + error.message, 'error');
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function copyToClipboard() {
            const jsonText = document.getElementById('json-output').textContent;
            navigator.clipboard.writeText(jsonText).then(() => {
                showStatus('📋 JSON copiado para a área de transferência!', 'success');
            }).catch(() => {
                // Fallback para dispositivos mais antigos
                const textArea = document.createElement('textarea');
                textArea.value = jsonText;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showStatus('📋 JSON copiado!', 'success');
            });
        }
        
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.innerHTML = `<div class="status ${type}">${message}</div>`;
            setTimeout(() => {
                status.innerHTML = '';
            }, 3000);
        }
        
        function autoRefresh() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
                showStatus('🛑 Auto refresh desativado', 'success');
                return;
            }
            
            autoRefreshInterval = setInterval(collectData, 30000);
            showStatus('🔄 Auto refresh ativado (30s)', 'success');
            collectData(); // Primeira coleta imediata
        }
        
        // Coleta inicial ao carregar a página
        window.onload = function() {
            collectData();
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Página principal"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/collect')
def api_collect():
    """API para coletar dados"""
    try:
        # Inicializa o coletor
        collector = MarketDataCollector()
        
        # Coleta os dados
        data = collector.collect_market_data()
        
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/json')
def api_json():
    """Retorna apenas o JSON dos dados"""
    try:
        collector = MarketDataCollector()
        data = collector.collect_market_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Iniciando servidor web...")
    print("📱 Acesse pelo celular em:")
    print("   http://localhost:8080")
    print("   http://seu-ip-local:8080")
    print("\n💡 Para descobrir seu IP:")
    print("   Windows: ipconfig")
    print("   Mac/Linux: ifconfig")
    print("\n🛑 Pressione Ctrl+C para parar")
    
    app.run(host='0.0.0.0', port=8080, debug=False) 