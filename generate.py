#!/usr/bin/python
#-*- coding: utf-8 -*-
import os
import sys
import re
import argparse
import Image
import webbrowser
import shutil
import math

import zipfile
import rarfile

def listDir(dirPath, fileExtList, normcase=False):
    if normcase:
        fileList = [os.path.normcase(f) for f in os.listdir(dirPath)]
    else:
        fileList = [f for f in os.listdir(dirPath)]
    fileList = [f for f in fileList if os.path.splitext(f)[1] in fileExtList]    
    return sorted(fileList)
    

def getCaptionsFromFilenames(dirPath, truncateIndexes=False):
    captions={}
    fileExtList=['.jpg', '.jpeg', '.JPG', '.JPEG']   
    filenames = [os.path.splitext(f)[0] for f in listDir(dirPath, fileExtList)]
    for filename in filenames:
        caption = filename
        if truncateIndexes:
            caption = re.sub(r'^[0-9]+', "", caption)
        caption = re.sub(r'\.(jpg|jpeg)', "", caption, flags=re.I)
        caption = re.sub(r'[_]', " ", caption)
        caption = "".join((caption[0].upper(), caption[1:]))
        captions[filename] = caption
    return captions


def getCatpionsFromFile(captionsFilePath, dirPath, withFilenames=True, withNumbers=False):
    captions = {}
    try:
        caption_file = open(os.path.join(dirPath, captionsFilePath), "r")
    except IOError, TypeError:
        return captions
    noErrors = 0
    fileExtList=['.jpg', '.jpeg', '.JPG', '.JPEG']   
    filenames = [os.path.splitext(f)[0] for f in listDir(dirPath, fileExtList)]
    for line, filename in zip(caption_file, filenames):        
        if withFilenames:
            filename = line.split()[0]
        if filename in captions:
            print "Filename %s appeared more than once!" % (filename)
            noErrors += 1
            filename = "Wrong filename %d" % noErrors
        if withFilenames or withNumbers:
            caption = " ".join(line.split()[1:])        
        else:
            caption = " ".join(line.split())  
        captions[filename] = caption
    caption_file.close()
    return captions

    
def resize_proportionally(filePath, max_height=720, max_width=0, out=None, force=False, genImages=True):
        '''
        Resizes file from filepath to given max_height or max_width (if bth are given max_height is ignored).
        Second dimension is resized proportionaly yto the first one.
        Result image is written to "out" path or "file_path" if "out" is not given
        Returns width and height of the new image
        ''' 
        out = out or filePath
        im = Image.open(filePath)
        width =  im.size[0]
        height = im.size[1]
        new_height = min(height, max_height) if not force else max_height
        new_width = width
        if max_width:
            new_width =  min(width, max_width)
            new_height = int(float(height) * new_width / width)
        else:
            new_width = int(float(width) * new_height / height)
        if genImages and (new_height != height or out != filePath):
            resized_im = im.resize((new_width, new_height), Image.ANTIALIAS)
            resized_im.save(out , 'JPEG', quality=75)
        
        return (new_width, new_height)

def find_minimum_height(dirPath, fileExtList=['.jpg', '.jpeg', '.JPG', '.JPEG']):
    min_height = 99999
    for filename in listDir(dirPath, fileExtList):
        filename = os.path.normcase(filename)
        filePath = os.path.join(dirPath, filename)
        im = Image.open(filePath)
        height = im.size[1]
        if height < min_height:
            min_height = height
    return min_height
        
def process(dirPath, thumb="", captions={}, 
            fileExtList=['.jpg', '.jpeg', '.JPG', '.JPEG'], 
            galleryFilePath="gallery.xml", outDir=None, 
            force_resize=False, equal_heights=True, max_height=720, thumb_number=1,
            genImages=True):
    imgOutDir = os.path.join(outDir, "images")
    if not os.path.isdir(imgOutDir):
        os.makedirs(imgOutDir)
    if (equal_heights and not force_resize):
        max_height = min(find_minimum_height(dirPath, fileExtList), max_height)
        
    with open(galleryFilePath, 'w+') as galleryFile:
        galleryFile.write('''<?xml version="1.0" encoding="UTF-8"?>\n''')    
        galleryFile.write('''<gallery frameColor="0xFFFFFF" frameWidth="15" imagePadding="20" displayTime="6" enableRightClickOpen="true">\n''')
        counter = 0
        for filename in listDir(dirPath, fileExtList):           
            counter+=1
            caption = captions.get(os.path.splitext(filename)[0], "")
            filename = os.path.normcase(filename)
            filePath = os.path.join(dirPath, filename)
            width, height = resize_proportionally(filePath, out=os.path.join(imgOutDir, filename), 
                force=force_resize, max_height=max_height, genImages=genImages)
            if filename == thumb or thumb == '' and counter==thumb_number:
                resize_proportionally(filePath, max_width=300, out=os.path.join(outDir, 'thumb.jpg'))
                thumb = None
            galleryFile.write('<image>\n')
            galleryFile.write('\t<url>%s</url>\n' % os.path.join("images/", filename))
            galleryFile.write('\t<caption>%s</caption>\n' % caption)
            galleryFile.write('\t<width>%d</width>\n' % width)
            galleryFile.write('\t<height>%d</height>\n' % height)
            galleryFile.write('</image>\n\n')
            

def copyIncludes(destDir):
    for f in ("autoviewer.swf", "swfobject.js", "index.html"):
        sourcePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), f)
        shutil.copy(sourcePath, os.path.join(destDir, f))

def message(text):
    print text


if __name__ == "__main__":    
    parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description = "Autoviewer gallery generator",
      prog = "autoviewgen",
      epilog = u"Author:\t Tomasz Zietkiewicz. 2012"
      )

    parser.add_argument('-d', '--dir', help='Path to directory with image files')
    parser.add_argument('-a', '--arch', help='Path to rar/zip file with image files', default=None)
    parser.add_argument('-o', '--out', help='Path to output directory. If not given source directory will be used', default=None)
    parser.add_argument('-c', '--captions', help='Path to captions file', default="captions.txt")
    parser.add_argument('-f', '--filenames', help='Captions contains filenames as a first word of caption', action="store_true")
    parser.add_argument('--numbers', help='Captions contains numbers as a first word of caption', action="store_true")
    parser.add_argument('-g', '--guess', help='Guess captions from filenames', action="store_true")
    parser.add_argument('-i', '--indexes', help='Truncate first digits from filename', action="store_true")
    parser.add_argument('-t', '--thumb', help='Name of a file whch will be used to generate thumbnail file', default="")
    parser.add_argument('-n', '--thumb_number', 
                        help='Number of image which will be used to generate thumbnail. Used only when argument "--thumb" not given',
                        type=int, default=1)
    parser.add_argument('-r', '--forceresize', help='Force resize of images (even if originals are smaller than target"', action="store_true")
    parser.add_argument('-e', '--equal_heights', help='''If forceresize is not set, all images will be downsized 
    proportionaly to have identical height as the one witch smallest height''', action="store_true")    
    
    parser.add_argument('-s', '--size', help='Target maximum image height', type=int, default=720)
    parser.add_argument('-C', '--correct', help='Do not generate image files, only xml and thumb', action="store_true")

    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.3')
    args = parser.parse_args()

    outDir = args.out or os.path.join(args.dir or  os.getcwd(), "gallery/")
    if not os.path.isdir(outDir):
        os.makedirs(outDir)
    tmpDir = os.path.join(outDir, "temp/")  

    generate_imgs = not args.correct
    
    try:
        if args.arch:
            try:
                ext = os.path.splitext(args.arch)[1]                
                if ext == '.zip'  :
                    arch = zipfile.ZipFile(args.arch, 'r')
                    error = arch.testzip()
                elif ext == '.rar' and rarfile.is_rarfile(args.arch):
                    arch = rarfile.RarFile(args.arch, 'r')
                    error = arch.testrar()
                else:
                    message("Given file is neither zip nor rar archive. Aborting.")
                    arch.close()
                    sys.exit()                    
                if error:
                    message("Error in file %s. Aborting." % error)
                    arch.close()
                    sys.exit()
                else:                                                      
                    os.makedirs(tmpDir)
                    arch.extractall(tmpDir)
                    args.dir = tmpDir
                    arch.close()
                    
            except zipfile.BadZipfile:
                message("Problem with your zip/rar file!")
                raise
            except Exception as e:
                message("Unexpected exception: %s" % e)
                raise
            
        args.dir = unicode(args.dir)
        
        if args.guess:
            captionsDict = getCaptionsFromFilenames(args.dir, truncateIndexes=args.indexes)
        else:
            captionsDict = getCatpionsFromFile(args.captions, args.dir, args.filenames, args.numbers)
        for filename, caption in sorted(captionsDict.items(), key=lambda t: t[0]):
            print filename + " " + caption

        process(args.dir, captions = captionsDict, thumb=args.thumb, 
                galleryFilePath=os.path.join(outDir, "gallery.xml"), 
                outDir=outDir, force_resize=args.forceresize,
                equal_heights=args.equal_heights,
                max_height=args.size, thumb_number=args.thumb_number,
                genImages=generate_imgs)
                
        copyIncludes(outDir)
    
    finally:
        if os.path.isdir(tmpDir):
            shutil.rmtree(tmpDir)
    
    indexFilePath = os.path.abspath(os.path.join(outDir, "index.html"))
    url = "file://%s" % indexFilePath
    print url 
    webbrowser.open(url, new=True)