To run in steps, repeat:

../../babysitter.py -w local binarysearch*.xml

To run all at once:

../../babysitter.py -w local binarysearch*.xml -p

To run at CERN, repeat:

../../babysitter.py -w cern *.xml

To automatically resubmit at CERN:

../../babysitter.py -w cern *.xml -p

To update every 2 minutes at CERN:

acrontab < ./cronjob

(Check crontabs with 'acrontab -l'. Remove crontabs with 'acrontab -r'.)

To clean:

rm *.log *00?.xml .binarysearch* work/*
