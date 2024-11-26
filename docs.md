# Calendar Application Routes

## **Authentication**
### `/signup` (GET)  
- **Shows**: A registration form.  
- **Actions**: Register as a new user.  
- **Elements**:  
  - Input fields: username, email, password.  
  - Submit button.  

### `/signup` (POST)  
- **Processes**: Registration form submission. Creates a new user in the database.  

### `/signin` (GET)  
- **Shows**: A login form.  
- **Actions**: Log in to the app.  
- **Elements**:  
  - Input fields: email, password.  
  - Submit button.  

### `/signin` (POST)  
- **Processes**: Login form submission. Authenticates the user.  

### `/logout` (POST)  
- **Processes**: Logs the user out.  

---

## **Calendar**
### `/calendar` (GET)  
- **Shows**: A calendar with tasks and deadlines.  
- **Actions**:  
  - View tasks and deadlines.  
  - Navigate between months.  
- **Elements**:  
  - Calendar grid.  
  - Navigation buttons (previous/next month).  

### `/calendar/add` (GET)  
- **Shows**: A form for adding a custom task.  
- **Actions**: Add a new task to the calendar.  
- **Elements**:  
  - Input fields: task title, date, description.  
  - Submit button.  

### `/calendar/add` (POST)  
- **Processes**: Form submission to add a custom task.  

### `/calendar/task/<id>` (GET)  
- **Shows**: Details of a specific task.  
- **Actions**: Edit or delete the task.  
- **Elements**:  
  - Buttons: "Edit Task," "Delete Task."  

### `/calendar/task/<id>/edit` (GET)  
- **Shows**: A form for editing task details.  
- **Actions**: Modify task details.  
- **Elements**:  
  - Pre-filled input fields: task title, date, description.  
  - Submit button.  

### `/calendar/task/<id>/edit` (POST)  
- **Processes**: Updates the task with the edited details.  

### `/calendar/task/<id>/delete` (POST)  
- **Processes**: Deletes the selected task.  

---

## **Integration**
### `/integrations/cogniterra` (GET)  
- **Shows**: Button to authorize Cogniterra.  
- **Actions**: Start the Cogniterra authorization process.  
- **Elements**: "Authorize with Cogniterra" button.  

### `/integrations/github` (GET)  
- **Shows**: Button to authorize GitHub Classroom.  
- **Actions**: Start the GitHub authorization process.  
- **Elements**: "Authorize with GitHub" button.  

### `/integrations/cogniterra/callback` (POST)  
- **Processes**: Callback from Cogniterra API to fetch deadlines.  

### `/integrations/github/callback` (POST)  
- **Processes**: Callback from GitHub API to fetch assignments.  
