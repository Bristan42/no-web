import os, sys
os.chdir("/Users/bristan/Desktop/code/no-web/_template-macon/output/maconnerie-martin")
sys.argv = ["server", "3458"]
import http.server
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=3458, bind="127.0.0.1")
