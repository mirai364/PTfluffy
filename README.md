https://sites.google.com/site/twisteroidambassador/ptff

# PTfluffy: A DJMax Online Note Chart Converter  

A small tool that reads/parses .pt files from DJMax Online, and saves them into .csv or .bms/.bme files.

## What it does:
* Read and parse *.pt files from the original DJMax Online. DJMax Portable series, DJMax Trilogy and DJMax Technica are not supported.
* Output all interpreted data into .csv files for analysis.
* Output note chart to .bms/.bme files that can be read by BMSE and bemani emulators.
* Converts all notes correctly including long (hold) notes and short (hit) notes.
* Converts background notes correctly.
* Converts speed/BPM changes correctly.
## What it doesn't do:
* Save volume and pan (left/right) of each individual note in .bms files. These information are saved to .csv files.
* Retrieve information of note charts, including title, composer, genre, etc. As far as I know this info is stored separately in a database in DJ Max Online.
* Unpack song data, including BGM, key sounds, BGA elements, etc. These data are stored in *.pak files. To unpack pak files please see the link on the bottom of this page.
## Usage:
This script requires Python 3.2.
```
usage: ptfluffy.py [-h] [-o BMSFILE] [-c CSVFILE] [-5 | -7] inputfile

Extract data from DJMax Online *.pt files. Version 20111013

positional arguments:
  inputfile   Filename of .pt file to extract from.

optional arguments:
  -h, --help  show this help message and exit
  -o BMSFILE  Filename of .bms/bme file to output to. Existing files will be
              overwritten without warning.
  -c CSVFILE  Filename of .csv file to output to. Includes all useful data
              extracted from .pt file. Existing files will be overwritten
              without warning.
  -5          Treat .pt file as 5-key chart.
  -7          Treat .pt file as 7-key chart. This is the default option.
```

## Final notes:
This tool is licensed under [GPL v3](http://www.gnu.org/licenses/gpl.html).  
This tool is provided AS IS. I am not responsible for any loss/consequences you may face by using this tool.  
This tool is for research purpose only. Please don't use it for any activity that may infringe copyright or otherwise illegal.  

