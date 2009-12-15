'''
Copyright 2009 Shane Dowling

This file is part of Wave Server Admin.

Wave Server Admin is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Wave Server Admin is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Wave Server Admin. If not, see http://www.gnu.org/licenses/.
'''
from waveapi import events
from waveapi import model
from waveapi import robot
from waveapi import document
from google.appengine.ext import db
import xmlrpclib
import hashlib
import logging
import re

class Server(db.Model):
    wave = db.StringProperty(required=True)
    auth_code = db.StringProperty(required=False)
    serveraddress = db.StringProperty(required=False)

def OnParticipantsChanged(properties, context):
    """Invoked when any participants have been added/removed."""
    added = properties['participantsAdded']
    for p in added:
        Notify(context)

def OnRobotAdded(properties, context):
    """Invoked when the robot has been added."""
    root_wavelet = context.GetRootWavelet()
    writeMessage(root_wavelet,"To add your server type server:http://address:port and auth:authentication_code into a blip, so for example server:http://example.com:8080 auth:123456 (I hope you pick a better password) ")

def OnBlipSubmitted(properties, context):
    logging.debug('Starting function')
    ''' This function is called when a user enters a blip '''

    ''' Blip is gotten '''
    blipId = properties['blipId']
    """logging.debug('blipId %s' % blipId)"""
    blip = context.GetBlipById(blipId) #OpBasedBlip
    ''' Wave id is gotten '''
    waveId = blip.GetWaveId()
    waveletId = blip.GetWaveletId()

    ''' Using the wave id we try get a valid server object '''
    servers = db.GqlQuery("SELECT * FROM Server WHERE wave = :1", waveId)
    server = servers.get()
    ''' If invalid blip return false'''
    if not blip:
        return True;

    ''' Get blip text '''
    doc = blip.GetDocument() # OpBasedDocument
    text = doc.GetText()
    root_wavelet = context.GetRootWavelet()

    if checkSettingsUpdate(text):
        if not server:
            server = Server(wave = waveId)
        if tryParseSettings(server,text):
            message = 'Thanks for updating your settings' 
            writeMessage(root_wavelet,message)
            return True

    if server and server.serveraddress:
        if re.search('http://',server.serveraddress):
            proxy = xmlrpclib.ServerProxy(server.serveraddress)
            ''' If server auth is valid ''' 
            if proxy.validAuth(server.auth_code):
                ''' Execute the commands in the blip'''
                output = proxy.runBash(text,server.auth_code)

                ''' If command output is valid'''
                if(output != False):
                    ''' Return the output to the user '''
                    writeMessage(root_wavelet,output)
                    return True
                else:
                    message = 'Invalid authentication details or a bad command, you may re-enter your details using the format server:http://url:port for example server:http://example.com:8080 and for authentication code use auth:123456 (but please use a better one than that)'
                    writeMessage(root_wavelet,message)
                    return True
            else: 
                    message = 'Bad server details, you may re-enter your details using the format server:http://url:port for example server:http://example.com:8080 and for authentication code use auth:123456 (but please use a better one than that)'
                    writeMessage(root_wavelet,message)
                    return True

    ''' If server doesn't exist '''
    if not server:
        logging.debug('Server does not exist')
        server = Server(wave = waveId)
        if tryParseSettings(server,text):
            logging.debug('Tried to parse settings')
            message = 'Thanks for updating your settings' 
            server.put()
        else:
            message = 'Your server does not exists or your details are invalid. You may re-enter your details using the format server:http://url:port for example server:http://example.com:8080 and for authentication code use auth:123456 (but please use a better one than that)'
            
        writeMessage(root_wavelet,message)
        return True

    if tryParseSettings(server,text):
        message = 'Thanks for updating your settings' 
        writeMessage(root_wavelet,message)
        return True

    message = 'Your server is down or your details are bad. You may re-enter your details using the format server:http://url:port for example server:http://example.com:8080 and for authentication code use auth:123456 (but please use a better one than that)'
    writeMessage(root_wavelet,message)
    logging.debug('End of the function') 
    return True

def checkSettingsUpdate(text):

    server_match = re.search('server:http://[a-z]+\.[a-z]+:[0-9]+',text);
    if server_match != None:   
        return True
    auth_match = re.search('auth:\S+', text); 
    if auth_match != None:
        return True

    return False

def tryParseSettings(server,text):
    logging.debug('Trying to parse the settings')
    data_entered = False
    ''' If the blip text contains strings with server: or password: in them '''

    ''' regex is /server:[a-z]+.[a-z]+:[0-9]+ '''
    server_match = re.search('server:http://[a-z]+\.[a-z]+:[0-9]+',text);
    if server_match != None:   
        server_string = server_match.group(0)
        data_entered = True
        logging.debug('Setting the server')
        server.serveraddress = server_string[7:]

    ''' regex is /auth:\S+ '''
    auth_match = re.search('auth:\S+', text); 
    if auth_match != None:
        auth_string = auth_match.group(0)
        data_entered = True
        server.auth_code = hashlib.sha512(auth_string[5:]).hexdigest()

    '''Add the text to the database'''
    if data_entered:
        server.put()

    return data_entered

def writeMessage(root_wavelet, message):
    logging.debug('Writing message via writeMessage')
    root_wavelet.CreateBlip().GetDocument().SetText("%s" % message)

 
def Notify(context):
    root_wavelet = context.GetRootWavelet()
    root_wavelet.CreateBlip().GetDocument().SetText("Hi everybody bleh!")

if __name__ == '__main__':
    myRobot = robot.Robot('linuxadmin', 
            image_url='http://waveserveradmin.appspot.com/icon.png',
            version='1',
            profile_url='http://waveserveradmin.appspot.com/')
    myRobot.RegisterHandler(events.BLIP_SUBMITTED, OnBlipSubmitted)
    myRobot.RegisterHandler(events.WAVELET_PARTICIPANTS_CHANGED, OnParticipantsChanged)
    myRobot.RegisterHandler(events.WAVELET_SELF_ADDED, OnRobotAdded)
    myRobot.Run()
