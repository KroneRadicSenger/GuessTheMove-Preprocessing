# Guess The Move Preprocessing
This is the Python Game preprocessing tool to generate analyzed games bundle for our Chess Guess The Move App created as part of our Bachelor Forschungsprojekt INF at University of Stuttgart.

## Abstract
First and foremost, the use of this python program is to analyze grandmaster chess games given by a PGN file and annotate the output analysis result file with full player names and elo ratings for every player in every analyzed game. Additionally, it also provides a live analysis server to which requests can be sent.

## Setup

## Prerequisite
Make sure you have Python 3.7 or later installed on your device as well as pip3 to use with it.

### Install dependencies
To install missing dependencies, use the following command
```python3 -m pip install -r requirements.txt```
(substitute ```python3``` with the command you use to run Python 3.7)

### Engine Configuration
You have to configure an ```ENGINE_PATH``` pointing to the UCI engine executable (i.e. Stockfish) in the ```engine.py``` file
inside the ```engine``` module.

### Opening Reader Configuration
To use the opening reader, you have to open the ```opening.py``` file inside the ```opening``` module and configure a ```ECO_FILES_DIRECTORY``` pointing to a directory containing Opening ECO table files. We have provided sample ECO files ready for you to use. These files are taken from ```https://github.com/niklasf/eco``` licensed under the ```CC0-1.0 License```.
### Gaviota Endgame Tablebase Probing Configuration
If you want to use endgame tablebase probing, you have to open the ```endgame.py``` file inside the ```endgame``` module and configure a ```GAVIOTA_FILE_PATH``` pointing to a directory containing Gaviota endgame tablebase files . You can build these Gaviota tablebases yourself or use prebuilt and compressed tablebases ready for download (e.g. under https://chess.cygnitec.com/tablebases/gaviota/5/). We recommend tablebases for endgames with up to five pieces left to allow the best possible endgame coverage. In addition to this, you have to uncomment the section after ```# TODO Remove comments to use endgame table base probing``` in the ```commands.py``` file.

## Execution

### Analyze games in a PGN file and create an analyzed games bundle from them

#####  1. Analyze games
To analyze one or multiple grandmaster games in a pgn file, you should use the following command
```python main.py analyze <GRANDMASTER_NAME> <PGN_FILE_PATH>```
where ```<GRANDMASTER_NAME>``` should be formatted as follows ```LastName,FirstName```.
As soon as the program terminates (this can take a while if you analyze many games at once), an
analysis output file will be saved to the ```output``` directory for each game. Besides that, the program creates a merged analysis output file which contains all of the analyzed games. Note that our tool only analyzes those grandmaster games in which the grandmaster won so not all input games will be included in the analysis output file(s).

#####     2. Annotate merged analysis output file
To annotate this merged analysis output file with full player names
and elo ratings for every analyzed game contained, you should use the following command
```python main.py annotate output.json```
This command will create an annotated version of the given analysis output file and save it in the
```output/annotated``` directory. Besides the json file, it will also add a gzipped variant of this file which can be used as an analyzed games bundle in the app. See the ```README.md```of the app for how to do this.

### Run live analysis server
Note: The live analysis server is not production ready yet.
To run the live analysis server in dev mode, use the following command
```python main.py api```
This will provide a REST API endpoint ```/analyse``` that is used by the live analysis mode in our Flutter App to
analyse arbitrary moves at any time.

## License
This project is licensed under the GPLv3 License. You can find the full license text in the
```LICENSE.md``` file.