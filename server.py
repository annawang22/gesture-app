from http.server import HTTPServer, SimpleHTTPRequestHandler

class CallbackHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Redirect /callback back to index.html with the query string intact
        if self.path.startswith('/callback'):
            query = self.path[len('/callback'):]
            self.send_response(302)
            self.send_header('Location', '/' + query)
            self.end_headers()
        else:
            super().do_GET()

HTTPServer(('127.0.0.1', 8888), CallbackHandler).serve_forever()