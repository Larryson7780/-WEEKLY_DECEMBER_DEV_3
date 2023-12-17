import http.server
import socketserver
import os
import cgi
from urllib.parse import unquote


class MonGestionnaireDeRequetes(http.server.SimpleHTTPRequestHandler):
    def list_files(self):
        files = os.listdir(self.directory)
        return files

    def delete_file(self, filename):
        # Supprimer le fichier demandé
        decoded_filename = unquote(filename)  # Décoder le nom du fichier
        file_path = os.path.join(self.directory, decoded_filename)
        try:
            os.remove(file_path)
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(
                f"Fichier {decoded_filename} supprimé avec succès. <a href='/'>Retour à la page principale</a>".encode(
                    'utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"Erreur lors de la suppression du fichier : {str(e)}".encode('utf-8'))

    def confirm_delete_file(self, filename):
        # Afficher la page de confirmation pour la suppression du fichier
        decoded_filename = unquote(filename)  # Décoder le nom du fichier
        html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Confirmation de suppression</title>
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        margin: 20px;
                    }}
                    h1 {{
                        color: #333;
                    }}
                    p {{
                        margin-bottom: 20px;
                    }}
                    a {{
                        color: #0066cc;
                        text-decoration: none;
                        font-weight: bold;
                        margin-right: 20px;
                    }}
                </style>
            </head>
            <body>
                <h1>Confirmation de suppression</h1>
                <p>Voulez-vous vraiment supprimer le fichier "{decoded_filename}" ?</p>
                <a href='/delete_confirmed/{filename}'>Oui</a>
                <a href='/'>Non</a>
            </body>
            </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            # Générer la liste des fichiers
            files = self.list_files()

            # Afficher la liste des fichiers avec des liens de suppression
            html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Liste des fichiers</title>
                    <style>
                        body {{
                            font-family: 'Arial', sans-serif;
                            margin: 20px;
                        }}
                        h1 {{
                            color: #333;
                        }}
                        ul {{
                            list-style-type: none;
                            padding: 0;
                        }}
                        li {{
                            margin-bottom: 10px;
                        }}
                        a {{
                            color: #0066cc;
                            text-decoration: none;
                            font-weight: bold;
                            margin-left: 10px;
                        }}
                        form {{
                            margin-top: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <h1>Liste des fichiers</h1>
                    <ul>
                        {"".join(f"<li>{file} - <a href='/delete/{file}'>Supprimer</a></li>" for file in files)}
                    </ul>
                    <h1>Formulaire d'Upload de Fichier</h1>
                    <form action="/upload" method="post" enctype="multipart/form-data">
                        <input type="file" name="file" required>
                        <br><br>
                        <input type="submit" value="Envoyer le fichier">
                    </form>
                </body>
                </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
        elif self.path.startswith('/delete/'):
            # Rediriger vers la page de confirmation avant la suppression
            filename = self.path[len('/delete/'):]
            self.confirm_delete_file(filename)
        elif self.path.startswith('/delete_confirmed/'):
            # Supprimer le fichier confirmé
            filename = self.path[len('/delete_confirmed/'):]
            self.delete_file(filename)
        else:
            # Si une autre route est demandée, traiter comme d'habitude
            super().do_GET()

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers['content-type'])
        if ctype == 'multipart/form-data':
            fs = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                  environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            if 'file' in fs:
                file_item = fs['file']
                if file_item.filename:
                    file_path = os.path.join(self.directory, file_item.filename)
                    with open(file_path, 'wb') as file:
                        file.write(file_item.file.read())
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    response = 'Fichier téléchargé avec succès. <a href="/">Retour à la page principale</a>'
                    self.wfile.write(response.encode('utf-8'))
                else:
                    self.send_error(400, 'Aucun fichier téléchargé.')
            else:
                self.send_error(400, 'Formulaire invalide.')
        else:
            self.send_error(400, 'Mauvais type de requête.')


# Définir le chemin du répertoire que vous souhaitez afficher et gérer
MonGestionnaireDeRequetes.directory = os.getcwd()

# Définir le numéro de port pour le serveur
PORT = 8000

# Créer le serveur et le lier au port spécifié
with socketserver.TCPServer(("", PORT), MonGestionnaireDeRequetes, bind_and_activate=False) as httpd:
    httpd.allow_reuse_address = True
    httpd.server_bind()
    httpd.server_activate()

    print(f"Serveur démarré sur le port {PORT}")

    try:
        # Exécuter le serveur indéfiniment
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
