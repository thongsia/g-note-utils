#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import struct
from string import Template

class DNTfile(object):
    """class to handle dnt files
    
    @attention: it is assumed that the document is rotated by 270 degrees (rotation=3),
    this is default on g-note 7100, so if dnt file uses different value the output of
    toSVG and simple_dnt2svg will have wrong orientation"""

    MARKER = struct.pack('4s2H4s','UEDY',0,0,'HARD')
    """@cvar: a 12 byte string that marks beggining of a dnt file"""
    PEN_CODES = { 0xa1:'black', 0xa3:'blue', 0xa5:'red', 0xe0:'none' }
    """@cvar: a color codes for pen"""
    PEN2CLASS = { 'black':'dnt-pen-black', 'blue':'dnt-pen-blue', 'red':'dnt-pen-red', 'none':'dnt-pen-none' }
    """@cvar: pen classes that are used for svg output"""
    SVG_TEMPLATE = '<polyline class=\"$svg_class\" points=\"$svg_path\" />\n'
    """@cvar: an svg template, $svg_class and $svg_path variables will be substituted by toSVG function,
    this variable can be edited to add more fields"""

    def __init__(self):
        self.version_major = 1 
        """@ivar: format version number, integer part"""
        self.version_minor = 0
        """@ivar: format version number, decimal part"""
        self.dpi = 0
        """@ivar: resolution, dot per inch"""
        self.x_size = 0
        """@ivar: X size"""
        self.y_size = 0
        """@ivar: Y size"""
        self.rotation = 0
        """@ivar: rotation (counter clockwise), the angle of rotation is M{90*rotation},
        0 - portrait up, this number is assumed to be 3 and not used in any calculations"""
        self.firmware = '1.2C'
        """@ivar: firmware version, string constant, default value 1.2C"""
        self.data_offset = 0x0
        """@ivar: position of data, default value is 0x40, the space between end of header and
        the start of data is filled with 0xff"""
        self.data = []
        """@ivar: a list of tuples that contain pen positions, 
        the format is (color code, x-position, y-position)"""
    
    def __str__(self):
        return 'Version:%2d.%0d\n'%(self.version_major, self.version_minor) \
                + 'DPI:%d\n'%(self.dpi) \
                + 'X size:%d\nY size:%d\n'%(self.x_size, self.y_size,) \
                + 'Rotation:%d\n'%(self.rotation) \
                + 'Firmware:%s\n'%(self.firmware,) \
                + 'Data offset:0x%x'%(self.data_offset)
    
    @classmethod
    def open(cls, file_name):
        """opens and reads datafile
        
        @param file_name: a name of a file to read
        @return: a DNTfile object attached to the file
        """
        fd = open(file_name, 'r') 
        # check if file is a dnt file, compare first 12 bytes
        if cls.MARKER != fd.read(12):
            fd.close()
            raise Exception('The header of the file doesn\'t match DNT file format.')

        dntobj = cls() # create an empty object
        # read the header from the file
        # version number
        dntobj.version_major = int(struct.unpack('H', fd.read(2))[0])
        dntobj.version_minor = int(struct.unpack('H', fd.read(2))[0])
        # no data area
        fd.read(6)
        # dpi
        dntobj.dpi = int(struct.unpack('H', fd.read(2))[0])
        # x and y size
        dntobj.x_size = int(struct.unpack('I', fd.read(4))[0])
        dntobj.y_size = int(struct.unpack('I', fd.read(4))[0])
        # skip some
        fd.read(2)
        # rotation
        dntobj.rotation = int(struct.unpack('B', fd.read(1))[0])
        # skip
        fd.read(1)
        # firmware version
        dntobj.firmware = struct.unpack('4s', fd.read(4))[0]
        # skip
        fd.read(4)
        # data position
        dntobj.data_offset = int(struct.unpack('H', fd.read(2))[0])

        # read data
        fd.seek(dntobj.data_offset) # go to data section
        rec = fd.read(8)
        while rec: # a loop over all records
            (pencolor, xlow, xhigh, ylow, yhigh, xytop) \
                    = struct.unpack('5BxBx', rec)
            # assemble pen position and color
            dntobj.data.append( \
                    (pencolor, xlow + (2<<6)*xhigh + (2<<13)*(int('00000011',2) & xytop), \
                     ylow + (2<<6)*yhigh + (2<<13)*(int('00001100',2) & xytop)))
            rec = fd.read(8)

        return dntobj
    # ==================== end of DNTfile.open ====================
    
    def copyHeader(self, dnt):
        """copies header information from another object"""

        self.version_major = dnt.version_major
        self.version_minor = dnt.version_minor
        self.dpi = dnt.dpi
        self.x_size = dnt.x_size
        self.y_size = dnt.y_size
        self.rotation = dnt.rotation
        self.firmware = dnt.firmware
        self.data_offset = dnt.data_offset
    
    def __str__(self):
        return 'Version:%2d.%0d\n'%(self.version_major, self.version_minor) \
                + 'DPI:%d\n'%(self.dpi) \
                + 'X size:%d\nY size:%d\n'%(self.x_size, self.y_size,) \
                + 'Rotation:%d\n'%(self.rotation) \
                + 'Firmware:%s\n'%(self.firmware,) \
                + 'Data offset:0x%x'%(self.data_offset)
    
    @classmethod
    def open(cls, file_name):
        """opens and reads datafile
        
        @param file_name: a name of a file to read
        @return: a DNTfile object attached to the file
        """
        fd = open(file_name, 'r') 
        # check if file is a dnt file, compare first 12 bytes
        if cls.MARKER != fd.read(12):
            fd.close()
            raise Exception('The header of the file doesn\'t match DNT file format.')

        dntobj = cls() # create an empty object
        # read the header from the file
        # version number
        dntobj.version_major = int(struct.unpack('H', fd.read(2))[0])
        dntobj.version_minor = int(struct.unpack('H', fd.read(2))[0])
        # no data area
        fd.read(6)
        # dpi
        dntobj.dpi = int(struct.unpack('H', fd.read(2))[0])
        # x and y size

    def toSVG(self):
        """returns a string that contains data in SVG format, no header, just SVG commands
        
        @note: the result contains a sequence of path commands, each belongs to one of 
        PEN2CLASS classes, use css etc. to modify the result
        @note: you can change DNTfile.SVG_TEMPLATE to modify output, safe_substitute is used
        so fields can be added to the template, otherwise use class marker
        @note: it is assumed that incoming data is rotated by 270 degrees from vertical
        and the output is rotated to vertical position"""

        if len(self.data) == 0:
            raise Exeption('Can\'t convert to SVG, no data')

        res = '' # result
        curpen = 'none' # no pen is set atm, pen up state
        path_data = '' # pen path
        for stroke in self.data:
            if curpen == self.PEN_CODES[stroke[0]]: # same pen as before add to path
                path_data += '%d,%d '%(self.y_size-stroke[2],stroke[1])
            else:
                if curpen != 'none': # new pen and old one is not none so finish path
                    res += Template(self.SVG_TEMPLATE).safe_substitute( \
                            svg_class = self.PEN2CLASS[curpen], svg_path = path_data) # update result
                    path_data = '' # flush path data, safety path_data should be flushed when new pen is detected
                if self.PEN_CODES[stroke[0]] != 'none': # the new pen is not none so start path
                    path_data = '%d,%d '%(self.y_size-stroke[2],stroke[1])
                curpen = self.PEN_CODES[stroke[0]] # always update pen
                
        return res
    # ==================== end of DNTfile.toSVG ==================== 

# ==================== end of DNTfile ====================

def simple_dnt2svg(dnt_name, svg_name, css_name = ''):
    """simple function to convert from data from dnt to svg format,
    used mainly for testing purposes 
    
    @param dnt_name: a name of dnt file
    @param svg_name: a name of output svg file
    @param css_name: if given it will be included verbatim into the output as the name for css file
    @note: see DNTfile.PEN2CLASS for the names of classes used in the output"""
    
    # template for output
    SVG_FILE_TEMPLATE = '<?xml version="1.0" standalone="no"?> \n' \
            + '$svg_css \n' \
            + '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" ' \
            + '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"> \n' \
            + '<svg width="$svg_width" height="$svg_height" viewBox="$svg_view_box" ' \
            + 'xmlns="http://www.w3.org/2000/svg" version="1.1"> \n' \
            + '$svg_data \n' \
            + '</svg>'
    if css_name != '': # if name of css is given add it to output 
        SVG_CSS_INSERT = '<?xml-stylesheet href="%s" type="text/css"?>'%css_name
    else: 
        SVG_CSS_INSERT = ''

    # read file
    dnt = DNTfile.open(dnt_name)

    # srite template out using data in dnt object
    sf = open(svg_name, 'w')
    sf.write(Template(SVG_FILE_TEMPLATE).safe_substitute( \
            svg_css = SVG_CSS_INSERT, \
            svg_width = str(float(dnt.y_size)/dnt.dpi)+'in', \
            svg_height = str(float(dnt.x_size)/dnt.dpi)+'in', \
            svg_view_box = '0 0 '+str(dnt.y_size)+' '+str(dnt.x_size), \
            svg_data = dnt.toSVG()))
    sf.close()
# ==================== end of simple_dnt2svg ====================

def split_pages(dnt):
    """the main function in this module, it split pages based on a marker

    The main purpose of this project is to upgrade interaction with 
    g-note device. To start a new page on a tablet you have to press
    new page button and sometimes you can forget to do this. The idea is to 
    use same page on the device but use some kind of marker in written
    text to separate pages. Editing old pages will be impossible but
    you don't have to worry about new page button. Then the interaction 
    with the tablet will be more like regular writing on a notebook.

    This implementation assumes that you start a new page when you write
    something in top right corner and then below 1/3 line on a page.
    One drawback is that you cant edit your writing in top right corner
    afterwards but this place is usually occupied by page number anyway.

    Top right corner is 0.5in but 0.5in area.
    
    @param dnt: a DNTfile object
    @return: a list of DNTfile objects that contain individual pages"""

    
    
if __name__ == '__main__':
   simple_dnt2svg('data/BK01-001.DNT', 'test.svg', 'mystyle.css') 
