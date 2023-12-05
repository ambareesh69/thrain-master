import os
import os.path
from flask import Flask, request, redirect, url_for, render_template, session, send_from_directory, send_file
from db_operations import create_connection, create_user, get_user_by_username
from werkzeug.utils import secure_filename
import DH
import pickle
import random

import io
from io import BytesIO
from google.cloud import storage


storage_client = storage.Client.from_service_account_json('src/gcp/long-perception-395509-5e8bb71a616e.json')
bucket = storage_client.get_bucket('sttpbucket')

# Function to upload file to GCS
def upload_to_gcs(local_file_path, bucket_name, gcs_file_name):
	storage_client = storage.Client.from_service_account_json('src/gcp/long-perception-395509-5e8bb71a616e.json')
	bucket = storage_client.get_bucket(bucket_name)
	blob = bucket.blob(gcs_file_name)
	blob.upload_from_filename(local_file_path)

	print('File {} uploaded to {}'.format(gcs_file_name, bucket_name))

BASE = '/Users/ambareesh7/Downloads/'
UPLOAD_FOLDER = BASE + '/thrain-master/src/web-application/media/text-files/'
UPLOAD_KEY = BASE + '/thrain-master/src/web-application/media/public-keys/'
UPLOAD_DATABASE = BASE + '/thrain-master/src/web-application/media/database/'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_empty_pickle(file_path):
    # Create an empty list and save it to a pickle file
    with open(file_path, 'wb') as file:
        pickle.dump([], file)

def check_and_create_pickles():
    # Check if database pickles exist, if not, create them with initial empty lists
    if not os.path.isfile(UPLOAD_DATABASE + "database.pickle"):
        create_empty_pickle(UPLOAD_DATABASE + "database.pickle")

    if not os.path.isfile(UPLOAD_DATABASE + "database_1.pickle"):
        create_empty_pickle(UPLOAD_DATABASE + "database_1.pickle")

check_and_create_pickles()

'''
-----------------------------------------------------------
					PAGE REDIRECTS
-----------------------------------------------------------
'''
def post_upload_redirect():
	return render_template('post-upload.html')

@app.route('/register')
def call_page_register_user():
	return render_template('register.html')

@app.route('/home')
def back_home():
	return render_template('index.html')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/upload-file')
def call_page_upload():
	return render_template('upload.html')
'''
-----------------------------------------------------------
				DOWNLOAD KEY-FILE
-----------------------------------------------------------
'''
@app.route('/public-key-directory/retrieve/key/<username>')
def download_public_key(username):
    public_keys_dir = BASE + '/thrain-master/src/web-application/media/public-keys/'
    
    for root, dirs, files in os.walk(public_keys_dir):
        for file in files:
            list_parts = file.split('-')
            if list_parts[0] == username:
                filename = os.path.join(public_keys_dir, file)
                return send_file(filename, attachment_filename='publicKey.pem', as_attachment=True)
    
    return render_template('public-key-list.html', msg='No public key found for this user')


@app.route('/file-directory/retrieve/file/<filename>')
def download_file(filename):
	filepath = UPLOAD_FOLDER+filename
	if(os.path.isfile(filepath)):
		return send_file(filepath, attachment_filename='EncryptedFile.txt',as_attachment=True)
	else:
		return render_template('file-list.html',msg='An issue encountered, our team is working on that')

'''
-----------------------------------------------------------
		BUILD - DISPLAY FILE - KEY DIRECTORY
-----------------------------------------------------------
'''
# Build public key directory
@app.route('/public-key-directory/')
def downloads_pk():
	username = []
	if(os.path.isfile(UPLOAD_DATABASE + "database_1.pickle")):
		pickleObj = open((UPLOAD_DATABASE + "database_1.pickle"),"rb")
		username = pickle.load(pickleObj)
		pickleObj.close()
	if len(username) == 0:
		return render_template('public-key-list.html',msg='Aww snap! No public key found in the database')
	else:
		return render_template('public-key-list.html',msg='',itr = 0, length = len(username),directory=username)

# Build file directory
@app.route('/file-directory/')
def download_f():
	for root,dirs,files in os.walk(UPLOAD_FOLDER):
		if(len(files) == 0):
			return render_template('file-list.html',msg='Aww snap! No file found in directory')
		else:
			return render_template('file-list.html',msg='',itr=0,length=len(files),list=files)

'''
-----------------------------------------------------------
				UPLOAD ENCRYPTED FILE
-----------------------------------------------------------
'''

@app.route('/data', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return 'NO FILE SELECTED'

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Upload the file to Google Cloud Storage
        upload_to_gcs(file_path, 'sttpbucket', filename)
        return post_upload_redirect()

    return 'Invalid File Format!'


'''
-----------------------------------------------------------
REGISTER UNIQUE USERNAME AND GENERATE PUBLIC KEY WITH FILE
-----------------------------------------------------------
'''
@app.route('/register-new-user', methods=['GET', 'POST'])
def register_user():
	global pubkey, privkey
	files = []
	privatekeylist = []
	usernamelist = []

    # Import pickle file to maintain uniqueness of the keys

	if os.path.isfile(UPLOAD_DATABASE + "database.pickle"):
		pickleObj = open(UPLOAD_DATABASE + "database.pickle", "rb")
		privatekeylist = pickle.load(pickleObj)
		pickleObj.close()
	if os.path.isfile(UPLOAD_DATABASE + "database_1.pickle"):
		pickleObj = open(UPLOAD_DATABASE + "database_1.pickle", "rb")
		usernamelist = pickle.load(pickleObj)
		pickleObj.close()
	# Declare a new list that consists of all usernames
	if request.form['username'] in usernamelist:
		return render_template('register.html', name='Username already exists')
	username = request.form['username']
	first_name = request.form['first-name']
	last_name = request.form['last-name']
	pin = int(random.randint(1, 128))
	pin = pin % 64
	# Generating a unique private key
	privatekey = DH.generate_private_key(pin)
	while privatekey in privatekeylist:
		privatekey = DH.generate_private_key(pin)
	privatekeylist.append(str(privatekey))
	usernamelist.append(username)
	# Save/update pickle
	pickleObj = open(UPLOAD_DATABASE + "database.pickle", "wb")
	pickle.dump(privatekeylist, pickleObj)
	pickleObj.close()
	pickleObj = open(UPLOAD_DATABASE + "database_1.pickle", "wb")
	pickle.dump(usernamelist, pickleObj)
	pickleObj.close()
	# Generating a new public key for a new user
	publickey = DH.generate_public_key(privatekey)
	# Save public key to file
	filename = UPLOAD_KEY + username + '-' + last_name.upper() + first_name.lower() + '-PublicKey.pem'
	with open(filename, "w") as fileObject:
		fileObject.write(str(publickey))
	# Store user information in the database
	conn = create_connection()
	user_info = (username, first_name, last_name, str(publickey), str(privatekey))
	create_user(conn, user_info)
	conn.close()

	return render_template('key-display.html', public_key=str(publickey), private_key=str(privatekey))




if __name__ == '__main__':
	app.run(host="0.0.0.0", port=80)
