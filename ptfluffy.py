"""
This tool extracts data from DJMax Online .pt files, and writes them to either .bms/bme or
 .csv files.
"""

##    PTfluffy
##    Copyright 2011 twisteroid_ambassador
##
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.

ver = '20190426'
debug = False

import argparse
import struct
import fractions
import csv
import os
import warnings
import sqlite3
warnings.filterwarnings('ignore')

class PTFileError(Exception):
    """Exception class for .pt file related exceptions."""
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

def getMPos(pos):
    """Calculate measure number and position in measure from an absolute position."""
    measureLength = 192
    frac = fractions.Fraction(pos%measureLength, measureLength)
    return [pos//measureLength, frac.numerator, frac.denominator]

def lcm(*z):
    """Calculates the least common multiple of arbitrary amount of numbers.
    
    If 0 arguments, return 1."""
    l = 1
    for a in z:
        l = l * a / fractions.gcd(l, a)
    return int(l)

def parsePTFile(bPTfile):
    """Parse .pt files and return lists of extracted data.
    
    Argument: bPTfile: a bytes object containing the entire content of .pt file
    Returns: (oggList, bpmList, trackList)
    oggList: a list of [ID, filename]
    bpmList: a list of [Position, BPM]
    trackList: a list of [TrackName, Track]
        Track: a list of [Position, ID, Vol, Pan, Length]
    """
    oggList = []
    bpmList = []
    trackList = []
    
    if bPTfile[0:4].decode() != 'PTFF':
        raise PTFileError("Invalid file header")
    
    # First section of .pt file: list of .ogg key notes
    filePos = 0x18
    recordLength = 0x42
    while bPTfile[filePos:filePos+4] != bytes('EZTR','ascii'):
        parseData = struct.unpack('<BB64s', bPTfile[filePos:filePos+recordLength])
        # Data structure: ID, unknown, NUL-terminated filename, padding(?)
        oggList.append((parseData[0], parseData[2].partition(b'\x00')[0].decode()))
        filePos = filePos + recordLength
    
    # Second section of .pt file: BPM changes
    filePos = filePos + 0x4e
    recordLength = 0x0b
    bpmList.append([0,0,0,1,0.]) # Initial BPM
    while bPTfile[filePos:filePos+4] != bytes('EZTR','ascii'):
        parseData = struct.unpack('<HxxBfBx', bPTfile[filePos:filePos+recordLength])
        # Data structure: Position, x, x, Type(?), BPM, unknown, x
        if parseData[1] == 3: # Type
            if parseData[0] == 0: # Position
                bpmList[0][4] = parseData[2]
            else:
                bpmList.append([parseData[0], parseData[2]])
        filePos = filePos + recordLength
    
    # Following sections of .pt file: Note tracks
    while filePos < len(bPTfile):
        trackList.append([])
        parseData = struct.unpack('<72s', bPTfile[filePos+6:filePos+78]) # Track name
        trackList[-1] = [parseData[0].partition(b'\x00')[0].decode(), []]
        
        filePos = filePos + 0x4e
        recordLength = 0x0b
        
        while filePos < len(bPTfile) and bPTfile[filePos:filePos+4] != bytes('EZTR','ascii'):
            parseData = struct.unpack('<HxxBBBBBH', bPTfile[filePos:filePos+recordLength])
            # Data structure: Position, x, x, Type(?), ID, Vol, Pan, unknown, Length
            if parseData[1] == 1:
                trackList[-1][1].append([parseData[0], parseData[2], parseData[3], parseData[4], parseData[6]])
            filePos = filePos + recordLength
            
    return (oggList, bpmList, trackList)
    
def getDifficulty(difficultName):
    difficultName = difficultName.lower()
  
    difficulty = 3
    if difficultName == 'ez': difficulty = 1
    if difficultName == 'nm': difficulty = 2
    if difficultName == 'hd': difficulty = 3
    if difficultName == 'mx': difficulty = 4
    if difficultName == 'sc': difficulty = 5
    if difficultName == 'easy': difficulty = 1
    if difficultName == 'normal': difficulty = 2
    if difficultName == 'hard': difficulty = 3

    return difficulty
 
def getFormalDifficultyName(difficulty):
    formalDifficultyName = 'HARD'

    if difficulty == 1: formalDifficultyName = 'EASY'
    if difficulty == 2: formalDifficultyName = 'NORMAL'
    if difficulty == 3: formalDifficultyName = 'HARD'
    if difficulty == 4: formalDifficultyName = 'MAXIMUM'
    if difficulty == 5: formalDifficultyName = 'SUPER-CRAZY'

    return formalDifficultyName
 
def getLevelIndex(difficultName):
    difficultName = difficultName.lower()
  
    levelIndex = 5
    if difficultName == 'ez': levelIndex = 3
    if difficultName == 'nm': levelIndex = 4
    if difficultName == 'hd': levelIndex = 5
    if difficultName == 'mx': levelIndex = 6
    if difficultName == 'sc': levelIndex = 7
    if difficultName == 'easy': levelIndex = 3
    if difficultName == 'normal': levelIndex = 4
    if difficultName == 'hard': levelIndex = 5

    return levelIndex

def getDbData(tag, key, levelIndex):
    # init
    dbpath = 'songinfo.db'
    idIndex = 0
    titleIndex = 2
    genreIndex = 3
    artistIndex = 5
    
    #connect
    connection = sqlite3.connect(dbpath)
    cursor = connection.cursor()

    # SELECT
    cursor.execute('SELECT * FROM songinfo WHERE tag = ?', (tag,))
    songinfo = cursor.fetchone()

    if songinfo[artistIndex] is None : artistIndex = 7

    cursor.execute('SELECT * FROM levelinfo WHERE songinfoId = ? and key = ?', (songinfo[idIndex],key))
    levelinfo = cursor.fetchone()
    return (songinfo[titleIndex], songinfo[genreIndex], songinfo[artistIndex], levelinfo[levelIndex])




# Parsing command line arguments with argparse
aparser = argparse.ArgumentParser(description='Extract data from DJMax Online *.pt files. Version ' + ver)
aparser.add_argument('inputfile', help='Filename of .pt file to extract from.', type=argparse.FileType('rb'))
aparser.add_argument('-o', help='Filename of .bms/bme file to output to. Existing files will be overwritten without warning.', \
                     dest='bmsfile')
aparser.add_argument('-c', help='Filename of .csv file to output to. Includes all useful data extracted from .pt file. ' + \
                     'Existing files will be overwritten without warning.', dest='csvfile')
akeys=aparser.add_mutually_exclusive_group()
akeys.add_argument('-5', help='Treat .pt file as 5-key chart.', action='store_true', dest='fivekey')
akeys.add_argument('-7', help='Treat .pt file as 7-key chart. This is the default option.', action='store_true', dest='sevenkey')

args=aparser.parse_args()
if not args.fivekey and not args.sevenkey:
    args.sevenkey = True

# Read .pt file
infilename = args.inputfile.name
if debug:
    print('PTfluffy v ' + ver )
    print('')

print('Reading ' + infilename + '... ', end='')

infile = bytes(args.inputfile.read())
args.inputfile.close()
print('Done.')

if debug:
    print('Parsing... ', end='')
oggList, bpmList, trackList = parsePTFile(infile)
if debug:
    print('Done.')

# Write CSV file
if args.csvfile is not None:
    if debug:
        print('Writing to CSV file ' + args.csvfile + ' ... ', end='')
    csvFile = open(args.csvfile, mode='w', newline='')
    csvWriter = csv.writer(open(args.csvfile, mode='w', newline=''), dialect='excel')
    csvWriter.writerow(['Data extracted from:',infilename])
    csvWriter.writerow(['Generated by:', 'PTfluffy ver' + ver])
    csvWriter.writerow('')
    
    csvWriter.writerow(['List of .ogg files:'])
    csvWriter.writerow(['ID', 'filename'])
    for item in oggList:
        csvWriter.writerow([format(item[0], '02X'), item[1]])
        
    csvWriter.writerow('')
    csvWriter.writerow(['Track:', 0, 'BPM changes'])
    csvWriter.writerow(['Pos', 'BPM'])
    for item in bpmList:
        csvWriter.writerow([item[0], item[1]])

    trackNum = 0
    for track in trackList:
        trackNum = trackNum + 1
        csvWriter.writerow('')
        csvWriter.writerow(['Track:', trackNum, track[0]])
        csvWriter.writerow(['Pos', 'ID', 'Vol', 'Pan', 'Length'])
        for item in track[1]:
            csvWriter.writerow([item[0], format(item[1], '02X'), item[2], item[3], item[4]])

    del csvWriter
    csvFile.close()
    if debug:
        print('Done.')

# Write BMS file
if args.bmsfile is not None:
    bmsFileName = args.bmsfile

    baseName = os.path.basename(infilename)
    root_ext_pair = os.path.splitext(baseName)
    params = root_ext_pair[0].split('_') 
    
    index = 1
    tag = params[0]
    difficultName = 'hd'
    key = ''
    if (len(params) > 2):
        difficultName = params[index]
        index += 1
        # Exception handling(elasticstar_remix)
        if (difficultName == 'remix'):
            tag = tag + '_remix'
            key = params[index][0:1]
            difficultName = 'hd'
            index += 1

        if (len(params) > index):
            key = params[index][0:1]
            if key != '5' and key != '7':
                key = params[index - 1][0:1]
                difficultName = params[index]
            
    else:
        key = params[index][0:1]
        difficultName = params[index][2:4]

    if debug:
        print([tag, difficultName, key])
    difficulty = getDifficulty(difficultName)
    title, genre, artist, playLevel  = getDbData(tag, key, getLevelIndex(difficultName))
    formalDifficultyName = getFormalDifficultyName(difficulty)
    if debug:
        print('DB data [Title "%s", Genre "%s", Artist "%s", Difficulty %d[%s], PlayLevel %d]' % (title, genre, artist, difficulty, formalDifficultyName, playLevel))

    os.makedirs('chart\\' + tag, exist_ok=True)
    bmsFileName = 'chart\\' + tag + '\\@' + title + ' [1P' + key + 'K '+ formalDifficultyName + '].bms'

    if (key == '7'): args.sevenkey = True
    if (key == '5'): args.sevenkey = False
 
    if debug:
        print('Writing to BMS file %s ...' % bmsFileName, end='')
    bmsFile = []

    bmsFile.append('\n')
    bmsFile.append('* ----------------------HEADER FIELD\n')
    bmsFile.append('\n')
    bmsFile.append('#PLAYER 1\n')
    bmsFile.append('#GENRE ' + genre + '\n')
    bmsFile.append('#TITLE ' + title + '\n')
    bmsFile.append('#ARTIST ' + artist + '\n')
    bmsFile.append('#BPM ' + str(bpmList[0][4]) + '\n')
    bmsFile.append('#PLAYLEVEL ' + str(playLevel) + '\n')
    bmsFile.append('#RANK 3\n') # EASY
    bmsFile.append('\n')
    bmsFile.append('\n')

    bmsFile.append('#DIFFICULTY ' + str(difficulty) + '\n')
    bmsFile.append('#LNOBJ ZZ\n')
    bmsFile.append('#LNTYPE 1\n')
    bmsFile.append('\n')

    # .ogg file definintions
    for item in oggList:
        bmsFile.append('#WAV' + format(item[0], '02X') + ' SND\\' + item[1] + '\n')

    bmsFile.append('\n')
    bmsFile.append('\n')
    bmsFile.append('*---------------------- MAIN DATA FIELD\n')
    bmsFile.append('\n')
    bmsFile.append('\n')

    # BPM definitions
    bpms = sorted(set([x[1] for x in bpmList]))
    for item in bpms:
        bmsFile.append('#BPM' + format(bpms.index(item)+1, '02X') + ' ' + str(item) + '\n')

    # BPM changes in track 08
    bmsBPMList = [getMPos(x[0]) + [x[1]] for x in bpmList]
    for m in sorted(set([x[0] for x in bmsBPMList])):
        bpmMeasure = [x for x in bmsBPMList if x[0] == m]
        denom = lcm(*[x[2] for x in bpmMeasure])
        measure = [0] * denom
        for item in bpmMeasure:
            measure[int(item[1]*denom/item[2])] = bpms.index(item[3])+1
        bmsFile.append('#%03d08:' % m + ''.join(['%02X' % x for x in measure]) + '\n')

    
    # Playable tracks are 11, 12, 13, 14, 15, [18, 19]
    # BGM tracks are all 01
    if args.sevenkey:
        bmsTrackMapping = {2:12, 3:13, 4:14, 5:15, 6:18, 9:11, 10:19}
        bmsLNTrackMapping = {2:52, 3:53, 4:54, 5:55, 6:58, 9:51, 10:59}
    else:
        bmsTrackMapping = {2:11, 3:12, 4:13, 5:14, 6:15}
        bmsLNTrackMapping = {2:51, 3:52, 4:53, 5:54, 6:55}
        
    # Create separate short & long notes list for playable tracks
    bmsSNList = []
    LNList = []
    bmsLNList = []
    bmsMaxMeasure = 0
    for t in range(len(trackList)):
        if t in bmsTrackMapping:
            bmsSNList.append([getMPos(x[0]) + [x[1]] for x in trackList[t][1] if x[4] <= 6])
            LNList = [[x[0], x[1], x[4]] for x in trackList[t][1] if x[4] > 6]
            bmsLNList.append([])
            for x in LNList:
                bmsLNList[-1].append(getMPos(x[0]) + [x[1]])
                bmsLNList[-1].append(getMPos(x[0] + x[2]) + [x[1]])
            bmsMaxMeasure = max(bmsMaxMeasure, 0, *[x[0] for x in bmsSNList[-1]])
            bmsMaxMeasure = max(bmsMaxMeasure, 0, *[x[0] for x in bmsLNList[-1]])
        else:
            bmsSNList.append([getMPos(x[0]) + [x[1]] for x in trackList[t][1]])
            bmsLNList.append([])
            bmsMaxMeasure = max(bmsMaxMeasure, 0, *[x[0] for x in bmsSNList[-1]])
    
    # append Note tracks
    notesCount = 0;
    for t in range(len(bmsSNList)):
        if not bmsSNList[t] and not bmsLNList[t]: continue # Skip empty tracks
        
        if bmsTrackMapping.get(t, 1) > 1 :
            if bmsSNList[t]: notesCount += len(bmsSNList[t])
            if bmsLNList[t]: notesCount += len(bmsLNList[t])
        
        # Short note tracks
        trackLabel = '%02d' % bmsTrackMapping.get(t, 1)
        for m in range(bmsMaxMeasure+1):
            noteMeasure = [x for x in bmsSNList[t] if x[0] == m]
            denom = lcm(*[x[2] for x in noteMeasure])
            measure = [0] * denom
            for item in noteMeasure:
                measure[int(item[1]*denom/item[2])] = item[3]
            bmsFile.append('#%03d%s:' % (m, trackLabel) + ''.join(['%02X' % x for x in measure]) + '\n')
        
        # Long note tracks
        if not bmsLNList[t]: continue
        trackLabel = '%02d' % bmsLNTrackMapping.get(t, 1)
        for m in range(bmsMaxMeasure+1):
            noteMeasure = [x for x in bmsLNList[t] if x[0] == m]
            denom = lcm(*[x[2] for x in noteMeasure])
            measure = [0] * denom
            for item in noteMeasure:
                measure[int(item[1]*denom/item[2])] = item[3]
            bmsFile.append('#%03d%s:' % (m, trackLabel) + ''.join(['%02X' % x for x in measure]) + '\n')

    bmsFile.insert(0, '; 2P = 0\n')
    bmsFile.insert(0, '; 1P = ' + str(notesCount) + '\n')

    with open(bmsFileName, mode='w', encoding='utf-8') as f:
        f.writelines(bmsFile)
    
    if debug:
        print('Done.')
