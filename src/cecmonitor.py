#! /usr/bin/env python

# from http://stackoverflow.com/questions/11524586/accessing-logcat-from-android-via-python
import Queue
import subprocess
import threading
import traceback
import socket
import time
import datetime
import logging
import argparse
import os
from threading import Thread
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner

logger = logging.getLogger(__name__)

class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    '''

    def __init__(self, fd, queue):
        assert isinstance(queue, Queue.Queue)
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd
        self._queue = queue

    def run(self):
        '''The body of the tread: read lines and put them on the queue.'''
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)

    def eof(self):
        '''Check whether there is no more content to expect.'''
        return not self.is_alive() and self._queue.empty()

class Monitor:
    '''
    TV Logcat monitor for our magic string
    '''
    tvIpAddress = None

    def __init__(self, tvIpAddress):
        self.tvIpAddress = tvIpAddress

        self.validateConfig()

    def validateConfig(self):
        if not self.tvIpAddress:
            raise ValueError('TV IP address must be specified')

    def turnOffTv(self):
        # Send a shell command
        logging.info('shutting off TV')
        tvPowerProcess = subprocess.Popen(['adb', 'shell', 'input', 'keyevent', '26'], stdout=subprocess.PIPE)  

    def connectToTv(self):
        processAdb = subprocess.Popen(['adb', 'connect', self.tvIpAddress], stdout=subprocess.PIPE)
        # Wait until process terminates
        while processAdb.poll() is None:
            logger.debug('waiting for adb connection')
            time.sleep(0.5)
        out, err = processAdb.communicate()
        if 'unable to connect' in out:
            logger.debug('found error connecting setting return code to 1')
            processAdb.returncode = 1
        return processAdb    

    def substring_matches_line(self, line):
        target_substring = "HdmiCecLocalDevice: ---onMessage--fuli---messageOpcode:157"
        return target_substring in line

    def tvLog(self):
        process = subprocess.Popen(['adb', 'logcat', '-T', '5'], stdout=subprocess.PIPE)
        # Launch the asynchronous readers of the process' stdout.
        stdout_queue = Queue.Queue()
        stdout_reader = AsynchronousFileReader(process.stdout, stdout_queue)
        stdout_reader.start()
        while not stdout_reader.eof():
            while not stdout_queue.empty():
                line = stdout_queue.get()
                logger.debug(line)
                if self.substring_matches_line(line):
                    self.turnOffTv()
                    process.kill()
                    process = None 
        return process
    
    def cecWatcher(self):
        process = None
        processConnect = None
        while True:
            try:
                if processConnect is  None  or processConnect.poll() is not None:
                    processConnect = self.connectToTv()
                if processConnect.returncode ==  0:
                    process = self.tvLog()
                else:
                    logger.debug('connectToTv returned non-zero exit code')
                    pass
            
            except Exception as exception:
                logger.error('inner exception:')
                traceback.print_exc()
            finally:
                if process is not None:
                    process.kill() 

    def runForever(self):
        logger.info('starting background thread')
        backgroundThread = Thread(target=self.cecWatcher)
        backgroundThread.start()
           
def setupLogging(verbose, logToDisk):
    logLevel = logging.DEBUG if verbose else logging.INFO

    handlers = [
            logging.StreamHandler(),
            ]
    if logToDisk:
        handlers.append(logging.FileHandler('/tmp/cecmonitor.log'))
    loggingConfig = {'level': logLevel,
                     'format': '%(asctime)s [%(levelname)s] %(message)s',
                     'handlers': handlers}
    logging.basicConfig(**loggingConfig)

def check_existing_processes():
    """
    Check for existing processes by ps grepping. Filter out grep itself, matches with current PID, and /dev/null            for cron jobs. If another process is found, logs the found processes and exit the script
    """
    pid = os.getpid()
    pipe = subprocess.Popen(
    'ps aux | grep %s | grep -v grep | grep -v vim | grep -v "/dev/null" | grep -v "bash -c" | grep -v %s ' % (   
        'cecmonitor', pid), shell=True, stdout=subprocess.PIPE).stdout
    output = pipe.read().decode('utf-8')
    if output != '':
        logging.error('%s is already running, existing process: \n %s' % (__file__, output))        
        raise SystemExit()

def main():
    parser = argparse.ArgumentParser(description='Start the CEC Monitor.')
    parser.add_argument('-i', '--tv_ip_address', type=str, help='The IP address of the Android TV')
    parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='store_true')
    parser.add_argument('-l', '--log_to_disk', default=False,
                        help='Log to /tmp/hdmi_cec_to_adb.log', action='store_true')

    args = parser.parse_args()
    setupLogging(args.verbose, args.log_to_disk) 
    check_existing_processes()
    monitor = Monitor(args.tv_ip_address)
    try:
        monitor.runForever()
    except:
        logger.exception('Unhandled exception')


if __name__ == '__main__':
    main()
