#-*- coding: utf-8 -*-
import os
import argparse
import Image
import webbrowser

def listDir(dirPath, fileExtList):
    fileList = [os.path.normcase(f) for f in os.listdir(dirPath)]
    fileList = [f for f in fileList if os.path.splitext(f)[1] in fileExtList]    
    return sorted(fileList)
    

def getCatpions(captionsFilePath, dirPath, withFilenames=True):
    captions = {}
    try:
        caption_file = open(captionsFilePath, "r")
    except IOError, TypeError:
        return captions
    noErrors = 0
    fileExtList=['.jpg', '.jpeg', '.JPG', '.JPEG']   
    filenames = [os.path.splitext(f)[0] for f in listDir(dirPath, fileExtList)]
    for line, filename in zip(caption_file, filenames):        
        if(withFilenames):
            filename = line.split()[0]
        if filename in captions:
            print "Filename %s appeared more than once!" % (filename)
            noErrors += 1
            filename = "Wrong filename %d" % noErrors
        if(withFilenames):
            caption = " ".join(line.split()[1:])        
        else:
            caption = " ".join(line.split())  
        captions[filename] = caption
    caption_file.close()
    return captions

def openGalleryFile(galleryFilePath):
    galleryFile = open(galleryFilePath, "r")
    lines = galleryFile.readlines()
    galleryFile.close()

    galleryFile = open(galleryFilePath+".backup", "w")
    for line in lines:
        galleryFile.write(line)
    galleryFile.close()

    galleryFile = open(galleryFilePath, "w")
    return galleryFile
    
def resize_proportionally(filePath, max_height=720, max_width=0, out=None):
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
        new_height = min(height, max_height)
        new_width = width
        if max_width:
            new_width =  min(width, max_width)
            new_height = int(float(height) * new_width / width)
        else:
            new_width = int(float(width) * new_height / height)
        if new_height != height or out != filePath:
            resized_im = im.resize((new_width, new_height), Image.ANTIALIAS)
            resized_im.save(out , 'JPEG', quality=75)
        return (new_width, new_height)


def process(dirPath, thumb="", captions={}, fileExtList=['.jpg', '.jpeg', '.JPG', '.JPEG'], galleryFilePath="gallery.xml"):
    galleryFile = openGalleryFile(galleryFilePath)
    galleryFile.write('''<?xml version="1.0" encoding="UTF-8"?>\n''')    
    galleryFile.write('''<gallery frameColor="0xFFFFFF" frameWidth="15" imagePadding="20" displayTime="6" enableRightClickOpen="true">\n''')
    #galleryFile.close()    
    #galleryFile = open(galleryFilePath, 'a')
    for filename in listDir(dirPath, fileExtList):           
        filePath = os.path.join(dirPath, filename)
        caption = captions.get(os.path.splitext(filename)[0], "")
        width, height = resize_proportionally(filePath)
        if filePath == thumb:
            import pdb;pdb.set_trace()
            resize_proportionally(filePath, max_width=300, out='thumb.jpg')
        galleryFile.write('<image>\n')
        galleryFile.write('\t<url>%s</url>\n' % filePath)
        galleryFile.write('\t<caption>%s</caption>\n' % caption)
        galleryFile.write('\t<width>%d</width>\n' % width)
        galleryFile.write('\t<height>%d</height>\n' % height)
        galleryFile.write('</image>\n\n')
    galleryFile.close()


if __name__ == "__main__":    
    parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      description = "Autoviewer gallery generator",
      prog = "autoviewgen",
      epilog = u"Author:\t Tomasz Zietkiewicz. 2012"
      )

    parser.add_argument('-d', '--dir', help='Path to directory with image files', default="images")
    parser.add_argument('-c', '--captions', help='Path to captions file', default="captions.txt")
    parser.add_argument('-f', '--filenames', help='Captions contains filenames as a first wrd of caption', action="store_true")
    parser.add_argument('-t', '--thumb', help='Path to file whoch will be used to generate thumbnail file', default="")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.3')
    args = parser.parse_args()
           
    captionsDict = getCatpions(args.captions, args.dir, args.filenames)
    for filename, caption in sorted(captionsDict.items(), key=lambda t: t[0]):
        print filename + " " + caption
    process(args.dir, captions = captionsDict, thumb=args.thumb)
    
    indexFilePath = os.path.abspath("index.html")
    url = "file://%s" % indexFilePath
    print url 
    webbrowser.open(url, new=True)