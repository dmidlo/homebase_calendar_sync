"""
google/auth.py

This module provides classes and functions for authenticating with Google APIs, including Google
Drive, Slide, and Session APIs.

Classes:
    AuthGoogle -- A class for managing Google authentication credentials and services.

Methods:
    AuthGoogle.__init__ -- Initializes the AuthGoogle class by setting the necessary attributes and
            calling the credentials fetching methods.
    AuthGoogle.refresh_google_auth_creds -- Refreshes Google authentication credentials.
    AuthGoogle.initiate_google_oauth_flow -- Initiates a Google OAuth flow for retrieving credentials.
    AuthGoogle.fetch_credentials -- Fetches the credentials for the provided API scopes.
    AuthGoogle.create_slides_service -- Creates and returns a Google Slides service object.
    AuthGoogle.create_drive_service -- Creates and returns a Google Drive service object.
    AuthGoogle.create_google_authorized_session -- Creates and returns a Google authorized session object.

Attributes:
    AuthGoogle.creds -- The Google authentication credentials.
    AuthGoogle.slides_service -- The Google Slides service object.
    AuthGoogle.drive_service -- The Google Drive service object.
    AuthGoogle.google_authorized_session -- The authorized Google session object.

"""

import json
import string
import random
import os
import pickle
import base64
from pathlib import Path
from io import BytesIO
from dataclasses import dataclass, field

import yaml
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.transport.requests import AuthorizedSession
from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import Resource
from googleapiclient.discovery import build

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from InquirerPy import inquirer
from InquirerPy.validator import PathValidator

from .. import config

class AuthGoogle:
    """
    A class for managing Google authentication credentials and services.

    Args:
        api_scopes (list[str]): A list of API scopes to authorize.

    Attributes:
        creds (Credentials): The Google authentication credentials.
        slides_service (Resource): The Google Slides service object.
        drive_service (Resource): The Google Drive service object.
        google_authorized_session (AuthorizedSession): The authorized Google session object.

    Methods:
        __call__() -> None: Raises NotImplementedError.
        refresh_google_auth_creds() -> Union[Credentials, None]: Refreshes Google authentication credentials.
        initiate_google_oauth_flow(api_scopes: list[str]) -> Credentials: Initiates a Google OAuth flow for retrieving credentials.
        fetch_credentials(api_scopes: list[str]) -> None: Fetches the credentials for the provided API scopes.
        create_slides_service() -> build: Creates and returns a Google Slides service object.
        create_drive_service() -> build: Creates and returns a Google Drive service object.
        create_google_authorized_session() -> AuthorizedSession: Creates and returns an authorized Google session object.
    """

    def __init__(self, api_scopes: list[str]) -> None:
        """Initializes an AuthGoogle instance with the provided API scopes.

        Args:
            api_scopes (list[str]): A list of API scopes required for authentication.

        Returns:
            None

        Raises:
            None

        This method initializes an instance of AuthGoogle with the provided API scopes. It fetches the
        Google authentication credentials, creates Google Slides and Drive services, and creates an
        authorized session for accessing Google APIs. These properties are stored as instance variables.
        """
        self.fetch_credentials(api_scopes)
        self.creds = Credentials.from_authorized_user_info(
            config.META.google_client_token
        )

        self.slides_service: Resource = self.create_slides_service()
        self.drive_service: Resource = self.create_drive_service()
        self.calendar_service: Resource = self.create_calendar_service()
        self.google_authorized_session: AuthorizedSession = (
            self.create_google_authorized_session()
        )

    @property
    def creds(self):
        """Getter method for accessing the credentials of the object.

        Returns:
            Any: The credentials associated with the object.
        """
        return self._creds

    @creds.setter
    def creds(self, creds):
        """Setter method for 'creds' attribute.

        Args:
            creds (Any): The new value to set for the 'creds' attribute.

        Raises:
            TypeError: If 'creds' is not of the expected data type.
        """
        self._creds = creds

    @creds.deleter
    def creds(self):
        """Deleter method for 'creds' attribute.

        Raises:
            AttributeError: If 'creds' attribute is not present.
        """
        del self._creds

    @property
    def slides_service(self):
        """Getter method for 'slides_service' attribute.

        Returns:
            googleapiclient.discovery.Resource: The slides service object.

        """
        return self._slides_service

    @slides_service.setter
    def slides_service(self, slides_service):
        """Setter method for 'slides_service' attribute.

        Args:
            slides_service (googleapiclient.discovery.Resource): The slides service object.

        """
        self._slides_service = slides_service

    @slides_service.deleter
    def slides_service(self):
        """Deleter method for 'slides_service' attribute.

        Deletes the slides service object associated with this instance.
        """
        del self._slides_service

    @property
    def drive_service(self):
        """Getter method for 'drive_service' attribute.

        Returns the Google Drive service object associated with this instance.

        Returns:
            The Google Drive service object associated with this instance.
        """
        return self._drive_service

    @drive_service.setter
    def drive_service(self, drive_service):
        """Setter method for 'drive_service' attribute.

        Sets the Google Drive service object associated with this instance.

        Args:
            drive_service (googleapiclient.discovery.Resource): The Google Drive service
                object to be associated with this instance.
        """
        self._drive_service = drive_service

    @drive_service.deleter
    def drive_service(self):
        """Deleter method for 'drive_service' attribute.

        Deletes the Google Drive service object associated with this instance.
        """
        del self._drive_service

    @property
    def google_authorized_session(self):
        """Get the authorized Google session.

        Returns:
            AuthorizedSession: The authorized Google session object associated with this instance.
        """
        return self._google_authorized_session

    @google_authorized_session.setter
    def google_authorized_session(self, google_authorized_session):
        """Set the authorized Google session.

        Args:
            google_authorized_session (AuthorizedSession):
                    The authorized Google session object to set.
        """
        self._google_authorized_session = google_authorized_session

    @google_authorized_session.deleter
    def google_authorized_session(self):
        """Delete the authorized Google session.

        Deletes the authorized Google session associated with the instance, effectively revoking the
        authorization.
        """
        del self._google_authorized_session

    @staticmethod
    def refresh_google_auth_creds() -> dict | None:
        """
        Refreshes the Google authorization credentials by obtaining a new access token using the
        refresh token, if the provided credentials are expired and a refresh token is available.

        Returns:
            Credentials | None: The refreshed authorization credentials as a dict object,
            or None if `config.META.google_client_token` is None, or if the provided credentials are
            already valid and not expired, or if a refresh token is not available.
        """
        # Using short-circuiting
        if config.META.google_client_token:
            creds = Credentials.from_authorized_user_info(
                config.META.google_client_token
            )

            if creds and not creds.valid and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            return json.loads(Credentials.to_json(creds))
        return None

    @staticmethod
    def initiate_google_oauth_flow(api_scopes: list[str]) -> dict:
        """
        Initiates the Google OAuth flow to obtain authorization credentials for a user.

        This method initiates the Google OAuth flow to obtain authorization credentials. If the
        provided credentials (`config.META.google_client_token`) are not available or invalid, the
        flow is started using the client secrets file (`config.META.google_client_secret`) and the
        requested API scopes (`api_scopes`). The user is prompted to authenticate and authorize the
        application using a local server flow with a dynamically allocated port. Once the user
        completes the authorization flow, the obtained credentials are returned.

        Args:
            api_scopes (list[str]): A list of API scopes required for the authorization.

        Returns:
            dict: The obtained authorization credentials info as a dict object.

        Raises:
            ValueError: If `config.META.google_client_token` is already set.

        Note:
            The client configuration should be set in `config.META.google_client_secret` before calling this method.
            The client secrets file can be downloaded from the Google Cloud Console at:
            https://console.cloud.google.com/apis/credentials?project=YOUR_PROJECT
        """
        if not config.META.google_client_token:
            try:
                flow: "InstalledAppFlow" = InstalledAppFlow.from_client_config(
                    config.META.google_client_secret, api_scopes
                )
                return json.loads(Credentials.to_json(flow.run_local_server(port=0)))
            except ValueError as e:
                if "client secrets" in str(e).lower():
                    print(
                        "No Google Auth Credentials found. \n download a new client_secrets.json file from: https://console.cloud.google.com/apis/credentials"
                    )
                    raise SystemExit

        return config.META.google_client_token

    def fetch_credentials(self, api_scopes) -> None:
        """
        Fetches Google OAuth2 credentials and stores them in the `config.META.google_client_token`
        configuration variable. This method first attempts to refresh the existing credentials using
        the `refresh_google_auth_creds` static method. If the credentials are not valid or are not
        available, the `initiate_google_oauth_flow` method is called to start a new OAuth flow to
        obtain authorization credentials. Once the credentials are obtained, they are stored in
        `config.META.google_client_token`.

        Args:
            api_scopes (list[str]): A list of API scopes required for the authorization.
        """
        config.META(google_client_token=self.refresh_google_auth_creds())
        config.META(google_client_token=self.initiate_google_oauth_flow(api_scopes))
        config.META(google_client_token=self.refresh_google_auth_creds())

    def create_slides_service(self) -> build:
        """Create and return an instance of Google Slides service.

        Creates and returns an instance of the Google Slides service (`build`) from the
        `google-auth` and `google-api-python-client` libraries, using the `slides` API version 1,
        and the stored credentials (`self.creds`) for authentication.

        Returns:
            build: An instance of the Google Slides service (`build`) for making API requests.
        """
        return build("slides", "v1", credentials=self.creds)

    def create_drive_service(self) -> build:
        """Create and return an instance of Google Drive service.

        Creates and returns an instance of the Google Drive service (`build`) from the
        `google-auth` and `google-api-python-client` libraries, using the `drive` API version 3,
        and the stored credentials (`self.creds`) for authentication.

        Returns:
            build: An instance of the Google Drive service (`build`) for making API requests.
        """
        return build("drive", "v3", credentials=self.creds)

    def create_calendar_service(self) -> build:
        """Create and return an instance of Google Calendar service.

        Creates and returns an instance of the Google Calendar service (`build`) from the
        `google-auth` and `google-api-python-client` libraries, using the `drive` API version 3,
        and the stored credentials (`self.creds`) for authentication.

        Returns:
            build: An instance of the Google Calendar service (`build`) for making API requests.
        """
        return build("calendar", "v3", credentials=self.creds)

    def create_google_authorized_session(self) -> AuthorizedSession:
        """Create and return an authorized session using Google credentials.

        Creates and returns an instance of the `AuthorizedSession` class from the `google-auth`
        library, using the stored credentials (`self.creds`) for authorization.

        Returns:
            AuthorizedSession: An authorized session with Google services.
        """
        return AuthorizedSession(self.creds)

def get_artifacts_path():
    settings_path = Path.cwd() / config.META_SETTINGS_FILE
    metadata_path = Path.cwd() / config.META_DATA_FILE

    if settings_path.exists() and metadata_path.exists():
        return settings_path, metadata_path

    return Path.home() / config.META_SETTINGS_FILE, Path.home() / config.META_DATA_FILE

@dataclass
class Metadata:
    _instance = None
    app_settings_path, app_metadata_path = get_artifacts_path()
    google_client_secret: dict = field(default_factory=dict)
    google_client_token: Credentials | None = None

    def __call__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.write()

    def __new__(cls):
        if cls.app_settings_path.exists() and cls.app_metadata_path.exists():
            return super().__new__(cls)

        cls.generate_settings(cls.app_settings_path)
        return super().__new__(cls)

    @classmethod
    def metadata_singleton_factory(cls):
        if not cls._instance:
            if cls.app_settings_path.exists() and cls.app_metadata_path.exists():
                cls._instance = Metadata.read(
                    cls.app_metadata_path,
                    Metadata.get_project_meta(cls.app_settings_path),
                )
            else:
                cls._instance = Metadata()
        return cls._instance

    @staticmethod
    def generate_settings(settings_path: Path):
        settings = Metadata.generate_yaml_dict()
        Metadata.write_settings(settings_path, settings)

    @staticmethod
    def generate_client_id():
        return "".join(
            random.choice(string.ascii_letters + string.digits + string.punctuation)
            for _ in range(1028)
        )

    @staticmethod
    def generate_project_id():
        return os.urandom(16)

    @staticmethod
    def generate_yaml_dict():
        yaml_dump = {
            "client_id": base64.urlsafe_b64encode(
                Metadata.generate_client_id().encode("ascii")
            ),
            "project_id": Metadata.generate_project_id(),
        }
        yaml_dump["project_meta"] = Metadata.generate_derived_key(
            yaml_dump["client_id"], yaml_dump["project_id"]
        )

        return yaml_dump

    @staticmethod
    def generate_derived_key(client_id, project_id):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=project_id, iterations=100000
        )

        return base64.urlsafe_b64encode(kdf.derive(client_id))

    @staticmethod
    def write_settings(settings_path: Path, settings: dict):
        try:
            home_dir = Path.home()
            if not home_dir.exists():
                raise ValueError("Home directory does not exist")
        except (KeyError, ValueError):
            settings_path = Path.cwd() / settings_path.name

        if not settings_path.exists():
            settings_path.touch()

        with settings_path.open("w") as file:
            file.write(yaml.safe_dump(settings))

    @staticmethod
    def get_client_id(settings_path: Path):
        with settings_path.open("r") as file:
            settings = yaml.safe_load(file)
        return settings["client_id"]

    @staticmethod
    def get_project_id(settings_path: Path):
        with settings_path.open("r") as file:
            settings = yaml.safe_load(file)
        return settings["project_id"]

    @staticmethod
    def get_project_meta(meta_path: Path):
        if meta_path.exists():
            with meta_path.open("r") as file:
                settings = yaml.safe_load(file)
            return settings["project_meta"]

    @classmethod
    def read(cls, metadata_path: Path, project_meta):
        if metadata_path.exists():
            with metadata_path.open("rb") as file:
                data = file.read()
                decoder = Fernet(project_meta)
                decoded_data = BytesIO(decoder.decrypt(data))
                return pickle.load(decoded_data)
        return cls

    def write(self):
        dump = BytesIO()
        pickle.dump(self, dump)
        encoder = Fernet(Metadata.get_project_meta(self.app_settings_path))
        encoded_dump = encoder.encrypt(dump.getvalue())

        data = BytesIO(encoded_dump)

        if not self.app_metadata_path.exists():
            self.app_metadata_path.touch()

        with self.app_metadata_path.open("wb") as file:
            file.write(data.getvalue())

    def import_google_client_secret_json(self, file_path: str):
        path = Path(file_path)

        with Path.open(path, "r") as file:
            data = json.load(file)

        self(google_client_secret=data)

    def check_for_client_secret_and_import(self):
        try:
            secrets_json = next(Path.cwd().glob("client_secret*.json"))
        except StopIteration:
            secrets_json = None

        if secrets_json:
            self.import_google_client_secret_json(secrets_json)
            secrets_json.unlink()

def import_client_secret(client_secret: bool | str) -> None:
    config.META = Metadata.metadata_singleton_factory()
    try:
        default_path = str(next(Path.cwd().glob("client_secret*.json")))
    except StopIteration:
        default_path = str(Path(".").resolve())

    if isinstance(client_secret, bool):
        client_secret_path = inquirer.filepath(
            message="path to 'client_secret.json:'",
            default=default_path,
            validate=PathValidator(is_file=True, message="input is not a file"),
            only_files=True,
        ).execute()
    else:
        client_secret_path = client_secret

    config.META.import_google_client_secret_json(client_secret_path)
    Path(client_secret_path).unlink()
    config.META(
        google_client_token=AuthGoogle.initiate_google_oauth_flow(config.API_SCOPES)
    )

    print("Imported client_secrets.json file.")
    print(f"...deleted authentication artifacts: {client_secret_path}")
    raise SystemExit

def reset_auth_cache() -> None:
    app_settings_path, app_metadata_path = get_artifacts_path()

    try:
        app_metadata_path.unlink()
        app_settings_path.unlink()
    except FileNotFoundError:
        print("no auth cache to reset.")
