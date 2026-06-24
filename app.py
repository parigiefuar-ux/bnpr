from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    # Prende l'URL di destinazione dall'header X-Target-Url
    target_url = request.headers.get('X-Target-Url')
    
    if not target_url:
        return "Benvenuto nel Proxy! Specifica un URL da proxare nell'header X-Target-Url", 400

    try:
        # Rimuove gli header che non vogliamo inoltrare al target
        headers_to_forward = {}
        for key, value in request.headers:
            key_lower = key.lower()
            # Rimuoviamo tutti gli header che possono rivelare l'IP o che sono specifici della CDN
            if key_lower not in ['host', 'x-target-url', 'connection', 'content-length'] and not key_lower.startswith('x-forwarded-') and not key_lower.startswith('cdn-') and key_lower not in ['x-real-ip', 'true-client-ip', 'cf-connecting-ip']:
                headers_to_forward[key] = value

        # Inoltra la richiesta al target
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers_to_forward,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            verify=False,
            timeout=15
        )

        # Rimuove gli header hop-by-hop dalla risposta
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        return f"Errore nel proxy: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
