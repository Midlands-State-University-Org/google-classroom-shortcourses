from django.shortcuts import render, redirect
from google_auth_oauthlib.flow import Flow
from django.http import HttpResponseRedirect
from django.conf import settings
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
import os
import json
from django.utils.timezone import now
from .models import Course
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def home(request):
    return render(request, 'home.html')

def google_classroom_login(request):
    credentials_path = os.path.join(settings.BASE_DIR, 'credentials.json')

    # Ensure the credentials file is a dictionary
    with open(credentials_path, 'r') as file:
        credentials_data = json.load(file)

    SCOPES = [
        'https://www.googleapis.com/auth/classroom.courses',
        'https://www.googleapis.com/auth/classroom.coursework.me',
        'https://www.googleapis.com/auth/classroom.rosters',
        'https://www.googleapis.com/auth/classroom.profile.emails',
    ]

    # Use the parsed credentials dictionary to initialize the Flow object
    flow = Flow.from_client_config(
        credentials_data,  # Pass the dictionary, not the file path
        scopes=SCOPES,
        redirect_uri='http://localhost:8000/oauth2callback'
    )

    # Get the authorization URL
    authorization_url, _ = flow.authorization_url(prompt='consent')

    # Redirect the user to the Google OAuth2 login page
    return HttpResponseRedirect(authorization_url)




def oauth2callback(request):
    # Define the path to the credentials.json file
    credentials_path = os.path.join(settings.BASE_DIR, 'credentials.json')

    # Define the required Google OAuth2 scopes
    SCOPES = [
        'https://www.googleapis.com/auth/classroom.courses',
        'https://www.googleapis.com/auth/classroom.coursework.me',
        'https://www.googleapis.com/auth/classroom.rosters',
        'https://www.googleapis.com/auth/classroom.profile.emails',
    ]

    # Initialize the OAuth2 flow
    flow = Flow.from_client_secrets_file(
        credentials_path,
        scopes=SCOPES,
        redirect_uri='http://localhost:8000/oauth2callback'
    )

    # Fetch the token using the authorization response
    authorization_response = request.build_absolute_uri()  # Get the full URL of the request
     
    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as e:
        # Handle token fetching errors
        error_message = str(e)  # Extract the error message
        return HttpResponseRedirect(f'/error-page/?error_message={error_message}')

    # Extract credentials from the flow
    credentials = flow.credentials

    # Save credentials in the session as JSON
    request.session['google_credentials'] = credentials.to_json()

    # Redirect to the dashboard
    return HttpResponseRedirect('/dashboard/')





def create_class_view(request, name, section, room):
    credentials = Credentials.from_authorized_user_info(
        request.session.get('google_credentials')
    )
    service = build('classroom', 'v1', credentials=credentials)
    course = {
        'name': name,
        'section': section,
        'room': room,
        'ownerId': 'me',  # Uses the authenticated user's account
    }
    service.courses().create(body=course).execute()
    
    
# def list_classes(request):
#     credentials = Credentials.from_authorized_user_info(
#         request.session.get('google_credentials')
#     )
#     service = build('classroom', 'v1', credentials=credentials)
#     results = service.courses().list().execute()
#     return results.get('courses', [])


# def dashboard(request):
#     classes = list_classes(request)
#     return render(request, 'dashboard.html', {'classes': classes})



def list_classes(credentials):
    """
    Fetches a list of classes from the Google Classroom API.
    """
    try:
        service = build('classroom', 'v1', credentials=credentials)
        results = service.courses().list().execute()
        return results.get('courses', [])
    except Exception as e:
        # Log the error and return an empty list or handle it appropriately
        print(f"Error fetching classes: {e}")
        return []



def dashboard(request):
    # Retrieve and deserialize credentials from the session
    credentials_json = request.session.get('google_credentials')

    # Ensure credentials are valid and properly formatted
    if not credentials_json:
        return HttpResponseRedirect('/login/')  # Redirect to login if credentials are missing

    try:
        # Parse the JSON string into a dictionary
        credentials_info = json.loads(credentials_json)
    except json.JSONDecodeError:
        return HttpResponseRedirect('/error-page/?error_message=Invalid credentials format')

    # Create a Credentials object
    try:
        credentials = Credentials.from_authorized_user_info(credentials_info)
    except Exception as e:
        return HttpResponseRedirect(f'/error-page/?error_message=Failed to load credentials: {str(e)}')

    # Use the credentials to interact with the Google Classroom API
    # classes = list_classes(credentials) 
    # Fetch classes from Google Classroom API
    google_classes = list_classes(credentials)

    # Fetch classes with alias 'p' from the Course table
    alias_p_courses = Course.objects.filter(alias='p')

    # Filter the Google Classroom classes to match those in the Course table
    filtered_classes = [
        gc_class for gc_class in google_classes
        if any(gc_class['id'] == course.googleclassroomid for course in alias_p_courses)
    ]
    return render(request, 'dashboard.html', {'classes': filtered_classes})



def error_page(request):
    """
    Renders an error page when token fetching or other OAuth-related issues occur.
    """
    error_message = request.GET.get('error_message', 'An unexpected error occurred.')
    return render(request, 'error_page.html', {'error_message': error_message})



# @login_required
def create_class(request):
    """
    View to render a form for class creation, save details to the database, 
    and create a class in Google Classroom.
    """
    # Handle GET request: Render the form
    if request.method == 'GET':
        return render(request, 'create_class.html')

    # Handle POST request: Process form submission
    elif request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        alias = request.POST.get('alias', 'p')
        

        # Retrieve and deserialize credentials from the session
        credentials_json = request.session.get('google_credentials')
        if not credentials_json:
            return HttpResponseRedirect('/login/')  # Redirect to login if credentials are missing

        try:
            credentials_info = json.loads(credentials_json)
            credentials = Credentials.from_authorized_user_info(credentials_info)
        except Exception as e:
            return HttpResponseRedirect(f'/error-page/?error_message=Failed to load credentials: {str(e)}')

        # Create a class in Google Classroom
        try:
            service = build('classroom', 'v1', credentials=credentials)

            new_class = {
                'name': name,
                'descriptionHeading': description[:100],  # Classroom description header has a limit
                'description': description,
                'ownerId': 'me',  # 'me' refers to the authenticated user
            }

            created_class = service.courses().create(body=new_class).execute()

            # Save class details to the database
            course = Course.objects.create(
                name=name,
                description=description,
                price=price,
                ownerid=created_class['ownerId'],  # Assuming the logged-in user's email is available
                datecreated=now(),
                alias=alias,
                googleclassroomid=created_class['id'],  # Use the ID returned by Google Classroom
            )
            
            # Redirect to the dashboard with a success message and Google Classroom link
            # google_classroom_url = created_class.get('courseGroup', '')
            # return HttpResponseRedirect(f'/dashboard/?message=Class+created+successfully&google_classroom_url={google_classroom_url}')

            # Redirect to the dashboard with a success message
            return HttpResponseRedirect('/dashboard/?message=Class+created+successfully')

        except HttpError as e:
            print(f"Google API Error: {e}")
            return HttpResponseRedirect(f'/error-page/?error_message=Failed+to+create+class:+{e}')
        except Exception as e:
            print(f"Unexpected error: {e}")
            return HttpResponseRedirect(f'/error-page/?error_message=An+unexpected+error+occurred:+{e}')



# def create_class(request):
#     """
#     View to render a form for class creation, save details to the database, 
#     and create a class in Google Classroom with alias.
#     """
#     # Handle GET request: Render the form
#     if request.method == 'GET':
#         return render(request, 'create_class.html')

#     # Handle POST request: Process form submission
#     elif request.method == 'POST':
#         # Get form data
#         name = request.POST.get('name')
#         description = request.POST.get('description')
#         price = request.POST.get('price')
#         alias = request.POST.get('alias', 'p')

#         # Retrieve and deserialize credentials from the session
#         credentials_json = request.session.get('google_credentials')
#         if not credentials_json:
#             return HttpResponseRedirect('/login/')  # Redirect to login if credentials are missing

#         try:
#             credentials_info = json.loads(credentials_json)
#             credentials = Credentials.from_authorized_user_info(credentials_info)
#         except Exception as e:
#             return HttpResponseRedirect(f'/error-page/?error_message=Failed to load credentials: {str(e)}')

#         # Create a class in Google Classroom
#         try:
#             service = build('classroom', 'v1', credentials=credentials)

#             # Prepare the new class data
#             new_class = {
#                 'name': name,
#                 'descriptionHeading': description[:100],  # Classroom description header limit
#                 'description': description,
#                 'ownerId': 'me',  # 'me' refers to the authenticated user
#             }

#             # Create the class in Google Classroom
#             created_class = service.courses().create(body=new_class).execute()

#             # Add alias to the created class
#             service.courses().aliases().create(
#                 courseId=created_class['id'], 
#                 body={'alias': f'd:p:{alias}'}
#             ).execute()

#             # Save class details to the database
#             course = Course.objects.create(
#                 name=name,
#                 description=description,
#                 price=price,
#                 ownerid=created_class['ownerId'],# Save the ownerId from Google Classroom API response
#                 alias=alias,
#                 datecreated=now(),
#                 googleclassroomid=created_class['id'],  # Use the ID returned by Google Classroom
#             )

#             # Redirect to dashboard with message and Google Classroom link
#             return HttpResponseRedirect(f'/dashboard/?message=Class+created+successfully')

#         except Exception as e:
#             # Handle any errors
#             return HttpResponseRedirect(f'/error-page/?error_message=Failed+to+create+class:+{str(e)}')




def logout_view(request):
    """
    Logs out the user, clears the session, and removes Google Classroom credentials.
    Redirects to the login page or home page after logout.
    """
    # Clear Google Classroom credentials from the session
    if 'google_credentials' in request.session:
        del request.session['google_credentials']
    
    # Log the user out and clear the Django session
    logout(request)  
    
    # Redirect to the login page or home page
    return redirect('home') 