from __future__ import annotations
import json
import param
import panel as pn
from datafed.CommandLib import API
from file_selector import FileSelector
from google.protobuf.json_format import MessageToJson
import os
import time
from dotenv import load_dotenv # type: ignore
from util import get_file_metadata  # Import the utility function
import threading
import datetime
import glob
# import zipfile  # No longer needed - zipping logic commented out
load_dotenv()
FILE_PATH = os.getenv("FILE_PATH")
globus_key = "/shared-data/globus-endpoint_id.txt"
ep=''
try:
    with open(globus_key, "r") as file:
        # Read the entire file content and strip whitespace
        content = file.read().strip()
        print("Endpoint is:", content, "length:", len(content))
        ep = content
    print(f'os.environ:{ep}')
except FileNotFoundError:
    print(f"Warning: Globus endpoint file not found at {globus_key}")
    ep = ""
pn.extension('material')
pn.extension('jsoneditor')

class DataFedApp(param.Parameterized):
    df_api = param.ClassSelector(class_=API, default=None)

    username = param.String(default="", label="Username")
    password = param.String(default="", label="Password")

    title = param.String(default="", label="Title")
    metadata = param.String(default="", label="Metadata (JSON format)")

    record_id = param.Selector(default=None, objects={}, label="Select Record")
    update_metadata = param.String(default="", label="Update Metadata (JSON format)")
    metadata_changed = param.Boolean(default=False, label="Metadata Changed")
    show_update_button = param.Boolean(default=False, label="Show Update Button")

    source_id = param.String(default="", label="Source ID")
    dest_collection = param.String(default="", label="Destination Collection")

    login_status = param.String(default="", label="Login Status")
    record_output = param.String(default="", label="Record Output")
    projects_output = param.String(default="", label="Projects Output")
    selected_project = param.String(default="", label="Selected Project")

    current_user = param.String(default="Not Logged In", label="Current User")
    current_context = param.String(default="No Context", label="Current Context")
    
    selected_context = param.Selector(default='root', objects={}, label="Select Context")
    available_contexts = param.Dict(default={}, label="Available Contexts")
    selected_collection = param.Selector(objects={}, label="Select Collection")
    available_collections = param.Dict(default={}, label="Available Collections")

    show_login_panel = param.Boolean(default=False)

    record_alert_message = param.String(default="", label="Record Alert Message")  # For alerts

    # New parameters for automated processing
    auto_processing = param.Boolean(default=False, label="Auto Processing")
    processing_status = param.String(default="Idle", label="Processing Status")
    current_file = param.String(default="", label="Current File")
    progress = param.Integer(default=0, label="Progress")
    total_files = param.Integer(default=0, label="Total Files")
    task_id = param.String(default="", label="Current Task ID")
    log_file = param.String(default="backup_log.json", label="Log File Path")

    # New parameters for file tracking
    processed_files_list = param.List(default=[], label="Processed Files")
    unprocessed_files_list = param.List(default=[], label="Unprocessed Files")
    current_processing_file = param.String(default="", label="Currently Processing")

    original_metadata = param.Dict(default={}, label="Original Metadata")  # To track the original metadata
    metadata_json_editor = pn.widgets.JSONEditor(name='Metadata', mode='text', width=600,)

    def __init__(self, **params):
        params['df_api'] = API() 
        super().__init__(**params)
        self.login_button = pn.widgets.Button(name='Login', button_type='primary')
        self.login_button.on_click(self.toggle_login_panel)
        
        self.create_button = pn.widgets.Button(name='Create Record', button_type='primary')
        self.create_button.on_click(self.create_record)
        
        self.read_button = pn.widgets.Button(name='Read Record', button_type='primary')
        self.read_button.on_click(self.read_record)
        
        self.update_button = pn.widgets.Button(name='Update Record', button_type='primary')
        self.update_button.on_click(self.update_record)
        self.update_button.visible = False  # Initially hidden
        
        self.delete_button = pn.widgets.Button(name='Delete Record', button_type='danger')
        self.delete_button.on_click(self.delete_record)
        
        self.transfer_button = pn.widgets.Button(name='Transfer Data', button_type='primary')
        self.transfer_button.on_click(self.transfer_data)
        
        self.projects_button = pn.widgets.Button(name='View Projects', button_type='primary')
        self.projects_button.on_click(self.get_projects)

        self.logout_button = pn.widgets.Button(name='Logout', button_type='warning')
        self.logout_button.on_click(self.logout)

        # New buttons for automated processing
        self.start_auto_button = pn.widgets.Button(name='Start Auto Processing', button_type='success')
        self.start_auto_button.on_click(self.start_auto_processing)
        
        self.stop_auto_button = pn.widgets.Button(name='Stop Auto Processing', button_type='danger')
        self.stop_auto_button.on_click(self.stop_auto_processing)
        self.stop_auto_button.disabled = True

        self.projects_json_pane = pn.pane.JSON(object=None, name='Projects Output', depth=3, width=600, height=400)
        self.metadata_json_editor = pn.widgets.JSONEditor(name='Metadata', width=600)
        self.record_output_pane = pn.pane.Markdown("<h3>Status Empty</h3>", name='Status', width=600)

        self.file_selector = FileSelector(FILE_PATH)
        self.file_selector.param.watch(self.update_metadata_from_file_selector, 'value')
        
        # Initialize file_path with default FILE_PATH
        self.file_path = FILE_PATH
        
        # Create directory selector using the existing FileSelector module
        self.auto_processing_dir_selector = FileSelector(
            directory=FILE_PATH,
            name='Auto Processing Directory',
            width=600,
            height=400
        )
        self.auto_processing_dir_selector.param.watch(self.on_directory_changed, 'directory')
        
        # Create sync button to sync file selector with auto-processing directory
        self.sync_file_selector_button = pn.widgets.Button(
            name='🔗 Sync File Selector',
            button_type='light',
            width=150
        )
        self.sync_file_selector_button.on_click(self.sync_file_selector_with_auto_processing_dir)
        
        # Set a better default directory if the current one doesn't exist
        self._ensure_valid_directory()
        
        # Update the directory selector to show the current directory
        self.update_directory_selector_display()

        self.param.watch(self.update_collections, 'selected_context')
        self.param.watch(self.update_collections, 'selected_collection')

        self.record_output_pane.object = ""

        self.metadata_json_editor.param.watch(self.on_metadata_change, 'value')
        self.param.watch(self.toggle_update_button_visibility, 'metadata_changed')
        self.endpoint_pane = pn.pane.Markdown("<h3>Endpoint Not Connected</h3>", name='Endpoint_Status', width=600)
        pn.state.onload(self.initial_login_check)

        # Progress status
        self.progress_status = pn.pane.Markdown("", width=600)

        # Create panes for file tracking
        self.current_file_pane = pn.pane.Markdown(
            "### Currently Processing\n\nNo file being processed",
            css_classes=['md-text']
        )
        self.processed_files_pane = pn.pane.Markdown(
            "### Processed Files\n\nNo files processed yet",
            css_classes=['md-text']
        )
        self.unprocessed_files_pane = pn.pane.Markdown(
            "### Files to Process\n\nNo files in queue",
            css_classes=['md-text']
        )

    def initial_login_check(self):
        try:
            user_info = self.df_api.getAuthUser()
            if user_info:
                self.current_user = user_info
                self.current_context = self.df_api.getContext()
                ids, titles = self.get_available_contexts()
                self.available_contexts = {title: id_ for id_, title in zip(ids, titles)}
                self.param['selected_context'].objects = self.available_contexts
                self.selected_context = ids[0] if ids else None
                self.record_output_pane.object = "<h3>User in session!</h3>"
                if ep:
                    self.df_api.endpointDefaultSet(ep)
                    print(f"Successfully set up the endpoint with ID: {ep}")
                else:
                    print("No endpoint ID found. Please check the environment variable.")

            else:
                self.current_user = "Not Logged In"
                self.current_context = "No Context"
        except Exception as e:
            self.record_output_pane.object = f"<h3>Error: {e}</h3>"

    def toggle_login_panel(self, event=None):
        self.show_login_panel = not self.show_login_panel  
    def toggle_update_button_visibility(self, event):
        self.update_button.visible = self.metadata_changed


    def check_login(self, event):
        try:
            self.df_api.loginByPassword(self.username, self.password)
            user_info = self.df_api.getAuthUser()
            if hasattr(user_info, 'username'):
                self.current_user = user_info.username
            else:
                self.current_user = str(user_info)
            self.current_context = self.df_api.getContext()
            ids, titles = self.get_available_contexts()
            self.available_contexts = {title: id_ for id_, title in zip(ids, titles)}
            self.param['selected_context'].objects = self.available_contexts
            self.selected_context = ids[0] if ids else None
            self.record_output_pane.object = "<h3>Login Successful!</h3>"
            self.show_login_panel = False
            if ep:
                self.df_api.endpointDefaultSet(ep)
                print(f"Successfully set up the endpoint with ID: {ep}")
            else:
                print("No endpoint ID found. Please check the environment variable.")
            self.update_records()
        except Exception as e:
            self.record_output_pane.object = f"<h3>Invalid username or password: {e}</h3>"
    def logout(self, event):
        self.df_api.logout()
        self.current_user = "Not Logged In"
        self.current_context = "No Context"
        self.record_output_pane.object = "<h3>Logged out successfully!</h3>"
        self.username = ""
        self.password = ""
                    
    def update_collections(self, event):
        context_id = self.selected_context

        if context_id:
            collections = self.get_collections_in_context(context_id)
            self.available_collections = collections
            self.param['selected_collection'].objects = collections  # Update collection options in the Selector
            if self.selected_collection is None:
                self.selected_collection = 'root'  # Default to 'root'
            self.update_records()


    def get_collections_in_context(self, context):
        try:
            self.df_api.setContext(context)
            items_list = self.df_api.collectionItemsList('root', context=context)
            collections = {item.title: item.id for item in items_list[0].item if item.id.startswith("c/")}
            collections['root'] = 'root' 
            return collections
        except Exception as e:
            print(f"Error fetching collections: {e}")
            return {"Error": str(e)}


    def update_metadata_from_file_selector(self, event):
        try:
            selected_file = self.file_selector.value[0] if self.file_selector.value else None
            if selected_file:
                print(f"Selected file: {self.file_selector.value}")
                metadata = get_file_metadata(selected_file) 
                self.metadata_json_editor.value = metadata if metadata else {}
            else:
                self.metadata_json_editor.value = {}
        except json.JSONDecodeError as e:
            self.metadata_json_editor.value = {"error": f"Invalid JSON file: {e}"}
        except Exception as e:
            self.metadata_json_editor.value = {"error": f"Error processing file: {e}"}

    def create_record(self, event):
        if not self.title or not self.metadata_json_editor.value:
            self.record_output_pane.object = "<h3>Error: Title and metadata are required</h3>"
            return
        
        # Check if we have a file selected or if we should use the auto-processing directory
        file_to_upload = None
        if self.file_selector.value and len(self.file_selector.value) > 0:
            file_to_upload = self.file_selector.value[0]
        elif hasattr(self, 'file_path') and self.file_path:
            # If no file is selected but we have an auto-processing directory, 
            # we could create a record with just metadata
            self.record_output_pane.object = "<h3>Warning: No file selected. Creating record with metadata only.</h3>"
            
        try:
            if self.selected_context:
                self.df_api.setContext(self.selected_context)
            response = self.df_api.dataCreate(
                title=self.title,
                metadata=json.dumps(self.metadata_json_editor.value),
                parent_id=self.available_collections[self.selected_collection] 
            )
            record_id = response[0].data[0].id
            
            if file_to_upload:
                try:
                    res = self.df_api.dataPut(
                        data_id=record_id, 
                        wait=False,
                        path=file_to_upload
                    )
                    print(f"res:{res}")
                    self.record_output_pane.object = f"<h3>Success: Record created with ID {record_id} and file uploaded: {res}</h3>"
                except Exception as e:
                    self.record_output_pane.object = f"<h3>Error: Failed to add file to record: {e}</h3>"    
            else:
                self.record_output_pane.object = f"<h3>Success: Record created with ID {record_id} (metadata only)</h3>"
                
            self.update_records()
        except Exception as e:
            self.record_output_pane.object = f"<h3>Error: Failed to create record: {e}</h3>"

    def update_records(self,event=None):
        try:
            selected_collection = self.available_collections.get(self.selected_collection)
            items_list = self.df_api.collectionItemsList(coll_id=self.selected_collection, context=self.selected_context)
            records = {item.title: item.id for item in items_list[0].item if item.id.startswith("d/")}
            self.param['record_id'].objects = records
            if records:
                self.record_id = next(iter(records))
            else:
                self.record_id = None
                self.record_output_pane.object = "<h3>No records found in the selected collection</h3>"
        
        except Exception as e:
            self.record_output_pane.object = f"<h3>Error: Failed to fetch records: {e}</h3>"

    def on_metadata_change(self, event):
        """Callback to handle changes in the JSON editor."""
        self.metadata_changed = True
    def update_metadata_from_file_selector(self, event):
            try:
                selected_file = self.file_selector.value[0] if self.file_selector.value else None
                if selected_file:
                    print(f"Selected file: {self.file_selector.value}")
                    metadata = get_file_metadata(selected_file)  # Get metadata using utility function
                    
                    # If there is metadata, set the mode to 'tree'
                    if metadata:
                        self.metadata_json_editor.mode = 'tree'
                        self.metadata_json_editor.value = metadata
                    else:
                        # If no metadata, set the mode to 'text'
                        self.metadata_json_editor.mode = 'text'
                        self.metadata_json_editor.value = {}
                else:
                    # If no file is selected, set the mode to 'text' and clear the editor
                    self.metadata_json_editor.mode = 'text'
                    self.metadata_json_editor.value = {}
            except json.JSONDecodeError as e:
                self.metadata_json_editor.value = {"error": f"Invalid JSON file: {e}"}
            except Exception as e:
                self.metadata_json_editor.value = {"error": f"Error processing file: {e}"}

    def read_record(self, event):
        if not self.record_id:
            self.record_output_pane.object = "<h3>Warning: Record ID is required</h3>"
            return
        try:            
            if self.selected_context:
                response = self.df_api.dataView(data_id=self.record_id, context=self.selected_context)
                res = MessageToJson(response[0])
                res_json = json.loads(res)

                for record in res_json.get('data', []):
                    if 'metadata' in record:
                        try:
                            record['metadata'] = json.loads(record['metadata'])
                        except json.JSONDecodeError:
                            pass

                self.original_metadata = res_json['data'][0]['metadata']
                self.metadata_json_editor.value = res_json
                self.metadata_changed = False  # Reset the change flag after loading

                self.record_output_pane.object = f"<h3>Record Data</h3>"
        except Exception as e:
            self.record_output_pane.object = f"<h3>Error: Failed to read record: {e}</h3>"

    def update_record(self, event=None):
        if not self.record_id or not self.metadata_json_editor.value:
            self.record_output_pane.object = "<h3>Warning: Record ID and metadata are required</h3>"
            return

        try:
            if self.selected_context and self.metadata_changed:
                self.df_api.setContext(self.selected_context)
                
                # Prepare parameters for the dataUpdate call
                update_params = {
                    'data_id': self.record_id,
                    'metadata': None,
                    'title': None,
                    'alias': None,
                    'description': None,
                    'tags': None,
                    'extension': None,
                    'schema': None,
                    'schema_enforce': None,
                    'deps_add': None,
                    'deps_rem': None,
                    'raw_data_file': None,
                    'context': self.selected_context
                }

                current_metadata = self.metadata_json_editor.value['data'][0]

                # Compare fields and populate update_params with changes
                if current_metadata.get('title') != self.original_metadata.get('title'):
                    update_params['title'] = current_metadata.get('title')

                if current_metadata.get('alias') != self.original_metadata.get('alias'):
                    update_params['alias'] = current_metadata.get('alias')

                if current_metadata.get('description') != self.original_metadata.get('description'):
                    update_params['description'] = current_metadata.get('description')

                if current_metadata.get('tags') != self.original_metadata.get('tags'):
                    update_params['tags'] = current_metadata.get('tags')

                if current_metadata.get('extension') != self.original_metadata.get('extension'):
                    update_params['extension'] = current_metadata.get('extension')

                if current_metadata.get('schema') != self.original_metadata.get('schema'):
                    update_params['schema'] = current_metadata.get('schema')

                if current_metadata.get('schema_enforce') != self.original_metadata.get('schema_enforce'):
                    update_params['schema_enforce'] = current_metadata.get('schema_enforce')

                if current_metadata.get('deps_add') != self.original_metadata.get('deps_add'):
                    update_params['deps_add'] = current_metadata.get('deps_add')

                if current_metadata.get('deps_rem') != self.original_metadata.get('deps_rem'):
                    update_params['deps_rem'] = current_metadata.get('deps_rem')

                if current_metadata.get('raw_data_file') != self.original_metadata.get('raw_data_file'):
                    update_params['raw_data_file'] = current_metadata.get('raw_data_file')

                # Check if metadata has changed
                updated_metadata = self.get_changed_fields(self.original_metadata.get('metadata', {}), current_metadata.get('metadata', {}))
                if updated_metadata:
                    update_params['metadata'] = json.dumps(updated_metadata)

                # Remove parameters that are None (not updated)
                update_params = {k: v for k, v in update_params.items() if v is not None}
                print(f"update_params:{update_params}")
                if update_params:
                    # Call the dataUpdate method with the updated parameters
                    response = self.df_api.dataUpdate(**update_params)
                    self.record_output_pane.object = f"<h3>Success: Record updated with new metadata</h3>"
                    self.metadata_changed = False  # Reset the change flag after updating
                else:
                    self.record_output_pane.object = f"<h3>No changes detected to update</h3>"
        except Exception as e:
            self.record_output_pane.object = f"<h3>Error: Failed to update record: {e}</h3>"

    def get_changed_fields(self, original: dict, current: dict) -> dict:
        """Compare original and current metadata, returning only changed fields."""
        changed_fields = {}
        for key, value in current.items():
            if key not in original or original[key] != value:
                changed_fields[key] = value
        return changed_fields

    def delete_record(self, event):
        if not self.record_id:
            self.record_output_pane.object = "<h3>Warning: Record ID is required</h3>"
            return
        try:
            if self.selected_context:
                self.df_api.setContext(self.selected_context)
            response = self.df_api.dataDelete(f"{self.record_id}")
            self.metadata_json_editor.value = {}  # Clear the JSON editor
            self.original_metadata = {}  # Reset the original metadata tracking
            self.record_output_pane.object = f"<h3>Success: Record :{self.record_id} successfully deleted  </h3>"
            self.update_records()
            self.record_id = None
        except Exception as e:
            self.record_output_pane.object = f"<h3>Error: Failed to delete record: {e}</h3>"

    def transfer_data(self, event):
        if not self.source_id or not self.dest_collection:
            self.record_output_pane.object = "<h3>Warning: Source ID and destination collection are required</h3>"
            return
        try:
            if self.selected_context:
                self.df_api.setContext(self.selected_context)
            source_record = self.df_api.dataView(f"d/{self.source_id}")
            source_details = source_record[0].data[0]
            new_record = self.df_api.dataCreate(
                title=source_details.title,
                metadata=source_details.metadata,
                parent=self.dest_collection
            )
            new_record_id = new_record[0].data[0].id
            self.df_api.dataMove(f"d/{self.source_id}", new_record_id)
            self.record_output_pane.object = f"<h3>Success: Data transferred to new record ID: {new_record_id}</h3>"
        except Exception as e:
            self.record_output_pane.object = f"<h3>Error: Failed to transfer data: {e}</h3>"

    def get_projects(self, event):
        try:
            response = self.df_api.projectList()
            projects = response[0].item
            projects_list = [{"id": project.id, "title": project.title} for project in projects]
            self.projects_json_pane.object = projects_list
        except Exception as e:
            self.projects_json_pane.object = {"error": str(e)}

    def get_available_contexts(self):
        try:
            response = self.df_api.projectList()
            projects = response[0].item
            return [project.id for project in projects], [project.title for project in projects]
        except Exception as e:
            return [f"Error: {e}"]

    def to_dict(self, data_str):
        data_dict = {}
        for line in data_str.strip().split('\n'):
            key, value = line.split(": ", 1)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value == 'true':
                value = True
            elif value == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
        data_dict[key] = value
        return data_dict

    def start_auto_processing(self, event=None):
        """Start automated processing of new data files"""
        if self.auto_processing:
            return
            
        self.auto_processing = True
        self.processing_status = "Starting..."
        self.start_auto_button.disabled = True
        self.stop_auto_button.disabled = False
        
        # Start processing in a separate thread to avoid blocking the UI
        processing_thread = threading.Thread(target=self.process_new_data, daemon=True)
        processing_thread.start()
        
    def stop_auto_processing(self, event=None):
        """Stop automated processing"""
        self.auto_processing = False
        self.processing_status = "Stopping..."
        self.start_auto_button.disabled = False
        self.stop_auto_button.disabled = True
        
    def update_file_tracking_panes(self):
        """Update the file tracking panes with current status"""
        # Update current file pane
        if self.current_processing_file:
            self.current_file_pane.object = f"### Currently Processing\n\n**File:** {os.path.basename(self.current_processing_file)}\n\n**Progress:** {self.progress}%"
        else:
            self.current_file_pane.object = "### Currently Processing\n\nNo file being processed"

        # Update processed files pane
        if self.processed_files_list:
            processed_text = "### Processed Files\n\n"
            for file in self.processed_files_list[-10:]:  # Show last 10 files
                processed_text += f"✅ {os.path.basename(file)}\n"
            self.processed_files_pane.object = processed_text
        else:
            self.processed_files_pane.object = "### Processed Files\n\nNo files processed yet"

        # Update unprocessed files pane
        if self.unprocessed_files_list:
            unprocessed_text = "### Files to Process\n\n"
            for file in self.unprocessed_files_list[:10]:  # Show next 10 files
                unprocessed_text += f"⏳ {os.path.basename(file)}\n"
            self.unprocessed_files_pane.object = unprocessed_text
        else:
            self.unprocessed_files_pane.object = "### Files to Process\n\nNo files in queue"

    def process_single_file(self, dir_path):
        """Process a single file or directory with DataFed operations"""
        try:
            dirname = os.path.basename(dir_path)
            file_title = os.path.splitext(dirname)[0]
            zip_path = None  # Initialize zip_path variable
            
            print(f"Starting to process: {dirname}")
            
            # Check if it's a directory
            if os.path.isdir(dir_path):
                print(f"Directory detected: {dir_path}")
                # ZIP LOGIC COMMENTED OUT - Processing directory directly instead of zipping
                # # Create temp_zips directory if it doesn't exist
                # # Use current auto-processing directory for temp_zips
                # base_dir = self.file_path if hasattr(self, 'file_path') and self.file_path else FILE_PATH
                # temp_zips_dir = os.path.join(base_dir, "temp_zips")
                # try:
                #     if not os.path.exists(temp_zips_dir):
                #         os.makedirs(temp_zips_dir, exist_ok=True)
                #         print(f"Created temp_zips directory: {temp_zips_dir}")
                #     
                #     # Test write permissions
                #     test_file = os.path.join(temp_zips_dir, "test_write.tmp")
                #     try:
                #         with open(test_file, 'w') as f:
                #             f.write("test")
                #         os.remove(test_file)
                #     except (IOError, PermissionError) as e:
                #         error_msg = f"Permission error: Cannot write to temp_zips directory. Please check permissions for: {temp_zips_dir}"
                #         print(error_msg)
                #         self.record_output_pane.object = f"<h3>{error_msg}</h3>"
                #         return False
                #         
                # except PermissionError as e:
                #     error_msg = f"Permission error: Cannot create temp_zips directory. Please check permissions for: {base_dir}"
                #     print(error_msg)
                #         self.record_output_pane.object = f"<h3>{error_msg}</h3>"
                #         return False
                # except Exception as e:
                #     error_msg = f"Error creating temp_zips directory: {str(e)}"
                #         print(error_msg)
                #         self.record_output_pane.object = f"<h3>{error_msg}</h3>"
                #         return False
                # 
                # # Create a zip file of the directory with timestamp
                # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                # zip_filename = f"{file_title}_{timestamp}.zip"
                # zip_path = os.path.join(temp_zips_dir, zip_filename)
                # 
                # try:
                #     print(f"Creating zip file: {zip_path}")
                #     
                #     # First, count total files for progress bar
                #     total_files = 0
                #     for root, dirs, files in os.walk(dir_path):
                #         total_files += len(files)
                #     
                #     self.processing_status = "Zipping directory..."
                #     self.total_files = total_files
                #     self.progress = 0
                #     self.current_processing_file = f"Zipping {dirname}"
                #         self.update_file_tracking_panes()
                #     
                #     processed_files = 0
                #     with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                #         for root, dirs, files in os.walk(dir_path):
                #             for file in files:
                #                 try:
                #                     file_full_path = os.path.join(root, file)
                #                     # Calculate the relative path for the file in the zip
                #                     rel_path = os.path.relpath(file_full_path, dir_path)
                #                     zipf.write(file_full_path, rel_path)
                #     
                #                                     # Update progress
                #                                     processed_files += 1
                #                                     self.progress = int((processed_files / total_files) * 100)
                #                                     self.current_processing_file = f"Zipping {dirname} - {processed_files}/{total_files} files"
                #                                     self.update_file_tracking_panes()
                #     
                #                                 except PermissionError as e:
                #                                     print(f"Permission error accessing file {file_full_path}: {str(e)}")
                #                                     continue
                #                                 except Exception as e:
                #                                     print(f"Error processing file {file_full_path}: {str(e)}")
                #                                     continue
                #     
                #     print(f"Successfully created zip file: {zip_path}")
                #     # Use the zip file for further processing
                #     dir_path = zip_path
                #     dirname = zip_filename
                #     file_title = os.path.splitext(dirname)[0]
                #     
                #     # Add zip file to cleanup tracking
                #     self.add_to_zip_zip_cleanup_log(zip_path)
                #     
                #     # Reset progress for next stage
                #     self.progress = 0
                #     self.current_processing_file = f"Uploading {dirname}"
                #         self.update_file_tracking_panes()
                #     
                # except PermissionError as e:
                #     error_msg = f"Permission error: Cannot create zip file. Please check permissions for: {temp_zips_dir}"
                #     print(error_msg)
                #         self.record_output_pane.object = f"<h3>{error_msg}</h3>"
                #         return False
                # except Exception as e:
                #     error_msg = f"Error creating zip file: {str(e)}"
                #     print(error_msg)
                #         self.record_output_pane.object = f"<h3>{error_msg}</h3>"
                #         return False
                
                # Process directory directly without zipping
                print(f"Processing directory directly: {dir_path}")
                self.processing_status = f"Processing directory: {dirname}"
                self.current_processing_file = f"Processing {dirname}"
                self.update_file_tracking_panes()
            
            # Try to extract metadata if possible, otherwise use basic file info
            try:
                metadata = get_file_metadata(dir_path)
                print(f"Successfully extracted metadata for {dirname}")
            except Exception as e:
                print(f"Could not extract specialized metadata: {str(e)}")
                # Create basic metadata with file stats
                try:
                    file_stat = os.stat(dir_path)
                    metadata = {
                        "filename": dirname,
                        "filesize": file_stat.st_size,
                        "modified_time": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        "created_time": datetime.datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        "file_type": os.path.splitext(dirname)[1],
                        "error": str(e)
                    }
                    print(f"Created basic metadata for {dirname}")
                except PermissionError as e:
                    error_msg = f"Permission error: Cannot access file metadata. Please check permissions for: {dir_path}"
                    print(error_msg)
                    self.record_output_pane.object = f"<h3>{error_msg}</h3>"
                    return False
                except Exception as e:
                    error_msg = f"Error accessing file metadata: {str(e)}"
                    print(error_msg)
                    self.record_output_pane.object = f"<h3>{error_msg}</h3>"
                    return False
                
            # Set the context
            if self.selected_context:
                self.df_api.setContext(self.selected_context)
                print(f"Using context: {self.selected_context}")
                
            # Create record
            print(f"Creating DataFed record for {dirname}")
            response = self.df_api.dataCreate(
                title=file_title,
                metadata=json.dumps(metadata),
                parent_id=self.available_collections[self.selected_collection]
            )
            
            record_id = response[0].data[0].id
            self.task_id = record_id
            print(f"Created record with ID: {record_id}")
            
            # Put data
            print(f"Uploading file to DataFed: {dir_path}")
            try:
                res = self.df_api.dataPut(
                    data_id=record_id,
                    wait=False,
                    path=dir_path
                )
                print(f"res: {res}")
                self.record_output_pane.object = f"<h3>Success: Record created with ID {record_id}</h3>"
                print(f"File upload initiated for {dirname} with record {record_id}")
            except PermissionError as e:
                error_msg = f"Permission error: Cannot upload file to DataFed. Please check permissions for: {dir_path}"
                print(error_msg)
                self.record_output_pane.object = f"<h3>{error_msg}</h3>"
                return False
            except Exception as e:
                error_msg = f"Error uploading file to DataFed: {str(e)}"
                print(error_msg)
                self.record_output_pane.object = f"<h3>{error_msg}</h3>"
                return False
            
            return True
            
        except Exception as e:
            error_msg = f"Error processing directory {dir_path}: {str(e)}"
            print(error_msg)
            self.record_output_pane.object = f"<h3>{error_msg}</h3>"
            return False

    # ZIP CLEANUP METHODS COMMENTED OUT - No longer creating zip files
    # def add_to_zip_cleanup_log(self, zip_path):
    #     """Add a zip file to the cleanup tracking log"""
    #     # Use current auto-processing directory for cleanup log
    #     base_dir = self.file_path if hasattr(self, 'file_path') and self.file_path else FILE_PATH
    #     cleanup_log_path = os.path.join(base_dir, "zip_cleanup_log.json")
    #     try:
    #         # Create or load the cleanup log
    #         if os.path.exists(cleanup_log_path):
    #         with open(cleanup_log_path, 'r') as f:
    #             cleanup_data = json.load(f)
    #         else:
    #             cleanup_data = {"zip_files": {}}
    #         
    #         # Add the zip file with current timestamp
    #         cleanup_data["zip_files"][zip_path] = datetime.datetime.now().isoformat()
    #         
    #         # Save the updated log
    #         with open(cleanup_log_path, 'w') as f:
    #             json.dump(cleanup_data, f, indent=2)
    #             
    #     except Exception as e:
    #         print(f"Error updating zip cleanup log: {str(e)}")
    # 
    # def cleanup_old_zip_files(self):
    #     """Clean up zip files that are older than 2 hours"""
    #     # Use current auto-processing directory for cleanup
    #     base_dir = self.file_path if hasattr(self, 'file_path') and self.file_path else FILE_PATH
    #     if not base_dir:
    #         print("No valid directory for cleanup")
    #         return
    #             
    #         cleanup_log_path = os.path.join(base_dir, "zip_cleanup_log.json")
    #         if not os.path.exists(cleanup_log_path):
    #             return
    #             
    #         try:
    #             with open(cleanup_path, 'r') as f:
    #                 cleanup_data = json.load(f)
    #             
    #             current_time = datetime.datetime.now()
    #             files_to_remove = []
    #             
    #             # Check each zip file
    #             for zip_path, timestamp_str in cleanup_data["zip_files"].items():
    #                 timestamp = datetime.datetime.fromisoformat(timestamp_str)
    #                 age = current_time - timestamp
    #                 
    #                 # If file is older than 2 hours
    #                 if age.total_seconds() > 7200:  # 2 hours in seconds
    #                     if os.path.exists(zip_path):
    #                         try:
    #                             os.remove(zip_path)
    #                             print(f"Cleaned up old zip file: {zip_path}")
    #                             files_to_remove.append(zip_path)
    #                         except Exception as e:
    #                             print(f"Error removing zip file {zip_path}: {str(e)}")
    #                     else:
    #                         files_to_remove.append(zip_path)
    #             
    #             # Remove cleaned up files from the log
    #             for zip_path in files_to_remove:
    #                 del cleanup_data["zip_files"][zip_path]
    #             
    #             # Save the updated log
    #             with open(cleanup_log_path, 'w') as f:
    #                 json.dump(cleanup_data, f, indent=2)
    #                 
    #         except Exception as e:
    #             print(f"Error in zip cleanup process: {str(e)}")

    def get_processed_files(self):
        """Get the list of already processed files from the log"""
        # Use current auto-processing directory for log file
        base_dir = self.file_path if hasattr(self, 'file_path') and self.file_path else FILE_PATH
        if not base_dir:
            print("No valid directory for log file")
            return []
            
        log_path = os.path.join(base_dir, self.log_file)
        try:
            with open(log_path, 'r') as f:
                log_data = json.load(f)
                return log_data.get("processed_dirs", [])
        except (json.JSONDecodeError, FileNotFoundError):
            # If the file doesn't exist or is invalid, create a new one
            with open(log_path, 'w') as f:
                json.dump({"processed_dirs": []}, f)
            return []
            
    def add_to_processed_log(self, dirname):
        """Add a processed directory to the log"""
        # Use current auto-processing directory for log file
        base_dir = self.file_path if hasattr(self, 'file_path') and self.file_path else FILE_PATH
        if not base_dir:
            print("No valid directory for log file")
            return
            
        log_path = os.path.join(base_dir, self.log_file)
        try:
            with open(log_path, 'r') as f:
                log_data = json.load(f)
                
            if dirname not in log_data["processed_dirs"]:
                log_data["processed_dirs"].append(dirname)
                
            # Add timestamp
            if "timestamps" not in log_data:
                log_data["timestamps"] = {}
                    
            log_data["timestamps"][dirname] = datetime.datetime.now().isoformat()
            
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"Error updating log file: {str(e)}")

    def process_new_data(self):
        """Process new data files in directories"""
        # Use the current auto-processing directory
        base_dir = self.file_path if hasattr(self, 'file_path') and self.file_path else FILE_PATH
        print(f"Base directory: {base_dir}")
        
        try:
            # Check if base directory is valid
            if not base_dir or not os.path.exists(base_dir) or not os.path.isdir(base_dir):
                print(f"Invalid base directory: {base_dir}")
                self.processing_status = f"Error: Invalid base directory {base_dir}"
                return
            
            # Create log file if it doesn't exist
            log_path = os.path.join(base_dir, self.log_file)
            print(f"Log path: {log_path}")
            
            # Make sure the directory exists
            log_dir = os.path.dirname(log_path)
            if not os.path.exists(log_dir):
                print(f"Creating log directory: {log_dir}")
                os.makedirs(log_dir, exist_ok=True)
                
            if not os.path.exists(log_path):
                print(f"Creating new log file at {log_path}")
                with open(log_path, 'w') as f:
                    json.dump({"processed_dirs": []}, f)
                print(f"Created new log file at {log_path}")
                
            while self.auto_processing:
                # Get the current directory at the start of each cycle
                current_base_dir = self.file_path if hasattr(self, 'file_path') and self.file_path else FILE_PATH
                if current_base_dir != base_dir:
                    base_dir = current_base_dir
                    print(f"Directory changed during processing, now using: {base_dir}")
                
                # ZIP CLEANUP COMMENTED OUT - No longer creating zip files
                # self.cleanup_old_zip_files()
                
                # Read the log file to get processed directories
                processed_dirs = self.get_processed_files()
                self.processed_files_list = processed_dirs
                print(f"Found {len(processed_dirs)} previously processed directories in log")
                
                # Get all directories and files in the base directory
                all_items = []
                
                # First, add files in the current directory
                current_files = []
                try:
                    for item in os.listdir(base_dir):
                        item_path = os.path.join(base_dir, item)
                        if os.path.isfile(item_path):
                            # Skip temp files and logs
                            if not item.startswith('.') and not item.endswith('.tmp') and not item.endswith('.log'):
                                current_files.append(item_path)
                except Exception as e:
                    print(f"Error reading current directory: {e}")
                
                # Then add subdirectories
                all_dirs = []
                for root, dirs, files in os.walk(base_dir):
                    # Skip $RECYCLE.BIN directory and temp_zips directory
                    if os.path.basename(root) in ["$RECYCLE.BIN", "temp_zips"]:
                        print(f"Skipping directory: {root}")
                        continue
                    
                    # Add the current directory if it's not the base directory itself
                    if root != base_dir:
                        all_dirs.append(root)
                
                # Combine files and directories
                all_items = current_files + all_dirs
                
                print(f"Found {len(current_files)} files and {len(all_dirs)} directories to process")
                print(f"Total items to process: {len(all_items)}")
                
                # Filter out already processed items
                new_items = [item for item in all_items if os.path.basename(item) not in processed_dirs]
                self.unprocessed_files_list = [os.path.basename(item) for item in new_items]
                
                print(f"Found {len(new_items)} new unprocessed items")
                for item in new_items[:5]:  # Print up to 5 examples
                    print(f"  - {item}")
                if len(new_items) > 5:
                    print(f"  - ... and {len(new_items) - 5} more")
                
                if new_items:
                    self.processing_status = f"Found {len(new_items)} new items to process"
                    self.total_files = len(new_items)
                    self.progress = 0
                    
                    for idx, item_path in enumerate(new_items):
                        if not self.auto_processing:
                            break
                            
                        itemname = os.path.basename(item_path)
                        self.current_file = itemname
                        self.current_processing_file = itemname
                        
                        # Check if it's a file or directory
                        if os.path.isfile(item_path):
                            self.processing_status = f"Processing file {itemname}"
                            print(f"Processing file {idx+1}/{len(new_items)}: {itemname}")
                        else:
                            self.processing_status = f"Processing directory {itemname}"
                            print(f"Processing directory {idx+1}/{len(new_items)}: {itemname}")
                        
                        self.progress = int((idx / self.total_files) * 100)
                        
                        # Update the file tracking panes
                        self.update_file_tracking_panes()
                        
                        # Process the item (file or directory)
                        success = self.process_single_file(item_path)
                        
                        if success:
                            print(f"Successfully processed: {itemname}")
                            # Add to processed items log
                            self.add_to_processed_log(itemname)
                            # Update processed items list
                            self.processed_files_list.append(itemname)
                            # Remove from unprocessed items list
                            if itemname in self.unprocessed_files_list:
                                self.unprocessed_files_list.remove(itemname)
                        else:
                            print(f"Failed to process: {itemname}")
                        
                        # Update the file tracking panes again
                        self.update_file_tracking_panes()
                        
                        # Small delay to prevent overwhelming the system
                        time.sleep(1)
                    
                    self.progress = 100
                    self.processing_status = "Processing complete"
                    self.current_processing_file = ""
                    print("Completed processing batch of items")
                else:
                    self.processing_status = "No new items found"
                    print("No new items found in this scan")
                
                # Update the file tracking panes one last time
                self.update_file_tracking_panes()
                
                # Wait before checking again
                print(f"Waiting 5 seconds before next scan...")
                time.sleep(5)
                
        except Exception as e:
            error_msg = f"Error in process_new_data: {str(e)}"
            print(error_msg)
            self.processing_status = f"Error: {str(e)}"
            self.auto_processing = False
            self.start_auto_button.disabled = False
            self.stop_auto_button.disabled = True

    # Removed update_auto_processing_directory method - no longer needed

    def change_auto_processing_directory(self, new_directory):
        """Change the auto-processing directory"""
        if os.path.exists(new_directory) and os.path.isdir(new_directory):
            old_path = getattr(self, 'file_path', 'Not set')
            self.file_path = new_directory
            print(f"Auto-processing directory changed from '{old_path}' to: {new_directory}")
            # Update the file selector as well
            self.file_selector.directory = new_directory
            # Update the auto-processing directory selector to show current directory
            self.auto_processing_dir_selector.directory = new_directory
        else:
            print(f"Invalid directory: {new_directory}")

    def get_current_directory_display(self):
        """Get the current directory for display purposes"""
        return self.file_path if hasattr(self, 'file_path') else FILE_PATH

    def validate_and_change_directory(self, new_directory):
        """Validate and change the directory if valid"""
        if os.path.exists(new_directory) and os.path.isdir(new_directory):
            self.change_auto_processing_directory(new_directory)
            return True
        else:
            print(f"Directory validation failed: {new_directory}")
            return False
    

    
    def on_directory_changed(self, event):
        """Handle directory changes in the auto-processing directory selector"""
        if event.new:
            new_dir = event.new
            print(f"Directory changed to: {new_dir}")
            print(f"Previous file_path was: {getattr(self, 'file_path', 'Not set')}")
            
            if os.path.exists(new_dir) and os.path.isdir(new_dir):
                self.change_auto_processing_directory(new_dir)
                print(f"Successfully updated file_path to: {self.file_path}")
            else:
                print(f"Invalid directory: {new_dir}")
                # Revert to previous valid directory
                if hasattr(self, 'file_path') and self.file_path:
                    self.auto_processing_dir_selector.directory = self.file_path
    
    def update_directory_selector_display(self):
        """Update the directory selector to show the current auto-processing directory"""
        if hasattr(self, 'file_path') and self.file_path:
            self.auto_processing_dir_selector.directory = self.file_path
            print(f"Updated directory selector to show: {self.file_path}")
    
    def sync_file_selector_with_auto_processing_dir(self, event=None):
        """Sync the main file selector with the current auto-processing directory"""
        if hasattr(self, 'file_path') and self.file_path:
            self.file_selector.directory = self.file_path
            print(f"Synced file selector with auto-processing directory: {self.file_path}")
    
    def get_auto_processing_directory_info(self):
        """Get information about the current auto-processing directory"""
        if hasattr(self, 'file_path') and self.file_path:
            try:
                if os.path.exists(self.file_path):
                    files = [f for f in os.listdir(self.file_path) if os.path.isfile(os.path.join(self.file_path, f))]
                    dirs = [f for f in os.listdir(self.file_path) if os.path.isdir(os.path.join(self.file_path, f))]
                    total_size = sum(os.path.getsize(os.path.join(self.file_path, f)) for f in files)
                    return {
                        'path': self.file_path,
                        'file_count': len(files),
                        'dir_count': len(dirs),
                        'total_size': total_size,
                        'exists': True
                    }
                else:
                    return {'path': self.file_path, 'exists': False}
            except Exception as e:
                return {'path': self.file_path, 'error': str(e)}
        return {'path': None, 'exists': False}
    
    def go_to_parent_directory(self, event=None):
        """Navigate to the parent directory"""
        if hasattr(self, 'file_path') and self.file_path:
            parent_dir = os.path.dirname(self.file_path)
            if parent_dir and parent_dir != self.file_path:
                self.change_auto_processing_directory(parent_dir)
                print(f"Navigated to parent directory: {parent_dir}")
            else:
                print("Already at root directory")
        else:
            print("No directory path set")
    
    def go_to_home_directory(self, event=None):
        """Navigate to the user's home directory"""
        home_dir = os.path.expanduser("~")
        if os.path.exists(home_dir) and os.path.isdir(home_dir):
            self.change_auto_processing_directory(home_dir)
            print(f"Navigated to home directory: {home_dir}")
        else:
            print(f"Home directory not accessible: {home_dir}")
    
    def get_breadcrumb_display(self):
        """Get a breadcrumb display of the current path"""
        if not hasattr(self, 'file_path') or not self.file_path:
            return "No path set"
        
        try:
            # Split the path into components
            path_parts = self.file_path.split(os.sep)
            if path_parts[0] == '':
                path_parts[0] = '/'
            
            # Create clickable breadcrumb
            breadcrumb_parts = []
            current_path = ""
            
            for i, part in enumerate(path_parts):
                if part == '/':
                    current_path = '/'
                else:
                    current_path = os.path.join(current_path, part) if current_path else part
                
                if i == 0:
                    breadcrumb_parts.append(f"`{part}`")
                else:
                    breadcrumb_parts.append(f"`{part}`")
            
            return " / ".join(breadcrumb_parts)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _ensure_valid_directory(self):
        """Ensure we have a valid directory path, fallback to user's home if needed"""
        if not hasattr(self, 'file_path') or not self.file_path:
            # Try to set a sensible default
            home_dir = os.path.expanduser("~")
            if os.path.exists(home_dir) and os.path.isdir(home_dir):
                self.file_path = home_dir
                print(f"Set default directory to user home: {home_dir}")
            else:
                # Fallback to current working directory
                self.file_path = os.getcwd()
                print(f"Set default directory to current working directory: {self.file_path}")
        elif not os.path.exists(self.file_path) or not os.path.isdir(self.file_path):
            # Current path is invalid, try to find a valid one
            home_dir = os.path.expanduser("~")
            if os.path.exists(home_dir) and os.path.isdir(home_dir):
                self.file_path = home_dir
                print(f"Invalid directory path, set to user home: {home_dir}")
            else:
                self.file_path = os.getcwd()
                print(f"Invalid directory path, set to current working directory: {self.file_path}")
    
    def get_auto_processing_files_count(self):
        """Get the count of files in the auto-processing directory"""
        try:
            if hasattr(self, 'file_path') and os.path.exists(self.file_path):
                files = [f for f in os.listdir(self.file_path) if os.path.isfile(os.path.join(self.file_path, f))]
                return len(files)
            return 0
        except Exception:
            return 0
