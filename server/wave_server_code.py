'''
Copyright 2009 Shane Dowling

This file is part of Wave Server Admin.

Wave Server Admin is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Wave Server Admin is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Wave Server Admin. If not, see http://www.gnu.org/licenses/.
'''
import xmlrpclib
import hashlib
import time
from SimpleXMLRPCServer import SimpleXMLRPCServer


auth_code='a_good_password'
#The url of the server, will error if invalid
server_url='example.com'
#Can be set to any port, but must be root for under 1024(I wouldn't recommend this!)
port = 8080 

def validAuth(client_auth):
    return hashlib.sha512(auth_code).hexdigest() == client_auth

#This function takes Bash commands and returns them
def runBash(cmd, client_auth):
    if hashlib.sha512(auth_code).hexdigest() != client_auth:
        return False
    import subprocess
    import select

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #I've had the most success with 3 seconds, times out otherwise
    time.sleep(3)
    p.kill()

    out = p.stdout.read().strip()
    return out  #This is the stdout from the shell command

server = SimpleXMLRPCServer((server_url, port))
print "Listening on port %s..." % port
server.register_function(runBash, "runBash")
server.register_function(validAuth, "validAuth")
server.serve_forever()

