from livereload import Server

server = Server()
server.watch('pogoda_teraz.html')
server.watch('style.css')
server.serve(root='.', open_url_delay=1)