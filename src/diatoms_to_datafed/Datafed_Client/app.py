import panel as pn
from datafed_app import DataFedApp

app = DataFedApp()
app.login_button.button_type = 'success'
app.logout_button.button_type = 'danger'
app.update_button.button_type = 'primary'
app.login_button.icon = 'sign-in'
app.logout_button.icon = 'sign-out'
app.update_button.icon = 'edit'
app.start_auto_button.icon = 'play'
app.stop_auto_button.icon = 'stop'


@pn.depends(app.param.current_user)
def login_logout_button(current_user):
    if current_user == "Not Logged In":
        return app.login_button  # Show login button if not logged in
    else:
        return app.logout_button  # Show logout button if logged in
@pn.depends(app.metadata_json_editor.param.value)
def update_button_visibility(metadata_json_editor_value):
    if metadata_json_editor_value:  # If there's content in the editor
        return app.update_button  # Show the update button
    else:
        return pn.pane.Markdown("") 
    
def on_update_button_click(event):
    app.update_record()
    pn.state.notifications.success('Record updated successfully!', duration=2000)

app.update_button.on_click(on_update_button_click)
# Define the header
header = pn.Row(
    pn.layout.HSpacer(),
    pn.pane.Markdown("**User:**"    ),
    pn.bind(lambda current_user: pn.pane.Markdown(f"**{current_user}**"), app.param.current_user),
    pn.layout.Spacer(width=20),
    app.logout_button,
    pn.layout.Spacer(width=20),
    pn.layout.HSpacer()
)
@pn.depends(app.param.record_alert_message)
def record_alert(record_alert_message):
    return pn.Column(
        pn.pane.Markdown(f"### {record_alert_message}"),
        pn.widgets.Button(name='Close', button_type='danger', on_click=lambda event: app.clear_alert_message())
    ) if record_alert_message else None

# Define the login pane
login_pane = pn.Column(
    pn.Param(app.param.username),
    pn.Param(app.param.password, widgets={'password': pn.widgets.PasswordInput}),
    pn.widgets.Button(name='Submit Login', button_type='primary', on_click=app.check_login),
    pn.Param(app.param.login_status),
)

# Automated processing panel
@pn.depends(app.param.progress, app.param.processing_status, app.param.current_file, app.param.task_id)
def auto_processing_panel(progress, status, current_file, task_id):
    # Update progress bar value directly from the parameter
    progress_bar = pn.widgets.Progress(name="Progress", value=progress, width=400)
    
    return pn.Column(
        pn.pane.Markdown("## Automated Data Processing"),
        pn.Row(app.start_auto_button, app.stop_auto_button),
        pn.Row(
            pn.Column(
                pn.pane.Markdown(f"**Status:** {status}"),
                pn.pane.Markdown(f"**Current File:** {current_file}"),
                pn.pane.Markdown(f"**Task ID:** {task_id}"),
                progress_bar,
                pn.pane.Markdown(f"**Progress:** {progress}%"),
            )
        ),
        pn.Row(app.record_output_pane)
    )

# Define the record management pane
record_pane = pn.Column(
    pn.Param(app.param.selected_context, widgets={'selected_context': pn.widgets.Select}),
    pn.Param(app.param.selected_collection, widgets={'selected_collection': pn.widgets.Select}),
    pn.Tabs(
        ("Create Record", pn.Column(
            pn.Row(pn.Param(app.param.title), app.file_selector, app.metadata_json_editor),  # Updated here
            app.create_button, 
            app.record_output_pane
        )),
        ("Read Record", pn.Column(pn.Param(app.param.record_id), pn.Column(app.read_button,app.update_button,app.delete_button,), app.record_output_pane,app.metadata_json_editor)),
        ("Auto Processing", auto_processing_panel)
        )
)

# conflict commit ("Transfer Data", pn.Column(pn.Param(app.param.source_id), pn.Param(app.param.dest_collection), app.transfer_button, app.record_output_pane)),
# Dynamically show the login pane or the record management pane based on login status
@pn.depends(app.param.current_user)
def main_content(current_user):
    if current_user == "Not Logged In":
        return login_pane
    else:
        return record_pane


# Use MaterialTemplate for the layout
# Add this CSS at the beginning of app.py
pn.config.raw_css.append("""
body {
    background-color: white;
}
.bk-btn {
    # position: fixed;
    z-index: 1000;
}
select {
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    padding: 8px;
    border-radius: 4px;
    font-size: 14px;
}
.bk-btn-primary {
    background-color: #007bff;
    color: white;
}
.pn-loading-spinner {
    display: none !important;
}
.
""")
# Append CSS to make buttons float

# Apply custom CSS to the template
template = pn.template.BootstrapTemplate(title='DataFed Management', theme='default')

template.header.append(header)
template.main.append(main_content)  # Append the main content function directly
template.modal.append(record_alert)

# Conditionally show the login pane as a modal
template.modal.append(pn.bind(lambda show: login_pane if show else None, app.param.show_login_panel))

pn.state.onload(lambda: app.toggle_login_panel(None))  # Ensure modal can be triggered

template.servable()
