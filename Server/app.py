from flask import Flask, jsonify, request
import subprocess
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/trigger', methods=['POST'])
def trigger_relay():
    """
    HTTP POST isteği geldiğinde relay_control.py betiğini çalıştırır.
    Relay numarası parametresi alabilir.
    """
    try:
        # POST verilerini al
        relay_number = None
        try:
            # Content-Type kontrolü
            if request.content_type and 'application/json' in request.content_type:
                data = request.get_json() or {}
                relay_number = data.get('relayNumber', None)
            else:
                # JSON değilse query parameter olarak kontrol et
                relay_number = request.args.get('relayNumber', None)
            
            logger.info(f"Received request with relay number: {relay_number}")
        except Exception as e:
            logger.warning(f"Parameter parse error (using default): {e}")
            relay_number = None

        # Komutu hazırla
        cmd = ['python3', 'relay_control.py']
        
        # Relay numarası varsa argüman olarak ekle
        if relay_number:
            cmd.append(str(relay_number))

        logger.info(f"Executing command: {' '.join(cmd)}")

        # Alt süreci başlat
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
            cwd='/home/visioai/Projects/alpr-client/relay_control'
        )

        logger.info(f"Script executed successfully. Output: {result.stdout}")

        # Başarılı yanıt
        response = {
            "status": "success",
            "message": "relay_control.py betiği başarıyla çalıştırıldı.",
            "relayNumber": relay_number,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip() if result.stderr else None
        }
        return jsonify(response), 200

    except subprocess.TimeoutExpired:
        logger.error("Script execution timeout")
        response = {
            "status": "error",
            "message": "Betik çalıştırılırken zaman aşımı oluştu."
        }
        return jsonify(response), 408

    except subprocess.CalledProcessError as e:
        logger.error(f"Script execution error: {e}")
        response = {
            "status": "error",
            "message": f"Betik çalıştırılırken hata oluştu: {e}",
            "stderr": e.stderr,
            "returncode": e.returncode
        }
        return jsonify(response), 500

    except Exception as e:
        logger.error(f"Server error: {e}")
        response = {
            "status": "error",
            "message": f"Sunucu hatası: {str(e)}"
        }
        return jsonify(response), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Sunucu durumunu kontrol etmek için basit bir endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Flask relay server is running"
    }), 200

if __name__ == '__main__':
    logger.info("Starting Flask relay server on 0.0.0.0:9747")
    app.run(host='0.0.0.0', port=9747, debug=True)