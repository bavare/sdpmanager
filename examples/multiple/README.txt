To create all the files:

python3 ./jobscreator.py

To run all at the same time (not recommended):

../../babysitter.py -w local *.xml

To run in sequence:

../../babysitter.py -w local *.xml -p

To run at CERN:

../../babysitter.py -w cern *.xml

To clean:

rm *_[0-9].* work/* .multiple_*
