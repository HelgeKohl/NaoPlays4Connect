# -*- encoding: UTF-8 -*-

"""Example: Say `My {Body_part} is touched` when receiving a touch event"""

import qi
import argparse
import functools
import sys
import vision_definitions
import random
from magic import VideoImage
import time
import threading
import time
import functools
import socket
import time
import pickle
import os
import struct
from struct import calcsize
import math
import almath

#from threading import Timer
import threading

# nao moves
import disco_move
import wipe_forehead
import hello_move


BUFFER_SIZE = 2048#65536#1024#6553600
ENDPOINT_NAO = "10.3.141.194"
ENDPOINT_NAO_PORT = 9559
ENDPOINT_SERVER = '10.3.141.140' #'10.3.141.59'
ENDPOINT_SERVER_PORT = 9001
#ENDPOINT_SERVER_PORT = 1755





class GameMinimal(object):
    """ A simple module able to react
        to touch events.
    """

    def __del__(self):
        self.video.close()
        self.t.join()
        self.landmark_detection_service.unsubscribe("landmarkTest")
        # self.sayHelloTask.stop()
        # self.socket_client.close()

    def __init__(self, app):
        super(GameMinimal, self).__init__()

        # Get the services ALMemory, ALTextToSpeech.
        app.start()
        session = app.session
        self.memory_service = session.service("ALMemory")
        self.tts = session.service("ALTextToSpeech")
        self.motion_service = session.service("ALMotion")  # not sure that it works
        self.posture_service = session.service("ALRobotPosture")
        self.landmark_detection_service = session.service("ALLandMarkDetection")
        self.landmark_detection_service.subscribe("landmarkTest")
        self.tracker_service = session.service("ALTracker")
        self.tracker_service.unregisterAllTargets()
        self.leds_service = session.service("ALLeds")
        #######################################################

        #######################################################

        '''
         motion and posture services are not tested on a robot
         may be does not work
        '''

        # Wake up robot
        #self.motion_service.wakeUp()

        # Send robot to Stand Init
        #self.posture_service.goToPosture("Crouch", 0.5)

        #self.motion_service.rest()
        ########################################

        self.game_state = 0
        #######################################
        try:
            self.tts.setLanguage("German")
        except RuntimeError:
            print "You need to install German language in order to hear correctly these sentences."

        #######################################

        # Connect to an Naoqi Event.
        self.touch = self.memory_service.subscriber("TouchChanged")
        self.id = self.touch.signal.connect(functools.partial(self.onTouched, "TouchChanged"))

        self.video = VideoImage(ENDPOINT_NAO, ENDPOINT_NAO_PORT)
        self.video.setResolution(640)
        self.video.subscribeCamera()
        self.video.setCamera(0)  # top camera

        ## repeat checking game status in separate thread
        ## if game status = 0, say the phrase
        self.t = threading.Thread(target=self.boring_talk())
        self.t.daemon = True
        self.t.start()
        # say it only once!!!


    def nao_hello(self):
            self.motion_service.wakeUp()
            self.motion_service.setStiffnesses("Body", 1.0)
            self.motion_service.moveInit()
            # trying to wave and talk at the same time
            self.motion_service.angleInterpolationBezier(hello_move.names, hello_move.times, hello_move.keys)
            self.tts.say("Hallo! Ich bin Nao! Ich möchte spielen! Wenn Du spielen willst, berühr meinen Kopf!")
            #self.motion_service.wait(id,0)
            #### if doesnt work then use without post
            #self.motion_service.angleInterpolationBezier(hello_move.names, hello_move.times, hello_move.keys)

            self.posture_service.goToPosture("Crouch", 0.5)
            self.motion_service.setStiffnesses("Body", 0.0)
            self.motion_service.rest()

    def nao_wipeforehead(self):
        self.motion_service.wakeUp()
        self.motion_service.setStiffnesses("Body", 1.0)
        self.motion_service.moveInit()
        self.motion_service.angleInterpolationBezier(wipe_forehead.names, wipe_forehead.times, wipe_forehead.keys)
        self.posture_service.goToPosture("Crouch", 0.5)
        self.motion_service.setStiffnesses("Body", 0.0)
        self.motion_service.rest()

    def nao_dance(self):
        self.motion_service.wakeUp()
        self.motion_service.setStiffnesses("Body", 1.0)
        self.motion_service.moveInit()
        self.motion_service.angleInterpolationBezier(disco_move.names, disco_move.times, disco_move.keys)
        self.posture_service.goToPosture("Crouch", 0.5)
        self.motion_service.setStiffnesses("Body", 0.0)
        self.motion_service.rest()

    def check_landmark_parameters(self, markData):
        #print 'markdata:', markData
        if(not markData or len(markData) == 0 or int(markData[1][0][1][0]) != 85):
            return False
        else:
            landmarkTheoreticalSize = 0.06
            #check distance and angular size
            smth = markData[1][0][0][0]
            wzCamera = markData[1][0][0][1]
            wyCamera = markData[1][0][0][2]
            angularSize = markData[1][0][0][3]
            # Get current camera position in NAO space.
            currentCamera = "CameraTop"
            transform = self.motion_service.getTransform(currentCamera, 2, True)
            distanceFromCameraToLandmark = landmarkTheoreticalSize / (2 * math.tan(angularSize / 2))
            transformList = almath.vectorFloat(transform)
            robotToCamera = almath.Transform(transformList)

            # Compute the rotation to point towards the landmark.
            cameraToLandmarkRotationTransform = almath.Transform_from3DRotation(0, wyCamera, wzCamera)

            # Compute the translation to reach the landmark.
            cameraToLandmarkTranslationTransform = almath.Transform(distanceFromCameraToLandmark, 0, 0)

            # Combine all transformations to get the landmark position in NAO space.
            robotToLandmark = robotToCamera * cameraToLandmarkRotationTransform * cameraToLandmarkTranslationTransform

            print "x " + str(robotToLandmark.r1_c4) + " (in meters)"
            print "y " + str(robotToLandmark.r2_c4) + " (in meters)"
            print "z " + str(robotToLandmark.r3_c4) + " (in meters)"

            print smth, wzCamera, wyCamera, angularSize
            flag1 = False
            if (smth >= 1 and smth<=1.1 and math.fabs(wzCamera)>=0.006 and math.fabs(wzCamera)<=0.25
            and math.fabs(wyCamera)>=0.01 and math.fabs(wyCamera)<=0.25
            and math.fabs(angularSize)>=0.09 and math.fabs(angularSize)<=0.12):
                flag1 = True
            flag2 = False
            if(math.fabs(robotToLandmark.r1_c4)>=0.5 and math.fabs(robotToLandmark.r1_c4)<=0.75
            and math.fabs(robotToLandmark.r2_c4)>=0.001 and math.fabs(robotToLandmark.r2_c4)<=0.4
            and math.fabs(robotToLandmark.r3_c4)>=0.4 and math.fabs(robotToLandmark.r3_c4)<=0.55):
                flag2 = True
            print flag1, flag2
            return (flag1 and flag2)



    def nao_check_fieldgame_visibility(self):

        self.motion_service.waitUntilMoveIsFinished()
        self.posture_service.goToPosture('Crouch',0.5)

        #detect landmark with several head positions
        self.tts.say("Ich werde jetzt versuchen das Spielfeld zu finden")

        degree_markData = {}
        t = 0.5
        for d in [-50,-40,-30,-20,-10,0,10,20,30,40,50]:
            self.motion_service.angleInterpolation(["HeadYaw"], [math.radians(d)], [t], True)
            markData = self.memory_service.getData("LandmarkDetected")
            if(self.check_landmark_parameters(markData) == True):
                print d, 'degrees are OK'
                degree_markData[d] = markData
            if(d!=0):
                self.motion_service.angleInterpolation(["HeadYaw"], [math.radians(0)], [t], True)

        if(len(degree_markData)==0):
            self.tts.say('Ich sehe kein Spielfeld und kann noch nicht spielen')
            return False
        else:
            # set the head position to the first good value
            #to do: find the best value from the dictionary
            d = degree_markData.keys()[0]
            print 'final', d
            self.motion_service.angleInterpolation(["HeadYaw"], [math.radians(d)], [t], True)
            if(d==0):
                self.motion_service.setStiffnesses("Body", 0.0)
                self.motion_service.rest()
            return True

        #markData = self.memory_service.getData("LandmarkDetected")

        #if (self.check_landmark_parameters(markData)==False):
        #   self.tts.say('Ich sehe kein Spielfeld und kann noch nicht spielen')
        #    return False
        #else:
        #    return True

    def try_to_find_position(self):
        # Add target to track.
        targetName = "LandMark"
        targetSize = 0.06
        self.tracker_service.registerTarget(targetName, [targetSize, [107]])
        self.posture_service.goToPosture("StandInit", 0.5)
        # set mode
        mode = "Move"
        self.tracker_service.setMode(mode)
        # tracker_service.toggleSearch(True)
        # 60 cm from target
        # tracker_service.setRelativePosition([-0.6, -0.1, 0.0, 0.1, 0.1, 0.3])
        self.tracker_service.setRelativePosition([0, 0, 0.0, 0.1, 0.1, 0.1])
        # Then, start tracker.
        self.tracker_service.track(targetName)
        count_tries = 0
        while True:
            time.sleep(10)
            # markData = memoryProxy.getData("LandmarkDetected")
            # print 'current mark', markData
            #print tracker_service.getTargetPosition(0)
            #print motionProxy.moveIsActive()
            if(self.motion_service.moveIsActive() == False):
                if(self.nao_check_fieldgame_visibility()):
                    self.tracker_service.stopTracker()
                    self.tracker_service.unregisterAllTargets()
                    break
                count_tries +=1
            if(count_tries>3):
                self.tts.say('Ich kann doch nicht spielen')
                return False

        #if(self.nao_check_fieldgame_visibility()):
        self.tts.say('Ich kann jetzt spielen')
        return True
        #else:
        #    self.tts.say('Ich kann doch nicht spielen')
        #    return False

    def boring_talk(self):
        while True:

            self.motion_service.waitUntilMoveIsFinished()
            if (self.game_state == 0):
                self.touch.signal.disconnect(self.id)
                self.nao_hello()
                # commented to run in parallel with hand waving in nao_hello function
                #self.tts.say("Hallo! Ich bin Nao! Ich möchte spielen! Wenn Du spielen willst, berühr meinen Kopf!")
                self.id = self.touch.signal.connect(functools.partial(self.onTouched, "TouchChanged"))
            time.sleep(20)
    def num2word (self, num):
        num = int(num)
        if(num==1):
            return "eins"
        elif(num==2):
            return "zwei"
        elif(num==3):
            return "drei"
        elif (num == 4):
            return "vier"
        elif (num == 5):
            return "fünf"
        elif (num == 6):
            return "sechs"
        elif (num == 7):
            return "sieben"

    def send_img(self, fname):
        # open sockets
        TCP_IP = ENDPOINT_SERVER  # '192.168.0.176'
        TCP_PORT = ENDPOINT_SERVER_PORT

        connected = False
        while not connected:
            try:
                self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_client.connect((TCP_IP, TCP_PORT))
                connected = True
            except socket.error:
                print 'no connection to socket, try to reconnect  after 1 sec'
                time.sleep(1)
        # send image

        filename = fname
        f = open(filename, 'rb')
        nBytes = os.path.getsize(filename)
        recieved_f = [-10, -10]
        packed_f = struct.pack('!ii', recieved_f[0], recieved_f[1])
        print (calcsize('!ii'))

        print ("file size:", nBytes, type(nBytes))

        print('CLIENT: nBytes={nBytes}')
        # Send 4-byte network order frame size and image
        # NB: not sending header for UNITY server, but the eof at the end
        print 'size of nBytes',calcsize('<i')
        hdr = struct.pack('<i', nBytes)
        sentFlag = False
        while not sentFlag:
            try:
                self.socket_client.sendall(hdr)
                print 'sent hdr'
                l = f.read(BUFFER_SIZE)
                while (l):
                    self.socket_client.send(l)
                    # print('Sent ',repr(l))
                    l = f.read(BUFFER_SIZE)
                    if not l:
                        # print ('error sending image file')
                        f.close()
                        break
                #time.sleep(10)
                #self.socket_client.send(b"<EOF>")

                print('receiving data...')
                data = self.socket_client.recv(8)
                # Decode received data into UTF-8
                data = struct.unpack('<ii', data)
                # Convert decoded data into list
                recieved_f = data
                print('obtained response:', recieved_f)
                self.socket_client.close()
                sentFlag = True
            except socket.error:
                print 'socket error with sending or getting the response, try to reconnect and send/receive again'
                #was passiert in unity ml?  potential game status problems?
                self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_client.connect((TCP_IP, TCP_PORT))

        # magic_number = 16777216
        # state_val = int(recieved_f[0] / magic_number)
        # column_val = int(recieved_f[1] / magic_number)
        state_val = int(recieved_f[0])# / magic_number)
        column_val = int(recieved_f[1])# / magic_number)
        print 'state: ', state_val
        print 'column: ', column_val
        return [state_val,column_val]

    def onTouched(self, strVarName, value):
        """ This will be called each time a touch
        is detected.

        """
        # Disconnect to the event when talking,
        # to avoid repetitions
        self.touch.signal.disconnect(self.id)



        if (self.game_state == 0):
            self.game_state = 1
            #
            if(not self.nao_check_fieldgame_visibility()):
                self.tts.say ('Ich werde mit deiner Hilfe das Spielfeld suchen. Nimm die Karte mit dem Rad und zeig mir, wo ich hingehen soll')
                if(not self.try_to_find_position()):
                    self.game_state = 0
                else:
                    print "Starting new game"
                    self.tts.say("Super! Dann fangen wir gleich an! Mach deinen Zug und berühr meinen Kopf")

            else:
                #self.motion_service.rest()
                print "Starting new game"
                self.leds_service.rasta(3)
                self.tts.say("Super! Dann fangen wir gleich an! Mach deinen Zug und berühr meinen Kopf")
        elif (self.game_state == 1):
            self.tts.say("Warte, ich muss kurz überlegen!")
            img_fname = self.video.getImageInfo()
            resp = self.send_img(img_fname)
            while(resp[0]==6):
               self.tts.say("Ich muss mir das genauer ansehen!")
               img_fname = self.video.getImageInfo()
               resp = self.send_img(img_fname)

            if (resp[0] == 0):
                self.tts.say("Du hast keinen Zug gemacht! Mach deinen Zug und berühr meinen Kopf")
            elif (resp[0] == 1):
                self.tts.say("Etwas stimmt nicht! Du schummelst! Ich will nicht mit Dir spielen!")
                self.game_state = 0
            elif (resp[0] == 2):
                self.tts.say("Mein Zug ist Spalte Nummer " + self.num2word(str(resp[1] + 1)))
                self.tts.say("Hurra! Ich habe gewonnen! Ich bin einfach toll!")
                self.nao_dance()
                self.game_state = 0
            elif (resp[0] == 3):
                self.tts.say("Ich habe verloren. Schade!")
                self.nao_wipeforehead()
                self.game_state = 0
            elif (resp[0] == 4):  # maybe check here that the user has put the chip in. check and then ask again
                self.tts.say("Jetzt weiss ich! Mein Zug ist Spalte Nummer " + self.num2word(str(resp[1]+1)) + ". Kannst Du mir bitte helfen und meinen Chip einwerfen? Danke! Danach mach Deinen Zug und berühr meinen Kopf!")
            elif (resp[0] == 5):  # maybe check here that the user has put the chip in. check and then ask again
                self.tts.say("Es ist Unentschieden. Wir haben beide gut gespielt! Danke!")
                self.game_state = 0


        touched_bodies = []
        for p in value:
            if p[1]:
                touched_bodies.append(p[0])
        print touched_bodies

        # Reconnect again to the event
        self.id = self.touch.signal.connect(functools.partial(self.onTouched, "TouchChanged"))


def dummyAction():
    # do your operations here
    #qi.info("async example", "My dummy action is over")
    '''
    print 'foo'
    timer = threading.Timer(0.1, dummyAction, args=())
    timer.start()
    '''

    while True:
        print 'hello'
        time.sleep(1)


# Test Send File Stephan
# if __name__ == "__main__":
#     ip = ENDPOINT_NAO
#     port = ENDPOINT_NAO_PORT
#     try:
#         # Initialize qi framework.
#         connection_url = "tcp://" + ip + ":" + str(port)
#         app = qi.Application(["GameMinimal", "--qi-url=" + connection_url])
#     except RuntimeError:
#         print ("Can't connect to Naoqi at ip \"" + ip + "\" on port " + str(port) + ".\n"
#                                                                                     "Please check your script arguments. Run with -h option for help.")
#         sys.exit(1)
#     # try:
#     game = GameMinimal(app)
#     game.send_img("C:\\Development\\nao\\nao\\client_server_sockets_send_img_py\\drawing.png")

if __name__ == "__main__":

    '''
    t = threading.Thread(target=dummyAction)
    t.daemon = True
    t.start()
    t.join()
    '''

    ip = ENDPOINT_NAO
    port = ENDPOINT_NAO_PORT
    try:
        # Initialize qi framework.
        connection_url = "tcp://" + ip + ":" + str(port)
        app = qi.Application(["GameMinimal", "--qi-url=" + connection_url])
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + ip + "\" on port " + str(port) + ".\n"
                                                                                    "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    try:
        game = GameMinimal(app)
        app.start()
        #session = app.session
        #memory_service = session.service("ALMemory")

        # tts = session.service("ALTextToSpeech")
        # sayHelloCallable = functools.partial(tts.say, "hello")
       
        app.run()
    except KeyboardInterrupt:
        print "Interrupted by user, shutting down"
        # game.video.close()
        app.stop()
        sys.exit(0)

