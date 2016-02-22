# file simTagStreamer.py simulates a robot in an arena

from sensorPlanTCP import SensorPlanTCP
from redRobotSim import DummyRobotSim
from joy import JoyApp, progress
from joy.decl import *
from waypointShared import WAYPOINT_HOST, APRIL_DATA_PORT
from socket import (
  socket, AF_INET,SOCK_DGRAM, IPPROTO_UDP, error as SocketError,
  )

class RobotSimulatorApp( JoyApp ):
  """Concrete class RobotSimulatorApp <<singleton>>
     A JoyApp which runs the DummyRobotSim robot model in simulation, and
     emits regular simulated tagStreamer message to the desired waypoint host.
     
     Used in conjection with waypointServer.py to provide a complete simulation
     environment for Project 1
  """    

  def __init__(self,wphAddr=WAYPOINT_HOST,*arg,**kw):
    JoyApp.__init__( self,
      confPath="$/cfg/JoyApp.yml",
      ) 
    self.srvAddr = (wphAddr, APRIL_DATA_PORT)
    self.auto = False;
    
  def onStart( self ):
    # Set up socket for emitting fake tag messages
    s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    s.bind(("",0))
    self.sock = s
    # Set up the sensor receiver plan
    self.sensor = SensorPlanTCP(self,server=self.srvAddr[0])
    self.sensor.start()
    self.robSim = DummyRobotSim(fn=None)
    self.timeForStatus = self.onceEvery(1)
    self.timeForLaser = self.onceEvery(1/15.0)
    self.timeForFrame = self.onceEvery(1/20.0)
    progress("Using %s:%d as the waypoint host" % self.srvAddr)
    self.T0 = self.now
    # Setup autonomous mode timer
    self.timeForAuto = self.onceEvery(1/20.0)

  def showSensors( self ):
    ts,f,b = self.sensor.lastSensor
    if ts:
      progress( "Sensor: %4d f %d b %d" % (ts-self.T0,f,b)  )
    else:
      progress( "Sensor: << no reading >>" )
    ts,w = self.sensor.lastWaypoints
    if ts:
      progress( "Waypoints: %4d " % (ts-self.T0) + str(w))
    else:
      progress( "Waypoints: << no reading >>" )
  
  def emitTagMessage( self ):
    """Generate and emit and update simulated tagStreamer message"""
    self.robSim.refreshState()
    # Get the simulated tag message
    msg = self.robSim.getTagMsg()
    # Send message to waypointServer "as if" we were tagStreamer
    self.sock.sendto(msg, self.srvAddr)
    
  def onEvent( self, evt ):
    # periodically, show the sensor reading we got from the waypointServer
    if self.timeForStatus(): 
      self.showSensors()
      progress( self.robSim.logLaserValue(self.now) )
      # generate simulated laser readings
    elif self.timeForLaser():
      self.robSim.logLaserValue(self.now)
    # update the robot and simulate the tagStreamer
    if self.timeForFrame(): 
      self.emitTagMessage()
    # if in autonomous mode, check on auto task
    if self.auto and self.timeForAuto():
      self.robSim.autoTask()

    if evt.type == KEYDOWN:

      if evt.key == K_UP and not self.auto:
        self.robSim.moveY(1)
        return progress("(say) Move up")
      elif evt.key == K_DOWN and not self.auto:
        # self.robSim.move(-0.5)
        self.robSim.moveY(-1)
        return progress("(say) Move down")
      elif evt.key == K_LEFT and not self.auto:
        self.robSim.moveX(-1)
        return progress("(say) Move left")
      elif evt.key == K_RIGHT and not self.auto:
        self.robSim.moveX(1)
        return progress("(say) Move right")
      elif evt.key == K_TAB:
        self.auto = ~self.auto
        if self.auto: 
          return progress("(say) toggle autonomous mode on")
        else:
          return progress("(say) toggle sutonomous mode off")
      # Use superclass to show any other events
      else:
        return JoyApp.onEvent(self,evt)
    return # ignoring non-KEYDOWN events


#K_UNKNOWN K_FIRST K_BACKSPACE K_TAB K_CLEAR K_RETURN K_PAUSE K_ESCAPE K_SPACE K_EXCLAIM K_QUOTEDBL K_HASH K_DOLLAR K_AMPERSAND K_QUOTE K_LEFTPAREN K_RIGHTPAREN K_ASTERISK K_PLUS K_COMMA K_MINUS K_PERIOD K_SLASH K_0 K_1 K_2 K_3 K_4 K_5 K_6 K_7 K_8 K_9 K_COLON K_SEMICOLON K_LESS K_EQUALS K_GREATER K_QUESTION K_AT K_LEFTBRACKET K_BACKSLASH K_RIGHTBRACKET K_CARET K_UNDERSCORE K_BACKQUOTE K_a K_b K_c K_d K_e K_f K_g K_h K_i K_j K_k K_l K_m K_n K_o K_p K_q K_r K_s K_t K_u K_v K_w K_x K_y K_z K_DELETE K_KP0 K_KP1 K_KP2 K_KP3 K_KP4 K_KP5 K_KP6 K_KP7 K_KP8 K_KP9 K_KP_PERIOD K_KP_DIVIDE K_KP_MULTIPLY K_KP_MINUS K_KP_PLUS K_KP_ENTER K_KP_EQUALS K_UP K_DOWN K_RIGHT K_LEFT K_INSERT K_HOME K_END K_PAGEUP K_PAGEDOWN K_F1 K_F2 K_F3 K_F4 K_F5 K_F6 K_F7 K_F8 K_F9 K_F10 K_F11 K_F12 K_F13 K_F14 K_F15 K_NUMLOCK K_CAPSLOCK K_SCROLLOCK K_RSHIFT K_LSHIFT K_RCTRL K_LCTRL K_RALT K_LALT K_RMETA K_LMETA K_LSUPER K_RSUPER K_MODE K_HELP K_PRINT K_SYSREQ K_BREAK K_MENU K_POWER K_EURO K_LAST KMOD_NONE KMOD_LSHIFT KMOD_RSHIFT KMOD_LCTRL KMOD_RCTRL KMOD_LALT KMOD_RALT KMOD_LMETA KMOD_RMETA KMOD_NUM KMOD_CAPS KMOD_MODE KMOD_CTRL KMOD_SHIFT KMOD_ALT KMOD_META


if __name__=="__main__":
  print """
  Running the robot simulator

  Listens on local port 0xBAA (2986) for incoming waypointServer
  information, and also transmits simulated tagStreamer messages to
  the waypointServer. 
  """
  import sys
  if len(sys.argv)>1:
      app=RobotSimulatorApp(wphAddr=sys.argv[1])
  else:
      app=RobotSimulatorApp(wphAddr=WAYPOINT_HOST)
  app.run()

