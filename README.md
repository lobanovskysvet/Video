# **General information**
This script is  intended to solve the task of automated video conversion, which is stored on the remote Drive.
To accomplish this task, the following logical blocks were implemented: read arguments from the CMD, multithreaded upload/download of the corresponding files to a temporary folder, multithreaded video conversion, that applies particular logo image on as a watermark for first 10 seconds.
# **Required libs**
The following libraries will be installed :
  * moviePy
  * google-api-python-client
# **Managed installation**
Use pip  to manage your installation
# **Quickstart**
  To run quickstart, you'll need:
  * Python 3.6 or greater.
  * The pip package management tool.
  * A Google account with Google Drive enabled.

### **Step 1: Install the Google Client Library**
   Run the following command to install the library using pip:
     
   *pip install --upgrade google-api-python-client*
   
### **Step 2: Install the MoviePy Library**
   Run the following command to install the library using pip:
   
   *pip install moviepy*
 
### **Step 3: Turn on the Drive API**
  1. Use this wizard to create or select a project in the Google Developers Console and automatically turn on the API. Click Continue, then Go to credentials.
  2. On the Add credentials to your project page, click the Cancel button.
  3. At the top of the page, select the OAuth consent screen tab. Select an Email address, enter a Product name if not already set, and click the Save button.
  4. Select the Credentials tab, click the Create credentials button and select OAuth client ID.
  5. Select the application type Other, enter the name "Drive API Quickstart", and click the Create button.
  6. Click OK to dismiss the resulting dialog.
  7. Click the file_download (Download JSON) button to the right of the client ID.
  8. Move this file to your working directory and rename it client_secret.json.
      
# **Supported formats**
   
  video: ***.mp4/.avi***
  
  image: ***.jpg/.png***

# **Args for startup**
***BoseLogo.png*** ***ResultFolder*** ***F:/temp/*** ***assets*** ***input***
 1. ***BoseLogo.png***: name with extension that exists on the remote Drive
 2. ***ResultFolder***: name of the folder on the remote Drive that would be used as a destination folder
 3.  ***F:/temp/***  : full path to local storage that would be used for temporary file storing
 4. ***assets*** ***input***: name of the folder (can be specified any amount)on the remote Drive that would be used as a source folder
