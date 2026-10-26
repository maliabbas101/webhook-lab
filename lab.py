from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json


def simulate(config):
    statuses = config.get('statuses', [500, 500, 200])
    copies = config.get('copies', 2)
    attempts = config.get('attempts', 4)
    delay = config.get('delay', 1)
    deduplicate = config.get('deduplicate', True)
    if not isinstance(statuses, list) or not 1 <= len(statuses) <= 20:
        raise ValueError('Provide between 1 and 20 response codes.')
    if any(type(code) is not int or not 100 <= code <= 599 for code in statuses):
        raise ValueError('Response codes must be integers from 100 to 599.')
    for name, value, maximum in [('copies', copies, 10), ('attempts', attempts, 10), ('delay', delay, 60)]:
        if type(value) is not int or not 1 <= value <= maximum:
            raise ValueError(f'{name} must be an integer from 1 to {maximum}.')
    if type(deduplicate) is not bool:
        raise ValueError('deduplicate must be true or false.')

    rows = []
    seen = False
    processed = 0
    elapsed = 0
    exhausted = 0
    for copy in range(1, copies + 1):
        delivered = False
        for attempt in range(1, attempts + 1):
            status = statuses[min(attempt - 1, len(statuses) - 1)]
            success = 200 <= status < 300
            retryable = status in (408, 429) or status >= 500
            outcome = 'retry scheduled' if retryable and attempt < attempts else 'failed'
            if success:
                outcome = 'duplicate skipped' if seen and deduplicate else 'processed'
                processed += outcome == 'processed'
                seen = True
                delivered = True
            wait = delay * 2 ** (attempt - 1) if retryable and not success and attempt < attempts else 0
            rows.append(dict(copy=copy, attempt=attempt, status=status, at=elapsed, wait=wait, outcome=outcome))
            elapsed += wait
            if success or not retryable:
                break
        exhausted += not delivered
    return dict(rows=rows, processed=processed, failed_deliveries=exhausted, virtual_seconds=elapsed)


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/health':
            return self.respond(200, b'{"status":"ok"}')
        if self.path != '/':
            return self.respond(404, b'{"error":"Not found"}')
        self.respond(200, Path(__file__).with_name('index.html').read_bytes(), 'text/html; charset=utf-8')

    def do_POST(self):
        if self.path != '/api/simulate':
            return self.respond(404, b'{"error":"Not found"}')
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 8192:
                raise ValueError('Request body must be between 1 and 8192 bytes.')
            config = json.loads(self.rfile.read(length))
            if not isinstance(config, dict):
                raise ValueError('Request body must be an object.')
            result = simulate(config)
        except (ValueError, UnicodeDecodeError) as error:
            return self.respond(400, json.dumps({'error': str(error)}).encode())
        self.respond(200, json.dumps(result).encode())


if __name__ == '__main__':
    print('Webhook Lab: http://127.0.0.1:8000')
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
