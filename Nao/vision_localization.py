# -*- encoding: UTF-8 -*-
from naoqi import ALProxy

import math
import almath # py2 -m pip install almath==1.6.8
import time

ENDPOINT_NAO = "10.3.141.194"
ENDPOINT_NAO_PORT = 9559

# Set here your robto's ip.
#ip = "127.0.0.1"
# Set here the size of the landmark in meters.
landmarkTheoreticalSize = 0.06 #in meters
# Set here the current camera ("CameraTop" or "CameraBottom").
currentCamera = "CameraTop"

memoryProxy = ALProxy("ALMemory", ENDPOINT_NAO, 9559)
landmarkProxy = ALProxy("ALLandMarkDetection", ENDPOINT_NAO, 9559)
ttsProxy = ALProxy("ALTextToSpeech", ENDPOINT_NAO, 9559)
postureProxy = ALProxy("ALRobotPosture", ENDPOINT_NAO, 9559)
motionProxy  = ALProxy("ALMotion", ENDPOINT_NAO, 9559)
tracker_service = ALProxy("ALTracker", ENDPOINT_NAO, 9559)
tracker_service.unregisterAllTargets()

# Subscribe to LandmarkDetected event from ALLandMarkDetection proxy.
landmarkProxy.subscribe("landmarkTest")

# initialize angle
angle = 100000
dist = 100000

motionProxy.wakeUp()
postureProxy.goToPosture("StandInit", 0.5)
motionProxy.rest()
postureProxy.goToPosture("Crouch", 0.5)

print "Current robot position:", motionProxy.getRobotPosition(True)
#exit(0)
#angle>5 or angle<-5 or
while ( dist>0.7):

    print angle, dist

    ttsProxy.say("I am looking for the landmark")
    # Wait for a mark to be detected.
    markData = memoryProxy.getData("LandmarkDetected")
    while (not markData or len(markData) == 0 or int(markData[1][0][1][0])!=85):
        markData = memoryProxy.getData("LandmarkDetected")

    ttsProxy.say("Found it!")
    print markData
    print markData[1][0][1][0]


    # Retrieve landmark center position in radians.
    wzCamera = markData[1][0][0][1]
    wyCamera = markData[1][0][0][2]

    # Retrieve landmark angular size in radians.
    angularSize = markData[1][0][0][3]


    #angle
    angle =  markData[1][0][0][1]
    print "angle:", angle*180.0/math.pi
    angle = angle*180.0/math.pi

    angle_size = angularSize*180.0/math.pi

    print "anglular size:",angle_size

    # Compute distance to landmark.
    distanceFromCameraToLandmark = landmarkTheoreticalSize / ( 2 * math.tan( angularSize / 2))
    motionProxy = ALProxy("ALMotion", ENDPOINT_NAO, 9559)

    # Get current camera position in NAO space.
    transform = motionProxy.getTransform(currentCamera, 2, True)
    transformList = almath.vectorFloat(transform)
    robotToCamera = almath.Transform(transformList)

    # Compute the rotation to point towards the landmark.
    cameraToLandmarkRotationTransform = almath.Transform_from3DRotation(0, wyCamera, wzCamera)

    # Compute the translation to reach the landmark.
    cameraToLandmarkTranslationTransform = almath.Transform(distanceFromCameraToLandmark, 0, 0)

    # Combine all transformations to get the landmark position in NAO space.
    robotToLandmark = robotToCamera * cameraToLandmarkRotationTransform *cameraToLandmarkTranslationTransform

    print "x " + str(robotToLandmark.r1_c4) + " (in meters)"
    print "y " + str(robotToLandmark.r2_c4) + " (in meters)"
    print "z " + str(robotToLandmark.r3_c4) + " (in meters)"

    dist = robotToLandmark.r1_c4
    dist_y = robotToLandmark.r2_c4



    #robotPositionFinal = almath.Pose2D(almath.vectorFloat(motionProxy.getRobotPosition(False)))

    # compute robot Move with the second call of walk API
    # so between nextRobotPosition and robotPositionFinal
    #robotMove = almath.pose2DInverse(nextRobotPosition) * robotPositionFinal
    #ttsProxy.say("Distance to Landmark is " + str(dist))
    #ttsProxy.say("Angle " + str(angle))
    '''
    if(dist>0.7):
        ttsProxy.say("I am too far away. I am walking forward")
        postureProxy.goToPosture("StandInit", 0.5)
        #motionProxy.moveTo(dist-0.6, -0.1,markData[1][0][0][3])
        
        motionProxy.moveTo(1,0,0)
        time.sleep(0.5)
        motionProxy.stopMove()
    '''

    if (robotToLandmark.r2_c4 > 0.05 or robotToLandmark.r2_c4 < -0.05):
        ttsProxy.say("I want to correct my side position.")
        postureProxy.goToPosture("StandInit", 0.5)
        # motionProxy.moveTo(dist-0.6, -0.1,markData[1][0][0][3])

        motionProxy.walkTo(dist-0.6, dist_y, 0)
        print "Current robot position:", motionProxy.getRobotPosition(True)
        #break
        #time.sleep(0.5)
        #motionProxy.stopMove()



    '''
    if(angle>5 or angle<-5):
        ttsProxy.say("The angle to the landmark is too extreme. Let me turn a bit.")
        # Speed walk  (MaxStepX = 0.06 m)
        # Could be faster: see walk documentation
        try:
            motionProxy.wakeUp()
            postureProxy.goToPosture("StandInit", 0.5)
            theta = 1
            if angle< 0:
                theta = -1
            motionProxy.moveToward(0, -1, theta*0.1)
            time.sleep(3)
            motionProxy.stopMove()


            # Go to rest position
            postureProxy.goToPosture("Crouch", 0.5)
            motionProxy.rest()
        except Exception, errorMsg:
            print str(errorMsg)
            print "This example is not allowed on this robot."
            exit()
    '''

# Go to rest position
postureProxy.goToPosture("Crouch", 0.5)
motionProxy.rest()


landmarkProxy.unsubscribe("landmarkTest")

