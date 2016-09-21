#!/usr/bin/env python

import sys
import urllib2
import json
from copy import deepcopy
import time
import datetime

class DockerRegistry(object):
    def __init__(self, server):
        self.server = server
        self.version = "unknown"

        try:
            if self.__is_registry_v1():
                self.version = 'v1'
            elif self.__is_registry_v2():
                self.version = 'v2'
            else:
                raise Exception("unknown registry version")
        except Exception, e:
            print e
            #raise Exception("Can not connect to the registry server <%s>" % server)

    def __get_registry_version(self):
        try:
            urllib2.Request('http://{}/v2/'.format(self.server))
        except:
            raise

    def __is_registry_v1(self):
        try:
            req = urllib2.Request('http://{}/'.format(self.server))
            response = urllib2.urlopen(req)
            if "docker-registry server" in response.read():
                return True
            else:
                return False
        except:
            raise

    def __is_registry_v2(self):
        try:
            req = urllib2.Request('http://{}/v2/'.format(self.server))
            response = urllib2.urlopen(req)
            return True
        except:
            return False

    def get_images(self):
        if self.version == 'v1':
            return self.__get_images_v1()
        elif self.version == 'v2':
            return self.__get_images_v2()

        return None

    def __get_images_v1(self):
        images = {}
        try:
            # First get all images
            for i in range(3):
                req = urllib2.Request('http://{}/v1/search'.format(self.server))
                response = urllib2.urlopen(req)
                recv_json = json.load(response)
                for item in recv_json['results']:
                    if item['name'] not in images:
                        images[item['name']] = []

            # Get all tags for each image
            for image_name in images:
                tag_list = self.__get_tags_for_image_v1(image_name)
                images[image_name] = tag_list

            return images
        except Exception, e:
            print e

    def __get_images_v2(self):
        images = {}
        try:
            # First get all images
            for i in range(3):
                req = urllib2.Request('http://{}/v2/_catalog'.format(self.server))
                response = urllib2.urlopen(req)
                recv_json = json.load(response)
                for image in recv_json['repositories']:
                    if image not in images:
                        images[image] = []

            # Get all tags for each image
            for image_name in images:
                tag_list = self.__get_tags_for_image_v2(image_name)
                images[image_name] = tag_list

            return images
        except Exception, e:
            print e

    def __get_tags_for_image_v1(self, image_name):
        tag_list = []

        try:
            req = urllib2.Request('http://{}/v1/repositories/{}/tags'.format(self.server, image_name))
            response = urllib2.urlopen(req)

            if response.getcode() == 200:
                recv_json = json.load(response)
                for key, value in recv_json.items():
                    tag_list.append(key)
        except:
            raise

        return tag_list

    def __get_tags_for_image_v2(self, image_name):
        tag_list = []

        try:
            req = urllib2.Request('http://{}/v2/{}/tags/list'.format(self.server, image_name))
            response = urllib2.urlopen(req)

            if response.getcode() == 200:
                recv_json = json.load(response)
        except:
            raise

        return recv_json['tags']

    def __get_tags_for_image(self, image_name):
        if self.version == 'v1':
            return self.__get_tags_for_image_v1(image_name)
        elif self.version == 'v2':
            return self.__get_tags_for_image_v2(image_name)
    
    def is_image_exist(self, image_name, tag):
        tags = self.__get_tags_for_image(image_name)
        if len(tags) == 0 or tag not in tags:
            return False

        return True

def main(argv):
    try:
        registry = DockerRegistry(argv[0])
        #print "registry version is " + registry.version
        images =  registry.get_images()

        for image_name, tags in images.items():
            for tag in tags:
                print "{}/{}:{}".format(argv[0], image_name, tag)
    except Exception, e:
        print e

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print "Usage: registry <url>"
        print "For example: registry 172.30.10.195:5000"
        sys.exit(1)

    main(sys.argv[1:])
