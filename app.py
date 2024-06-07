import http.server
from socketserver import ThreadingMixIn, TCPServer
import os
import json

PORT = 8000  # You can use any port number

# Change the current working directory to the 'public' folder
os.chdir('public')

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
            content = self.insert_products()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(content.encode())
        elif self.path.startswith('/product-'):
            product_id = self.path.split('-')[1]
            content = self.create_product_page(product_id)
            if content:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode())
            else:
                self.send_error(404)
        else:
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def insert_products(self):
        # Read the index.html content
        with open('index.html', 'r') as file:
            html_content = file.read()

        # Read the products.json content
        with open('products.json', 'r') as file:
            products = json.load(file)

        # Extract product details (name, id, thumbnail)
        product_details = [
            (product.get('name'), product.get('id'), product.get('thumbnail'), product.get('price', '0'))
            for product in products.get('products', [])
        ]

        # Create HTML div elements for each product
        product_divs_html = ''
        for name, product_id, thumbnail, price in product_details:
            product_divs_html += f'''
                <a href="/product-{product_id}">
                    <div class="product">
                        <img src="images/thumbnails/{thumbnail}" alt="{name}">
                        <div class="product-details">
                        <p class="name">{name}</p>
                        <p class="price">{price}€</p>
                        </div>
                    </div>
                </a>
            '''

        # Wrap product divs in a container
        product_divs_html = f'<div class="product-container">{product_divs_html}</div>'

        # Inject product divs into the HTML content
        html_content = self.replace_element_by_id(html_content, 'product-list', product_divs_html)
        return html_content

    def create_product_page(self, product_id):
        # Read the products.json content
        with open('products.json', 'r') as file:
            products = json.load(file)

        # Find the product with the specified ID
        product = next((p for p in products.get('products', []) if p.get('id') == product_id), None)

        if not product:
            return None

        # Read the product.html template content
        with open('product.html', 'r') as file:
            html_content = file.read()

        # Create the main product details HTML
        def additional_images():
            # Create HTML for additional images
            additional_images_html = '<div class="additional-images">'
            for image in product.get('images', []):
                additional_images_html += f'<img src="images/products/{product.get('id')}/{image}" alt="{product.get('name')}">'
            additional_images_html += '</div>'
            return additional_images_html
            
        product_details_html = f'''
        <div>
            <h1>{product.get('name')}</h1>
            <p>ID: {product.get('id')}</p>
            <img src="images/thumbnails/{product.get('thumbnail')}" alt="{product.get('name')}">
            {additional_images()}
            <p>{product.get('description', 'No description provided.')}</p>
            <a href="/">Back to products</a>
        </div>
        '''

        # Replace the element in product.html with the combined product details and images
        html_content = self.replace_element_by_id(html_content, 'product-details', product_details_html)
        return html_content

    def replace_element_by_id(self, html_content, element_id, new_content):
        # This function replaces the inner HTML of an element with a specific ID
        marker_start = f'id="{element_id}"'
        marker_end = '</div>'
        start_index = html_content.find(marker_start)
        if start_index == -1:
            return html_content

        start_index = html_content.find('>', start_index) + 1
        end_index = html_content.find(marker_end, start_index)
        return html_content[:start_index] + new_content + html_content[end_index:]

    def send_error(self, code, message=None):
        if code == 404:
            self.path = '/404.html'
            self.send_response(code)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            try:
                with open(self.path[1:], 'r') as file:
                    self.wfile.write(file.read().encode())
            except FileNotFoundError:
                self.wfile.write(b"404 - File not found.")
        else:
            super().send_error(code, message)

# Create a threaded HTTP server class to handle multiple clients
class ThreadedHTTPServer(ThreadingMixIn, TCPServer):
    """Handle requests in a separate thread."""

# Create a threaded HTTP server
with ThreadedHTTPServer(("", PORT), CustomHandler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
