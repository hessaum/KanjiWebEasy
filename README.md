KanjiWebEasy
============

Website made to users learn how to read NHK Web Easy articles

Setup for Windows
============

<ol>
<li>
Download Github for Windows https://windows.github.com/
</li>
<li>
Drap and drop https://github.com/SebastienGllmt/KanjiWebEasy.git into the Github for Windows application and place file in the default path
</li>
<li>
Download Python 3.4 from https://www.python.org/downloads/
</li>
<li>
Download https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py to some folder
</li>
<li>
Go to the folder where you placed get-pip.py. Inside the folder, shift+right click "open command window here"
</li>
<li>
Type <b>without</b> quotes: "C:/Python34/python.exe get-pip.py"
</li>
<li>
Go to C:\Python34\Scripts and shift+right click "open command window here"
</li>
<li>
Type <b>without</b> quotes: "pip install virtualenv"
</li>
<li>
Go to My Documents/Github/KanjiWebEasy
</li>
<li>
Once in the folder, Shift+Right click and select "Open command window here"
</li>
<li>
Type <b>without</b> quotes: "C:\Python34\Scripts\virtualenv venv"
</li>
<li>
Go to KanjiWebEasy/venv/scripts or KanjiWebEasy/venv/bin
</li>
<li>
Once in the folder, Shift+Right click and select "Open command window here"
</li>
<li>
Type <b>without</b> quotes: "pip install -r ../../requirements.txt" <br>
If you get a missing DLL error, download the Visual C++ redistribution from https://www.microsoft.com/en-us/download/details.aspx?id=48145 (probably x86)
</li>
<li>
Download Redis 2.8.17 from https://github.com/MSOpenTech/redis/releases
</li>
<li>
Put the contents of the .zip file in a foler on your C drive called "Redis 2.8.17"
</li>
</ol>

Launching for Windows
============
<ol>
<li>
Go to the folder where you put Redis then Shift+Right click and select "Open command window here" <br>
<b>Note</b>: You may have to run cmd as an admin, in which case launch cmd as admin and then cd into your Redis directory.
</li>
<li>
Type <b>without</b> quotes: "redis-server"
</li>
<li>
Go to KanjiWebEasy/venv/scripts or KanjiWebEasy/venv/bin
</li>
<li>
Once in the folder, Shift+Right click and select "Open command window here"
</li>
<li>
Type <b>without</b> quotes: "activate.bat"
</li>
<li>
Type <b>without</b> quotes: "cd ../.."
</li>
<li>
Type <b>without</b> quotes: "set PYTHONPATH=."
</li>
<li>
Type <b>without</b> quotes: "python -m japandb"
</li>
<li>
Open up your browser of choice and go to http://localhost:5000/
</li>
</ol>

Push a Change
============
<ol>
<li>
Open up Github for Windows
</li>
<li>
Select the KanjiWebEasy repository from the list
</li>
<li>
Sync any changes that may have happened (the sync button is at the top right)
</li>
<li>
View the list of uncommitted changed (it doesn't appear if you haven't made any changes)
</li>
<li>
Check which files you want to commit (note, you don't have to pull all your changes in the same commit. You can split them up)
</li>
<li>
Enter a Summary/Description of the changes and press "Commit to master"
</li>
<li>
Once all your changes have been made, press Sync again
</li>
</ol>

<b>Note</b>: Your changes will not appear on the live site even after you push a change.

Setup for Linux (Tested on Linux Mint)
============

<ol>
<li>
Make sure you have the latest packages "sudo apt-get update"
</li>
<li>
Install all the packages we will need "sudo apt-get install git redis-server python3.4 python3.4-dev python3-pip python-virtualenv"
</li>
<li>
Clone the repository wherever you want the project "git clone https://github.com/SebastienGllmt/KanjiWebEasy.git" (this step takes a long time)
</li>
<li>
Navigate into the KanjiWebEasy directory you just cloned "cd KanjiWebEasy"
</li>
<li>
Setup the virtual environment "virtualenv venv"
</li>
<li>
Install the project requirements "sudo pip3 install -r requirements.txt"
</li>
</ol>
<div>
If you prefer a one line install use this. It will clone the project and set everything up in the current directory. <br>
sudo apt-get update; sudo apt-get install git redis-server python3.4 python3.4-dev python3-pip python-virtualenv; git clone https://github.com/SebastienGllmt/KanjiWebEasy.git; cd KanjiWebEasy; virtualenv venv; sudo pip3 install -r requirements.txt
</div>

Launching for Linux (Tested on Linux Mint)
============
<ol>
<li>
Run "redis-server"
</li>
<li>
Navigate to the KanjiWebEasy folder "source venv/bin/activate"
</li>
<li>
Run "python3.4 -m japandb" in the KanjiWebEasy folder
</li>
<li>
Open up your browser of choice and go to http://localhost:5000/
</li>
</ol>
