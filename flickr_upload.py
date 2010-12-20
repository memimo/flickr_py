import flickrapi
import signal, os
import glob
import sys
from optparse import OptionParser
import ConfigParser

'''
A simple flicker uploader 
Mehdi Mirza memirzamo@gmail.com  August 2010

for flickrapi refer to:
http://stuvel.eu/projects/flickrapi

'''

#Custom exception
class TimeoutException(Exception): 
    pass 

#-----
def status(progress, done):
    '''Update status of upload'''

    if done:
        print "Done uploading"
    #else:
    #    sys.stdout.write(" %d%% " % int(progress))
    #   sys.stdout.flush()

#------
def aut(api_key, api_secret):
    '''flickr authentication'''

    flickr = flickrapi.FlickrAPI(api_key, api_secret)
    (token, frob) = flickr.get_token_part_one(perms='write')
    if not token: raw_input("Press ENTER after you authorized this program")
    flickr.get_token_part_two((token, frob))

    return flickr


#---------
def upload(flickr, file_list, public, alarm_time):
    ''' Upload files to flickr
        flickr: flickr object
        files: list of files to be uploaded
        alarm_time: maximum allowed time for each file'''

    def timeout_handler(signum, frame):
        ''' Timout handler for upload'''

        raise TimeoutException()

    #List of files not uploaded
    err_list = []

    for item in file_list:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler) 
        signal.alarm(alarm_time)
        try:
            flickr.upload(filename = item, is_public = int(public), callback = status)
        except Exception, e:
            err_list.append(item)
        finally:
            signal.signal(signal.SIGALRM, old_handler) 

        signal.alarm(0)

    return err_list

#------
def get_files_dir(directory):
    '''get list of multimedia files in a directoru'''

    if directory[-1] !=  '/' : directory += '/'

    files = glob.glob(directory + '*.JPG')
    files.extend(glob.glob(directory + '*.jpg'))
    files.extend(glob.glob(directory + '*.AVI'))
    files.extend(glob.glob(directory + '*.avi'))

    return files 


#-----
def get_files_list(path):
    '''Read list of files from a file'''

    f = open(path, 'r')
    f_list = f.readlines()
    f_list = [item.rstrip('\n') for item in f_list]

    return f_list

#-------
def save(e_list):
    '''save list of files in a text file'''

    f = open('err_list.txt', 'w')
    for item in e_list:
        f.write(item + '\n')
    f.close()

#--------
def get_keys(conf_fname):
    '''read the api_key and api_secret from the config file'''

    config = ConfigParser.ConfigParser()

    #check if files exists
    if not os.path.isfile(conf_fname):
        config.add_section('App_Info')
        api_key = config.set('AppInfo', 'api_key', '')
        api_secret = config.set('AppInfo', 'api_secret', '')
        with open(conf_fname, 'w') as configfile:
            config.write(configfile)
        raise NameError('Pleas fill App info in config file')
    else:
        config.read(conf_fname)

    api_key = config.get('AppInfo', 'api_key')
    api_secret = config.get('AppInfo', 'api_secret')

    return api_key, api_secret


#---------Main----
def main():

    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)

    parser.add_option("-d", "--directory",  dest = "source_dir", 
                      default = os.getcwd(), help = "The source \
                      directory of multimedia files")
    parser.add_option("-c", "--config",  dest = "config_fname", 
                      default = '.config', help = "Path to config file in \
                      which api_key and api_secret is stored")
    parser.add_option("-t", "--time", dest = "alarm_time", default = 60, 
                      help = "Maximum allowed time for each file upload")
    parser.add_option("-l", "--list", dest = "file_list", default = None, 
                      help = "List of files to upload")
    parser.add_option("-p", "--public", dest = "public", default = False, 
                      action = "store_true", help = "Publicly available?")

    (options, args) = parser.parse_args()


    #get config
    api_key, api_secret = get_keys(options.config_fname)
    #Authentication
    print 'Authenting...'
    flickr = aut(api_key, api_secret)

    #Upload
    print 'Uploading...'
    if options.file_list != None:
        file_l = get_file_list(options.file_list)
    else:
        file_l = get_files_dir(options.source_dir)

    if len(file_l) == 0:
        raise NameError('No file to upload')

    err_list = upload(flickr, file_l,options.public, options.alarm_time)
    #Handle un-uploaded files
    while err_list != []:
        print 'The were an error uploading following files: ', err_list
        print 'Do you like to try again?'
        ans = sys.stdin.readline()
        if ans == "y\n":
            err_list = upload(flickr, err_list, options.public, options.alarm_time)
        else:
            print 'Would you like to save list of remaining files?'
            ans = sys.stdin.readline()
            if ans == "y\n": 
                #save the list in a file
                save(err_list)
            else:
                err_list = []


if __name__ == "__main__":
    main()
