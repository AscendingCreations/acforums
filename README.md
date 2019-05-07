# acforum

For ascending creations forum software.

add psycopg2-binary to the requirements or install it to get  Full sql support.

# Get Started
1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`
If you're on Python 3.6 or less skip step 4.
4. `pip install -U https://github.com/celery/celery/archive/master.zip`
5. `python3 acforum setup`
If you do not want to seed user data skip step 6.
6. `python3 acforum setup_mass`
This will run a local Copy of the forums.
7. `python3 acforum run` 
Go into the forums via : http://127.0.0.1:5000 and register an account then copy
and past the activation URL From the command line into the browser to Activate your first account.
Login with the first account to make sure it is activated then go into the command and press
ctrl+c to stop the local website.
Run the Following Command
8. ` python3 acforum user groups add` 
Then Enter in the Email you used for the Admin account and then enter in 
'administrators' to add it to the Group.
9. 'go into config.py and modify the OWNER = 'genusis' to be 
your login name.'
This will prevent the account from getting banned by someone you could have 
granted permissions too and makes it so they can not remove permissions
from you as well.


# Contributors
Alex Lopez  			Theme Design
Andrew Wheeler  		Forum Software Creator
Stephan Van Schaiks  	Authz Creator and Base python project creator
Thank you Testers! 